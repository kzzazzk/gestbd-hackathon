import io
import requests
import json
import psycopg2
from PyPDF2 import PdfReader
import subprocess

DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "database": "demoDB",
    "user": "userPSQL",
    "password": "passPSQL"
}

MODEL_NAME = "mistral:instruct"

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

def get_text_from_pdf_url(pdf_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(pdf_url, headers=headers, timeout=15)
        response.raise_for_status()
        reader = PdfReader(io.BytesIO(response.content))
        text = "".join(page.extract_text() + "\n\n" for page in reader.pages if page.extract_text())
        return text
    except Exception as e:
        print(f"Error fetching/reading PDF: {e}")
        return None

def analyze_text(instructions, pdf_text):
    prompt = f"{instructions}\n\nText:\n{pdf_text}"
    try:
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME],
            input=prompt,
            capture_output=True,
            text=True
        )
        raw_output = result.stdout.strip()
        json_start = raw_output.find("{")
        json_end = raw_output.rfind("}") + 1
        return json.loads(raw_output[json_start:json_end])
    except Exception as e:
        print(f"Error running Ollama: {e}")
        return {"programming_languages": []}

def process_json(result_dict):
    return result_dict.get('programming_languages', [])

def insert_technologies_for_obra(conn, obra_id, languages_list):
    get_or_create_sql = """
    WITH inserted AS (
        INSERT INTO tecnologia (nombre)
        VALUES (%s)
        ON CONFLICT (nombre) DO NOTHING
        RETURNING id
    )
    SELECT id FROM inserted
    UNION
    SELECT id FROM tecnologia WHERE nombre = %s;
    """
    insert_link_sql = """
    INSERT INTO obra_tecnologia (obra_id, tecnologia_id)
    VALUES (%s, %s)
    ON CONFLICT (obra_id, tecnologia_id) DO NOTHING;
    """
    with conn.cursor() as cur:
        for lang in languages_list:
            cur.execute(get_or_create_sql, (lang, lang))
            tecnologia_id = cur.fetchone()[0]
            cur.execute(insert_link_sql, (obra_id, tecnologia_id))
            print(f"Linked Obra ID {obra_id} -> Tecnologia ID {tecnologia_id} ('{lang}')")

def process_all_obras():
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = False
        with conn.cursor() as read_cur:
            read_cur.execute("SELECT id, direccion_fuente FROM obra")
            obras = read_cur.fetchall()
        print(f"Found {len(obras)} obras to process.")

        for obra_id, pdf_url in obras:
            print(f"\nProcessing Obra ID: {obra_id}")
            try:
                text = get_text_from_pdf_url(pdf_url)
                if not text:
                    print(f"No text extracted. Skipping Obra ID: {obra_id}")
                    continue
                analysis_result = analyze_text(instructions, text)
                languages_list = process_json(analysis_result)
                if languages_list:
                    insert_technologies_for_obra(conn, obra_id, languages_list)
                conn.commit()
                print(f"Successfully processed Obra ID: {obra_id}")
            except Exception as e:
                print(f"Error processing Obra ID {obra_id}: {e}")
                conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    process_all_obras()
