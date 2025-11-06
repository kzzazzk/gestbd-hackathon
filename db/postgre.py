import psycopg2
from postgredb_structure import sql_script

# Dtoas de conexion
conexion = psycopg2.connect(
    host="localhost",
    port=5432,
    database="midb",
    user="user",
    password="password"
)

# Crea un cursor
cursor = conexion.cursor()
print("✅ Conexión exitosa a PostgreSQL")

# Ejecuta una consulta de prueba
cursor.execute("SELECT version();")
version = cursor.fetchone()
print("Versión de PostgreSQL:", version)

# Añadir las si no estan creadas
cursor.execute(sql_script)
conexion.commit()

# Listar tablas existentes
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public';
""")

tablas = cursor.fetchall()
print("📋 Tablas actuales:")
for t in tablas:
    print("  -", t[0])

# Cierra conexión
cursor.close()
conexion.close()

#########################################################################################################################
#########################################################################################################################

