# Implementation Guide - Step by Step

This guide walks you through implementing the semantic search system from scratch.

## Phase 1: Setup & Data Preparation (Day 1, Morning)

### 1.1 Create Project Structure

```bash
mkdir trademarkia-semantic-search
cd trademarkia-semantic-search

mkdir -p data/{raw,processed} src notebooks tests
touch src/__init__.py
```

### 1.2 Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 1.3 Create requirements.txt

Copy from provided file and install:

```bash
pip install -r requirements.txt
```

### 1.4 Download Dataset

The dataset is automatically downloaded using sklearn:

```python
from sklearn.datasets import fetch_20newsgroups
newsgroups = fetch_20newsgroups(subset='all')
```

## Phase 2: Data Preprocessing (Day 1, Afternoon)

### 2.1 Implement preprocessing.py

**Key decisions documented in code:**

```python
# Remove email headers - they're metadata, not content
# Remove quoted text (>) - redundant from previous messages
# Remove signatures (--) - personal info
# Remove URLs/emails - identifiers, not semantic
# Keep subjects - often contain key terms
# Filter docs <50 chars - likely corrupt
```

### 2.2 Run Preprocessing

```bash
cd src
python preprocessing.py
```

Output: `data/processed/cleaned_newsgroups.parquet`

### 2.3 Verify Output

```python
import pandas as pd
df = pd.read_parquet('../data/processed/cleaned_newsgroups.parquet')
print(df.head())
print(df['category'].value_counts())
```

## Phase 3: Embeddings & Vector Database (Day 1, Evening)

### 3.1 Implement embeddings.py

**Model choice: all-MiniLM-L6-v2**
- Why: Fast, 384-dim, good for retrieval
- Alternative considered: all-mpnet-base-v2 (slower but higher quality)

**Vector DB choice: ChromaDB**
- Why: No server, metadata filtering, easy persistence
- Alternative considered: FAISS (faster but less features)

### 3.2 Generate Embeddings

```bash
python embeddings.py
```

This will:
- Load cleaned data
- Generate embeddings (batched, ~5-10 mins)
- Store in ChromaDB
- Test search functionality

### 3.3 Verify Vector DB

```python
from embeddings import EmbeddingManager
em = EmbeddingManager()
print(f"Documents: {em.get_document_count()}")
results = em.search("space shuttle", n_results=5)
print(results)
```

## Phase 4: Fuzzy Clustering (Day 2, Morning)

### 4.1 Implement clustering.py

**Critical decisions:**

1. **Number of clusters:** Don't hardcode!
```python
# Test range 15-30
# Use metrics: silhouette, davies-bouldin, FPC
optimal_n = find_optimal_clusters(embeddings, 15, 30)
```

2. **Why fuzzy (not K-means)?**
```python
# Real documents have overlapping topics
# "Gun legislation" = politics + firearms
# Soft assignments reflect reality
```

### 4.2 Run Clustering

```bash
python clustering.py
```

This takes 10-20 minutes and will:
- Test different cluster counts
- Select optimal number (with evidence)
- Fit Fuzzy C-Means
- Analyze cluster composition
- Save model & membership matrix

### 4.3 Analyze Results

The script prints:
- Optimal cluster count + justification
- Top terms per cluster
- Boundary document examples
- Cluster purity metrics

**Expected findings:**
- Clusters are more granular than 20 original categories
- Meaningful semantic groupings
- Clear boundary cases (split membership)

## Phase 5: Semantic Cache (Day 2, Afternoon)

### 5.1 Implement cache.py

**THE critical tunable parameter: similarity_threshold**

```python
# Test different thresholds
thresholds = [0.85, 0.90, 0.92, 0.95, 0.98]

# 0.85: Very aggressive (more hits, risk semantic drift)
# 0.92: Sweet spot (empirically determined)
# 0.98: Very conservative (almost exact matches)
```

**Cluster-aware lookup:**

```python
# Instead of O(n) search through all cached queries:
# 1. Find query's dominant cluster
# 2. Only search cached queries in same cluster
# Result: O(n/k) where k = num clusters (~20x speedup)
```

### 5.2 Test Cache

```bash
python cache.py
```

Should demonstrate:
- Similar queries matching despite different wording
- Cluster-based indexing working
- Statistics tracking

### 5.3 Threshold Exploration

Document findings:

| Threshold | Hit Rate | False Positives | Use Case |
|-----------|----------|-----------------|----------|
| 0.85 | High | Some | Aggressive caching |
| 0.92 | Medium | Very few | Production (recommended) |
| 0.98 | Low | None | Maximum precision |

## Phase 6: FastAPI Service (Day 2, Evening)

### 6.1 Implement main.py

**State management:**
```python
# Global singleton pattern
embedding_manager: Optional[EmbeddingManager] = None
semantic_cache: Optional[SemanticCache] = None
fuzzy_clusterer: Optional[FuzzyClusterer] = None

# Initialize in lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load models
    global embedding_manager, semantic_cache, fuzzy_clusterer
    # ... initialization ...
    yield
    # Shutdown: cleanup
```

**Thread safety:**
```python
# Cache uses locks for concurrent access
self.lock = Lock()
with self.lock:
    # Critical section
```

### 6.2 Start Server

```bash
cd src
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 6.3 Test All Endpoints

Use `test_api.py`:

```bash
python test_api.py
```

Or manually:

```bash
# Health
curl http://localhost:8000/health

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "space shuttle"}'

# Stats
curl http://localhost:8000/cache/stats

# Clear
curl -X DELETE http://localhost:8000/cache
```

## Phase 7: Analysis & Documentation (Day 3, Morning)

### 7.1 Create Jupyter Notebook

Open `notebooks/analysis.ipynb` and run all cells.

This generates:
- Cluster visualizations (t-SNE)
- Purity analysis
- Boundary document examples
- Entropy analysis
- Top terms per cluster

**Save outputs for submission!**

### 7.2 Document Design Decisions

In code comments, document:
- Why you removed headers but kept subjects
- Why all-MiniLM-L6-v2 over other models
- Why ChromaDB over FAISS/Pinecone
- How you determined optimal cluster count
- Why 0.92 threshold works best
- How cluster-aware indexing improves performance

### 7.3 Update README

Ensure README includes:
- Clear setup instructions
- API usage examples
- Design decision summaries
- Clustering analysis highlights

## Phase 8: Dockerization (Day 3, Afternoon)

### 8.1 Create Dockerfile

Key points:
```dockerfile
# Use slim base image
FROM python:3.9-slim

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY src/ ./src/
COPY data/ ./data/

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.2 Create docker-compose.yml

```yaml
services:
  semantic-search-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data  # Persist data
```

### 8.3 Test Docker

```bash
# Build
docker-compose build

# Run
docker-compose up

# Test
curl http://localhost:8000/health
```

## Phase 9: Final Polish & Submission (Day 3, Evening)

### 9.1 GitHub Repository

```bash
# Initialize git
git init
git add .
git commit -m "Initial commit: Semantic search system"

# Create GitHub repo and push
git remote add origin <your-repo-url>
git push -u origin main

# Grant access
# Settings → Collaborators → Add recruitments@trademarkia.com
```

### 9.2 Verification Checklist

- [ ] `python setup.py` runs successfully
- [ ] API starts with single command: `uvicorn main:app`
- [ ] All endpoints work (`test_api.py` passes)
- [ ] Docker builds and runs
- [ ] README has clear instructions
- [ ] Code has meaningful comments
- [ ] Clustering analysis in notebook
- [ ] .gitignore excludes data/models
- [ ] Repository accessible to recruitments@trademarkia.com

### 9.3 Submit

1. Fill out submission form: https://forms.gle/4RpHZpAi8rbG9QCE8
2. Provide:
   - GitHub repository link
   - (Optional) Live deployment URL
3. Double-check access permissions

## Tips for Success

### Do's ✅
- Document decisions in code comments
- Show evidence for cluster count selection
- Explore threshold parameter systematically
- Keep setup simple (single command)
- Test everything before submitting
- Write clear commit messages

### Don'ts ❌
- Don't hardcode cluster count without justification
- Don't use Redis or caching libraries
- Don't skip the clustering analysis
- Don't leave code uncommented
- Don't over-engineer (KISS principle)
- Don't submit without testing Docker

## Troubleshooting

### "Out of memory during clustering"
```python
# Use subset of embeddings
embeddings = embeddings[:5000]
```

### "ChromaDB persistence error"
```bash
# Clear and rebuild
rm -rf data/processed/chroma_db
python embeddings.py
```

### "Import errors in Docker"
```dockerfile
# Set PYTHONPATH
ENV PYTHONPATH=/app/src
```

### "Slow embedding generation"
```python
# Reduce batch size
embeddings = model.encode(texts, batch_size=128)  # Instead of 256
```

## Estimated Timeline

| Phase | Time | Cumulative |
|-------|------|------------|
| Setup & Preprocessing | 2h | 2h |
| Embeddings | 2h | 4h |
| Clustering | 3h | 7h |
| Cache Implementation | 3h | 10h |
| FastAPI Service | 2h | 12h |
| Analysis & Documentation | 2h | 14h |
| Docker & Polish | 1h | 15h |
| **Total** | **15h** | Over 2-3 days |

Can be compressed to 10-12 hours if focused.

## Success Metrics

Your submission should demonstrate:

1. ✅ **Technical competence**: Clean code, proper architecture
2. ✅ **Understanding**: Well-justified design decisions
3. ✅ **Analysis**: Meaningful clustering insights
4. ✅ **Production readiness**: Docker, tests, documentation
5. ✅ **Attention to detail**: Comments, README, error handling

Good luck! 🚀
