#!/usr/bin/env python3
"""
Campaign-specific Vector Store for RAG-based Extraction

Uses ChromaDB with persistent storage per campaign.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class CampaignVectorStore:
    """ChromaDB wrapper with campaign-specific persistence."""

    def __init__(self, campaign_dir: str, collection_name: str = "document_chunks"):
        """
        Initialize the vector store for a campaign.

        Args:
            campaign_dir: Path to the campaign folder
                         (e.g., world-state/campaigns/my-campaign/)
            collection_name: Name of the ChromaDB collection
        """
        self.campaign_dir = Path(campaign_dir)
        self.vectors_dir = self.campaign_dir / "vectors"
        self.collection_name = collection_name
        self._client = None
        self._collection = None

        # Ensure vectors directory exists
        self.vectors_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_available() -> bool:
        """Check if ChromaDB is available."""
        try:
            import chromadb
            return True
        except ImportError:
            return False

    def _ensure_client(self):
        """Lazy-load ChromaDB client and collection."""
        if self._client is None:
            import chromadb
            from chromadb.config import Settings

            # Use persistent storage in the campaign's vectors folder
            self._client = chromadb.PersistentClient(
                path=str(self.vectors_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )

            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    def add_chunks(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> int:
        """
        Add chunks with embeddings to the vector store.

        Args:
            chunks: List of text chunks
            embeddings: List of embedding vectors (as lists, not numpy arrays)
            metadatas: Optional list of metadata dicts per chunk
            ids: Optional list of unique IDs. Auto-generated if not provided.

        Returns:
            Number of chunks added
        """
        self._ensure_client()

        if len(chunks) == 0:
            return 0

        # Generate IDs if not provided
        if ids is None:
            # Get current count to avoid ID collisions
            current_count = self._collection.count()
            ids = [f"chunk_{current_count + i}" for i in range(len(chunks))]

        # Default metadata if not provided
        if metadatas is None:
            metadatas = [{"index": i} for i in range(len(chunks))]

        # Ensure embeddings are lists (ChromaDB requirement)
        embeddings_list = [
            emb.tolist() if hasattr(emb, 'tolist') else list(emb)
            for emb in embeddings
        ]

        # Add to collection
        self._collection.add(
            documents=chunks,
            embeddings=embeddings_list,
            metadatas=metadatas,
            ids=ids
        )

        return len(chunks)

    def query_similar(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query for similar chunks.

        Args:
            query_embedding: Query embedding vector (as list)
            n_results: Maximum number of results to return
            where: Optional metadata filter
            where_document: Optional document content filter

        Returns:
            Dict with 'ids', 'documents', 'metadatas', 'distances'
        """
        self._ensure_client()

        # Convert numpy to list if needed
        if hasattr(query_embedding, 'tolist'):
            query_embedding = query_embedding.tolist()

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )

        # Flatten results (query returns nested lists for batch queries)
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    def query_by_text(
        self,
        query_text: str,
        embedder,
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query for similar chunks using text (embeds the query automatically).

        Args:
            query_text: Query text to embed and search
            embedder: LocalEmbedder instance to use for embedding
            n_results: Maximum number of results
            where: Optional metadata filter

        Returns:
            Dict with 'ids', 'documents', 'metadatas', 'distances'
        """
        query_embedding = embedder.embed(query_text)
        return self.query_similar(
            query_embedding.tolist(),
            n_results=n_results,
            where=where
        )

    def get_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """
        Get all chunks with a specific category.

        Args:
            category: Category name (e.g., 'npc', 'location')
            limit: Maximum number to return

        Returns:
            List of chunk dicts with 'id', 'document', 'metadata'
        """
        self._ensure_client()

        results = self._collection.get(
            where={"category": category},
            limit=limit,
            include=["documents", "metadatas"]
        )

        chunks = []
        for i, doc_id in enumerate(results["ids"]):
            chunks.append({
                "id": doc_id,
                "document": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {}
            })

        return chunks

    def count(self) -> int:
        """Get total number of chunks in the collection."""
        self._ensure_client()
        return self._collection.count()

    def count_by_category(self) -> Dict[str, int]:
        """Get chunk counts by category."""
        self._ensure_client()

        # ChromaDB doesn't have a direct group-by, so we get all and count
        results = self._collection.get(include=["metadatas"])

        counts = {}
        for metadata in results["metadatas"]:
            cat = metadata.get("category", "uncategorized")
            counts[cat] = counts.get(cat, 0) + 1

        return counts

    def clear(self):
        """Clear all chunks from the collection."""
        self._ensure_client()
        # Delete collection and recreate
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def persist(self):
        """
        Persist the vector store to disk.

        Note: ChromaDB PersistentClient auto-persists, but this method
        is kept for explicit clarity and future compatibility.
        """
        # PersistentClient handles this automatically
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        self._ensure_client()

        return {
            "campaign_dir": str(self.campaign_dir),
            "vectors_dir": str(self.vectors_dir),
            "collection_name": self.collection_name,
            "total_chunks": self.count(),
            "by_category": self.count_by_category(),
        }


def main():
    """Test the vector store."""
    import tempfile

    if not CampaignVectorStore.is_available():
        print("ChromaDB not installed!")
        print("Install with: pip install chromadb")
        return

    # Create temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CampaignVectorStore(tmpdir)
        print(f"Created store at: {tmpdir}")

        # Add some test chunks
        chunks = [
            "The old wizard Gandalf lives in a tower.",
            "A dark dungeon filled with traps and treasure.",
            "The +2 longsword glows with magical fire.",
        ]

        # Fake embeddings for testing (would use real embedder in practice)
        import random
        embeddings = [[random.random() for _ in range(384)] for _ in chunks]

        metadatas = [
            {"category": "npc", "confidence": 0.9},
            {"category": "location", "confidence": 0.85},
            {"category": "item", "confidence": 0.95},
        ]

        added = store.add_chunks(chunks, embeddings, metadatas)
        print(f"Added {added} chunks")

        # Get stats
        stats = store.get_stats()
        print(f"Stats: {json.dumps(stats, indent=2, ensure_ascii=False)}")

        # Query similar
        results = store.query_similar(embeddings[0], n_results=2)
        print(f"Query results: {len(results['documents'])} documents")


if __name__ == "__main__":
    main()
