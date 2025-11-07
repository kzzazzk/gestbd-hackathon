# -*- coding: utf-8 -*-
"""
OpenAlex (pyalex, Topics v2) -> CSVs
Filtros:
- is_oa=true
- has_pdf_url=true
- has_oa_accepted_or_published_version=true
- language=en
- primary_topic.field.id = Computer Science
- primary_topic.subfield.id = Artificial Intelligence
- Keywords = OR de lenguajes
- Jerarquía = Physical Sciences -> CS -> AI -> topics
"""

import pandas as pd
from dateutil import parser as dtparser
from pyalex import Works, Topics, Concepts, config # Concepts ya no se usa, pero se mantiene por si acaso

# -------- Config --------
config.email = "tu_correo@ejemplo.com"   # pon tu email

# -------- Utilidades --------
def decompress_abstract(inv_idx):
    if not inv_idx:
        return None
    pos, maxpos = {}, -1
    for w, idxs in inv_idx.items():
        for i in idxs:
            pos[i] = w
            if i > maxpos:
                maxpos = i
    return " ".join(pos.get(i, "") for i in range(maxpos + 1)).strip() or None

def parse_date_safe(s):
    if not s:
        return None
    try:
        return dtparser.parse(s).date().isoformat()
    except Exception:
        return str(s)

def topic_id(name: str, level: str):
    """Devuelve el id de Topics v2 (level: 'domain'|'field'|'subfield')."""
    items = Topics().search(name).get(per_page=20)
    # exacto nombre + nivel
    for t in items or []:
        if (t.get("display_name") or "").lower() == name.lower() and t.get("level") == level:
            return t["id"].split("/")[-1]
    # si no exacto, primero con ese nivel
    for t in items or []:
        if t.get("level") == level:
            return t["id"].split("/")[-1]

def fetch_topics_hierarchy(topic_ids_from_works, base_topic_ids):
    """
    Catálogo de Topics v2 + jerarquía.
    Construye la jerarquía desde los tópicos (L1-L2) encontrados en las obras
    y asegura que la jerarquía base (Dominio > Campo > Subcampo) esté presente.
    """
    names, edges = {}, set()
    
    # 1. Asegurar que la jerarquía base esté
    edges.add((base_topic_ids["domain"], base_topic_ids["field"]))
    edges.add((base_topic_ids["field"], base_topic_ids["subfield"]))
    
    # 2. Juntar todos los IDs: los de las obras + los base
    all_topic_ids = set(topic_ids_from_works)
    all_topic_ids.update(base_topic_ids.values())
    norm_ids = [tid.split("/")[-1] for tid in all_topic_ids if tid]
    
    # 3. Consultar la API de Topics en lotes
    batch = 50
    for i in range(0, len(norm_ids), batch):
        chunk = norm_ids[i:i+batch]
        try:
            items = Topics().filter(openalex_id="|".join(chunk)).get(per_page=len(chunk))
        except Exception as e:
            print(f"Error en lote de Topics: {e}")
            continue
            
        for t in items:
            tid = t["id"].split("/")[-1]
            names[tid] = t.get("display_name") or tid
            
            # Añadir nombres de ancestros (por si no estaban en el lote)
            if t.get("domain") and t["domain"].get("id"):
                names[t["domain"]["id"].split("/")[-1]] = t["domain"].get("display_name")
            if t.get("field") and t["field"].get("id"):
                names[t["field"]["id"].split("/")[-1]] = t["field"].get("display_name")
            if t.get("subfield") and t["subfield"].get("id"):
                names[t["subfield"]["id"].split("/")[-1]] = t["subfield"].get("display_name")

            # 4. Conectar tópicos individuales (L1-L2) a su subcampo (AI)
            if t.get("level") in ('topic', 'subtopic') and t.get("subfield") and t["subfield"].get("id"):
                subfield_id = t["subfield"]["id"].split("/")[-1]
                # Solo conectar si su padre es el subcampo de IA que buscamos
                if subfield_id == base_topic_ids["subfield"]:
                    edges.add((subfield_id, tid))
                    
    return names, edges

# -------- Descarga (filtros servidor) --------
def download_works(n_max=10000, field_id=None, subfield_id=None):
    keywords = [
        '"C programming language"', '"Java Programming Language"', "JavaScript", "Rust",
        "HTML", "SQL", "Scala", "Swift", "Java", "Dart", "Perl", "MATLAB", "Lisp",
        "Haskell", "COBOL", "Prolog", "Fortran", "Python",
    ]
    search_query = " OR ".join(keywords)
    
    # Usar un diccionario para filtros con puntos
    filters_dict = {
        "is_oa": "true",
        "has_pdf_url": "true",
        "has_oa_accepted_or_published_version": "true",
        "language": "en",
    }
    
    # Añadir filtros de tópicos si se proveen
    if field_id:
        filters_dict["primary_topic.field.id"] = field_id
    if subfield_id:
        filters_dict["primary_topic.subfield.id"] = subfield_id

    w = (
        Works()
        .search(search_query)
        .filter(**filters_dict) # <- Se usa el desempaquetado (**)
    )

    results = []
    print(f"  Paginando obras con filtros: {filters_dict}")
    for page in w.paginate(per_page=200, n_max=n_max):
        results.extend(page)
    return results

# -------- Construcción de DataFrames --------
def build_dataframes(works, base_topic_ids):
    # 1. Usar 'topics' (v2) en lugar de 'concepts' (v1)
    topic_ids = set()
    for w in works:
        for t in (w.get("topics") or []): # <- CAMBIO AQUÍ
            if t.get("id"):
                topic_ids.add(t["id"])

    # 2. Llamar a la nueva función de jerarquía de Topics v2
    print(f"  Encontrados {len(topic_ids)} tópicos (v2) únicos en las obras.")
    print("  Construyendo jerarquía (Topics v2)...")
    topic_names, edges = fetch_topics_hierarchy(topic_ids, base_topic_ids)
    print(f"  Total {len(topic_names)} tópicos en el mapa, {len(edges)} relaciones.")

    # tematica
    tematica_map, tematica_rows = {}, []
    for i, (cid, name) in enumerate(sorted(topic_names.items()), start=1):
        tematica_map[cid] = i
        tematica_rows.append({"id": i, "nombre_campo": name})
    tematica_df = pd.DataFrame(tematica_rows, columns=["id", "nombre_campo"])

    # obra
    obra_rows = []
    for i, w in enumerate(works, start=1):
        openalex_id = w.get("id")
        title = (w.get("title") or "").strip()
        abstract = decompress_abstract(w.get("abstract_inverted_index")) if w.get("abstract_inverted_index") else (w.get("abstract") or None)

        # 3. Usar 'primary_topic' para el ID de temática
        primary_topic = w.get("primary_topic")
        tematica_id = None
        if primary_topic and primary_topic.get("id"):
            tematica_id = tematica_map.get(primary_topic["id"].split("/")[-1])

        doi = w.get("doi")
        if doi:
            direccion = f"https://doi.org/{doi.split('/')[-1]}"
        else:
            pl = w.get("primary_location") or {}
            direccion = pl.get("landing_page_url") or (w.get("best_oa_location") or {}).get("landing_page_url") or openalex_id

        obra_rows.append({
            "id": i,
            "direccion_fuente": direccion or "",
            "titulo": title,
            "abstract": abstract,
            "fecha_publicacion": parse_date_safe(w.get("publication_date")) or str(w.get("publication_year") or ""),
            "idioma": (w.get("language") or "").lower() or None,
            "num_citas": int(w.get("cited_by_count") or 0),
            "fwci": None,
            "tematica_id": tematica_id, # <- CAMBIO AQUÍ
        })

    obra_df = pd.DataFrame(
        obra_rows,
        columns=["id","direccion_fuente","titulo","abstract","fecha_publicacion","idioma","num_citas","fwci","tematica_id"]
    )

    # tematica_contenida
    tcont_rows = []
    for parent, child in sorted(edges):
        p = tematica_map.get(parent)
        h = tematica_map.get(child)
        if p and h and p != h:
            tcont_rows.append({"tematica_padre_id": p, "tematica_hijo_id": h})
    tematica_contenida_df = pd.DataFrame(tcont_rows, columns=["tematica_padre_id","tematica_hijo_id"]).drop_duplicates()

    return {"tematica": tematica_df, "obra": obra_df, "tematica_contenida": tematica_contenida_df}

# -------- Main --------
if __name__ == "__main__":
    print("🔍 Buscando IDs de Tópicos (v2)…")
    # 1. Obtener los IDs de la jerarquía base
    domain_id = topic_id("Physical Sciences", "domain")
    field_id = topic_id("Computer Science", "field")
    subfield_id = topic_id("Artificial Intelligence", "subfield")
    
    if not (domain_id and field_id and subfield_id):
        print("Error: No se pudieron encontrar los IDs de tópicos base. Saliendo.")
        exit()

    base_topic_ids = {
        "domain": domain_id,
        "field": field_id,
        "subfield": subfield_id
    }
    print(f"  - Dominio: {domain_id} (Physical Sciences)")
    print(f"  - Campo: {field_id} (Computer Science)")
    print(f"  - Subcampo: {subfield_id} (Artificial Intelligence)")

    print("🔍 Descargando obras (filtrando por Campo y Subcampo)…")
    # 2. Pasar los IDs para filtrar
    works = download_works(n_max=10000, field_id=field_id, subfield_id=subfield_id)
    print(f"➡️ Obras descargadas: {len(works)}")

    print("🧱 Construyendo DataFrames (usando Topics v2)…")
    # 3. Pasar los IDs para construir la jerarquía
    dfs = build_dataframes(works, base_topic_ids=base_topic_ids)

    print("💾 Exportando CSVs…")
    dfs["tematica"].to_csv("tematica.csv", index=False, encoding="utf-8")
    dfs["obra"].to_csv("obra.csv", index=False, encoding="utf-8")
    dfs["tematica_contenida"].to_csv("tematica_contenida.csv", index=False, encoding="utf-8")

    print("✅ Listo: tematica.csv, obra.csv, tematica_contenida.csv")