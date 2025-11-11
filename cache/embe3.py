import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np  # Import numpy for handling embeddings

n_clusters = 100

# 1. Cargar tus tecnologías
try:
    df = pd.read_csv("tecnologia_clustered.csv")
    print("CSV file 'tecnologia.csv' loaded successfully.")
except FileNotFoundError:
    print("Error: 'tecnologia.csv' not found.")
    exit()

try:
    df = df.drop("tecnologia_nueva", axis=1)
except Exception as e:
    pass

# Filter out rows where no description was found, as they will have empty embeddings
df_with_desc = df[df["descripcion"].str.len() > 0].copy()

if df_with_desc.empty:
    print("No descriptions were found for any technology. Cannot proceed to clustering.")
    exit()

# 3. Crear embeddings
print("Encoding descriptions into embeddings...")
model = SentenceTransformer("all-MiniLM-L6-v2")
# Use the filtered DataFrame for encoding
embeddings = model.encode(df_with_desc["descripcion"].tolist())
print("Encoding complete.")

# 4. Clustering
# We set n_init=10 to suppress a future warning, which is standard practice.
 # You can change this number
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)

# Fit the model and assign the cluster ID to the new column
# We are only clustering the rows that have a description
df_with_desc["tecnologia_nueva"] = kmeans.fit_predict(embeddings)

# 5. Guardar el nuevo CSV
# Now, we merge this cluster information back into the original DataFrame
# This ensures we have the full list, with clusters assigned only where possible
df_final = df.merge(df_with_desc[["id", "tecnologia_nueva"]], on="id", how="left")

# Replace NaN (for rows without description/cluster) with a placeholder, e.g., -1
df_final["tecnologia_nueva"] = df_final["tecnologia_nueva"].fillna(-1).astype(int)

output_file = "tecnologia_clustered.csv"
df_final.to_csv(output_file, index=False)

print(f"\nSuccessfully created new file: '{output_file}'")
print(f"Rows without a description were assigned cluster ID -1.")

# 6. Explorar los clusters
print("\n--- Exploring Clusters (showing top 10 from each) ---")
for i in range(n_clusters):
    print(f"\n--- Cluster {i} ---")
    # Get names from the *clustered* dataframe
    cluster_names = df_with_desc[df_with_desc["tecnologia_nueva"] == i]["nombre"].head(10).tolist()
    if cluster_names:
        for name in cluster_names:
            print(f"  - {name}")
    else:
        print("  (Empty cluster)")