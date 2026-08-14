#!/usr/bin/env python3
"""
Long-term campaign memory — so a 50-session campaign remembers itself.

Builds a recall index over the campaign's OWN lived history (session summaries +
facts) and maintains a tiered, consolidating memoir (always-on arc summary +
recent verbatim + compressed older + retrievable archive) so memory stays
high-signal and bounded. A provenance dimension separates book-canon from
our-story so the huge imported world stays out of always-loaded context while the
threads you actually touched surface. session-log.md remains the canonical ledger
— this only reads it.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager

_CANON_CATEGORIES = {"plot_world", "world_building"}


class CampaignMemory(EntityManager):
    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)
        self.memory_file = "campaign-memory.json"

    def gather(self) -> List[Dict[str, Any]]:
        """Collect memory entries from the campaign's own history (read-only)."""
        entries: List[Dict[str, Any]] = []

        log_path = self.campaign_dir / "session-log.md"
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8")
            for block in text.split("## Session Started:"):
                if "### Session Ended:" not in block:
                    continue
                after = block.split("### Session Ended:", 1)[1]
                body = []
                for ln in after.splitlines()[1:]:
                    s = ln.strip()
                    if s == "---":
                        break
                    if s and not s.startswith("**"):  # skip the structured footer lines
                        body.append(s)
                if body:
                    entries.append({"text": " ".join(body), "provenance": "our-story",
                                    "source": "session-log", "tier": "recent"})

        facts = self.json_ops.load_json("facts.json") or {}
        if isinstance(facts, dict):
            for cat, items in facts.items():
                if not isinstance(items, list):
                    continue
                prov = "book-canon" if cat in _CANON_CATEGORIES else "our-story"
                for it in items:
                    t = it.get("fact") if isinstance(it, dict) else str(it)
                    if t:
                        entries.append({"text": t, "provenance": prov,
                                        "source": f"facts:{cat}", "tier": "archive"})
        return entries

    # ---- GM-authored arc entries (the real consolidation tier) ----
    #
    # gather() can only re-read what the log already says; an ARC entry is the
    # GM's own end-of-session synthesis — what changed, who matters now, what
    # debts are open. Written via `gm-recall.sh arc '<json>'` at session end.

    def add_arc(self, summary: str, who_matters: List[str] = None,
                open_debts: List[str] = None) -> Dict[str, Any]:
        """Append a GM-authored arc entry. Returns the stored entry."""
        data = self.json_ops.load_json(self.memory_file) or {}
        entry = {
            "summary": (summary or "").strip(),
            "who_matters": [str(x) for x in (who_matters or []) if str(x).strip()],
            "open_debts": [str(x) for x in (open_debts or []) if str(x).strip()],
            "at": self.get_timestamp(),
        }
        data.setdefault("arcs", []).append(entry)
        self.json_ops.save_json(self.memory_file, data)
        return entry

    def arcs(self) -> List[Dict[str, Any]]:
        return (self.json_ops.load_json(self.memory_file) or {}).get("arcs", [])

    @staticmethod
    def _arc_text(a: Dict[str, Any]) -> str:
        bits = [a.get("summary", "")]
        if a.get("who_matters"):
            bits.append("Who matters: " + ", ".join(a["who_matters"]))
        if a.get("open_debts"):
            bits.append("Open debts: " + "; ".join(a["open_debts"]))
        return " ".join(b for b in bits if b)

    # ---- index build + recall ----

    def refresh(self) -> int:
        """Rebuild the recall collection (called on save). Preserves arcs, and
        (when RAG deps are installed) embeds entries for semantic recall —
        re-embedding only when the entry texts actually changed, since this
        runs on every autosave."""
        entries = self.gather()
        entries += [{"text": self._arc_text(a), "provenance": "our-story",
                     "source": "arc", "tier": "arc"} for a in self.arcs()]
        data = self.json_ops.load_json(self.memory_file) or {}
        data["entries"] = entries

        texts = [e["text"] for e in entries]
        import hashlib
        content_hash = hashlib.md5("\x1f".join(texts).encode("utf-8")).hexdigest()
        if data.get("entries_hash") != content_hash:
            data["entries_hash"] = content_hash
            data["embeddings"] = self._embed_batch(texts)  # None when deps missing
        self.json_ops.save_json(self.memory_file, data)
        return len(entries)

    @staticmethod
    def _embed_batch(texts):
        """Embed texts via LocalEmbedder; None when RAG deps are missing."""
        if not texts:
            return []
        try:
            from rag.embedder import LocalEmbedder
            vecs = LocalEmbedder().embed_batch(texts)
            return [[round(float(x), 4) for x in v] for v in vecs]
        except ImportError:
            return None

    def recall(self, query: str, top_k: int = 5, provenance: str = None) -> List[Dict[str, Any]]:
        """Recall over the campaign's history: cosine over stored embeddings
        when available, keyword overlap otherwise."""
        data = self.json_ops.load_json(self.memory_file) or {}
        entries = data.get("entries") or self.gather()
        vectors = data.get("embeddings")

        if vectors and len(vectors) == len(entries):
            hits = self._recall_semantic(query, entries, vectors, top_k, provenance)
            if hits is not None:
                return hits
        return self._recall_keyword(query, entries, top_k, provenance)

    @staticmethod
    def _recall_semantic(query, entries, vectors, top_k, provenance):
        """Cosine top-k; None when deps are missing (caller falls back)."""
        try:
            from rag.embedder import LocalEmbedder
        except ImportError:
            return None
        q = LocalEmbedder().embed(query)
        import math
        qn = math.sqrt(sum(x * x for x in q)) or 1.0
        scored = []
        for e, v in zip(entries, vectors):
            if provenance and e.get("provenance") != provenance:
                continue
            dot = sum(a * b for a, b in zip(q, v))
            vn = math.sqrt(sum(b * b for b in v)) or 1.0
            scored.append((dot / (qn * vn), e))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    @staticmethod
    def _recall_keyword(query, entries, top_k, provenance):
        if provenance:
            entries = [e for e in entries if e.get("provenance") == provenance]
        q = set(re.findall(r"\w+", query.lower()))
        if not q:
            return []
        scored = []
        for e in entries:
            tw = set(re.findall(r"\w+", e["text"].lower()))
            s = len(q & tw)
            if s > 0:
                scored.append((s, e))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def memoir(self) -> Dict[str, Any]:
        """Tiered, bounded memoir: real arc entries first, raw history behind."""
        entries = self.gather()
        recent = [e for e in entries if e["tier"] == "recent"]
        archive = [e for e in entries if e["tier"] == "archive"]
        arcs = self.arcs()
        # A GM-authored arc entry is the arc summary; the last raw session
        # summary (truncated) is only the fallback for campaigns without arcs.
        arc = self._arc_text(arcs[-1]) if arcs else (recent[-1]["text"][:300] if recent else "")
        return {
            "arc_summary": arc,
            "arc_entries": len(arcs),
            "recent": recent[-3:],
            "compressed_older": max(0, len(recent) - 3),
            "archive_count": len(archive),
            "canon_count": sum(1 for e in entries if e["provenance"] == "book-canon"),
        }


def main():
    import argparse
    import json
    from cli_output import wants_json, strip_json_flag, emit

    parser = argparse.ArgumentParser(description="Campaign memory")
    sub = parser.add_subparsers(dest="action")
    r = sub.add_parser("recall"); r.add_argument("query", nargs="+")
    r.add_argument("--top-k", type=int, default=5)
    r.add_argument("--provenance", choices=["our-story", "book-canon"])
    sub.add_parser("refresh")
    sub.add_parser("memoir")
    a = sub.add_parser("arc", help="Record the GM's end-of-session arc entry")
    a.add_argument("entry", help='JSON: {"summary": "...", "who_matters": [...], "open_debts": [...]}')

    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))
    if not args.action:
        parser.print_help(); sys.exit(1)

    m = CampaignMemory()
    if args.action == "recall":
        out = m.recall(" ".join(args.query), top_k=args.top_k,
                       provenance=getattr(args, "provenance", None))
    elif args.action == "refresh":
        out = {"indexed": m.refresh()}
    elif args.action == "arc":
        try:
            payload = json.loads(args.entry)
        except ValueError:
            payload = {"summary": args.entry}  # bare prose is a valid arc summary
        if not isinstance(payload, dict) or not str(payload.get("summary", "")).strip():
            from cli_output import emit_error
            sys.exit(emit_error("arc entry needs a summary", json_mode=json_mode))
        out = m.add_arc(payload.get("summary", ""),
                        who_matters=payload.get("who_matters"),
                        open_debts=payload.get("open_debts"))
        m.refresh()  # arcs join the recall index immediately
    else:
        out = m.memoir()

    if json_mode:
        emit(out, json_mode=True)
    else:
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
