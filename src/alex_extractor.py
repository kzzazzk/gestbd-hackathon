import requests
import csv
import time
import os

BASE_URL = "https://api.openalex.org/works"
PER_PAGE = 200
KEYWORDS = [
    "python","c-programming-language","javascript","java","java-programming-language",
    "sql","dart","swift","cobol","fortran","matlab","prolog","lisp","haskell","rust","perl",
    "scala","html","html5"
]
SUBFIELD_ID = "subfields/1702"
LANGUAGE = "languages/en"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # go up one level from src/
CACHE_DIR = os.path.join(BASE_DIR, "cache")

CSV_OBRA = os.path.join(CACHE_DIR, "obra.csv")
CSV_TEMATICA = os.path.join(CACHE_DIR, "tematica.csv")
CSV_TEMATICA_CONTENIDA = os.path.join(CACHE_DIR, "tematica_contenida.csv")

os.makedirs(CACHE_DIR, exist_ok=True)

BASE_TOPICS = ["Physical Sciences", "Computer Science", "Artificial Intelligence"]

def reconstruct_abstract(abstract_inverted_index):
    if not abstract_inverted_index or not isinstance(abstract_inverted_index, dict):
        return ""
    position_map = {}
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            position_map[pos] = word
    return " ".join(position_map[pos] for pos in sorted(position_map.keys()))

def fetch_page(url, params, max_retries=5, delay_base=2):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            print(f"⚠️ Warning: Bad response {response.status_code}, retrying...")
        except Exception as e:
            print(f"⚠️ Warning: Exception during request: {e}")
        retries += 1
        time.sleep(delay_base ** retries)
    print(f"❌ Error: Failed to fetch page after {max_retries} retries.")
    return None

def initialize_csv_files():
    os.makedirs(os.path.dirname(CSV_OBRA), exist_ok=True)
    with open(CSV_OBRA, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "id","direccion_fuente","titulo","abstract","fecha_publicacion",
            "idioma","num_citas","fwci","tematica_id","doi"
        ])
    print(f"Initialized '{CSV_OBRA}' for writing works.")

def fetch_all_works():
    tematica_map = {}
    next_tematica_id = 1
    obra_id = 1
    page = 1
    total_results = None

    while True:
        params = {
            "page": page,
            "per_page": PER_PAGE,
            "filter": f"open_access.is_oa:true,has_content.pdf:true,primary_topic.subfield.id:{SUBFIELD_ID},best_oa_location.is_accepted:true,language:{LANGUAGE},keywords.id:{'|'.join(KEYWORDS)}",
            "sort": "cited_by_count:desc"
        }
        data = fetch_page(BASE_URL, params)
        if not data or "results" not in data:
            print(f"No data returned for page {page}, stopping.")
            break

        works = data["results"]
        if total_results is None:
            total_results = data.get("meta", {}).get("count", 0)
            print(f"Total results to fetch (approximate): {total_results}")

        print(f"Fetched page {page} with {len(works)} works.")

        with open(CSV_OBRA, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for work in works:
                # --- PDF URL ---
                pdf_url = work.get("best_oa_location", {}).get("pdf_url")
                if not pdf_url:
                    continue

                # --- DOI ---
                doi = work.get("doi", "")

                titulo = work.get("title", "")
                abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
                fecha_publicacion = work.get("publication_date", "")
                idioma = work.get("language", LANGUAGE)
                num_citas = work.get("cited_by_count", 0)
                fwci = work.get("fwci", "")
                primary_topic = work.get("primary_topic")
                if not primary_topic:
                    continue
                topic_name = primary_topic.get("display_name", "Unknown Topic")
                if topic_name not in tematica_map:
                    tematica_map[topic_name] = next_tematica_id
                    next_tematica_id += 1
                tematica_id = tematica_map[topic_name]

                writer.writerow([
                    obra_id, pdf_url, titulo, abstract, fecha_publicacion,
                    idioma, num_citas, fwci, tematica_id, doi
                ])
                obra_id += 1

        if page * PER_PAGE >= total_results or not works:
            break
        page += 1

    print(f"Finished fetching all works. Total works saved: {obra_id-1}")
    return tematica_map

def save_tematica_csv(tematica_map):
    os.makedirs(os.path.dirname(CSV_TEMATICA), exist_ok=True)
    with open(CSV_TEMATICA, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id","nombre_campo"])
        for topic_name, topic_id in tematica_map.items():
            writer.writerow([topic_id, topic_name])
    print(f"Saved '{CSV_TEMATICA}' with {len(tematica_map)} topics.")

def update_tematica_and_generate_contenida():
    if not os.path.exists(CSV_TEMATICA):
        raise FileNotFoundError(f"{CSV_TEMATICA} not found.")

    tematicas = {}
    rows = []
    with open(CSV_TEMATICA, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            rows.append(row)
            tematicas[row["nombre_campo"].strip()] = row["id"]

    max_id = max(r["id"] for r in rows)
    for topic in BASE_TOPICS:
        if topic not in tematicas:
            max_id += 1
            tematicas[topic] = max_id
            rows.append({"id": max_id, "nombre_campo": topic})
            print(f"Added base topic '{topic}' with id={max_id}")

    with open(CSV_TEMATICA, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "nombre_campo"])
        writer.writeheader()
        writer.writerows(rows)

    relaciones = [
        {"id_padre": tematicas["Physical Sciences"], "id_hijo": tematicas["Computer Science"]},
        {"id_padre": tematicas["Computer Science"], "id_hijo": tematicas["Artificial Intelligence"]}
    ]
    ai_id = tematicas["Artificial Intelligence"]
    for nombre, id_ in tematicas.items():
        if nombre not in BASE_TOPICS:
            relaciones.append({"id_padre": ai_id, "id_hijo": id_})
    relaciones = [{"id_padre": p, "id_hijo": h} for p, h in {(r["id_padre"], r["id_hijo"]) for r in relaciones}]

    os.makedirs(os.path.dirname(CSV_TEMATICA_CONTENIDA), exist_ok=True)
    with open(CSV_TEMATICA_CONTENIDA, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id_padre", "id_hijo"])
        writer.writeheader()
        writer.writerows(relaciones)

    print(f"'{CSV_TEMATICA}' updated with {len(rows)} topics.")
    print(f"'{CSV_TEMATICA_CONTENIDA}' generated with {len(relaciones)} relations.")

def main():
    print("Starting OpenAlex fetch process...")
    initialize_csv_files()
    tematica_map = fetch_all_works()
    save_tematica_csv(tematica_map)
    update_tematica_and_generate_contenida()
    print("Finished fetching and processing all works and topics.")

if __name__ == "__main__":
    main()
