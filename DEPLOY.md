# 🚀 DEPLOYMENT INSTRUCTIONS

## Quick Deploy (Copy-Paste Ready)

### Step 1: Extract and Setup (5 minutes)

```bash
# Navigate to the project folder
cd trademarkia-semantic-search

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### Step 2: Initialize System (10-15 minutes, ONE-TIME only)

```bash
# This downloads data, generates embeddings, and performs clustering
python setup.py
```

**What happens:**
- Downloads 20 Newsgroups dataset (~20,000 documents)
- Cleans and preprocesses text
- Generates embeddings using sentence-transformers
- Performs fuzzy clustering analysis
- Saves everything to `data/processed/`

**Expected output:**
```
================================================================================
SEMANTIC SEARCH SYSTEM - INITIAL SETUP
================================================================================

STEP 1: DATA PREPROCESSING
Loaded 18846 documents
✓ Saved cleaned data to data/processed/cleaned_newsgroups.parquet

STEP 2: GENERATING EMBEDDINGS
✓ Added 18846 documents to vector database

STEP 3: FUZZY CLUSTERING
✓ Optimal number of clusters: 24
✓ Saved clustering to data/processed/fuzzy_clustering.pkl

STEP 4: VERIFICATION
✓ data/processed/cleaned_newsgroups.parquet
✓ data/processed/chroma_db
✓ data/processed/fuzzy_clustering.pkl

✓ SETUP COMPLETE!
```

### Step 3: Start the API Server

```bash
# Navigate to src directory
cd src

# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Server starts at:** http://localhost:8000

**You should see:**
```
================================================================================
STARTING SEMANTIC SEARCH SERVICE
================================================================================

1. Loading embedding model and vector database...
   Vector database contains 18846 documents

2. Loading fuzzy clustering model...
   Loaded clustering with 24 clusters

3. Initializing semantic cache...
   Cache ready

================================================================================
SERVICE READY
================================================================================

Endpoints:
  POST   /query          - Semantic search
  GET    /cache/stats    - Cache statistics
  DELETE /cache          - Clear cache
  GET    /health         - Health check
```

### Step 4: Test the API (In a new terminal)

```bash
# Activate venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run automated tests
python test_api.py
```

**Or test manually:**

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Test 2: Semantic search
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "NASA space shuttle mission"}'

# Test 3: Similar query (should hit cache)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "spacecraft launch to orbit"}'

# Test 4: Cache statistics
curl http://localhost:8000/cache/stats

# Test 5: Clear cache
curl -X DELETE http://localhost:8000/cache
```

### Step 5: View API Documentation

Open browser: http://localhost:8000/docs

Interactive Swagger UI with all endpoints documented.

---

## 🐳 Docker Deployment (Alternative)

### Option A: Quick Docker Run

```bash
# First, run setup locally to generate data
python setup.py

# Build and run with docker-compose
docker-compose up --build
```

### Option B: Manual Docker

```bash
# Build image
docker build -t semantic-search-api .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  semantic-search-api
```

**Access API at:** http://localhost:8000

---

## 📊 Using Jupyter Notebook for Analysis

```bash
# Make sure venv is activated
source venv/bin/activate

# Start Jupyter
jupyter notebook

# Open: notebooks/analysis.ipynb
```

**The notebook includes:**
- Cluster size distribution
- Category vs cluster confusion matrix
- Membership distribution analysis
- Boundary document examples
- t-SNE visualization
- Top terms per cluster
- Entropy analysis

---

## 🧪 Example API Usage

### Python Example

```python
import requests

# Query the API
response = requests.post(
    "http://localhost:8000/query",
    json={"query": "gun control legislation"}
)

result = response.json()
print(f"Cache hit: {result['cache_hit']}")
print(f"Dominant cluster: {result['dominant_cluster']}")
print(f"Top documents: {len(result['result']['documents'])}")
```

### JavaScript Example

```javascript
fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'computer graphics rendering' })
})
.then(res => res.json())
.then(data => console.log(data));
```

### cURL Examples

```bash
# Space/Astronomy queries
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Mars rover mission"}'

# Politics queries
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "gun control laws"}'

# Technology queries
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "graphics card GPU"}'

# Sports queries
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "baseball game score"}'
```

---

## 🎯 For GitHub Submission

### Step 1: Initialize Git Repository

```bash
cd trademarkia-semantic-search

git init
git add .
git commit -m "feat: Complete semantic search system with fuzzy clustering and semantic cache"
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `trademarkia-semantic-search`
3. Description: "Semantic search system with fuzzy clustering and intelligent caching"
4. **Keep it Private** (for now)
5. Don't initialize with README (we already have one)
6. Click "Create repository"

### Step 3: Push to GitHub

```bash
# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/trademarkia-semantic-search.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Grant Access

1. Go to repository Settings
2. Click "Collaborators and teams"
3. Click "Add people"
4. Add: **recruitments@trademarkia.com**
5. Select "Write" access
6. Send invitation

### Step 5: Submit

1. Go to: https://forms.gle/4RpHZpAi8rbG9QCE8
2. Fill in:
   - Your details
   - GitHub repository link: `https://github.com/YOUR_USERNAME/trademarkia-semantic-search`
   - (Optional) Live deployment URL if you deploy to cloud
3. Submit

---

## 🔍 Verification Checklist

Before submitting, verify:

- [ ] `python setup.py` completes successfully
- [ ] `uvicorn main:app` starts the server
- [ ] `python test_api.py` passes all tests
- [ ] `docker-compose up` works (if using Docker)
- [ ] All files have meaningful comments
- [ ] README.md is clear and complete
- [ ] Repository is on GitHub
- [ ] Access granted to recruitments@trademarkia.com
- [ ] Submission form filled out

---

## 📁 File Structure (Final)

```
trademarkia-semantic-search/
├── README.md                    ✓ Comprehensive docs
├── QUICKSTART.md               ✓ 5-min guide
├── IMPLEMENTATION_GUIDE.md     ✓ Step-by-step
├── requirements.txt            ✓ Dependencies
├── setup.py                    ✓ Initialization
├── test_api.py                ✓ Tests
├── Dockerfile                  ✓ Container
├── docker-compose.yml         ✓ Orchestration
├── .gitignore                 ✓ Git config
│
├── src/
│   ├── __init__.py            ✓ Package init
│   ├── preprocessing.py       ✓ Part 1: Data cleaning
│   ├── embeddings.py          ✓ Part 1: Vector DB
│   ├── clustering.py          ✓ Part 2: Fuzzy clustering
│   ├── cache.py              ✓ Part 3: Semantic cache
│   └── main.py               ✓ Part 4: FastAPI
│
├── notebooks/
│   └── analysis.ipynb        ✓ Analysis
│
└── data/
    ├── raw/.gitkeep          ✓ Placeholder
    └── processed/            ✓ Generated during setup
        ├── cleaned_newsgroups.parquet
        ├── chroma_db/
        ├── fuzzy_clustering.pkl
        └── membership_matrix.npy
```

---

## 🆘 Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution:**
```bash
# Make sure venv is activated
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Use different port
uvicorn main:app --host 0.0.0.0 --port 8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9  # Mac/Linux
```

### Issue: "Out of memory during setup"
**Solution:**
- Reduce batch size in `src/embeddings.py` line 82: `batch_size=128`
- Or use subset: modify `setup.py` to use `subset='train'` instead of `'all'`

### Issue: "ChromaDB persistence error"
**Solution:**
```bash
# Clear and rebuild
rm -rf data/processed/chroma_db
python setup.py
```

### Issue: "sklearn download error"
**Solution:**
```bash
# Manual download
from sklearn.datasets import fetch_20newsgroups
fetch_20newsgroups(subset='all', download_if_missing=True)
```

---

## 💡 Pro Tips

1. **First time?** Follow QUICKSTART.md
2. **Want to understand?** Read IMPLEMENTATION_GUIDE.md
3. **Customizing?** All key parameters are documented in code
4. **Issues?** Check troubleshooting section above
5. **Interview prep?** Review design decisions in code comments

---

## 📞 Support

- **Documentation:** See README.md
- **Issues:** Create GitHub issue after repo setup
- **Contact:** recruitments@trademarkia.com

---

## 🎉 You're Ready!

Everything is set up and ready to go. Just:
1. Run `python setup.py` (one time)
2. Start server with `uvicorn main:app`
3. Test with `python test_api.py`
4. Push to GitHub
5. Submit the form

**Good luck with your submission!** 🚀
