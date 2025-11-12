#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, SKOS, XSD
import os
# --- Namespaces ---
SCHEMA = Namespace("https://schema.org/")
OPENALEX = Namespace("https://openalex.org/")
g = Graph()
g.bind("schema", SCHEMA)
g.bind("skos", SKOS)
g.bind("openalex", OPENALEX)

# --- PostgreSQL connection ---
DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "database": "demoDB",
    "user": "userPSQL",
    "password": "passPSQL",
}

try:
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    print("Connected to database ✅")

    # --- 1. TEMÁTICA ---
    cur.execute("SELECT id, nombre_campo FROM tematica;")
    for tmid, nombre in cur.fetchall():
        tema_uri = OPENALEX[f"tematica_{tmid}"]
        g.add((tema_uri, RDF.type, SKOS.Concept))
        if nombre:
            g.add((tema_uri, SKOS.prefLabel, Literal(nombre)))

    print("Mapped table: tematica ✅")

    # tematica_contenida → skos:broader/narrower
    cur.execute("SELECT tematica_padre_id, tematica_hijo_id FROM tematica_contenida;")
    for parent, child in cur.fetchall():
        if parent and child:
            parent_uri = OPENALEX[f"tematica_{parent}"]
            child_uri = OPENALEX[f"tematica_{child}"]
            g.add((parent_uri, SKOS.narrower, child_uri))
            g.add((child_uri, SKOS.broader, parent_uri))

    # --- 2. TECNOLOGÍA ---
    cur.execute("SELECT id, nombre, tipo, version FROM tecnologia;")
    for tid, nombre, tipo, version in cur.fetchall():
        tech_uri = OPENALEX[f"tecnologia_{tid}"]
        g.add((tech_uri, RDF.type, SCHEMA.SoftwareApplication))
        if nombre:
            g.add((tech_uri, SCHEMA.name, Literal(nombre)))
        if tipo:
            g.add((tech_uri, SCHEMA.applicationCategory, Literal(tipo)))
        if version:
            g.add((tech_uri, SCHEMA.softwareVersion, Literal(version)))

    print("Mapped table: tecnologia ✅")

    # --- 3. OBRA ---
    cur.execute("""
        SELECT id, doi, direccion_fuente, titulo, abstract, fecha_publicacion,
               idioma, num_citas, fwci, tematica_id
        FROM obra;
    """)
    for (
        oid, doi, direccion_fuente, titulo, abstract, fecha_publicacion,
        idioma, num_citas, fwci, tematica_id
    ) in cur.fetchall():
        obra_uri = OPENALEX[f"obra_{oid}"]
        g.add((obra_uri, RDF.type, SCHEMA.ScholarlyArticle))
        if doi:
            g.add((obra_uri, SCHEMA.identifier, Literal(doi)))
        if direccion_fuente:
            g.add((obra_uri, SCHEMA.url, Literal(direccion_fuente)))
        if titulo:
            g.add((obra_uri, SCHEMA.name, Literal(titulo)))
        if abstract:
            g.add((obra_uri, SCHEMA.abstract, Literal(abstract)))
        if fecha_publicacion:
            g.add((obra_uri, SCHEMA.datePublished, Literal(fecha_publicacion, datatype=XSD.date)))
        if idioma:
            g.add((obra_uri, SCHEMA.inLanguage, Literal(idioma)))
        if num_citas is not None:
            g.add((obra_uri, SCHEMA.citationCount, Literal(num_citas, datatype=XSD.integer)))
        if fwci is not None:
            g.add((obra_uri, SCHEMA.metric, Literal(fwci, datatype=XSD.float)))
        if tematica_id:
            g.add((obra_uri, SCHEMA.about, OPENALEX[f"tematica_{tematica_id}"]))

    print("Mapped table: obra ✅")

    # obra_tecnologia → schema:mentions
    cur.execute("SELECT obra_id, tecnologia_id FROM obra_tecnologia;")
    for oid, tid in cur.fetchall():
        if oid and tid:
            g.add((OPENALEX[f"obra_{oid}"], SCHEMA.mentions, OPENALEX[f"tecnologia_{tid}"]))

    print("Mapped relationships ✅")

    # --- 4. EXPORT ---
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory where this script lives
    output_dir = os.path.join(base_dir, "../db")
    output_file = os.path.join(output_dir, "openalex_graph.ttl")

    os.makedirs(output_dir, exist_ok=True)
    g.serialize(destination=output_file, format="turtle")

except psycopg2.Error as e:
    print("❌ Database error:", e)

except Exception as e:
    print("❌ Unexpected error:", e)

finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
    print("PostgreSQL connection closed 🔒")
