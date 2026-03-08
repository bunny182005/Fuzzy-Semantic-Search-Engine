#!/usr/bin/env python3
"""
Setup Script for Semantic Search System

This script initializes the entire system:
1. Preprocesses the data
2. Generates embeddings
3. Performs fuzzy clustering
4. Prepares the system for API use

Run this once before starting the API server.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from preprocessing import NewsGroupPreprocessor
from embeddings import EmbeddingManager
from clustering import FuzzyClusterer
import numpy as np
import pandas as pd


def main():
    print("="*80)
    print("SEMANTIC SEARCH SYSTEM - INITIAL SETUP")
    print("="*80)
    
    # Step 1: Preprocess data
    print("\n" + "="*80)
    print("STEP 1: DATA PREPROCESSING")
    print("="*80)
    
    preprocessor = NewsGroupPreprocessor()
    df = preprocessor.load_and_clean_dataset("data/raw/20_newsgroups")
    
    # Save cleaned data
    os.makedirs('data/processed', exist_ok=True)
    output_path = 'data/processed/cleaned_newsgroups.parquet'
    df.to_parquet(output_path, index=False)
    print(f"\n✓ Saved cleaned data to {output_path}")
    
    # Print statistics
    stats = preprocessor.get_statistics(df)
    print(f"\n✓ Processed {stats['total_documents']} documents")
    print(f"✓ {stats['unique_categories']} categories")
    print(f"✓ Average length: {stats['avg_length']:.0f} characters")
    
    # Step 2: Generate embeddings
    print("\n" + "="*80)
    print("STEP 2: GENERATING EMBEDDINGS")
    print("="*80)
    
    em = EmbeddingManager(persist_directory='./data/processed/chroma_db')
    
    # Check if already populated
    if em.get_document_count() == 0:
        print("\nAdding documents to vector database...")
        em.add_documents(df)
        print(f"\n✓ Added {em.get_document_count()} documents to vector database")
    else:
        print(f"\n✓ Vector database already contains {em.get_document_count()} documents")
    
    # Test search
    print("\n✓ Testing semantic search...")
    test_results = em.search("space shuttle launch", n_results=3)
    print("  Sample query: 'space shuttle launch'")
    print(f"  Found {len(test_results['documents'][0])} results")
    
    # Step 3: Fuzzy clustering
    print("\n" + "="*80)
    print("STEP 3: FUZZY CLUSTERING")
    print("="*80)
    
    # Check if clustering already exists
    clustering_path = 'data/processed/fuzzy_clustering.pkl'
    
    if os.path.exists(clustering_path):
        print(f"\n✓ Clustering model already exists at {clustering_path}")
        print("  Loading existing model...")
        clusterer = FuzzyClusterer()
        clusterer.load(clustering_path)
    else:
        print("\nGenerating embeddings for clustering...")
        embeddings_dict = em.get_all_embeddings()
        doc_ids = sorted(embeddings_dict.keys())
        embeddings = np.array([embeddings_dict[doc_id] for doc_id in doc_ids])
        
        print(f"✓ Loaded {len(embeddings)} embeddings")
        
        # Find optimal number of clusters
        print("\nFinding optimal number of clusters...")
        print("(This may take several minutes...)")
        clusterer = FuzzyClusterer()
        optimal_n, metrics = clusterer.find_optimal_clusters(
            embeddings,
            min_clusters=18,
            max_clusters=28,
            step=2
        )
        
        print(f"\n✓ Optimal number of clusters: {optimal_n}")
        
        # Fit clustering
        clusterer.n_clusters = optimal_n
        u = clusterer.fit(embeddings)
        
        print(f"✓ Fuzzy Partition Coefficient: {clusterer.fpc:.4f}")
        
        # Analyze clusters
        print("\nAnalyzing cluster composition...")
        analysis = clusterer.analyze_clusters(df)
        
        # Save clustering
        clusterer.save(clustering_path)
        np.save('data/processed/membership_matrix.npy', u)
        
        print(f"\n✓ Saved clustering to {clustering_path}")
        
        # Print cluster summary
        print("\nCluster Summary:")
        for cluster_id in range(min(5, clusterer.n_clusters)):
            size = analysis['cluster_sizes'][cluster_id]
            top_terms = ', '.join([term for term, _ in analysis['top_terms'][cluster_id][:5]])
            print(f"  Cluster {cluster_id} (n={size}): {top_terms}")
    
    # Step 4: Final verification
    print("\n" + "="*80)
    print("STEP 4: VERIFICATION")
    print("="*80)
    
    required_files = [
        'data/processed/cleaned_newsgroups.parquet',
        'data/processed/chroma_db',
        'data/processed/fuzzy_clustering.pkl'
    ]
    
    all_exist = True
    for filepath in required_files:
        exists = os.path.exists(filepath)
        status = "✓" if exists else "✗"
        print(f"{status} {filepath}")
        all_exist = all_exist and exists
    
    # Final status
    print("\n" + "="*80)
    if all_exist:
        print("✓ SETUP COMPLETE!")
        print("="*80)
        print("\nYou can now start the API server:")
        print("\n  cd src")
        print("  uvicorn main:app --host 0.0.0.0 --port 8000")
        print("\nOr using Docker:")
        print("\n  docker-compose up")
    else:
        print("✗ SETUP INCOMPLETE")
        print("="*80)
        print("\nSome required files are missing. Please check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
