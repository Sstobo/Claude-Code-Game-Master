#!/usr/bin/env python3
"""
RAG Extractor - Document Vectorization for /enhance

Simple pipeline:
1. Extract text from document
2. Split into chunks
3. Embed chunks locally
4. Store in campaign-specific vector store

No categorization - all chunks are stored uniformly and queried by semantic similarity.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from lib.rag.embedder import LocalEmbedder
from lib.rag.vector_store import CampaignVectorStore


class RAGExtractor:
    """Document vectorization for semantic search."""

    DEFAULT_CHUNK_SIZE = 3000

    def __init__(
        self,
        campaign_dir: str,
        chunk_size: int = None,
        embedder: Optional[LocalEmbedder] = None,
    ):
        """
        Initialize the RAG extractor for a campaign.

        Args:
            campaign_dir: Path to the campaign folder
            chunk_size: Target size for text chunks (default 3000 chars)
            embedder: Optional embedder instance (creates one if not provided)
        """
        self.campaign_dir = Path(campaign_dir)
        self.chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE

        # Initialize components
        self.embedder = embedder or LocalEmbedder()
        self.vector_store = CampaignVectorStore(campaign_dir)

        # Track extraction state
        self._document_name: Optional[str] = None
        self._extraction_metadata: Dict = {}

    def extract_from_document(
        self,
        filepath: str,
        clear_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Extract text from a document and store as vectors.

        Args:
            filepath: Path to the document (PDF, DOCX, TXT, etc.)
            clear_existing: Whether to clear existing vectors first (default: False)

        Returns:
            Dict with extraction stats
        """
        filepath = Path(filepath)
        self._document_name = filepath.stem

        print(f"RAG Extraction: {filepath.name}")
        print("=" * 50)

        # Clear existing vectors if explicitly requested
        if clear_existing:
            print("Clearing existing vectors...")
            self.vector_store.clear()
        else:
            existing_count = self.vector_store.count()
            if existing_count > 0:
                print(f"Preserving {existing_count} existing vectors (use clear_existing=True to reset)")

        # Step 1: Extract raw text
        print("Step 1: Extracting text from document...")
        raw_text = self._extract_text(filepath)
        print(f"  Extracted {len(raw_text):,} characters")

        # Step 2: Split into chunks
        print("Step 2: Splitting into chunks...")
        chunks = self._split_into_chunks(raw_text)
        print(f"  Created {len(chunks)} chunks")

        # Step 3: Embed all chunks
        print("Step 3: Embedding chunks...")
        embeddings = self.embedder.embed_batch(
            chunks,
            batch_size=32,
            show_progress=True
        )
        print(f"  Embedded {len(embeddings)} chunks")

        # Step 4: Store in vector database
        print("Step 4: Storing in vector database...")
        self._store_chunks(chunks, embeddings)

        stats = self.vector_store.get_stats()
        print(f"  Stored {stats['total_chunks']} chunks total")

        # Save extraction metadata
        self._extraction_metadata = {
            "source_file": str(filepath),
            "document_name": self._document_name,
            "extraction_date": datetime.now().isoformat(),
            "total_chars": len(raw_text),
            "total_chunks": len(chunks),
            "chunk_size": self.chunk_size,
        }

        print("\nExtraction complete!")
        return self._extraction_metadata

    def query(
        self,
        query_text: str,
        n_results: int = 20
    ) -> List[Dict]:
        """
        Query the vector store by semantic similarity.

        Args:
            query_text: Text to search for
            n_results: Maximum number of results

        Returns:
            List of chunk dicts with 'text', 'metadata', 'distance'
        """
        results = self.vector_store.query_by_text(
            query_text,
            self.embedder,
            n_results=n_results
        )

        # Format results
        formatted = []
        for i in range(len(results["documents"])):
            formatted.append({
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
                "distance": results["distances"][i] if results["distances"] else 0.0
            })

        return formatted

    def get_extraction_metadata(self) -> Dict:
        """Get metadata about the last extraction."""
        return self._extraction_metadata.copy()

    def get_stats(self) -> Dict:
        """Get current statistics."""
        return {
            "campaign_dir": str(self.campaign_dir),
            "vector_store": self.vector_store.get_stats(),
            "extraction": self._extraction_metadata,
        }

    def _extract_text(self, filepath: Path) -> str:
        """Extract text from a document file."""
        from lib.content_extractor import ContentExtractor

        extractor = ContentExtractor()
        return extractor.extract_text(str(filepath))

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks of approximately chunk_size characters."""
        chunks = []

        # Try to split by headers first (markdown or common patterns)
        header_pattern = r'^(?:#{1,3}\s+.+|[A-Z][A-Z\s]+:|Chapter \d+|PART [IVX]+)'
        sections = re.split(f'({header_pattern})', text, flags=re.MULTILINE)

        current_chunk = ""

        for section in sections:
            if not section.strip():
                continue

            if len(current_chunk) + len(section) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # If section itself is too large, split it further
                if len(section) > self.chunk_size:
                    sub_chunks = self._split_by_paragraphs(section)
                    chunks.extend(sub_chunks[:-1])  # Add all but last
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_chunk = section
            else:
                current_chunk += section

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # If we got very few chunks, fall back to paragraph splitting
        if len(chunks) <= 1 and len(text) > self.chunk_size:
            chunks = self._split_by_paragraphs(text)

        return chunks

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs, respecting chunk size."""
        chunks = []
        paragraphs = text.split('\n\n')

        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _store_chunks(self, chunks: List[str], embeddings):
        """Store chunks in the vector store with basic metadata."""
        metadatas = []
        for i in range(len(chunks)):
            metadatas.append({
                "chunk_index": i,
                "document": self._document_name or "unknown",
            })

        # Store all chunks
        self.vector_store.add_chunks(
            chunks=chunks,
            embeddings=[emb.tolist() for emb in embeddings],
            metadatas=metadatas,
            ids=[f"doc_{i:04d}" for i in range(len(chunks))]
        )


def main():
    """CLI for RAG extraction."""
    import sys
    import json
    import tempfile

    if len(sys.argv) < 2:
        print("Usage: rag_extractor.py <filepath> [campaign_dir]")
        print("\nVectorizes a document for semantic search with /enhance.")
        sys.exit(1)

    filepath = sys.argv[1]
    campaign_dir = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp()

    print(f"Document: {filepath}")
    print(f"Campaign: {campaign_dir}")
    print()

    extractor = RAGExtractor(campaign_dir)
    metadata = extractor.extract_from_document(filepath, clear_existing=True)

    print("\n" + "=" * 50)
    print("Stats:")
    print(json.dumps(extractor.get_stats(), indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
