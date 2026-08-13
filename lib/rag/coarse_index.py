#!/usr/bin/env python3
"""
Coarse chapter index — points INTO the retained book text, it is not the fidelity.

The old pipeline routed all fidelity through weak all-MiniLM 3000-char chunks.
This demotes embeddings to a COARSE index whose only job is to find the right
CHAPTER, which the long-context reader then loads in full. The embedder is
pluggable (config-selected) and defaults to a dependency-free keyword scorer so
indexing/querying never requires loading a heavy model. Query templates branch by
content type so a novel import stops dragging retrieval toward D&D stat-block
vocabulary.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from book_bible import segment_into_chapters


def _template(query: str, content_type: str = "literary") -> str:
    """Branch the query by content type (literary prose vs game-module mechanics)."""
    if content_type == "game-module":
        return f"{query} stat block rules mechanics encounter"
    return f"{query} scene character atmosphere setting"


def _keyword_score(query: str, text: str) -> float:
    q = set(re.findall(r"\w+", query.lower()))
    t = set(re.findall(r"\w+", text.lower()))
    if not q:
        return 0.0
    return len(q & t)


class CoarseIndex:
    """A chapter-granularity index that returns POINTERS, never chunk blobs."""

    def __init__(self, embedder: str = "keyword"):
        self.embedder = embedder  # pluggable: "keyword" (default) or a model name
        self.chapters: List[Dict[str, Any]] = []

    def build(self, text: str) -> int:
        self.chapters = segment_into_chapters(text)
        return len(self.chapters)

    def _score(self, query: str, text: str) -> float:
        if self.embedder == "keyword":
            return _keyword_score(query, text)
        # A real embedder is loaded lazily only when configured (kept out of tests).
        # Falls back to keyword scoring when RAG deps are missing.
        try:
            from rag.embedder import LocalEmbedder
            emb = LocalEmbedder(self.embedder)
            return float(emb.similarity(emb.embed(query), emb.embed(text)))
        except ImportError:
            return _keyword_score(query, text)

    def query(self, query: str, content_type: str = "literary", top_k: int = 3) -> List[Dict[str, Any]]:
        """Return ranked CHAPTER POINTERS {index, title, score} — not the text."""
        templated = _template(query, content_type)
        scored = [(self._score(templated, c["text"]), c) for c in self.chapters]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [{"index": c["index"], "title": c["title"], "score": s}
                for s, c in scored[:top_k] if s > 0]

    def load_chapter(self, index: int) -> Dict[str, Any]:
        """Resolve a pointer to its full chapter text (what the long-context reader loads)."""
        for c in self.chapters:
            if c["index"] == index:
                return c
        return {}
