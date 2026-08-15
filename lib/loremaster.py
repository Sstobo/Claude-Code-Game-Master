#!/usr/bin/env python3
"""
Loremaster — grounded scene briefs from long-context reading, cached + gated.

Instead of stapling nearest-neighbor chunks, the Loremaster uses the coarse index
to FIND the relevant chapter, then reads a large span and returns a grounded
brief. Briefs are cached PER LOCATION and a deep read is gated to new/important
scenes — routine revisits reuse the cache, so the expensive read never fires every
turn. (The voice-grounded synthesis of the brief is the model's job in /gm; this
module owns the find/cache/gate/observe machinery + the source excerpt.)
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager
from book_bible import log_token_estimate
from rag.coarse_index import CoarseIndex


class Loremaster(EntityManager):
    def __init__(self, world_state_dir: str = None, book_text: Optional[str] = None):
        super().__init__(world_state_dir)
        self.cache_file = "loremaster-cache.json"
        self.index = CoarseIndex()
        text = book_text if book_text is not None else self._load_book_text()
        if text:
            self.index.build(text)

    def _load_book_text(self) -> str:
        for candidate in ("source/current-document.txt", "current-document.txt", "book-text.txt"):
            p = self.campaign_dir / candidate
            if p.exists():
                try:
                    return p.read_text(encoding="utf-8")
                except (IOError, ValueError):
                    return ""
        return ""

    def _cache(self) -> Dict[str, Any]:
        return self.json_ops.load_json(self.cache_file) or {}

    # Excerpt kept in the cache / default output. The FULL chapter span is
    # returned only on request (full=True) so a routine move never floods the
    # context with 20k chars.
    EXCERPT_CHARS = 1500

    def brief_for(self, location: str, important: bool = False,
                  full: bool = False) -> Dict[str, Any]:
        """Grounded brief for a scene. Deep-reads only on a new or important scene.

        full=True attaches the entire chapter span as `chapter_text` — the
        long-context read the GM does when it actually narrates the place. The
        full text is never cached (the cache holds pointers + excerpt; the book
        file is the storage).
        """
        cache = self._cache()
        in_cache = location in cache

        # Routine revisit: reuse the cache, NO deep read (keeps per-turn cost flat).
        if in_cache and not important:
            cached = dict(cache[location])
            cached["cache_hit"] = True
            cached["deep_read"] = False
            if full:
                cached["chapter_text"] = self._chapter_text(cached.get("chapters", []))
            return cached

        # New or important scene: find the chapter, read a span, ground the brief.
        pointers = self.index.query(location)
        excerpt = ""
        if pointers:
            chapter = self.index.load_chapter(pointers[0]["index"])
            excerpt = chapter.get("text", "")[:self.EXCERPT_CHARS]
            log_token_estimate(chapter.get("text", ""), label="loremaster")

        brief = {
            "location": location,
            "chapters": pointers,
            "grounded_excerpt": excerpt,
            "deep_read": True,
            "cache_hit": False,
        }
        cache[location] = brief
        self.json_ops.save_json(self.cache_file, cache)
        if full:
            brief = dict(brief)
            brief["chapter_text"] = self._chapter_text(pointers)
        return brief

    def _chapter_text(self, pointers) -> str:
        """Resolve the top chapter pointer to its full span text ("" if none)."""
        if not pointers:
            return ""
        return self.index.load_chapter(pointers[0].get("index", -1)).get("text", "")

    def has_book_text(self) -> bool:
        return bool(self.index.chapters)


def main():
    import argparse
    import json
    from cli_output import wants_json, strip_json_flag, emit

    parser = argparse.ArgumentParser(description="Loremaster scene brief")
    parser.add_argument("location", nargs="+")
    parser.add_argument("--important", action="store_true")
    parser.add_argument("--full", action="store_true",
                        help="include the entire chapter span (the long-context read)")
    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))

    brief = Loremaster().brief_for(" ".join(args.location),
                                   important=args.important, full=args.full)
    if json_mode:
        emit(brief, json_mode=True)
    elif args.full and brief.get("chapter_text"):
        meta = {k: v for k, v in brief.items() if k != "chapter_text"}
        print(json.dumps(meta, indent=2))
        print("\n--- FULL CHAPTER SPAN (ground the scene in this) ---")
        print(brief["chapter_text"])
    else:
        print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    main()
