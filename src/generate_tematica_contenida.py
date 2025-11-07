import csv
import os

# Archivos de entrada/salida
TEMATICA_CSV = "cache/tematica.csv"
TEMATICA_CONTENIDA_CSV = "cache/tematica_contenida.csv"

# Temáticas base
BASE_TOPICS = [
    "Physical Sciences",
    "Computer Science",
    "Artificial Intelligence",
]

# Leer tematica.csv y crear diccionario nombre -> id
tematicas = {}
rows = []

if not os.path.exists(TEMATICA_CSV):
    raise FileNotFoundError(f"No se encontró {TEMATICA_CSV}")

with open(TEMATICA_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    if "nombre_campo" not in reader.fieldnames:
        raise ValueError("❌ El archivo tematica.csv debe tener la columna 'nombre_campo'")
    for row in reader:
        row["id"] = int(row["id"])
        rows.append(row)
        tematicas[row["nombre_campo"].strip()] = row["id"]

# Calcular el próximo ID disponible
max_id = max(r["id"] for r in rows)

# Insertar los temas base si faltan
for topic in BASE_TOPICS:
    if topic not in tematicas:
        max_id += 1
        tematicas[topic] = max_id
        rows.append({"id": max_id, "nombre_campo": topic})
        print(f"➕ Añadido tema base '{topic}' con id={max_id}")

# Guardar tematica.csv actualizado
with open(TEMATICA_CSV, "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "nombre_campo"])
    writer.writeheader()
    writer.writerows(rows)

# Crear lista de relaciones
relaciones = []

# Relaciones jerárquicas fijas
relaciones.append({
    "id_padre": tematicas["Physical Sciences"],
    "id_hijo": tematicas["Computer Science"]
})
relaciones.append({
    "id_padre": tematicas["Computer Science"],
    "id_hijo": tematicas["Artificial Intelligence"]
})

# Vincular todas las demás temáticas con Artificial Intelligence
ai_id = tematicas["Artificial Intelligence"]
for nombre, id_ in tematicas.items():
    if nombre not in BASE_TOPICS:
        relaciones.append({
            "id_padre": ai_id,
            "id_hijo": id_
        })

# Eliminar duplicados
unique = {(r["id_padre"], r["id_hijo"]) for r in relaciones}
relaciones = [{"id_padre": p, "id_hijo": h} for p, h in unique]

# Guardar tematica_contenida.csv
os.makedirs(os.path.dirname(TEMATICA_CONTENIDA_CSV), exist_ok=True)
with open(TEMATICA_CONTENIDA_CSV, "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id_padre", "id_hijo"])
    writer.writeheader()
    writer.writerows(relaciones)

print(f"✅ '{TEMATICA_CSV}' actualizado con {len(rows)} temáticas.")
print(f"✅ '{TEMATICA_CONTENIDA_CSV}' generado con {len(relaciones)} relaciones únicas.")
