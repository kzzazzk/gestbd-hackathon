import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 1. Cargar tus tecnologías
try:
    df = pd.read_csv("tecnologia.csv")
    print("CSV file 'tecnologia.csv' loaded successfully.")
except FileNotFoundError:
    print("Error: 'tecnologia.csv' not found.")
    exit()

# 2. Define your "Clean List" of target technologies
# These are the "labels" we want to map everything to.
# I'm using the main list we built in our previous chat.
target_languages = [
    'Java', 'Python', 'C', 'C++', 'JavaScript', 'Lisp', 'Prolog',
    'OCaml', 'BASIC', 'Visual Basic', 'Pascal', 'MATLAB', 'COBOL',
    'Octave', 'Objective-C', 'R', 'Perl', 'Lua', 'SQL', 'Fortran', 'C#'
]
print(f"Defined {len(target_languages)} target languages to map to.")


# 3. Crear embeddings for both lists
print("Loading sentence model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Encoding target languages...")
# Create embeddings for our "clean" list
target_embeddings = model.encode(target_languages)

print("Encoding technologies from CSV...")
# Create embeddings for our "dirty" list from the CSV
# We embed the names themselves, not the descriptions, for a more direct comparison
df_names = df["nombre"].tolist()
df_embeddings = model.encode(df_names)

print("Encoding complete.")

# 4. Find the Closest Match (This REPLACES K-Means)
print("Calculating similarities and finding closest matches...")

# Calculate the cosine similarity between ALL dirty names and ALL clean targets
# This creates a giant matrix: (num_df_names x num_target_languages)
sim_matrix = cosine_similarity(df_embeddings, target_embeddings)

# For each row in the matrix (each "dirty" name), find the index of the highest score
# np.argmax finds the *position* (index) of the maximum value
closest_target_indices = np.argmax(sim_matrix, axis=1)

# 5. Create the new column using the matched names
# Use the indices to "look up" the name from our target_languages list
df["tecnologia_nueva"] = [target_languages[i] for i in closest_target_indices]

# 6. Guardar el nuevo CSV
output_file = "tecnologia_mapped_ml.csv"
df.to_csv(output_file, index=False)

print(f"\nSuccessfully created new file: '{output_file}'")

# 7. Explorar los resultados
print("\n--- Exploring ML-Based Mapping Results (Sample) ---")
# Show some examples of what was mapped
sample_mappings = df[df["nombre"] != df["tecnologia_nueva"]]
print(sample_mappings[["id", "nombre", "tecnologia_nueva"]].head(20).to_markdown(index=False))

# Show a specific example
print("\n--- Checking for 'Java Bytecode' ---")
java_example = df[df["nombre"] == "Java Bytecode"]
print(java_example[["id", "nombre", "tecnologia_nueva"]].to_markdown(index=False))