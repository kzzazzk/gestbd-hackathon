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
    # Connect to the database
    connection = psycopg2.connect(**DB_PARAMS)
    cursor = connection.cursor()

    # Paths to CSV files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dir_cache = os.path.join(script_dir, '../cache')
    file_tematica = os.path.join(dir_cache, 'tematica.csv')
    file_tematica_contenida = os.path.join(dir_cache, 'tematica_contenida.csv')
    file_obra = os.path.join(dir_cache, 'obra.csv')

    # Read CSV files
    df_tematica = pd.read_csv(file_tematica)
    df_tematica_contenida = pd.read_csv(file_tematica_contenida)
    df_obra = pd.read_csv(file_obra)

    # Insert into 'tematica'
    for _, row in df_tematica.iterrows():
        cursor.execute("""
            INSERT INTO tematica (id, nombre_campo)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (int(row['id']), row['nombre_campo']))

    # Insert into 'tematica_contenida'
    for _, row in df_tematica_contenida.iterrows():
        cursor.execute("""
            INSERT INTO tematica_contenida (tematica_padre_id, tematica_hijo_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (int(row['id_padre']), int(row['id_hijo'])))

    # Insert into 'obra'
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
    print("✅ CSV data loaded successfully.")

if __name__ == "__main__":
    main()