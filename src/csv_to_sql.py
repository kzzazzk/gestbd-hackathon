import os
import pandas as pd
import psycopg2

DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "database": "demoDB",
    "user": "userPSQL",
    "password": "passPSQL"
}

def main():
    connection = psycopg2.connect(**DB_PARAMS)
    cursor = connection.cursor()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    dir_cache = os.path.join(script_dir, '../cache')

    # File paths
    file_tematica = os.path.join(dir_cache, 'tematica.csv')
    file_tematica_contenida = os.path.join(dir_cache, 'tematica_contenida.csv')
    file_obra = os.path.join(dir_cache, 'obra.csv')
    file_tecnologia = os.path.join(dir_cache, 'tecnologia.csv')
    file_obra_tecnologia = os.path.join(dir_cache, 'obra_tecnologia.csv')

    # Read CSVs
    df_tematica = pd.read_csv(file_tematica)
    df_tematica_contenida = pd.read_csv(file_tematica_contenida)
    df_obra = pd.read_csv(file_obra)
    df_tecnologia = pd.read_csv(file_tecnologia)
    df_obra_tecnologia = pd.read_csv(file_obra_tecnologia)

    # Insert tematica
    for _, row in df_tematica.iterrows():
        cursor.execute("""
            INSERT INTO tematica (id, nombre_campo)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (int(row['id']), row['nombre_campo'].strip() if pd.notna(row['nombre_campo']) else None))

    # Insert tematica_contenida
    for _, row in df_tematica_contenida.iterrows():
        cursor.execute("""
            INSERT INTO tematica_contenida (tematica_padre_id, tematica_hijo_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (int(row['id_padre']), int(row['id_hijo'])))

    # Insert obra
    for _, row in df_obra.iterrows():
        cursor.execute("""
            INSERT INTO obra (
                id, doi, direccion_fuente, titulo, abstract, fecha_publicacion,
                idioma, num_citas, fwci, tematica_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            int(row['id']),
            row.get('doi').strip() if pd.notna(row.get('doi')) else None,
            row['direccion_fuente'].strip() if pd.notna(row.get('direccion_fuente')) else None,
            row['titulo'].strip() if pd.notna(row.get('titulo')) else None,
            row.get('abstract').strip() if pd.notna(row.get('abstract')) else None,
            row.get('fecha_publicacion') if pd.notna(row.get('fecha_publicacion')) else None,
            row.get('idioma').strip() if pd.notna(row.get('idioma')) else None,
            int(row.get('num_citas', 0)) if pd.notna(row.get('num_citas')) else 0,
            float(row.get('fwci', 0.0)) if pd.notna(row.get('fwci')) else 0.0,
            int(row.get('tematica_id')) if pd.notna(row.get('tematica_id')) else None
        ))

    # Insert tecnologia
    for _, row in df_tecnologia.iterrows():
        cursor.execute("""
            INSERT INTO tecnologia (id, nombre, tipo, version)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            int(row['id']),
            row['nombre'].strip() if pd.notna(row['nombre']) else None,
            row.get('tipo').strip() if pd.notna(row.get('tipo')) else None,
            row.get('version').strip() if pd.notna(row.get('version')) else None
        ))

    # Insert obra_tecnologia
    for _, row in df_obra_tecnologia.iterrows():
        cursor.execute("""
            INSERT INTO obra_tecnologia (obra_id, tecnologia_id)
            VALUES (%s, %s)
            ON CONFLICT (obra_id, tecnologia_id) DO NOTHING
        """, (int(row['obra_id']), int(row['tecnologia_id'])))

    connection.commit()
    cursor.close()
    connection.close()
    print("✅ CSV data loaded successfully including tecnologia and obra_tecnologia.")

if __name__ == "__main__":
    main()
