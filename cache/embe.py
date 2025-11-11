# ==============================
# CLASIFICADOR DE TECNOLOGÍAS
# USANDO WIKIPEDIA + EMBEDDINGS + KMEANS
# ==============================

import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import time

# === 1. Cargar tus tecnologías ===
df = pd.read_csv("tecnologia.csv")

# === 2. Obtener descripciones desde Wikipedia ===
def get_description(term):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{term}"
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            return data.get("extract", "")
        else:
            return ""
    except:
        return ""

print("⏳ Obteniendo descripciones desde Wikipedia...")
df["descripcion"] = df["nombre"].apply(get_description)
print("✅ Descripciones obtenidas.")

# === 3. Generar embeddings ===
print("⏳ Generando embeddings con modelo 'all-MiniLM-L6-v2'...")
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(df["descripcion"].fillna("").tolist(), show_progress_bar=True)

# Normalizar (opcional)
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)
print("✅ Embeddings generados y normalizados.")

# === 4. Aplicar KMeans ===
n_clusters = 10  # puedes ajustar este número
print(f"⏳ Aplicando KMeans con {n_clusters} clusters...")
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
df["cluster"] = kmeans.fit_predict(embeddings_scaled)
print("✅ Clustering completado.")

# === 5. Identificar el cluster de lenguajes de programación ===
# Heurística: buscar el cluster donde aparezcan nombres de lenguajes conocidos
lenguajes_conocidos = {"python", "java", "c++", "c", "javascript", "php", "r", "go", "swift", "rust"}
cluster_counts = (
    df[df["nombre"].str.lower().isin(lenguajes_conocidos)]
    .groupby("cluster")
    .size()
    .sort_values(ascending=False)
)
if not cluster_counts.empty:
    cluster_lenguajes = cluster_counts.index[0]
else:
    cluster_lenguajes = None

df["es_lenguaje"] = df["cluster"] == cluster_lenguajes
print(f"✅ Cluster de lenguajes identificado: {cluster_lenguajes}")

# === 6. Guardar resultado ===
df.to_csv("tecnologias_clusterizadas.csv", index=False)
print("💾 Archivo guardado como 'tecnologias_clusterizadas.csv'")

# === 7. Mostrar resumen ===
for i in range(n_clusters):
    print(f"\n--- Cluster {i} ---")
    print(df[df["cluster"] == i]["nombre"].head(10).tolist())

