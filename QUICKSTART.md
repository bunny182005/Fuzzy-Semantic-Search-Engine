# Quick Start Guide

Get the semantic search system running in 5 minutes.

## Prerequisites

- Python 3.9+
- 4GB RAM
- 2GB disk space

## Step 1: Setup (5 minutes)

```bash
# Clone repository
git clone <your-repo-url>
cd trademarkia-semantic-search

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Initialize System (10-15 minutes, one-time)

```bash
# Run setup script
python setup.py
```

This will:
- Download & clean 20 Newsgroups dataset
- Generate embeddings (sentence-transformers)
- Perform fuzzy clustering
- Setup vector database (ChromaDB)

**Note:** This is a one-time setup. The data persists in `data/processed/`

## Step 3: Start API Server

```bash
cd src
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server starts at: http://localhost:8000

## Step 4: Test the API

In a new terminal:

```bash
# Activate venv
source venv/bin/activate

# Run test suite
python test_api.py
```

Or test manually with curl:

```bash
# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "space shuttle launch"}'

# Check cache stats
curl http://localhost:8000/cache/stats

# Clear cache
curl -X DELETE http://localhost:8000/cache
```

## Step 5: Explore API Documentation

Visit: http://localhost:8000/docs

FastAPI provides interactive documentation (Swagger UI).

## Using Docker (Alternative)

```bash
# First run setup.py locally to generate data
python setup.py

# Then build and run with Docker
docker-compose up --build
```

## Common Issues

**Issue:** "ModuleNotFoundError"
**Solution:** Make sure venv is activated and requirements are installed

**Issue:** "Connection refused" during tests
**Solution:** Make sure API server is running in another terminal

**Issue:** "Out of memory" during setup
**Solution:** Reduce batch size in embeddings.py (line 82)

## What's Next?

- Check out `notebooks/analysis.ipynb` for clustering analysis
- Read `README.md` for detailed documentation
- Experiment with different queries to test semantic cache
- Try adjusting similarity threshold in `src/main.py` (line 58)

## Example Queries to Try

```bash
# Space/astronomy
{"query": "NASA space mission"}
{"query": "spacecraft launch"} # Should hit cache

# Politics
{"query": "gun control legislation"}
{"query": "firearm laws"} # Should hit cache

# Technology
{"query": "computer graphics rendering"}
{"query": "3D graphics"} # Should hit cache

# Sports
{"query": "baseball game score"}
{"query": "baseball match results"} # Should hit cache
```

## Directory Structure After Setup

```
trademarkia-semantic-search/
├── data/
│   └── processed/
│       ├── cleaned_newsgroups.parquet  # Cleaned dataset
│       ├── chroma_db/                   # Vector database
│       ├── fuzzy_clustering.pkl         # Clustering model
│       └── membership_matrix.npy        # Membership matrix
├── src/                                 # Source code
└── venv/                                # Virtual environment
```

## Support

For issues or questions:
- GitHub Issues
- Email: recruitments@trademarkia.com

Happy searching! 🚀
