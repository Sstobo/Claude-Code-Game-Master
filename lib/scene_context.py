#!/usr/bin/env python3
"""
Unified scene-context entry point.

Collapses the confusing three-way choice (dm-search vs dm-enhance query vs
dm-enhance scene) into ONE call that returns structured context for the current
scene and any named entities: world-state facts (always) plus grounded source
passages from RAG (when a vector store exists). RAG is optional and degrades
gracefully — no vectors / no RAG deps simply means an empty `passages` list.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from search import WorldSearcher
from cli_output import emit, emit_error


class SceneContext:
    """One front door for 'what do I need to narrate this scene?'."""

    def __init__(self, world_state_dir: str = None):
        self.world_state_dir = world_state_dir
        self.searcher = WorldSearcher(world_state_dir)

    def current_location(self) -> str:
        """Resolve the party's current location from campaign state."""
        overview = self.searcher.json_ops.load_json("campaign-overview.json") or {}
        pos = overview.get("player_position", {})
        if isinstance(pos, dict):
            return pos.get("current_location", "") or ""
        return ""

    def build(self, location: str = None, entities: Optional[List[str]] = None) -> Dict[str, Any]:
        location = location or self.current_location()
        result: Dict[str, Any] = {
            "location": location,
            "world": {
                "location": self.searcher.get_location(location),
                "npcs_present": self.searcher.search_npcs_by_tag("locations", location),
            },
            "entities": {},
            "passages": [],
            "rag_available": False,
            "source": None,
        }
        for name in entities or []:
            result["entities"][name] = self.searcher.get_npc(name) or self.searcher.get_location(name)

        # Grounded source passages — optional. get_scene_context returns None when
        # the campaign has no vector store, and any RAG import/runtime error
        # degrades to world-state-only context rather than failing the scene.
        try:
            from entity_enhancer import EntityEnhancer
            scene = EntityEnhancer(self.world_state_dir).get_scene_context(location)
            if scene:
                result["rag_available"] = True
                result["source"] = scene.get("source")
                result["passages"] = scene.get("passages", scene.get("context", []))
        except Exception:
            pass

        return result


def main():
    import argparse

    json_mode = "--json" in sys.argv
    argv = [a for a in sys.argv[1:] if a != "--json"]

    parser = argparse.ArgumentParser(description="Unified scene context for the DM")
    parser.add_argument("location", nargs="?", help="Location (defaults to current)")
    parser.add_argument("--entity", action="append", default=[], help="Named entity to include (repeatable)")
    args = parser.parse_args(argv)

    ctx = SceneContext().build(args.location, args.entity)

    if json_mode:
        emit(ctx, json_mode=True)
        return

    print(f"=== SCENE CONTEXT: {ctx['location'] or '(unknown)'} ===")
    loc = ctx["world"]["location"]
    if loc:
        print(f"Location: {loc.get('description', '')}")
    present = ctx["world"]["npcs_present"]
    if present:
        print(f"NPCs present: {', '.join(present.keys())}")
    for name, data in ctx["entities"].items():
        print(f"- {name}: {'found' if data else 'unknown'}")
    if ctx["rag_available"]:
        print(f"Source passages ({ctx['source']}): {len(ctx['passages'])}")
    else:
        print("Source passages: (no RAG vectors for this campaign)")


if __name__ == "__main__":
    main()
