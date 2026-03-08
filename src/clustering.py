"""
Fuzzy Clustering Module

This module implements soft clustering using Fuzzy C-Means (FCM).

Why Fuzzy Clustering:
- Documents can belong to multiple topics simultaneously
- Example: "gun legislation" belongs to both politics AND firearms
- Hard clustering forces artificial boundaries
- FCM provides membership probabilities for each cluster

Number of Clusters Decision:
- Original dataset has 20 categories
- Real semantic structure is often more granular
- Will test range 15-30 and select based on:
  * Silhouette score
  * Davies-Bouldin index
  * FCM objective function (within-cluster variance)
- Justified by evidence, not convenience
"""

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA
import skfuzzy as fuzz
from typing import Tuple, Dict, List
import pickle
import matplotlib.pyplot as plt
import seaborn as sns


class FuzzyClusterer:
    """Implements fuzzy clustering for document embeddings."""
    
    def __init__(self, n_clusters: int = 25, m: float = 2.0, error: float = 0.005, maxiter: int = 1000):
        """
        Initialize fuzzy clustering.
        
        Args:
            n_clusters: Number of clusters (determined by optimization)
            m: Fuzziness parameter (2.0 is standard)
            error: Stopping criterion
            maxiter: Maximum iterations
        """
        self.n_clusters = n_clusters
        self.m = m
        self.error = error
        self.maxiter = maxiter
        self.cntr = None  # Cluster centers
        self.u = None  # Membership matrix
        self.u0 = None  # Initial membership
        self.d = None  # Distances
        self.jm = None  # Objective function history
        self.p = None  # Number of iterations
        self.fpc = None  # Fuzzy partition coefficient
    
    def find_optimal_clusters(
        self,
        embeddings: np.ndarray,
        min_clusters: int = 15,
        max_clusters: int = 30,
        step: int = 1
    ) -> Tuple[int, Dict]:
        """
        Find optimal number of clusters using multiple metrics.
        
        Args:
            embeddings: Document embeddings (n_docs, n_features)
            min_clusters: Minimum number of clusters to test
            max_clusters: Maximum number of clusters to test
            step: Step size for cluster range
        
        Returns:
            Optimal number of clusters and metrics dictionary
        """
        print("Finding optimal number of clusters...")
        cluster_range = range(min_clusters, max_clusters + 1, step)
        
        metrics = {
            'n_clusters': [],
            'silhouette': [],
            'davies_bouldin': [],
            'fpc': [],  # Fuzzy partition coefficient
            'objective': []  # FCM objective function
        }
        
        for n in cluster_range:
            print(f"Testing {n} clusters...")
            
            # Run FCM
            cntr, u, _, _, _, _, fpc = fuzz.cluster.cmeans(
                embeddings.T,  # FCM expects (n_features, n_samples)
                c=n,
                m=self.m,
                error=self.error,
                maxiter=self.maxiter,
                init=None
            )
            
            # Get hard cluster assignments for some metrics
            hard_clusters = np.argmax(u, axis=0)
            
            # Calculate metrics
            sil_score = silhouette_score(embeddings, hard_clusters, metric='cosine')
            db_score = davies_bouldin_score(embeddings, hard_clusters)
            
            metrics['n_clusters'].append(n)
            metrics['silhouette'].append(sil_score)
            metrics['davies_bouldin'].append(db_score)
            metrics['fpc'].append(fpc)
            metrics['objective'].append(np.sum(u ** self.m))
            
            print(f"  Silhouette: {sil_score:.4f}, Davies-Bouldin: {db_score:.4f}, FPC: {fpc:.4f}")
        
        # Find optimal based on metrics
        # Higher silhouette is better
        # Lower Davies-Bouldin is better
        # Higher FPC is better (more crisp partitions)
        
        optimal_idx = np.argmax(metrics['silhouette'])
        optimal_n = metrics['n_clusters'][optimal_idx]
        
        print(f"\nOptimal number of clusters: {optimal_n}")
        print(f"Based on highest silhouette score: {metrics['silhouette'][optimal_idx]:.4f}")
        
        return optimal_n, metrics
    
    def fit(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Fit fuzzy clustering to embeddings.
        
        Args:
            embeddings: Document embeddings (n_docs, n_features)
        
        Returns:
            Membership matrix (n_clusters, n_docs)
        """
        print(f"Fitting Fuzzy C-Means with {self.n_clusters} clusters...")
        
        # Run FCM
        # Note: skfuzzy expects (n_features, n_samples) format
        self.cntr, self.u, self.u0, self.d, self.jm, self.p, self.fpc = fuzz.cluster.cmeans(
            embeddings.T,
            c=self.n_clusters,
            m=self.m,
            error=self.error,
            maxiter=self.maxiter,
            init=None
        )
        
        print(f"Converged in {self.p} iterations")
        print(f"Fuzzy Partition Coefficient: {self.fpc:.4f}")
        
        return self.u
    
    def get_dominant_clusters(self) -> np.ndarray:
        """
        Get the dominant (highest membership) cluster for each document.
        
        Returns:
            Array of dominant cluster IDs (n_docs,)
        """
        return np.argmax(self.u, axis=0)
    
    def get_membership_distribution(self, doc_idx: int) -> Dict[int, float]:
        """
        Get cluster membership distribution for a single document.
        
        Args:
            doc_idx: Document index
        
        Returns:
            Dictionary mapping cluster_id to membership probability
        """
        return {i: float(self.u[i, doc_idx]) for i in range(self.n_clusters)}
    
    def find_boundary_documents(self, threshold: float = 0.3) -> List[int]:
        """
        Find documents with significant membership in multiple clusters.
        
        These are the "boundary cases" that don't fit neatly into one category.
        
        Args:
            threshold: Minimum membership to consider significant
        
        Returns:
            List of document indices that are boundary cases
        """
        boundary_docs = []
        
        for doc_idx in range(self.u.shape[1]):
            memberships = self.u[:, doc_idx]
            # Count clusters with significant membership
            significant_clusters = np.sum(memberships > threshold)
            
            if significant_clusters >= 2:
                boundary_docs.append(doc_idx)
        
        return boundary_docs
    
    def analyze_clusters(self, df: pd.DataFrame, top_n_terms: int = 10) -> Dict:
        """
        Analyze cluster composition and semantic meaning.
        
        Args:
            df: DataFrame with document text and metadata
            top_n_terms: Number of top terms to extract per cluster
        
        Returns:
            Dictionary with cluster analysis
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        print("Analyzing cluster composition...")
        
        analysis = {
            'cluster_sizes': [],
            'dominant_categories': {},
            'top_terms': {},
            'pure_examples': {},  # High membership in single cluster
            'boundary_examples': {}  # Split membership
        }
        
        # Get dominant clusters
        dominant_clusters = self.get_dominant_clusters()
        
        # Analyze each cluster
        for cluster_id in range(self.n_clusters):
            # Get documents in this cluster
            cluster_mask = dominant_clusters == cluster_id
            cluster_docs = df[cluster_mask]
            
            analysis['cluster_sizes'].append(len(cluster_docs))
            
            # Find dominant category
            if len(cluster_docs) > 0:
                category_dist = cluster_docs['category'].value_counts()
                analysis['dominant_categories'][cluster_id] = category_dist.to_dict()
            
            # Extract top terms using TF-IDF weighted by membership
            if len(cluster_docs) > 0:
                # Weight documents by their membership in this cluster
                doc_indices = cluster_docs.index.tolist()
                memberships = [self.u[cluster_id, idx] for idx in doc_indices]
                
                # TF-IDF
                vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
                tfidf_matrix = vectorizer.fit_transform(cluster_docs['text'])
                feature_names = vectorizer.get_feature_names_out()
                
                # Weight by membership
                weighted_tfidf = tfidf_matrix.multiply(np.array(memberships).reshape(-1, 1))
                term_scores = np.array(weighted_tfidf.sum(axis=0)).flatten()
                
                # Get top terms
                top_indices = term_scores.argsort()[-top_n_terms:][::-1]
                analysis['top_terms'][cluster_id] = [
                    (feature_names[i], float(term_scores[i]))
                    for i in top_indices
                ]
            
            # Find pure examples (high membership in this cluster)
            pure_indices = np.where(self.u[cluster_id] > 0.8)[0]
            if len(pure_indices) > 0:
                pure_idx = pure_indices[np.argmax(self.u[cluster_id, pure_indices])]
                analysis['pure_examples'][cluster_id] = {
                    'doc_id': int(pure_idx),
                    'membership': float(self.u[cluster_id, pure_idx]),
                    'text': df.iloc[pure_idx]['text'][:300]
                }
        
        # Find boundary examples
        boundary_indices = self.find_boundary_documents(threshold=0.25)
        for idx in boundary_indices[:20]:  # Limit to 20 examples
            memberships = self.get_membership_distribution(idx)
            # Sort by membership
            sorted_memberships = sorted(memberships.items(), key=lambda x: x[1], reverse=True)
            top_clusters = sorted_memberships[:3]  # Top 3 clusters
            
            analysis['boundary_examples'][int(idx)] = {
                'text': df.iloc[idx]['text'][:300],
                'memberships': {int(k): float(v) for k, v in top_clusters}
            }
        
        return analysis
    
    def save(self, path: str):
        """Save clustering model."""
        data = {
            'n_clusters': self.n_clusters,
            'm': self.m,
            'cntr': self.cntr,
            'u': self.u,
            'fpc': self.fpc
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"Saved clustering model to {path}")
    
    def load(self, path: str):
        """Load clustering model."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.n_clusters = data['n_clusters']
        self.m = data['m']
        self.cntr = data['cntr']
        self.u = data['u']
        self.fpc = data['fpc']
        print(f"Loaded clustering model from {path}")


if __name__ == "__main__":
    import os
    from embeddings import EmbeddingManager
    
    # Load embeddings
    print("Loading embeddings...")
    em = EmbeddingManager()
    embeddings_dict = em.get_all_embeddings()
    
    # Convert to array (ensure consistent ordering)
    doc_ids = sorted(embeddings_dict.keys())
    embeddings = np.array([embeddings_dict[doc_id] for doc_id in doc_ids])
    print(f"Loaded {len(embeddings)} embeddings")
    
    # Load document data
    df = pd.read_parquet('../data/processed/cleaned_newsgroups.parquet')
    
    # Find optimal clusters
    clusterer = FuzzyClusterer()
    optimal_n, metrics = clusterer.find_optimal_clusters(embeddings, 18, 28, 2)
    
    # Fit with optimal number
    clusterer.n_clusters = optimal_n
    u = clusterer.fit(embeddings)
    
    # Analyze clusters
    analysis = clusterer.analyze_clusters(df)
    
    # Print analysis
    print("\n" + "="*80)
    print("CLUSTER ANALYSIS")
    print("="*80)
    
    for cluster_id in range(clusterer.n_clusters):
        print(f"\nCluster {cluster_id} (size: {analysis['cluster_sizes'][cluster_id]})")
        print(f"Top terms: {', '.join([term for term, _ in analysis['top_terms'][cluster_id][:5]])}")
        if cluster_id in analysis['dominant_categories']:
            top_cat = max(analysis['dominant_categories'][cluster_id].items(), key=lambda x: x[1])
            print(f"Dominant category: {top_cat[0]} ({top_cat[1]} docs)")
    
    print("\n" + "="*80)
    print("BOUNDARY EXAMPLES (documents with split membership)")
    print("="*80)
    
    for doc_id, info in list(analysis['boundary_examples'].items())[:5]:
        print(f"\nDocument {doc_id}:")
        print(f"Memberships: {info['memberships']}")
        print(f"Text: {info['text'][:200]}...")
    
    # Save clustering
    clusterer.save('../data/processed/fuzzy_clustering.pkl')
    
    # Save membership matrix
    np.save('../data/processed/membership_matrix.npy', u)
