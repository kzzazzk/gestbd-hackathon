# OPENALEX-HACKATHON

A hackathon-project to extract scientific articles from [OpenAlex](https://openalex.org), analyse them with PDF → LLM workflows to detect programming technologies, store the results in PostgreSQL, and export a semantic RDF/Turtle graph for further querying. Scale was lowered due to time constraints

## 🧠 Overview

This project implements a data-pipeline as follows:

1. **OpenAlex extraction** — filter by sub-field and accessible PDFs  
2. **Cache in CSV** — intermediate checkpoints for reproducibility  
3. **PDF text extraction + LLM analysis** — detect mentioned programming technologies  
4. **PostgreSQL storage** — store metadata + analysis results  
5. **RDF/Turtle export** — build a semantic graph (using Schema.org + SKOS) for semantic queries (GraphDB, SPARQL…)

## 🚀 Status

- Source code: `src/` and `db/`  
- Cache folder: `cache/`  
- Final output in Turtle: `db/openalex_graph.ttl`  
- Docker compose files included for easy deployment  

## ⚙️ Requirements

- Python 3.8+  
- Dependencies:  
  - `requests`, `psycopg2`, `pandas`, `rdflib`, `PyMuPDF (fitz)`, `beautifulsoup4`, `openai`  
  - See `requirements.txt`  
- Docker (optional, for PostgreSQL/pgAdmin and GraphDB)  

## 🧩 Setup

1. If using Docker, create the network (if referenced in compose):  
   ```bash
   docker network create gestbd_net

2. Build and start the services with Docker Compose:  
   ```bash
   docker-compose up --build
   
This will start PostgreSQL, pgAdmin, and GraphDB, along with any required service containers.

3. Create a Python virtual environment (if running locally outside Docker) and install dependencies:   ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

4. Configure environment variables for the project:
    ```bash
    OPENAI_API_KEY=your_openai_api_key

5. Follow the `notebook/presentation.ipynb`

## 📝 Data Sources and Attribution
Considering that OpenAlex is a content aggregator, it is important to take into account the sources that feed it, primarily:

- The now-defunct Microsoft Academic Graph (MAG)

- Crossref

- ORCID

- arXiv

- Various academic publishers
## 📜 License

This project is released under the MIT License. See LICENSE for details.

