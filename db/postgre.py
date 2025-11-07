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
connection.autocommit = True
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



cursor.close()
connection.close()
