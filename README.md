# ⚡ SemantiCache: AI Search with Fuzzy Clustering & Smart Caching

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.103.0+-00a393.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.27.0+-FF4B4B.svg)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Storage-orange.svg)

This project moves beyond standard keyword matching to create an end-to-end semantic search pipeline. Built with **FastAPI**, **Streamlit**, and **ChromaDB**, it uses dense vector embeddings to understand the actual meaning behind a search query. 

By combining **Fuzzy C-Means clustering** (allowing documents to exist in multiple topic categories at once) with a custom **semantic caching layer**, the system slashes processing time for similar queries by over 95%, serving cached results in milliseconds.



## ✨ Key Features

* **Dense Vector Retrieval:** Uses Hugging Face's `all-MiniLM-L6-v2` sentence transformers to understand contextual meaning rather than relying on exact keyword matches.
* **Intelligent Semantic Caching:** Bypasses expensive vector database lookups. If a new query is conceptually similar to a previously cached query (similarity > 92%), it returns the cached result instantly.
* **Fuzzy C-Means Soft Clustering:** Implements `skfuzzy` to dynamically group results. Unlike strict K-Means, this allows real-world documents to belong to multiple topics simultaneously (e.g., 70% "Politics", 30% "Firearms").
* **Persistent Vector Database:** Integrates **ChromaDB** for efficient, scalable storage of 20,000+ document embeddings.
* **Interactive Web UI:** A beautiful, real-time frontend built with **Streamlit** to visualize search results and cache performance metrics.

## 🛠️ Tech Stack

* **Backend API:** FastAPI, Uvicorn, Pydantic
* **Frontend:** Streamlit
* **Machine Learning:** Sentence-Transformers, scikit-fuzzy, scikit-learn
* **Data & Storage:** ChromaDB, Pandas, NumPy, Parquet

## 📂 Project Structure

```text
├── src/
│   ├── main.py             # FastAPI server and endpoints
│   ├── preprocessing.py    # Text cleaning and data loading
│   ├── embeddings.py       # SentenceTransformer & ChromaDB logic
│   ├── clustering.py       # Fuzzy C-Means implementation
│   └── cache.py            # In-memory semantic caching system
├── data/                   # (Git Ignored) Processed DB and models
├── app.py                  # Streamlit frontend UI
├── setup.py                # Initialization script (Data pipeline)
├── test_api.py             # Automated API test suite
├── requirements.txt        # Python dependencies
└── README.md
```


##🚀 Quick Start Guide

## 1. Prerequisites & Installation
Ensure you have Python 3.9+ installed. Clone the repository and set up your virtual environment:

Bash
* git clone (https://github.com/bunny182005/Fuzzy-Semantic-Search-Engine.git)
* cd Fuzzy-Semantic-Search-Engine

* python -m venv venv
* source venv/bin/activate  # On Windows: venv\Scripts\activate

* pip install -r requirements.txt
#2. Initialize the Data Pipeline
Run the setup script from the root directory. This downloads the 20 Newsgroups dataset, cleans the text, generates vector embeddings, trains the fuzzy clustering model, and saves the system state locally.

  Bash
* python setup.py
(Note: Grab a coffee! This step takes a few minutes as it encodes 20,000 documents into the local vector database).

#3. Start the Backend API
*Launch the FastAPI server. Run this from the root directory, pointing Uvicorn to the src folder:

* Bash
* uvicorn main:app --app-dir src --host 0.0.0.0 --port 8000
* Interactive API Documentation is available at: http://localhost:8000/docs

#4. Start the Web UI
Open a new terminal, activate your virtual environment, and launch the Streamlit app:

* Bash
*streamlit run app.py
The UI will automatically open in your browser at http://localhost:8501.
