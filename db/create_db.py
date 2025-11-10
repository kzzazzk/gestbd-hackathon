import psycopg2
from psycopg2 import sql

DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "database": "demoDB",
    "user": "userPSQL",
    "password": "passPSQL"
}

sql_script = """CREATE TABLE IF NOT EXISTS tematica (
    id SERIAL PRIMARY KEY,
    nombre_campo TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tecnologia (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT,
    version TEXT
);

CREATE TABLE IF NOT EXISTS obra (
    id SERIAL PRIMARY KEY,
    doi TEXT UNIQUE,  -- NEW
    direccion_fuente TEXT NOT NULL,
    titulo TEXT NOT NULL,
    abstract TEXT,
    fecha_publicacion TEXT,
    idioma TEXT,
    num_citas INTEGER DEFAULT 0,
    fwci REAL,
    tematica_id INTEGER,
    FOREIGN KEY (tematica_id)
        REFERENCES tematica(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS obra_tecnologia (
    obra_id INTEGER NOT NULL,
    tecnologia_id INTEGER NOT NULL,
    PRIMARY KEY (obra_id, tecnologia_id),
    FOREIGN KEY (obra_id)
        REFERENCES obra(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (tecnologia_id)
        REFERENCES tecnologia(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tematica_contenida (
    tematica_padre_id INTEGER NOT NULL,
    tematica_hijo_id INTEGER NOT NULL,
    PRIMARY KEY (tematica_padre_id, tematica_hijo_id),
    FOREIGN KEY (tematica_padre_id)
        REFERENCES tematica(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (tematica_hijo_id)
        REFERENCES tematica(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CHECK (tematica_padre_id <> tematica_hijo_id)
);

CREATE INDEX IF NOT EXISTS idx_obra_tematica ON obra(tematica_id);
CREATE INDEX IF NOT EXISTS idx_obratec_tecnologia ON obra_tecnologia(tecnologia_id);
CREATE INDEX IF NOT EXISTS idx_tematica_hijo ON tematica_contenida(tematica_hijo_id);
"""

def main():
    # Connect to default database to check/create demoDB
    connection = psycopg2.connect(
        host=DB_PARAMS['host'],
        port=DB_PARAMS['port'],
        database="demoDB",
        user=DB_PARAMS['user'],
        password=DB_PARAMS['password']
    )
    connection.autocommit = True
    cursor = connection.cursor()

    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_PARAMS["database"],))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute(sql.SQL(f"CREATE DATABASE {DB_PARAMS['database']};"))
        print(f"✅ Database '{DB_PARAMS['database']}' created.")
    else:
        print(f"ℹ️ Database '{DB_PARAMS['database']}' already exists.")

    cursor.close()
    connection.close()

    # Connect to demoDB to create tables
    connection = psycopg2.connect(**DB_PARAMS)
    cursor = connection.cursor()
    cursor.execute(sql_script)
    connection.commit()
    cursor.close()
    connection.close()
    print("✅ Tables created or verified successfully.")

if __name__ == "__main__":
    main()