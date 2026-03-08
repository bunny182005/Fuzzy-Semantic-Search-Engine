"""
FastAPI Service for Semantic Search with Cache

This module implements the API endpoints for the semantic search system.

Endpoints:
- POST /query: Semantic search with cache
- GET /cache/stats: Cache statistics
- DELETE /cache: Clear cache

State Management:
- Global cache object (singleton pattern)
- Thread-safe operations
- Persistent vector DB, in-memory cache
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional
import numpy as np
from contextlib import asynccontextmanager
import time

# Import our custom modules
from embeddings import EmbeddingManager
from cache import SemanticCache
from clustering import FuzzyClusterer

# ============================================================================
# Global State Management
# ============================================================================

# These will be initialized on startup
embedding_manager: Optional[EmbeddingManager] = None
semantic_cache: Optional[SemanticCache] = None
fuzzy_clusterer: Optional[FuzzyClusterer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Initializes global state on startup, cleans up on shutdown.
    """
    global embedding_manager, semantic_cache, fuzzy_clusterer
    
    print("="*80)
    print("STARTING SEMANTIC SEARCH SERVICE")
    print("="*80)
    
    # Initialize embedding manager
    print("\n1. Loading embedding model and vector database...")
    embedding_manager = EmbeddingManager(
        persist_directory="./data/processed/chroma_db"
    )
    print(f"   Vector database contains {embedding_manager.get_document_count()} documents")
    
    # Load clustering model
    print("\n2. Loading fuzzy clustering model...")
    fuzzy_clusterer = FuzzyClusterer()
    try:
        fuzzy_clusterer.load('./data/processed/fuzzy_clustering.pkl')
        print(f"   Loaded clustering with {fuzzy_clusterer.n_clusters} clusters")
    except FileNotFoundError:
        print("   WARNING: Clustering model not found. Run clustering.py first.")
        print("   Service will continue but cluster features will be limited.")
    
    # Initialize semantic cache with optimal threshold
    # Based on empirical testing, 0.92 provides good balance
    print("\n3. Initializing semantic cache...")
    semantic_cache = SemanticCache(similarity_threshold=0.92)
    print("   Cache ready")
    
    print("\n" + "="*80)
    print("SERVICE READY")
    print("="*80)
    print("\nEndpoints:")
    print("  POST   /query          - Semantic search")
    print("  GET    /cache/stats    - Cache statistics")
    print("  DELETE /cache          - Clear cache")
    print("  GET    /health         - Health check")
    print("="*80 + "\n")
    
    yield
    
    # Shutdown
    print("\nShutting down service...")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Semantic Search API",
    description="Semantic search with fuzzy clustering and intelligent caching",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Request/Response Models
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for /query endpoint."""
    query: str = Field(..., description="Natural language search query", min_length=1)


class QueryResponse(BaseModel):
    """Response model for /query endpoint."""
    query: str
    cache_hit: bool
    matched_query: Optional[str] = None
    similarity_score: Optional[float] = None
    result: Dict
    dominant_cluster: int
    processing_time_ms: Optional[float] = None


class CacheStats(BaseModel):
    """Response model for /cache/stats endpoint."""
    total_entries: int
    hit_count: int
    miss_count: int
    total_queries: int
    hit_rate: float
    similarity_threshold: float


class CacheFlushResponse(BaseModel):
    """Response model for /cache DELETE endpoint."""
    message: str
    entries_cleared: int


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vector_db_docs": embedding_manager.get_document_count() if embedding_manager else 0,
        "cache_entries": len(semantic_cache.embedding_cache) if semantic_cache else 0
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Semantic search endpoint with intelligent caching.
    
    Process:
    1. Embed the query
    2. Determine dominant cluster
    3. Check semantic cache (cluster-aware)
    4. On miss: search vector DB, cache result
    5. Return response
    """
    start_time = time.time()
    
    if not embedding_manager or not semantic_cache:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    query_text = request.query.strip()
    
    try:
        # Step 1: Embed the query
        query_embedding = embedding_manager.embed_documents(
            [query_text],
            show_progress=False
        )[0]
        
        # Step 2: Determine dominant cluster
        if fuzzy_clusterer and fuzzy_clusterer.cntr is not None:
            # Calculate distance from query to each cluster center
            # cntr is (n_clusters, n_features), query_embedding is (n_features,)
            # axis=1 calculates the norm across the feature axis
            distances = np.linalg.norm(
                fuzzy_clusterer.cntr - query_embedding,
                axis=1
            )
            # Inverse distance weighting (closer = higher membership)
            memberships = 1 / (distances + 1e-10)
            memberships = memberships / memberships.sum()
            dominant_cluster = int(np.argmax(memberships))
        else:
            # Fallback if clustering not available
            dominant_cluster = 0
        
        # Step 3: Check cache
        cached_result = semantic_cache.get(
            query_text,
            query_embedding,
            dominant_cluster
        )
        
        if cached_result:
            # Cache hit!
            processing_time = (time.time() - start_time) * 1000
            
            return QueryResponse(
                query=query_text,
                cache_hit=True,
                matched_query=cached_result['matched_query'],
                similarity_score=cached_result['similarity_score'],
                result=cached_result['result'],
                dominant_cluster=cached_result['dominant_cluster'],
                processing_time_ms=processing_time
            )
        
        # Step 4: Cache miss - perform search
        search_results = embedding_manager.search(
            query_text,
            n_results=5
        )
        
        # Format results
        result = {
            'documents': search_results['documents'][0] if search_results['documents'] else [],
            'distances': [float(d) for d in search_results['distances'][0]] if search_results['distances'] else [],
            'metadatas': search_results['metadatas'][0] if search_results['metadatas'] else []
        }
        
        # Step 5: Cache the result
        semantic_cache.put(
            query_text,
            query_embedding,
            result,
            dominant_cluster
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return QueryResponse(
            query=query_text,
            cache_hit=False,
            matched_query=None,
            similarity_score=None,
            result=result,
            dominant_cluster=dominant_cluster,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.get("/cache/stats", response_model=CacheStats)
async def get_cache_stats():
    """
    Get cache statistics.
    
    Returns:
        Current cache state including hits, misses, and hit rate
    """
    if not semantic_cache:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    stats = semantic_cache.get_stats()
    
    return CacheStats(
        total_entries=stats['total_entries'],
        hit_count=stats['hit_count'],
        miss_count=stats['miss_count'],
        total_queries=stats['total_queries'],
        hit_rate=stats['hit_rate'],
        similarity_threshold=stats['similarity_threshold']
    )


@app.delete("/cache", response_model=CacheFlushResponse)
async def clear_cache():
    """
    Clear all cache entries and reset statistics.
    
    Returns:
        Confirmation message with number of entries cleared
    """
    if not semantic_cache:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    entries_before = len(semantic_cache.embedding_cache)
    semantic_cache.clear()
    
    return CacheFlushResponse(
        message="Cache cleared successfully",
        entries_cleared=entries_before
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\nStarting Semantic Search API...")
    print("Make sure you have:")
    print("  1. Run preprocessing.py to clean the data")
    print("  2. Run embeddings.py to populate the vector database")
    print("  3. Run clustering.py to generate cluster assignments")
    print("\nStarting server on http://0.0.0.0:8000")
    print("="*80)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False  # Set to True during development
    )