# -*- coding: utf-8 -*-
"""
OpenAlex (pyalex, Topics v2) -> CSVs
Filtros (como en tu captura):
- is_oa=true
- has_pdf_url=true
- has_oa_accepted_or_published_version=true
- language=en
- Field = Computer Science (primary_topic.field.id)
- Subfield = Artificial Intelligence (primary_topic.subfield.id)
- Keywords = OR de lenguajes
"""

import pandas as pd
from dateutil import parser as dtparser
from pyalex import Works, Topics, Concepts, config

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
    """Devuelve el id de Topics v2 (level: 'field'|'subfield')."""
    items = Topics().search(name).get(per_page=20)
    # exacto nombre + nivel
    for t in items or []:
        if (t.get("display_name") or "").lower() == name.lower() and t.get("level") == level:
            return t["id"].split("/")[-1]
    # si no exacto, primero con ese nivel
    for t in items or []:
        if t.get("level") == level:
            return t["id"].split("/")[-1]

def fetch_concepts_with_ancestors(concept_ids, batch=50):
    """Catálogo de conceptos + jerarquía para tematica/tematica_contenida."""
    names, edges = {}, set()
    norm = [cid.split("/")[-1] for cid in concept_ids if cid]
    for i in range(0, len(norm), batch):
        chunk = norm[i:i+batch]
        items = Concepts().filter(openalex_id="|".join(chunk)).get(per_page=len(chunk))
        for c in items:
            cid = c["id"].split("/")[-1]
            names[cid] = c.get("display_name") or cid
            for anc in (c.get("ancestors") or []):
                if anc.get("id"):
                    aid = anc["id"].split("/")[-1]
                    names[aid] = anc.get("display_name") or aid
                    edges.add((aid, cid))
    return names, edges

# -------- Descarga (filtros servidor) --------
def download_works(n_max=10000):
    cs_field_id = topic_id("Computer Science", "field")
    ai_subfield_id = topic_id("Artificial Intelligence", "subfield")

    keywords = [
        '"C programming language"', '"Java Programming Language"', "JavaScript", "Rust",
        "HTML", "SQL", "Scala", "Swift", "Java", "Dart", "Perl", "MATLAB", "Lisp",
        "Haskell", "COBOL", "Prolog", "Fortran", "Python",
    ]
    search_query = " OR ".join(keywords)

    w = (
        Works()
        .search(search_query)
        .filter(
            is_oa="true",
            has_pdf_url="true",
            has_oa_accepted_or_published_version="true",
            language="en",
            primary_topic_field_id=cs_field_id,       # ✅ válido
            primary_topic_subfield_id=ai_subfield_id  # ✅ válido
        )
    )

    results = []
    for page in w.paginate(per_page=200, n_max=n_max):
        results.extend(page)
    return results

# -------- Construcción de DataFrames --------
def build_dataframes(works, include_hierarchy=True):
    # conceptos + jerarquía
    concept_ids = set()
    for w in works:
        for c in (w.get("concepts") or []):
            if c.get("id"):
                concept_ids.add(c["id"])

    if include_hierarchy and concept_ids:
        concept_names, edges = fetch_concepts_with_ancestors(concept_ids)
    else:
        concept_names, edges = {}, set()
        for w in works:
            for c in (w.get("concepts") or []):
                if c.get("id"):
                    cid = c["id"].split("/")[-1]
                    concept_names[cid] = c.get("display_name") or cid

    # tematica
    tematica_map, tematica_rows = {}, []
    for i, (cid, name) in enumerate(sorted(concept_names.items()), start=1):
        tematica_map[cid] = i
        tematica_rows.append({"id": i, "nombre_campo": name})
    tematica_df = pd.DataFrame(tematica_rows, columns=["id", "nombre_campo"])

    # obra
    obra_rows = []
    for i, w in enumerate(works, start=1):
        openalex_id = w.get("id")
        title = (w.get("title") or "").strip()
        abstract = decompress_abstract(w.get("abstract_inverted_index")) if w.get("abstract_inverted_index") else (w.get("abstract") or None)

        # concepto con mayor score -> tematica_id
        concepts = w.get("concepts") or []
        primary = max(concepts, key=lambda c: c.get("score", 0)) if concepts else None
        tematica_id = None
        if primary and primary.get("id"):
            tematica_id = tematica_map.get(primary["id"].split("/")[-1])

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
            "tematica_id": tematica_id,
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
    print("🔍 Descargando con primary_topic_field_id + primary_topic_subfield_id…")
    works = download_works(n_max=10000)
    print(f"➡️ Obras descargadas: {len(works)}")

    print("🧱 Construyendo DataFrames…")
    dfs = build_dataframes(works, include_hierarchy=True)

    print("💾 Exportando CSVs…")
    dfs["tematica"].to_csv("tematica.csv", index=False, encoding="utf-8")
    dfs["obra"].to_csv("obra.csv", index=False, encoding="utf-8")
    dfs["tematica_contenida"].to_csv("tematica_contenida.csv", index=False, encoding="utf-8")

    print("✅ Listo: tematica.csv, obra.csv, tematica_contenida.csv")