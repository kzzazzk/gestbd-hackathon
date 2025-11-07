import os

import pandas as pd
import psycopg2
from psycopg2 import sql

from postgredb_structure import sql_script

# --- Step 1: Create database if missing ---
connection = psycopg2.connect(
    host="localhost",
    port=5432,
    database="demoDB",
    user="userPSQL",
    password="passPSQL"
)
#connection.autocommit = True
cursor = connection.cursor()

cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'demoDB';")
exists = cursor.fetchone()

if not exists:
    cursor.execute(sql.SQL("CREATE DATABASE demoDB;"))
    print("✅ Database 'demoDB' created.")
else:
    print("ℹ️ Database 'demoDB' already exists.")

# --- Step 2: Connect to demoDB and create tables ---

cursor.execute(sql_script)
connection.commit()

print("✅ Tables created or verified successfully.")

# --- Step 3: Uploda the tables with the data ---

dir_cache = '../cache'
file_tematica= os.path.join(dir_cache, 'tematica.csv')
file_tematica_contenida = os.path.join(dir_cache, 'tematica_contenida.csv')
file_obra = os.path.join(dir_cache, 'obra.csv')


df_obra = pd.read_csv(file_obra)
df_tematica = pd.read_csv(file_tematica)
df_tematica_contenida = pd.read_csv(file_tematica_contenida)

# --- Insertar en 'tematica' ---
for _, row in df_tematica.iterrows():
    cursor.execute("""
        INSERT INTO tematica (id, nombre_campo)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (int(row['id']), row['nombre_campo']))
    
# --- Insertar en 'tematica_contenida' ---
for _, row in df_tematica_contenida.iterrows():
    cursor.execute("""
        INSERT INTO tematica_contenida (tematica_padre_id, tematica_hijo_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (int(row['id_padre']), int(row['id_hijo'])))

# --- Insertar en 'obra' ---
for _, row in df_obra.iterrows():
    cursor.execute("""
        INSERT INTO obra (
            id, direccion_fuente, titulo, abstract, fecha_publicacion, idioma, num_citas, fwci, tematica_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (
        int(row['id']),
        row['direccion_fuente'],
        row['titulo'],
        row.get('abstract'),
        row.get('fecha_publicacion'),
        row.get('idioma'),
        int(row.get('num_citas', 0)),
        float(row.get('fwci', 0.0)),
        int(row.get('tematica_id')) if not pd.isna(row.get('tematica_id')) else None
    ))
    
connection.commit()

cursor.close()
connection.close()
