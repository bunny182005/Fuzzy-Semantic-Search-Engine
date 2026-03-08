"""
Embeddings and Vector Database Module

This module handles:
1. Generating embeddings using sentence-transformers
2. Storing embeddings in ChromaDB
3. Semantic search functionality

Model Choice: all-MiniLM-L6-v2
- Fast inference (~400 docs/sec on CPU)
- 384 dimensions (lightweight, good for clustering)
- Trained on 1B+ sentence pairs (good semantic quality)
- Suitable for search/retrieval tasks

Vector Store Choice: ChromaDB
- Embedded database (no separate server)
- Supports metadata filtering (critical for cluster-aware cache)
- Built-in cosine similarity search
- Easy to persist and reload
"""

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from tqdm import tqdm


class EmbeddingManager:
    """Manages document embeddings and vector database operations."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        persist_directory: str = "../data/processed/chroma_db"
    ):
        """
        Initialize embedding model and vector database.
        
        Args:
            model_name: HuggingFace model identifier
            persist_directory: Path to persist ChromaDB
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Embedding dimension: {self.embedding_dim}")
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="newsgroups",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
    def embed_documents(
        self,
        texts: List[str],
        batch_size: int = 256,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for a list of documents.
        
        Args:
            texts: List of text documents
            batch_size: Number of documents to process at once
            show_progress: Show progress bar
        
        Returns:
            numpy array of shape (n_docs, embedding_dim)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        return embeddings
    
    def add_documents(
        self,
        df: pd.DataFrame,
        batch_size: int = 1000
    ):
        """
        Add documents to ChromaDB with embeddings.
        
        Args:
            df: DataFrame with columns: doc_id, text, category
            batch_size: Number of documents to add at once
        """
        print(f"Generating embeddings for {len(df)} documents...")
        
        # Generate embeddings
        embeddings = self.embed_documents(
            df['text'].tolist(),
            batch_size=256
        )
        
        print("Adding documents to ChromaDB...")
        
        # Add in batches (ChromaDB has limits)
        for i in tqdm(range(0, len(df), batch_size)):
            batch_df = df.iloc[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            
            self.collection.add(
                embeddings=batch_embeddings.tolist(),
                documents=batch_df['text'].tolist(),
                metadatas=[
                    {
                        'doc_id': int(row['doc_id']),
                        'category': row['category'],
                        'length': int(row['length'])
                    }
                    for _, row in batch_df.iterrows()
                ],
                ids=[f"doc_{row['doc_id']}" for _, row in batch_df.iterrows()]
            )
        
        print(f"Added {len(df)} documents to vector database")
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        cluster_filter: Optional[int] = None
    ) -> Dict:
        """
        Search for similar documents using semantic similarity.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            cluster_filter: If provided, only search within this cluster
        
        Returns:
            Dictionary with results
        """
        # Embed query
        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True
        )[0]
        
        # Build where clause for cluster filtering
        where = None
        if cluster_filter is not None:
            where = {"dominant_cluster": cluster_filter}
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where
        )
        
        return results
    
    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Retrieve all embeddings from the database.
        
        Returns:
            Dictionary mapping doc_id to embedding vector
        """
        # Get all documents
        results = self.collection.get(
            include=['embeddings', 'metadatas']
        )
        
        embeddings_dict = {}
        for idx, metadata in enumerate(results['metadatas']):
            doc_id = metadata['doc_id']
            embedding = np.array(results['embeddings'][idx])
            embeddings_dict[doc_id] = embedding
        
        return embeddings_dict
    
    def update_metadata(self, doc_id: int, metadata: Dict):
        """
        Update metadata for a document (e.g., add cluster assignment).
        
        Args:
            doc_id: Document ID
            metadata: Dictionary of metadata to update
        """
        self.collection.update(
            ids=[f"doc_{doc_id}"],
            metadatas=[metadata]
        )
    
    def get_document_count(self) -> int:
        """Get total number of documents in the database."""
        return self.collection.count()


if __name__ == "__main__":
    # Test the embedding manager
    import os
    
    # Load cleaned data
    data_path = '../data/processed/cleaned_newsgroups.parquet'
    if not os.path.exists(data_path):
        print("Please run preprocessing.py first to generate cleaned data")
        exit(1)
    
    df = pd.read_parquet(data_path)
    print(f"Loaded {len(df)} documents")
    
    # Initialize embedding manager
    em = EmbeddingManager()
    
    # Check if already populated
    if em.get_document_count() == 0:
        # Add documents
        em.add_documents(df)
    else:
        print(f"Vector database already contains {em.get_document_count()} documents")
    
    # Test search
    print("\nTesting search functionality:")
    test_query = "space shuttle mission to mars"
    results = em.search(test_query, n_results=5)
    
    print(f"\nQuery: {test_query}")
    print("\nTop 5 results:")
    for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
        print(f"\n{i+1}. Similarity: {1 - distance:.4f}")
        print(f"   Text: {doc[:200]}...")
