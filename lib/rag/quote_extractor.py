#!/usr/bin/env python3
"""
Context Extractor for NPC Enrichment

Semantic extraction of relevant passages from vectorized document chunks.
Runs as Pass 2 during extraction workflow to enrich NPCs with context.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


class QuoteExtractor:  # Keep class name for backwards compatibility
    """
    Extracts quotes and voice characteristics for NPCs using semantic search.

    Queries the vector store for dialogue and speech patterns associated with
    each NPC, then enriches the NPC records with voice data.
    """

    def __init__(self, campaign_dir: str):
        """
        Initialize the quote extractor for a campaign.

        Args:
            campaign_dir: Path to the campaign folder containing vectors and npcs.json
        """
        self.campaign_dir = Path(campaign_dir)
        self.npcs_path = self.campaign_dir / "npcs.json"

        # Lazy-load RAG components
        self._vector_store = None
        self._embedder = None

    def _ensure_rag(self):
        """Lazy-load RAG components."""
        if self._vector_store is None:
            from lib.rag.vector_store import CampaignVectorStore
            from lib.rag.embedder import LocalEmbedder

            self._vector_store = CampaignVectorStore(str(self.campaign_dir))
            self._embedder = LocalEmbedder()

    def extract_context_for_npc(self, npc_name: str, n_results: int = 15) -> List[str]:
        """
        Query vectors for any relevant passages about a specific NPC.

        Args:
            npc_name: The name of the NPC to search for
            n_results: Maximum number of results per query type

        Returns:
            List of relevant text passages
        """
        self._ensure_rag()

        passages = []
        seen_passages = set()  # Deduplicate results

        # Broad queries to find any context about this NPC
        context_queries = [
            f'{npc_name}',  # Just the name
            f'{npc_name} character personality description',
            f'{npc_name} says speaks dialogue',
            f'{npc_name} appears scene encounter',
            f'{npc_name} background history motivation',
        ]

        for query in context_queries:
            results = self._vector_store.query_by_text(
                query,
                self._embedder,
                n_results=n_results
            )

            for doc, distance in zip(results['documents'], results['distances']):
                # Skip if already seen
                doc_key = doc[:200].lower()  # Use first 200 chars as key
                if doc_key in seen_passages:
                    continue

                # Only process if similarity is reasonable
                if distance > 1.3:
                    continue

                # Check if passage actually mentions the NPC
                if npc_name.lower() not in doc.lower():
                    continue

                seen_passages.add(doc_key)

                # Clean up the passage - remove page markers
                clean_doc = self._clean_passage(doc)
                passages.append(clean_doc)

        # Limit to most relevant passages
        return passages[:10]

    def _clean_passage(self, text: str, max_length: int = 500) -> str:
        """Remove page markers and other noise from passages, cap length."""
        import re
        # Remove page markers like "--- Page 142 ---"
        text = re.sub(r'---\s*Page\s*\d+\s*---\n?', '', text)
        # Remove OceanofPDF watermarks
        text = re.sub(r'OceanofPDF\.com\s*', '', text)
        # Clean up excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()

        # Cap length, try to break at sentence boundary
        if len(text) > max_length:
            truncated = text[:max_length]
            # Try to break at last sentence end
            last_period = truncated.rfind('. ')
            last_newline = truncated.rfind('\n')
            break_at = max(last_period, last_newline)
            if break_at > max_length // 2:
                text = truncated[:break_at + 1].strip()
            else:
                text = truncated.strip() + "..."

        return text

    # Keep old method name as alias for backwards compatibility
    def extract_voice_for_npc(self, npc_name: str, n_results: int = 10) -> Dict[str, Any]:
        """Legacy method - redirects to extract_context_for_npc."""
        passages = self.extract_context_for_npc(npc_name, n_results)
        return {
            "quotes": [],
            "source_passages": passages
        }

    def enrich_all_npcs(self) -> int:
        """
        Load npcs.json, enrich each NPC with voice data, save back.

        Returns:
            Count of NPCs enriched with at least one quote or passage
        """
        if not self.npcs_path.exists():
            print(f"  No npcs.json found at {self.npcs_path}")
            return 0

        # Check if vector store has any data
        self._ensure_rag()
        chunk_count = self._vector_store.count()
        if chunk_count == 0:
            print("  No vectors in store - skipping quote extraction")
            return 0

        # Load NPCs
        npcs = json.loads(self.npcs_path.read_text())
        if not npcs:
            print("  No NPCs to enrich")
            return 0

        enriched_count = 0

        for npc_name in npcs.keys():
            # Get semantic context passages
            new_passages = self.extract_context_for_npc(npc_name)

            # Merge with existing context from agent extraction
            existing_context = npcs[npc_name].get('context', [])

            # Combine: existing first (usually dialogue from agent), then semantic passages
            all_context = existing_context.copy()

            # Add new passages, deduplicating
            seen_keys = set(p[:100].lower() for p in all_context)
            for passage in new_passages:
                p_key = passage[:100].lower()
                if p_key not in seen_keys:
                    seen_keys.add(p_key)
                    all_context.append(passage)

            # Limit total context
            all_context = all_context[:15]

            # Update if we have context
            if all_context:
                npcs[npc_name]['context'] = all_context
                added = len(all_context) - len(existing_context)
                if added > 0:
                    enriched_count += 1
                    print(f"    {npc_name}: {len(all_context)} context passages (+{added} new)")

        # Save enriched NPCs
        self.npcs_path.write_text(json.dumps(npcs, indent=2, ensure_ascii=False))

        return enriched_count


def main():
    """CLI for testing context extraction."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: quote_extractor.py <campaign_dir> [npc_name]")
        print("  <campaign_dir>: Path to campaign folder with vectors and npcs.json")
        print("  [npc_name]: Optional - extract for specific NPC only")
        sys.exit(1)

    campaign_dir = sys.argv[1]
    extractor = QuoteExtractor(campaign_dir)

    if len(sys.argv) > 2:
        # Extract for specific NPC
        npc_name = sys.argv[2]
        print(f"Extracting context for: {npc_name}")
        passages = extractor.extract_context_for_npc(npc_name)
        print(f"Found {len(passages)} passages:")
        for i, p in enumerate(passages, 1):
            print(f"\n--- Passage {i} ---")
            print(p[:500] + "..." if len(p) > 500 else p)
    else:
        # Enrich all NPCs
        print(f"Enriching all NPCs in: {campaign_dir}")
        count = extractor.enrich_all_npcs()
        print(f"Enriched {count} NPCs with context")


if __name__ == "__main__":
    main()
