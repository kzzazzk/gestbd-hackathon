import csv
import os
import io
import requests
import json
import openai
import subprocess
from bs4 import BeautifulSoup
import fitz 


MODEL_NAME = "mistral:instruct"
PDF_TIMEOUT = 30
UNPAYWALL_EMAIL = "your_email@example.com"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
OBRAS_CSV = os.path.join(CACHE_DIR, "obra.csv")
TECN_CSV = os.path.join(CACHE_DIR, "tecnologia.csv")
OBRA_TECN_CSV = os.path.join(CACHE_DIR, "obra_tecnologia.csv")


instructions = """You are a text analysis assistant specialized in identifying programming languages mentioned in academic or technical articles.
Analyze the provided raw text (extracted directly from a PDF). Identify and return the main programming languages mentioned in the article (do not include frameworks, libraries, or tools).
If a “References” or “Bibliography” section appears, ignore all text after that marker.
Return strictly in JSON, like:
{
  "programming_languages": ["Python", "C", "Java"]
}
If none found:
{
  "programming_languages": []
}
"""

os.makedirs(CACHE_DIR, exist_ok=True)

# ----------------------
# CSV helpers
# ----------------------
def read_obras_from_csv(file_path):
    obras = []
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obras.append((int(row["id"]), row["direccion_fuente"], row.get("doi")))
    return obras

def init_csv(file_path, headers=None):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
        return 1
    max_id = 0
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        try:
            reader = csv.DictReader(f)
            for row in reader:
                val = row.get("id")
                if val:
                    try:
                        max_id = max(max_id, int(val))
                    except:
                        continue
        except:
            f.seek(0)
            for line in f:
                parts = line.split(",")
                if parts:
                    try:
                        max_id = max(max_id, int(parts[0].strip()))
                    except:
                        continue
    return max_id + 1

def append_unique_to_csv(file_path, row, headers=None, key_index=1):
    init_csv(file_path, headers=headers)
    existing_keys = set()
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        peek = next(reader, None)
        if headers and peek and all(h in peek for h in headers):
            pass
        else:
            if peek:
                try:
                    existing_keys.add(peek[key_index])
                except:
                    pass
        for r in reader:
            try:
                existing_keys.add(r[key_index])
            except:
                continue
    key = row[key_index] if len(row) > key_index else None
    if key not in existing_keys:
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)



def append_to_csv(file_path, row, headers=None):
    """Simple append without uniqueness (for obra_tecnologia)"""
    file_exists = os.path.exists(file_path)
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists and headers:
            writer.writerow(headers)
        writer.writerow(row)
def load_tecnologias(file_path):
    tech_map = {}
    if os.path.exists(file_path):
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tech_map[row["nombre"]] = int(row["id"])
    return tech_map

# ----------------------
# PDF + Analysis
# ----------------------
def get_text_from_pdf_url(pdf_url, doi=None):
    tried_urls = set()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    def fetch_unpaywall_pdf(doi):
        if not doi:
            return None
        try:
            unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
            r = requests.get(unpaywall_url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                pdf_link = data.get("best_oa_location", {}).get("url_for_pdf")
                if pdf_link:
                    print(f"📖 Found Unpaywall PDF: {pdf_link}")
                    return pdf_link
        except Exception as e:
            print(f"⚠️ Unpaywall fetch failed: {e}")
        return None


def get_text_from_pdf_url(pdf_url, doi=None):
    tried_urls = set()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    def fetch_unpaywall_pdf(doi):
        if not doi:
            return None
        try:
            unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
            r = requests.get(unpaywall_url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                pdf_link = data.get("best_oa_location", {}).get("url_for_pdf")
                if pdf_link:
                    print(f"📖 Found Unpaywall PDF: {pdf_link}")
                    return pdf_link
        except Exception as e:
            print(f"⚠️ Unpaywall fetch failed: {e}")
        return None

    def fetch_acm_pdf(doi):
        if not doi:
            return None
        try:
            acm_url = f"https://dl.acm.org/doi/pdf/{doi}"
            r = requests.head(acm_url, allow_redirects=True, timeout=10)
            if r.status_code == 200 and "pdf" in r.headers.get("Content-Type", "").lower():
                print(f"📄 Found ACM PDF: {acm_url}")
                return acm_url
        except Exception as e:
            print(f"⚠️ ACM fetch failed: {e}")
        return None

    while pdf_url and pdf_url not in tried_urls:
        tried_urls.add(pdf_url)
        try:
            response = requests.get(pdf_url, headers=headers, timeout=PDF_TIMEOUT)
            content_type = response.headers.get("Content-Type", "").lower()

            if "application/pdf" in content_type:
                try:
                    pdf_bytes = io.BytesIO(response.content)
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    text = "\n\n".join([page.get_text() for page in doc])
                    if not text.strip():
                        raise ValueError("No text extracted from PDF")
                    return text.strip(), pdf_url
                except Exception as e:
                    print(f"⚠️ PDF parse error with PyMuPDF: {e}")
                pdf_url = fetch_unpaywall_pdf(doi) or fetch_acm_pdf(doi)
                continue

            if "text/html" in content_type:
                soup = BeautifulSoup(response.text, "html.parser")
                body_text = soup.get_text(separator=' ', strip=True).lower()
                if any(x in body_text for x in ["not found", "error 404", "no encontrado", "access denied"]):
                    pdf_url = fetch_unpaywall_pdf(doi) or fetch_acm_pdf(doi)
                    continue
                text_labels = soup.select('[class*="textLayer"], [id*="textLayer"] div, span')
                texts = [el.get_text(separator=' ', strip=True) for el in text_labels]
                if texts:
                    return " ".join(texts), pdf_url
                pdf_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.pdf')]
                if pdf_links:
                    next_pdf = requests.compat.urljoin(pdf_url, pdf_links[0])
                    if next_pdf not in tried_urls:
                        pdf_url = next_pdf
                        continue
                pdf_url = fetch_unpaywall_pdf(doi) or fetch_acm_pdf(doi)
                continue

            pdf_url = fetch_unpaywall_pdf(doi) or fetch_acm_pdf(doi)

        except Exception as e:
            print(f"⚠️ Exception while fetching PDF: {e}")
            pdf_url = fetch_unpaywall_pdf(doi) or fetch_acm_pdf(doi)

    print("❌ No valid PDF or text found.")
    return None, None



def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a string for GPT models."""
    return len(ENCODING.encode(text))

def analyze_text(instructions, pdf_text):
    detected_languages = set()

    # 1️⃣ Try LLM first
    if pdf_text.strip():
        prompt = f"{instructions}\n\nText:\n{pdf_text}"
        try:
            result = subprocess.run(
                ["ollama", "run", MODEL_NAME],
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            raw = result.stdout.strip()
            json_start = raw.find("{")
            json_end = raw.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                llm_result = json.loads(raw[json_start:json_end])
                detected_languages.update(llm_result.get("programming_languages", []))
        except Exception:
            pass

    return {"programming_languages": sorted(detected_languages)}

# Make sure to set your API key in the environment
# export OPENAI_API_KEY="sk-..."
def analyze_text_with_gpt(pdf_text, model="gpt-5-nano"):
    """
    Analyze PDF text using ChatGPT Responses API.
    Returns a set of detected programming languages.
    Automatically skips blocked content.
    """
    detected_languages = set()

    # Blocked content check
    blocked_indicators = [
        "enable javascript and cookies to continue",
        "access denied",
        "not found",
        "error 404"
    ]
    preview_text = pdf_text[:300].replace("\n", " ").lower()
    if any(b in preview_text for b in blocked_indicators):
        print("⚠️ Blocked content detected, skipping analysis.")
        return {"programming_languages": []}

    # GPT-5 request
    try:
        response = openai.responses.create(
            model=model,
            input=f"""
            You are a text analysis assistant specialized in identifying programming languages mentioned in academic or technical articles.

            Task:
            1️⃣ Identify **only actual programming languages** used to write code.
            2️⃣ Do **NOT** include frameworks, libraries, standards, formal languages, or platforms.
            3️⃣ Ignore any text after a “References” or “Bibliography” section.
            4️⃣ Return strictly in JSON:

            {{"programming_languages": ["Python", "C", "Java"]}}

            If none found, return:

            {{"programming_languages": []}}


            Text:
            {pdf_text}
"""
        )
        raw = response.output_text.strip()
        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1
        if json_start != -1 and json_end != -1:
            llm_result = json.loads(raw[json_start:json_end])
            detected_languages.update(llm_result.get("programming_languages", []))
    except Exception as e:
        print(f"⚠️ GPT analysis failed: {e}")

    return {"programming_languages": sorted(detected_languages)}

# ----------------------
# Main loop
# ----------------------
def process_all_obras():
    obras = read_obras_from_csv(OBRAS_CSV)
    print(f"Found {len(obras)} obras in CSV.")

    next_tecn_id = init_csv(TECN_CSV, headers=["id","nombre"])
    next_link_id = init_csv(OBRA_TECN_CSV, headers=["id","obra_id","tecnologia_id"])

    for obra_id, pdf_url, doi in obras:
        print(f"\n🔹 Processing Obra ID: {obra_id}")
        try:
            # Step 1: fetch PDF text
            text, final_url = get_text_from_pdf_url(pdf_url, doi)
            if not text:
                print(f"❌ No valid PDF or text found.")
                print(f"⚠️ Skipping Obra ID {obra_id}, no text extracted.")
                continue
            else:
                preview = text[:300].replace("\n", " ").strip()
                print(f"📄 Text extracted for Obra ID {obra_id} ({len(text)} chars)")
                print(f"🔗 Source URL used: {final_url}")
                print(f"📝 Text preview: {preview}{'...' if len(text) > 300 else ''}")

            # Step 2: analyze with Ollama
            print(f"🤖 Analyzing text for Obra ID {obra_id}...")
            try:
                result = analyze_text_with_gpt(text)
            except Exception as e:
                print(f"⚠️ Analysis failed for Obra ID {obra_id}: {e}")
                result = {"programming_languages": []}

            languages = result.get("programming_languages", [])
            print(f"📝 Obra ID {obra_id} languages detected: {languages}")

            tech_map = load_tecnologias(TECN_CSV)  # { "Python": 89, "C": 90, ... }

            for lang in languages:
                if lang not in tech_map:
                    tech_map[lang] = next_tecn_id
                    append_to_csv(TECN_CSV, [next_tecn_id, lang], headers=["id","nombre"])
                    next_tecn_id += 1

                tecnologia_id = tech_map[lang]
                append_to_csv(OBRA_TECN_CSV, [next_link_id, obra_id, tecnologia_id], headers=["id","obra_id","tecnologia_id"])
                next_link_id += 1

        except Exception as e:
            print(f"⚠️ Unexpected error processing Obra ID {obra_id}: {e}")


if __name__ == "__main__":
    #Uncomment if you are testing runs 
    """for csv_file in [TECN_CSV, OBRA_TECN_CSV]:
        if os.path.exists(csv_file):
            os.remove(csv_file)
            print(f"🗑️ Deleted old CSV: {csv_file}")"""
    process_all_obras()
