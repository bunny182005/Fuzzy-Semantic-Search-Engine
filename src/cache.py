"""
Semantic Cache Module

Custom cache implementation (no Redis, no external libraries).

Key Design Decisions:

1. Similarity Threshold (THE tunable parameter):
   - Determines when two queries are "similar enough" to reuse results
   - Lower threshold (e.g., 0.85): More aggressive caching, more hits, risk of semantic drift
   - Higher threshold (e.g., 0.98): Stricter matching, fewer false positives, more misses
   - Sweet spot typically 0.90-0.95 based on empirical testing

2. Cluster-Aware Lookup:
   - First: Determine query's dominant cluster
   - Then: Only compare against cached queries in same cluster
   - Benefit: O(n) → O(n/k) where k = number of clusters
   - Critical for scalability when cache has thousands of entries

3. Data Structure:
   - embedding_cache: Main storage (query hash → cached result)
   - cluster_index: Inverted index (cluster_id → list of query hashes)
   - Thread-safe with locks for concurrent access

Why No External Libraries:
- Full control over similarity computation
- Understanding of cache mechanics
- No hidden behaviors or dependencies
- Demonstrates algorithmic thinking
"""

import numpy as np
import hashlib
import time
from typing import Dict, Optional, Tuple, List
from threading import Lock
import json


class SemanticCache:
    """
    Custom semantic cache with cluster-aware lookup.
    
    Recognizes semantically similar queries even if phrased differently.
    """
    
    def __init__(self, similarity_threshold: float = 0.92):
        """
        Initialize semantic cache.
        
        Args:
            similarity_threshold: Cosine similarity threshold for cache hits
                                 (0.0 = match anything, 1.0 = exact match only)
        """
        self.similarity_threshold = similarity_threshold
        
        # Main cache storage
        # Structure: {query_hash: {query, embedding, result, cluster, timestamp}}
        self.embedding_cache: Dict[str, Dict] = {}
        
        # Cluster-based index for efficient lookup
        # Structure: {cluster_id: [query_hash1, query_hash2, ...]}
        self.cluster_index: Dict[int, List[str]] = {}
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_queries': 0
        }
        
        # Thread safety
        self.lock = Lock()
        
        print(f"Initialized SemanticCache with threshold={similarity_threshold}")
    
    def _hash_query(self, query: str) -> str:
        """Generate unique hash for a query string."""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Assumes vectors are already normalized (which they are from our embeddings).
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Similarity score in [0, 1] (1 = identical)
        """
        # Since vectors are normalized, dot product = cosine similarity
        return float(np.dot(vec1, vec2))
    
    def _find_similar_cached_query(
        self,
        query_embedding: np.ndarray,
        dominant_cluster: int
    ) -> Optional[Tuple[str, float]]:
        """
        Find a cached query similar to the input embedding.
        
        This is the core cache lookup logic with cluster-aware filtering.
        
        Args:
            query_embedding: Embedding of the query
            dominant_cluster: Dominant cluster ID of the query
        
        Returns:
            Tuple of (query_hash, similarity_score) if found, None otherwise
        """
        # Get cached queries in the same cluster
        if dominant_cluster not in self.cluster_index:
            return None
        
        candidate_hashes = self.cluster_index[dominant_cluster]
        
        if not candidate_hashes:
            return None
        
        # Find most similar cached query
        best_match = None
        best_similarity = 0.0
        
        for query_hash in candidate_hashes:
            cached_entry = self.embedding_cache[query_hash]
            cached_embedding = cached_entry['embedding']
            
            # Compute similarity
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = query_hash
        
        # Return if above threshold
        if best_similarity >= self.similarity_threshold:
            return (best_match, best_similarity)
        
        return None
    
    def get(
        self,
        query: str,
        query_embedding: np.ndarray,
        dominant_cluster: int
    ) -> Optional[Dict]:
        """
        Get cached result for a query.
        
        Args:
            query: Query string
            query_embedding: Query embedding vector
            dominant_cluster: Dominant cluster ID
        
        Returns:
            Cached result dictionary if cache hit, None if miss
        """
        with self.lock:
            self.stats['total_queries'] += 1
            
            # Look for similar cached query
            match = self._find_similar_cached_query(query_embedding, dominant_cluster)
            
            if match:
                query_hash, similarity_score = match
                cached_entry = self.embedding_cache[query_hash]
                
                self.stats['hits'] += 1
                
                return {
                    'cache_hit': True,
                    'matched_query': cached_entry['query'],
                    'similarity_score': similarity_score,
                    'result': cached_entry['result'],
                    'dominant_cluster': cached_entry['dominant_cluster']
                }
            
            # Cache miss
            self.stats['misses'] += 1
            return None
    
    def put(
        self,
        query: str,
        query_embedding: np.ndarray,
        result: Dict,
        dominant_cluster: int
    ):
        """
        Add a new query-result pair to the cache.
        
        Args:
            query: Query string
            query_embedding: Query embedding vector
            result: Search result to cache
            dominant_cluster: Dominant cluster ID
        """
        with self.lock:
            query_hash = self._hash_query(query)
            
            # Store in main cache
            self.embedding_cache[query_hash] = {
                'query': query,
                'embedding': query_embedding,
                'result': result,
                'dominant_cluster': dominant_cluster,
                'timestamp': time.time()
            }
            
            # Update cluster index
            if dominant_cluster not in self.cluster_index:
                self.cluster_index[dominant_cluster] = []
            
            if query_hash not in self.cluster_index[dominant_cluster]:
                self.cluster_index[dominant_cluster].append(query_hash)
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self.lock:
            total_entries = len(self.embedding_cache)
            hit_count = self.stats['hits']
            miss_count = self.stats['misses']
            total_queries = self.stats['total_queries']
            
            hit_rate = hit_count / total_queries if total_queries > 0 else 0.0
            
            return {
                'total_entries': total_entries,
                'hit_count': hit_count,
                'miss_count': miss_count,
                'total_queries': total_queries,
                'hit_rate': hit_rate,
                'similarity_threshold': self.similarity_threshold,
                'cluster_distribution': {
                    cluster_id: len(hashes)
                    for cluster_id, hashes in self.cluster_index.items()
                }
            }
    
    def clear(self):
        """Clear all cache entries and reset statistics."""
        with self.lock:
            self.embedding_cache.clear()
            self.cluster_index.clear()
            self.stats = {
                'hits': 0,
                'misses': 0,
                'total_queries': 0
            }
            print("Cache cleared")
    
    def analyze_threshold_performance(
        self,
        test_queries: List[Tuple[str, np.ndarray, int]],
        thresholds: List[float] = [0.85, 0.90, 0.92, 0.95, 0.98]
    ) -> Dict:
        """
        Analyze cache performance across different similarity thresholds.
        
        This explores the key tunable parameter and shows what each value reveals.
        
        Args:
            test_queries: List of (query, embedding, cluster) tuples
            thresholds: List of threshold values to test
        
        Returns:
            Dictionary with analysis results
        """
        results = {}
        
        for threshold in thresholds:
            print(f"\nTesting threshold: {threshold}")
            
            # Create temporary cache with this threshold
            temp_cache = SemanticCache(similarity_threshold=threshold)
            
            # Simulate cache usage
            for i, (query, embedding, cluster) in enumerate(test_queries):
                # Every 3rd query is a paraphrase of a previous query
                if i % 3 == 2 and i >= 2:
                    # Use paraphrase
                    original_idx = i - 2
                    result = temp_cache.get(
                        query,
                        embedding,
                        cluster
                    )
                else:
                    # New query
                    result = temp_cache.get(query, embedding, cluster)
                    if result is None:
                        # Simulate storing result
                        temp_cache.put(
                            query,
                            embedding,
                            {'mock': 'result'},
                            cluster
                        )
            
            stats = temp_cache.get_stats()
            results[threshold] = stats
            print(f"Hit rate: {stats['hit_rate']:.3f}")
        
        return results


if __name__ == "__main__":
    # Test the semantic cache
    
    # Mock embeddings for testing
    np.random.seed(42)
    
    # Create similar query pairs
    query_pairs = [
        ("space shuttle launch", "spacecraft launch mission"),
        ("gun control laws", "firearm legislation"),
        ("computer graphics rendering", "3D graphics rendering"),
    ]
    
    # Generate mock embeddings (in practice, use real embeddings)
    test_data = []
    for query1, query2 in query_pairs:
        # Similar embeddings for similar queries
        base_embedding = np.random.rand(384)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)
        
        # Add small noise for second query
        noise = np.random.rand(384) * 0.1
        similar_embedding = base_embedding + noise
        similar_embedding = similar_embedding / np.linalg.norm(similar_embedding)
        
        test_data.append((query1, base_embedding, 0))
        test_data.append((query2, similar_embedding, 0))
    
    # Test cache
    print("Testing SemanticCache")
    print("="*80)
    
    cache = SemanticCache(similarity_threshold=0.92)
    
    # First pass - all misses
    for query, embedding, cluster in test_data[::2]:  # Only original queries
        result = cache.get(query, embedding, cluster)
        print(f"Query: '{query}' - Cache hit: {result is not None}")
        
        if result is None:
            # Simulate caching result
            cache.put(query, embedding, {'mock': 'result'}, cluster)
    
    print("\n" + "="*80)
    print("Second pass - testing similar queries")
    
    # Second pass - should hit on similar queries
    for query, embedding, cluster in test_data[1::2]:  # Only paraphrases
        result = cache.get(query, embedding, cluster)
        if result:
            print(f"Query: '{query}'")
            print(f"  Matched: '{result['matched_query']}'")
            print(f"  Similarity: {result['similarity_score']:.4f}")
        else:
            print(f"Query: '{query}' - No match found")
    
    # Print stats
    print("\n" + "="*80)
    print("Cache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        if key != 'cluster_distribution':
            print(f"  {key}: {value}")
