sql_script = """
CREATE TABLE IF NOT EXISTS tematica (
    id SERIAL PRIMARY KEY,
    nombre_campo TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tecnologia (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    version TEXT
);

CREATE TABLE IF NOT EXISTS obra (
    id SERIAL PRIMARY KEY,
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