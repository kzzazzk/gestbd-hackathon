#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, SKOS, XSD

# --- Namespaces ---
SCHEMA = Namespace("https://schema.org/")
OPENALEX = Namespace("https://openalex.org/")
g = Graph()
g.bind("schema", SCHEMA)
g.bind("skos", SKOS)
g.bind("openalex", OPENALEX)

# --- PostgreSQL connection ---
conn = psycopg2.connect(
    host="localhost",
    database="openalex",
    user="postgres",
    password="yourpassword"
)
cur = conn.cursor()

print("Connected to database ✅")

# --- 3. TEMÁTICA ---
cur.execute("SELECT id, nombre_campo FROM tematica;")
for tmid, nombre in cur.fetchall():
    tema_uri = OPENALEX[f"tematica_{tmid}"]
    g.add((tema_uri, RDF.type, SKOS.Concept))
    g.add((tema_uri, SKOS.prefLabel, Literal(nombre)))

print("Mapped table: tematica ✅")

# tematica_contenida → skos:broader
cur.execute("SELECT id_padre, id_hijo FROM tematica_contenida;")
for parent, child in cur.fetchall():
    #URI
    g.add((OPENALEX[f"tematica_{parent}"], SKOS.narrower, OPENALEX[f"tematica_{child}"]))
    g.add((OPENALEX[f"tematica_{child}"], SKOS.broader, OPENALEX[f"tematica_{parent}"]))

# --- 2. TECNOLOGÍA ---
cur.execute("SELECT id_tecnologia, nombre, tipo, version FROM tecnologia;")
for tid, nombre, tipo, version in cur.fetchall():
    tech_uri = OPENALEX[f"tecnologia_{tid}"]
    g.add((tech_uri, RDF.type, SCHEMA.SoftwareApplication))
    g.add((tech_uri, SCHEMA.name, Literal(nombre)))
    if tipo:
        g.add((tech_uri, SCHEMA.applicationCategory, Literal(tipo)))
    if version:
        g.add((tech_uri, SCHEMA.softwareVersion, Literal(version)))

print("Mapped table: tecnologia ✅")

# --- 1. OBRA ---
cur.execute("SELECT id, direccion_fuente, titulo, abstract, fecha_publicacion, idioma, num_citas, fwci, tematica_id, doi FROM obra;")
for oid, direccion_fuente, titulo, abstract, fecha_publicacion, idioma, num_citas, fwci, tematica_id, doi in cur.fetchall():
    obra_uri = OPENALEX[f"obra_{oid}"]
    g.add((obra_uri, RDF.type, SCHEMA.TechArticle))
    if direccion_fuente:
        g.add((obra_uri, SCHEMA.url, URIRef(direccion_fuente)))
    if titulo:
        g.add((obra_uri, SCHEMA.name, Literal(titulo)))
    if abstract:
        g.add((obra_uri, SCHEMA.abstract, Literal(abstract)))
    if fecha_publicacion:
        g.add((obra_uri, SCHEMA.datePublished, Literal(fecha_publicacion, datatype=XSD.date)))
    if idioma:
        g.add((obra_uri, SCHEMA.inLanguage, Literal(idioma)))
    if num_citas:
        g.add((obra_uri, SCHEMA.citationCount, Literal(num_citas, datatype=XSD.integer)))
    if fwci:
        g.add((obra_uri, SCHEMA.metric, Literal(fwci, datatype=XSD.float)))
    if tematica_id:
        g.add((obra_uri, SCHEMA.about, OPENALEX[f"tematica_{tematica_id}"]))
    if doi:
        g.add((obra_uri, SCHEMA.identifier, Literal(doi)))

print("Mapped table: obra ✅")

# --- 4. RELACIONES ---

# obra_tecnologia → schema:mentions
cur.execute("SELECT obra_id, tecnologia_id FROM obra_tecnologia;")
for oid, tid in cur.fetchall():
    #URI
    g.add((OPENALEX[f"obra_{oid}"], SCHEMA.mentions, OPENALEX[f"tecnologia_{tid}"]))


print("Mapped relationships ✅")

# --- 5. EXPORT ---
output_file = "openalex_graph.ttl"
g.serialize(destination=output_file, format="turtle")
print(f"RDF graph exported to {output_file} 🧩")

# --- 6. Cleanup ---
cur.close()
conn.close()
print("PostgreSQL connection closed 🔒")
