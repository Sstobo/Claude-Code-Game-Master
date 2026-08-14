#!/usr/bin/env python3
"""
Entity Enhancer Module for GM Tools

Provides RAG-based enhancement for campaign entities (NPCs, locations, items, plots).
Queries the campaign's vector store for passages mentioning an entity and returns
context that can be used to enrich the entity with additional details.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from json_ops import JsonOperations
from campaign_manager import CampaignManager


# Query templates for each entity type
ENTITY_QUERIES = {
    "npc": [
        "{name} personality traits characteristics",
        "{name} dialogue speaks says",
        "{name} appearance description",
        "{name} background history motivation",
        "{name} relationships allies enemies",
    ],
    "location": [
        "{name} description atmosphere",
        "{name} features rooms areas",
        "{name} inhabitants who lives",
        "{name} hazards dangers traps",
        "{name} secrets hidden",
    ],
    "dungeon": [
        "{name} layout rooms areas chambers",
        "{name} entrance entry way in",
        "{name} inhabitants monsters creatures",
        "{name} treasure loot gold rewards",
        "{name} traps hazards dangers secrets",
        "{name} boss leader chief final",
        "{name} history origin built purpose",
        "{name} description atmosphere feel",
    ],
    "item": [
        "{name} properties abilities",
        "{name} history origin",
        "{name} appearance description",
        "{name} powers effects",
    ],
    "plot": [
        "{name} objectives goals",
        "{name} complications obstacles",
        "{name} rewards consequences",
        "{name} connections related",
    ],
}


class EntityEnhancer:
    """
    RAG-based entity enhancement for D&D campaign entities.

    Searches the campaign's vector store for passages related to an entity,
    then provides suggested enhancements based on the source material.
    """

    def __init__(self, world_state_dir: str = None):
        """
        Initialize the entity enhancer for the active campaign.

        Args:
            world_state_dir: Base world state directory (defaults to "world-state")
        """
        base_dir = world_state_dir or "world-state"
        self.campaign_mgr = CampaignManager(base_dir)

        # Get active campaign directory
        self.campaign_dir = self.campaign_mgr.get_active_campaign_dir()
        self.json_ops = JsonOperations(str(self.campaign_dir))

        # Lazy-load RAG components
        self._vector_store = None
        self._embedder = None

    def _ensure_rag(self) -> bool:
        """
        Lazy-load RAG components.

        Returns:
            True if RAG is available, False otherwise
        """
        if self._vector_store is None:
            try:
                from lib.rag.vector_store import CampaignVectorStore
                from lib.rag.embedder import LocalEmbedder

                if not CampaignVectorStore.is_available():
                    return False

                self._vector_store = CampaignVectorStore(str(self.campaign_dir))
                self._embedder = LocalEmbedder()
                return True
            except ImportError as e:
                print(f"[ERROR] RAG components not available: {e}")
                return False
            except ValueError:
                # No active campaign to point the store at — RAG simply off.
                return False
        return True

    def find_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Search for an entity by name across all entity types.

        Search order: NPCs -> Locations -> Items -> Plots
        Uses exact match first, then fuzzy matching.
        Locations with 'dungeon' field are typed as 'dungeon'.

        Args:
            name: Entity name to search for

        Returns:
            Dict with 'type', 'name', 'data' if found, None otherwise
        """
        entity_files = [
            ("npc", "npcs.json"),
            ("location", "locations.json"),
            ("item", "items.json"),
            ("plot", "plots.json"),
        ]

        name_lower = name.lower()

        # First pass: exact match (case-insensitive)
        for entity_type, filename in entity_files:
            data = self.json_ops.load_json(filename)
            if not isinstance(data, dict):
                continue

            for key in data.keys():
                if key.lower() == name_lower:
                    # Check if location is actually a dungeon
                    actual_type = entity_type
                    if entity_type == "location" and data[key].get("dungeon"):
                        actual_type = "dungeon"
                    return {
                        "type": actual_type,
                        "name": key,
                        "data": data[key]
                    }

        # Second pass: substring match (search term contained in entity name)
        for entity_type, filename in entity_files:
            data = self.json_ops.load_json(filename)
            if not isinstance(data, dict):
                continue

            for key in data.keys():
                if name_lower in key.lower():
                    # Check if location is actually a dungeon
                    actual_type = entity_type
                    if entity_type == "location" and data[key].get("dungeon"):
                        actual_type = "dungeon"
                    return {
                        "type": actual_type,
                        "name": key,
                        "data": data[key]
                    }

        # Third pass: fuzzy match (similarity > 0.5)
        best_match = None
        best_score = 0.5  # Minimum threshold

        for entity_type, filename in entity_files:
            data = self.json_ops.load_json(filename)
            if not isinstance(data, dict):
                continue

            for key in data.keys():
                # Use sequence matching for similarity
                score = SequenceMatcher(None, name_lower, key.lower()).ratio()
                if score > best_score:
                    best_score = score
                    # Check if location is actually a dungeon
                    actual_type = entity_type
                    if entity_type == "location" and data[key].get("dungeon"):
                        actual_type = "dungeon"
                    best_match = {
                            "type": actual_type,
                            "name": key,
                            "data": data[key]
                        }

        return best_match

    def search_raw(self, query: str, n_results: int = 15) -> List[Dict[str, Any]]:
        """
        Direct RAG search without entity filtering.

        Returns raw passages for the GM to evaluate relevance.
        No name matching, no strict filtering - just semantic search.

        Args:
            query: Search query (keywords, phrases, questions)
            n_results: Max results to return

        Returns:
            List of passage dicts with 'text', 'distance', 'metadata'
        """
        if not self._ensure_rag():
            print("[ERROR] RAG not available - no vector store found")
            return []

        # Check if vector store has data
        if self._vector_store.count() == 0:
            print("[INFO] Vector store is empty - import a document first")
            return []

        results = self._vector_store.query_by_text(
            query,
            self._embedder,
            n_results=n_results
        )

        passages = []
        seen_passages = set()  # Deduplicate only

        for doc, distance, metadata in zip(
            results['documents'],
            results['distances'],
            results['metadatas']
        ):
            # Skip duplicates only
            doc_key = doc[:200].lower()
            if doc_key in seen_passages:
                continue
            seen_passages.add(doc_key)

            # Clean the passage
            clean_doc = self._clean_passage(doc)

            passages.append({
                "text": clean_doc,
                "distance": distance,
                "metadata": metadata
            })

        return passages

    @staticmethod
    def _enhancement_queries(name: str, entity_type: str) -> List[str]:
        """Retrieval strings for one entity: name+type, then type-specific templates."""
        templates = ENTITY_QUERIES.get(entity_type, ["{name}"])
        lead = f"{name} {entity_type}".strip()
        return [lead] + [t.format(name=name) for t in templates]

    def query_passages(self, name: str, entity_type: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Query the vector store for passages related to an entity.

        Uses name+type plus entity-type-specific templates. Returns semantically
        relevant passages; the caller still runs the relevance gate.

        Args:
            name: Entity name to search for
            entity_type: Type of entity (npc, location, item, plot)
            n_results: Max results per query

        Returns:
            List of passage dicts with 'text', 'distance', 'metadata'
        """
        if not self._ensure_rag():
            print("[ERROR] RAG not available - no vector store found")
            return []

        # Check if vector store has data
        if self._vector_store.count() == 0:
            print("[INFO] Vector store is empty - import a document first")
            return []

        passages = []
        seen_passages = set()  # Deduplicate

        queries = self._enhancement_queries(name, entity_type)

        for query in queries:
            results = self._vector_store.query_by_text(
                query,
                self._embedder,
                n_results=n_results
            )

            for doc, distance, metadata in zip(
                results['documents'],
                results['distances'],
                results['metadatas']
            ):
                # Skip duplicates (use first 200 chars as key)
                doc_key = doc[:200].lower()
                if doc_key in seen_passages:
                    continue

                # Skip only very low-relevance results (distance > 1.5)
                # Let GM judge everything else
                if distance > 1.5:
                    continue

                seen_passages.add(doc_key)

                # Clean the passage
                clean_doc = self._clean_passage(doc)

                passages.append({
                    "text": clean_doc,
                    "distance": distance,
                    "metadata": metadata
                })

        # Sort by relevance (lower distance = more relevant)
        passages.sort(key=lambda x: x['distance'])

        return passages[:20]  # Return more results, let GM filter

    def _clean_passage(self, text: str, max_length: int = 600) -> str:
        """Remove noise and cap length of passages."""
        import re

        # Remove page markers
        text = re.sub(r'---\s*Page\s*\d+\s*---\n?', '', text)
        # Remove OceanofPDF watermarks
        text = re.sub(r'OceanofPDF\.com\s*', '', text)
        # Clean up excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()

        # Cap length, try to break at sentence boundary
        if len(text) > max_length:
            truncated = text[:max_length]
            last_period = truncated.rfind('. ')
            last_newline = truncated.rfind('\n')
            break_at = max(last_period, last_newline)
            if break_at > max_length // 2:
                text = truncated[:break_at + 1].strip()
            else:
                text = truncated.strip() + "..."

        return text

    def get_enhancement_summary(self, entity: Dict, passages: List[Dict]) -> Dict[str, Any]:
        """
        Generate a summary of what can be enhanced for an entity.

        Args:
            entity: Entity dict from find_entity()
            passages: Passages from query_passages()

        Returns:
            Summary dict with entity info and passage count
        """
        return {
            "entity_type": entity["type"],
            "entity_name": entity["name"],
            "current_description": entity["data"].get("description", "No description"),
            "existing_context_count": len(entity["data"].get("context", [])),
            "found_passages": len(passages),
            "passages": passages
        }

    def apply_enhancements(
        self,
        entity_type: str,
        entity_name: str,
        new_context: List[str],
        new_description: Optional[str] = None,
        additional_fields: Optional[Dict] = None
    ) -> bool:
        """
        Apply enhancements to an entity by updating its JSON file.

        Uses additive merge strategy - new context is appended, not replaced.
        Existing user-added data is preserved.

        Args:
            entity_type: Type of entity (npc, location, item, plot)
            entity_name: Name of the entity to update
            new_context: List of new context passages to add
            new_description: Optional new/enhanced description
            additional_fields: Optional dict of other fields to update

        Returns:
            True on success, False on failure
        """
        filename_map = {
            "npc": "npcs.json",
            "location": "locations.json",
            "dungeon": "locations.json",  # Dungeons are stored in locations
            "item": "items.json",
            "plot": "plots.json",
        }

        filename = filename_map.get(entity_type)
        if not filename:
            print(f"[ERROR] Unknown entity type: {entity_type}")
            return False

        # Load current data
        data = self.json_ops.load_json(filename)
        if entity_name not in data:
            print(f"[ERROR] Entity '{entity_name}' not found in {filename}")
            return False

        entity = data[entity_name]

        # Merge context (additive, deduplicated)
        existing_context = entity.get("context", [])
        seen_keys = set(p[:100].lower() for p in existing_context)

        for passage in new_context:
            p_key = passage[:100].lower()
            if p_key not in seen_keys:
                seen_keys.add(p_key)
                existing_context.append(passage)

        # Limit total context
        entity["context"] = existing_context[:20]

        # Update description if provided and it's an enhancement
        if new_description:
            old_desc = entity.get("description", "")
            # Only update if new description is longer or different
            if len(new_description) > len(old_desc) or not old_desc:
                entity["description"] = new_description

        # Apply additional fields (with care not to overwrite important data)
        if additional_fields:
            for key, value in additional_fields.items():
                # Don't overwrite certain protected fields
                if key in ["name", "created", "source"]:
                    continue
                # Merge lists additively
                if isinstance(value, list) and isinstance(entity.get(key), list):
                    existing = set(entity[key])
                    for item in value:
                        if item not in existing:
                            entity[key].append(item)
                # Update other fields
                else:
                    entity[key] = value

        # Mark as enhanced
        entity["enhanced"] = True
        entity["enhanced_at"] = self.json_ops.get_timestamp()

        # Save
        data[entity_name] = entity
        if self.json_ops.save_json(filename, data):
            print(f"[SUCCESS] Enhanced {entity_type}: {entity_name}")
            print(f"  - Context passages: {len(entity['context'])}")
            return True

        return False

    def count_dungeon_rooms(self, dungeon_name: str) -> int:
        """
        Count rooms belonging to a dungeon.

        Searches locations.json for entries where the 'dungeon' field
        matches the given dungeon name.

        Args:
            dungeon_name: Name of the dungeon to count rooms for

        Returns:
            Number of rooms belonging to this dungeon
        """
        locations = self.json_ops.load_json("locations.json")
        if not isinstance(locations, dict):
            return 0

        return sum(
            1 for loc in locations.values()
            if loc.get("dungeon") == dungeon_name
        )

    def get_dungeon_info(self, dungeon_name: str) -> Dict[str, Any]:
        """
        Get information about a dungeon including room count and structure status.

        Args:
            dungeon_name: Name of the dungeon

        Returns:
            Dict with dungeon info: room_count, has_structure, rooms (if any)
        """
        locations = self.json_ops.load_json("locations.json")
        if not isinstance(locations, dict):
            return {"room_count": 0, "has_structure": False, "rooms": []}

        rooms = []
        for name, loc in locations.items():
            if loc.get("dungeon") == dungeon_name:
                rooms.append({
                    "name": name,
                    "room_number": loc.get("room_number", 0),
                    "discovered": loc.get("state", {}).get("discovered", False),
                    "cleared": loc.get("state", {}).get("cleared", False)
                })

        # Sort by room number
        rooms.sort(key=lambda r: r.get("room_number", 0))

        return {
            "dungeon_name": dungeon_name,
            "room_count": len(rooms),
            "has_structure": len(rooms) > 0,
            "rooms": rooms
        }

    def get_scene_context(self, location_name: str) -> Optional[Dict[str, Any]]:
        """
        Get scene context for GM use. Returns None if no RAG available.

        This method provides internal context for the GM to craft scenes,
        without exposing raw passages to the player. It also auto-enhances
        locations on first visit.

        Args:
            location_name: Name or description of the location

        Returns:
            Dict with 'source', 'location', and context data, or None if no RAG
        """
        # Check if vectors exist
        vectors_dir = self.campaign_dir / "vectors"
        if not vectors_dir.exists() or not any(vectors_dir.iterdir()):
            return None  # No RAG for this campaign

        # Try to find location in locations.json
        locations = self.json_ops.load_json("locations.json")
        location_data = None
        location_key = None

        if isinstance(locations, dict):
            # Try exact match first
            for name, data in locations.items():
                if location_name.lower() == name.lower():
                    location_key = name
                    location_data = data
                    break

            # Try substring match
            if not location_key:
                for name, data in locations.items():
                    if location_name.lower() in name.lower():
                        location_key = name
                        location_data = data
                        break

        # If enhanced, return stored context
        if location_data and location_data.get("enhanced") and location_data.get("context"):
            return {
                "source": "stored",
                "location": location_key,
                "context": location_data["context"][:5],  # Top 5 for GM reference
            }

        # Query RAG
        passages = self.search_raw(
            f"{location_name} atmosphere inhabitants features",
            n_results=8
        )

        if not passages:
            return None

        # Auto-enhance: store passages for future visits
        if location_key:
            context_texts = [p["text"][:500] for p in passages[:5]]  # Top 5, truncated
            self.apply_enhancements("location", location_key, context_texts)

        return {
            "source": "rag",
            "location": location_name,
            "passages": passages
        }

    def list_unenhanced(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List entities that haven't been enhanced yet.

        Background-tiered entities (`background: true`, set by extraction_cap) are
        skipped: the import keeps the book's whole cast, but a RAG round-trip per
        entity would then cost several times what the playable core costs. They are
        enhanced when they are promoted into play, not up front.

        Args:
            entity_type: Optional filter by type (npc, location, dungeon, item, plot)

        Returns:
            List of entity dicts with type, name, has_context
        """
        entity_files = {
            "npc": "npcs.json",
            "location": "locations.json",
            "item": "items.json",
            "plot": "plots.json",
        }

        # Handle dungeon as a special case of location
        if entity_type == "dungeon":
            entity_files = {"location": "locations.json"}
        elif entity_type:
            entity_files = {entity_type: entity_files.get(entity_type)}

        unenhanced = []

        for etype, filename in entity_files.items():
            if not filename:
                continue
            data = self.json_ops.load_json(filename)
            if not isinstance(data, dict):
                continue

            for name, entity_data in data.items():
                if not isinstance(entity_data, dict) or entity_data.get("background"):
                    continue
                if not entity_data.get("enhanced"):
                    # Determine actual type (location vs dungeon)
                    actual_type = etype
                    if etype == "location" and entity_data.get("dungeon"):
                        actual_type = "dungeon"

                    # Filter by dungeon if requested
                    if entity_type == "dungeon" and actual_type != "dungeon":
                        continue

                    unenhanced.append({
                        "type": actual_type,
                        "name": name,
                        "has_context": len(entity_data.get("context", [])) > 0
                    })

        return unenhanced

    # Relevance gate tuning.
    RELEVANCE_FLOOR = 1.0   # max distance for a non-name-bearing passage to be kept
    KEEP_TARGET = 4         # target passages per entity
    LOW_RELEVANCE_WARN_FRACTION = 0.25  # batch warns + exits non-zero at/above this share of total

    @staticmethod
    def _gate_passages(name, aliases, passages, floor=RELEVANCE_FLOOR, keep_target=KEEP_TARGET):
        """Relevance-gate raw passages for one entity.

        - Force-include every passage that literally names the entity or an alias.
        - Fill remaining slots only with passages at/under the similarity floor
          (drop below-floor instead of padding to a fixed N).
        - If nothing names the entity, attach nothing (wrong neighbours are worse
          than a thin sheet).
        - Return (kept_passages_sorted_by_distance, name_match_fraction).

        name_match_fraction = kept passages that name the entity / kept total
        (0.0 and empty kept when nothing names it).
        """
        terms = [t.lower() for t in ([name] + list(aliases or [])) if t]

        def names_entity(p):
            text = (p.get("text") or "").lower()
            return any(term in text for term in terms)

        name_bearing = [p for p in passages if names_entity(p)]
        if not name_bearing:
            return [], 0.0
        others = [p for p in passages if not names_entity(p) and p.get("distance", 99) <= floor]

        # Force-include all name-bearing; fill the rest from floor-passing others.
        fill = max(0, keep_target - len(name_bearing))
        others_sorted = sorted(others, key=lambda p: p.get("distance", 99))
        kept = name_bearing + others_sorted[:fill]
        kept.sort(key=lambda p: p.get("distance", 99))

        frac = (len(name_bearing) / len(kept)) if kept else 0.0
        return kept, frac

    @staticmethod
    def format_batch_summary(result: Dict[str, Any]) -> Tuple[str, int]:
        """Render the batch summary. Exit 1 at/above LOW_RELEVANCE_WARN_FRACTION of total."""
        enhanced = result.get("enhanced", 0)
        skipped = result.get("skipped", 0)
        low = result.get("low_relevance", 0)
        total = result.get("total", 0) or 0
        names = list(result.get("low_relevance_names") or [])
        frac = (low / total) if total else 0.0
        warn = frac >= EntityEnhancer.LOW_RELEVANCE_WARN_FRACTION

        lines = []
        if warn:
            lines.extend([
                "!" * 40,
                f"WARNING: {low}/{total} ({frac:.0%}) entities had 0 name-bearing passages.",
                f"Nothing attached. Threshold: {EntityEnhancer.LOW_RELEVANCE_WARN_FRACTION:.0%} of total.",
                "!" * 40,
                "",
            ])
        lines.extend([
            f"Enhanced: {enhanced}",
            f"Skipped:  {skipped}",
            f"Low-relevance (0 name-bearing, not attached): {low}",
            f"Total:    {total}",
        ])
        if names:
            lines.append("")
            lines.append("Worst offenders (0 name-bearing):")
            for n in names:
                lines.append(f"  - {n}")
        return "\n".join(lines), (1 if warn else 0)

    def batch_enhance(self, max_entities: Optional[int] = None) -> Dict[str, Any]:
        """
        Batch enhance all unenhanced entities, relevance-gated.

        Queries RAG for each entity, force-includes name-bearing passages, drops
        below-floor neighbours, and persists per-passage scores + a name-match
        fraction. Entities with zero name-bearing passages are reported (not
        enhanced) and get nothing attached.

        Returns:
            Dict with counts: enhanced, skipped, low_relevance, total,
            plus low_relevance_names.
        """
        unenhanced = self.list_unenhanced()

        if max_entities:
            unenhanced = unenhanced[:max_entities]

        total = len(unenhanced)
        enhanced = 0
        skipped = 0
        low_relevance = 0
        low_relevance_names: List[str] = []

        print(f"Found {total} unenhanced entities\n")

        for i, entity in enumerate(unenhanced, 1):
            etype = entity['type']
            name = entity['name']

            print(f"[{i}/{total}] {etype}: {name}... ", end="", flush=True)

            # Pull a wider candidate set, then gate.
            passages = self.query_passages(name, etype, n_results=8)

            if not passages:
                print("skipped (no passages)")
                skipped += 1
                continue

            found = self.find_entity(name)
            aliases = (found or {}).get("data", {}).get("aliases", []) if found else []
            kept, frac = self._gate_passages(name, aliases, passages)

            if not kept:
                low_relevance += 1
                low_relevance_names.append(name)
                print("reported (0 name-bearing — nothing attached)")
                continue

            context_texts = [p.get('text', '')[:500] for p in kept if p.get('text')]
            if not context_texts:
                print("skipped (no relevant passages)")
                skipped += 1
                continue

            scores = [round(float(p.get('distance', 0.0)), 4) for p in kept if p.get('text')]
            success = self.apply_enhancements(
                etype, name, context_texts,
                additional_fields={
                    "context_scores": scores,
                    "context_name_match_fraction": round(frac, 3),
                },
            )

            if success:
                print(f"enhanced! (name-match {frac:.0%})")
                enhanced += 1
            else:
                print("failed")
                skipped += 1

        return {
            "enhanced": enhanced,
            "skipped": skipped,
            "low_relevance": low_relevance,
            "low_relevance_names": low_relevance_names,
            "total": total
        }


def main():
    """CLI interface for entity enhancement."""
    import argparse

    parser = argparse.ArgumentParser(description='Entity enhancement using RAG')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Find entity
    find_parser = subparsers.add_parser('find', help='Find entity by name')
    find_parser.add_argument('name', help='Entity name to search for')

    # Query passages
    query_parser = subparsers.add_parser('query', help='Query passages for entity')
    query_parser.add_argument('name', help='Entity name')
    query_parser.add_argument('--type', help='Entity type (npc, location, item, plot)')
    query_parser.add_argument('-n', '--num', type=int, default=10, help='Max results per query')

    # Apply enhancements
    apply_parser = subparsers.add_parser('apply', help='Apply context to entity')
    apply_parser.add_argument('name', help='Entity name')
    apply_parser.add_argument('--context', action='append', help='Context passage to add')
    apply_parser.add_argument('--description', help='New description')

    # List unenhanced
    list_parser = subparsers.add_parser('list-unenhanced', help='List entities without enhancement')
    list_parser.add_argument('--type', help='Filter by entity type')

    # Summary command (find + query in one)
    summary_parser = subparsers.add_parser('summary', help='Get enhancement summary for entity')
    summary_parser.add_argument('name', help='Entity name')

    # Raw search command (no entity filtering)
    search_parser = subparsers.add_parser('search', help='Direct RAG search (no entity filtering)')
    search_parser.add_argument('query', help='Search query (keywords, phrases, questions)')
    search_parser.add_argument('-n', '--num', type=int, default=15, help='Max results')
    search_parser.add_argument('--full', action='store_true', help='Show full passage text')
    search_parser.add_argument('--excerpt-chars', type=int, default=350, help='Excerpt length when not using --full')

    # Dungeon check command
    dungeon_parser = subparsers.add_parser('dungeon-check', help='Check dungeon room structure')
    dungeon_parser.add_argument('name', help='Dungeon name to check')

    # Scene context command (GM-internal, minimal output)
    scene_parser = subparsers.add_parser('scene', help='Get scene context for GM use (minimal output)')
    scene_parser.add_argument('name', help='Location name or description')

    # Batch enhance command
    batch_parser = subparsers.add_parser('batch', help='Batch enhance all unenhanced entities')
    batch_parser.add_argument('-n', '--max', type=int, help='Max entities to process')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    enhancer = EntityEnhancer()

    if args.action == 'find':
        result = enhancer.find_entity(args.name)
        if result:
            print(f"Found {result['type'].upper()}: {result['name']}")
            print(json.dumps(result['data'], indent=2))
        else:
            print(f"No entity found matching: {args.name}")
            sys.exit(1)

    elif args.action == 'query':
        # First find the entity to get its type
        entity = enhancer.find_entity(args.name)
        if not entity:
            print(f"No entity found matching: {args.name}")
            sys.exit(1)

        entity_type = args.type or entity['type']
        print(f"Querying passages for {entity_type}: {entity['name']}")

        passages = enhancer.query_passages(entity['name'], entity_type, args.num)

        if passages:
            print(f"\nFound {len(passages)} relevant passages:\n")
            for i, p in enumerate(passages, 1):
                print(f"--- Passage {i} (relevance: {1 - p['distance']:.2f}) ---")
                print(p['text'][:500])
                print()
        else:
            print("No passages found. Is the vector store populated?")

    elif args.action == 'apply':
        entity = enhancer.find_entity(args.name)
        if not entity:
            print(f"No entity found matching: {args.name}")
            sys.exit(1)

        context = args.context or []
        if not context and not args.description:
            print("Provide --context or --description to apply")
            sys.exit(1)

        success = enhancer.apply_enhancements(
            entity['type'],
            entity['name'],
            context,
            args.description
        )
        if not success:
            sys.exit(1)

    elif args.action == 'list-unenhanced':
        unenhanced = enhancer.list_unenhanced(args.type)
        if unenhanced:
            print(f"Unenhanced entities: {len(unenhanced)}\n")
            for e in unenhanced:
                ctx_marker = "[has context]" if e['has_context'] else ""
                print(f"  [{e['type']}] {e['name']} {ctx_marker}")
        else:
            print("All entities have been enhanced!")

    elif args.action == 'summary':
        entity = enhancer.find_entity(args.name)
        if not entity:
            print(f"No entity found matching: {args.name}")
            sys.exit(1)

        print(f"Searching passages for: {entity['name']} ({entity['type']})")
        passages = enhancer.query_passages(entity['name'], entity['type'])

        summary = enhancer.get_enhancement_summary(entity, passages)
        print(json.dumps(summary, indent=2, default=str))

    elif args.action == 'search':
        print(f"RAG Search: {args.query}")
        print(f"Max results: {args.num}\n")

        passages = enhancer.search_raw(args.query, args.num)

        if passages:
            print(f"Found {len(passages)} passages:\n")
            for i, p in enumerate(passages, 1):
                relevance = 1 - p['distance']
                page = p['metadata'].get('page', '?')
                print(f"--- Passage {i} (relevance: {relevance:.2f}, page: {page}) ---")
                if args.full:
                    print(p['text'])
                else:
                    excerpt = p['text'][:args.excerpt_chars]
                    if len(p['text']) > args.excerpt_chars:
                        excerpt += "..."
                    print(excerpt)
                print()
        else:
            print("No passages found. Is the vector store populated?")

    elif args.action == 'dungeon-check':
        # First find the dungeon entity
        entity = enhancer.find_entity(args.name)

        if entity and entity['type'] == 'dungeon':
            dungeon_name = entity['data'].get('dungeon', entity['name'])
            info = enhancer.get_dungeon_info(dungeon_name)
        else:
            # Try using the name directly as dungeon name
            info = enhancer.get_dungeon_info(args.name)

        print(f"Dungeon: {info['dungeon_name']}")
        print(f"Room count: {info['room_count']}")
        print(f"Has structure: {info['has_structure']}")

        if info['rooms']:
            print("\nRooms:")
            for room in info['rooms']:
                status = []
                if room['discovered']:
                    status.append('discovered')
                if room['cleared']:
                    status.append('cleared')
                status_str = f" [{', '.join(status)}]" if status else ""
                print(f"  {room['room_number']}. {room['name']}{status_str}")
        else:
            print("\n** No room structure defined **")
            print("Consider spawning dungeon-architect to generate rooms.")

        # Output JSON for script parsing
        print("\n--- JSON ---")
        print(json.dumps(info, indent=2))

    elif args.action == 'scene':
        # GM-internal scene context (minimal output)
        result = enhancer.get_scene_context(args.name)

        if result is None:
            # Silent - no RAG available for this campaign
            pass
        elif result["source"] == "stored":
            print(f"[GM Context: {result['location']}]")
            for ctx in result["context"]:
                # Show first 100 chars of each context passage
                print(f"  • {ctx[:100]}...")
        else:
            # From RAG query
            loc_name = result.get("location", args.name)
            print(f"[GM Context: {loc_name} (from source)]")
            for p in result["passages"][:3]:
                print(f"  • {p['text'][:100]}...")

    elif args.action == 'batch':
        print("Batch Enhancement")
        print("=" * 40)
        print()

        max_entities = getattr(args, 'max', None)
        result = enhancer.batch_enhance(max_entities)

        print()
        print("=" * 40)
        text, code = EntityEnhancer.format_batch_summary(result)
        print(text)
        if code:
            sys.exit(code)


if __name__ == "__main__":
    main()
