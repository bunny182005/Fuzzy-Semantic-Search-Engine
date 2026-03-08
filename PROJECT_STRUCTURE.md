# 📁 Project Structure - Visual Guide

## Complete Directory Tree

```
trademarkia-semantic-search/
│
├── 📚 Documentation (5 files)
│   ├── README.md                      # Main documentation (start here!)
│   ├── QUICKSTART.md                  # Get running in 5 minutes
│   ├── IMPLEMENTATION_GUIDE.md        # Step-by-step walkthrough
│   ├── DEPLOY.md                      # Deployment instructions
│   └── CHECKLIST.md                   # Submission checklist
│
├── ⚙️ Configuration (4 files)
│   ├── requirements.txt               # Python dependencies
│   ├── .gitignore                     # Git ignore rules
│   ├── Dockerfile                     # Docker container definition
│   └── docker-compose.yml            # Docker orchestration
│
├── 🔧 Scripts (2 files)
│   ├── setup.py                       # One-command initialization
│   └── test_api.py                    # Automated API tests
│
├── 💻 Source Code (6 files in src/)
│   └── src/
│       ├── __init__.py               # Package initialization
│       ├── preprocessing.py          # ✅ Part 1: Data cleaning
│       ├── embeddings.py             # ✅ Part 1: Vector database
│       ├── clustering.py             # ✅ Part 2: Fuzzy clustering
│       ├── cache.py                  # ✅ Part 3: Semantic cache
│       └── main.py                   # ✅ Part 4: FastAPI service
│
├── 📊 Analysis (1 file in notebooks/)
│   └── notebooks/
│       └── analysis.ipynb            # Clustering visualization & analysis
│
└── 📦 Data (created during setup)
    └── data/
        ├── raw/                      # Original dataset (auto-downloaded)
        │   └── .gitkeep              # Preserve directory structure
        └── processed/                # Generated files (not in git)
            ├── cleaned_newsgroups.parquet      # Cleaned dataset
            ├── fuzzy_clustering.pkl            # Clustering model
            ├── membership_matrix.npy           # Cluster memberships
            ├── chroma_db/                      # Vector database
            └── .gitkeep                        # Preserve directory structure
```

## File Count

```
📄 Total Files in Repository: 19 files

Documentation:        5 files (README.md, QUICKSTART.md, etc.)
Configuration:        4 files (requirements.txt, Dockerfile, etc.)
Scripts:              2 files (setup.py, test_api.py)
Source Code:          6 files (preprocessing.py, embeddings.py, etc.)
Analysis:             1 file  (analysis.ipynb)
Placeholders:         2 files (.gitkeep files)
```

## What Gets Committed to Git

```bash
✅ Committed (tracked by git):
   - All documentation (*.md)
   - All source code (src/*.py)
   - Configuration files
   - Scripts
   - Notebooks
   - .gitkeep files (preserve structure)

❌ Not Committed (in .gitignore):
   - venv/ (virtual environment)
   - data/processed/*.parquet (generated data)
   - data/processed/*.pkl (models)
   - data/processed/*.npy (numpy arrays)
   - data/processed/chroma_db/ (vector database)
   - __pycache__/ (Python cache)
   - *.pyc (compiled Python)
```

## File Sizes (Approximate)

```
Code Files:
  preprocessing.py      ~5 KB    (160 lines)
  embeddings.py         ~7 KB    (210 lines)
  clustering.py         ~12 KB   (380 lines)
  cache.py             ~10 KB    (310 lines)
  main.py              ~8 KB     (250 lines)
  setup.py             ~6 KB     (170 lines)
  test_api.py          ~5 KB     (150 lines)

Documentation:
  README.md            ~20 KB    (comprehensive)
  IMPLEMENTATION_GUIDE ~15 KB    (step-by-step)
  QUICKSTART.md        ~5 KB     (quick reference)
  DEPLOY.md            ~12 KB    (deployment guide)
  CHECKLIST.md         ~10 KB    (submission checklist)

Total Repository Size: ~100 KB (source only)
Total After Setup: ~500 MB (with data & models)
```

## What Each File Does

### 📚 Documentation

| File | Purpose | When to Read |
|------|---------|--------------|
| **README.md** | Main documentation with API examples | First time setup |
| **QUICKSTART.md** | 5-minute getting started guide | Quick deployment |
| **IMPLEMENTATION_GUIDE.md** | Step-by-step implementation walkthrough | Learning/customizing |
| **DEPLOY.md** | Deployment instructions & troubleshooting | Before deployment |
| **CHECKLIST.md** | Submission verification checklist | Before submitting |

### ⚙️ Configuration

| File | Purpose | Edit? |
|------|---------|-------|
| **requirements.txt** | Python dependencies with versions | Rarely |
| **.gitignore** | Files to exclude from git | Rarely |
| **Dockerfile** | Container image definition | If customizing Docker |
| **docker-compose.yml** | Multi-container orchestration | If changing ports |

### 🔧 Scripts

| File | Purpose | Run When |
|------|---------|----------|
| **setup.py** | Initialize system (download data, build embeddings) | Once before first use |
| **test_api.py** | Automated API testing | After starting server |

### 💻 Source Code

| File | Lines | Purpose | Assessment Part |
|------|-------|---------|----------------|
| **preprocessing.py** | 160 | Data cleaning & preparation | Part 1 |
| **embeddings.py** | 210 | Embedding generation & ChromaDB | Part 1 |
| **clustering.py** | 380 | Fuzzy C-Means clustering | Part 2 |
| **cache.py** | 310 | Custom semantic cache | Part 3 |
| **main.py** | 250 | FastAPI service | Part 4 |
| **__init__.py** | 10 | Package initialization | - |

### 📊 Analysis

| File | Purpose | When to Use |
|------|---------|-------------|
| **analysis.ipynb** | Jupyter notebook with visualizations | After clustering complete |

## Key Design Decisions Per File

### preprocessing.py
```
✓ Removes email headers (noise)
✓ Keeps subject lines (key terms)
✓ Removes quoted text (redundant)
✓ Filters docs < 50 chars (corrupt)
```

### embeddings.py
```
✓ Model: all-MiniLM-L6-v2 (fast, quality)
✓ Vector DB: ChromaDB (no server needed)
✓ Batch processing (efficient)
✓ Normalized embeddings (cosine similarity)
```

### clustering.py
```
✓ Fuzzy C-Means (soft assignments)
✓ Evidence-based cluster count (15-30 range)
✓ Multiple metrics (silhouette, DB index)
✓ Boundary document detection
```

### cache.py
```
✓ Custom implementation (no Redis)
✓ Cluster-aware lookup (O(n/k) scaling)
✓ Similarity threshold: 0.92 (tunable)
✓ Thread-safe (locks)
```

### main.py
```
✓ 3 endpoints (query, stats, clear)
✓ Proper state management (lifespan)
✓ Error handling
✓ Single-command startup
```

## Execution Flow

```
1. First Time Setup:
   python setup.py
   ↓
   Downloads 20 Newsgroups → Cleans data → Generates embeddings
   ↓
   Performs clustering → Saves models to data/processed/

2. Start Server:
   cd src
   uvicorn main:app --host 0.0.0.0 --port 8000
   ↓
   Loads embeddings → Loads clustering → Initializes cache
   ↓
   Server ready at http://localhost:8000

3. Handle Query:
   POST /query {"query": "space shuttle"}
   ↓
   Embed query → Find dominant cluster → Check cache
   ↓
   If miss: Search vector DB → Cache result
   ↓
   Return response with cluster & cache info

4. View Stats:
   GET /cache/stats
   ↓
   Return hit rate, entries, threshold

5. Clear Cache:
   DELETE /cache
   ↓
   Reset all cache entries and stats
```

## Data Flow

```
Raw Text (20 Newsgroups)
    ↓
preprocessing.py → Clean Text
    ↓
embeddings.py → Vector Embeddings (384-dim)
    ↓
    ├─→ ChromaDB (Vector Store)
    └─→ clustering.py → Cluster Assignments
            ↓
        Membership Matrix (n_docs × n_clusters)
            ↓
        main.py (FastAPI)
            ↓
        cache.py (Semantic Cache)
            ↓
        Query Response
```

## Dependencies Graph

```
main.py
  ├─ embeddings.py
  │   └─ sentence-transformers
  │   └─ chromadb
  ├─ cache.py
  │   └─ numpy
  └─ clustering.py
      └─ scikit-fuzzy
      └─ sklearn

setup.py
  ├─ preprocessing.py
  │   └─ sklearn.datasets
  │   └─ pandas
  ├─ embeddings.py
  └─ clustering.py
```

## API Endpoints

```
GET /health
├─ Returns: Server status
└─ Use: Health check

POST /query
├─ Input: {"query": "text"}
├─ Returns: Search results + cache info
└─ Use: Main search endpoint

GET /cache/stats
├─ Returns: Hit rate, entries, metrics
└─ Use: Monitor cache performance

DELETE /cache
├─ Returns: Confirmation
└─ Use: Reset cache state
```

## Quick Reference Commands

```bash
# Setup (one time)
python setup.py

# Start server
cd src && uvicorn main:app --host 0.0.0.0 --port 8000

# Test
python test_api.py

# Docker
docker-compose up --build

# Jupyter
jupyter notebook notebooks/analysis.ipynb

# Git
git init
git add .
git commit -m "Initial commit"
git push origin main
```

---

**Total Project: 19 files, ~100 KB source, ~500 MB with data**

**Ready for submission!** 🚀
