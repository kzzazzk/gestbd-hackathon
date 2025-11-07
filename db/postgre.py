import psycopg2
from psycopg2 import sql
from postgredb_structure import sql_script

# --- Step 1: Create database if missing ---
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="demoDB",  # connect to default admin DB
    user="userPSQL",
    password="passPSQL"
)
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_database WHERE datname = 'demoDB';")
exists = cur.fetchone()

if not exists:
    cur.execute(sql.SQL("CREATE DATABASE demoDB;"))
    print("✅ Database 'demoDB' created.")
else:
    print("ℹ️ Database 'demoDB' already exists.")

cur.close()
conn.close()

# --- Step 2: Connect to demoDB and create tables ---
conexion = psycopg2.connect(
    host="localhost",
    port=5432,
    database="demoDB",
    user="userPSQL",
    password="passPSQL"
)

cursor = conexion.cursor()
cursor.execute(sql_script)
conexion.commit()

print("✅ Tables created or verified successfully.")

cursor.close()
conexion.close()
