#!/usr/bin/env python3
"""
Book Bible import helpers — long-context reading instead of chunk-and-delete.

The import flow keeps the book text (not deleted on cleanup), a world-bible
subagent reads LARGE spans (whole chapters via long context, not 3000-char
chunks) and emits a structured world-bible.json, and that bible AUTO-DRAFTS the
World Kit ruleset + campaign_rules. This module holds the deterministic, testable
pieces: chapter segmentation, the bible→ruleset/campaign_rules draft, and token
observability. The subagent read itself is orchestrated by the /import command.
"""

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from overview_seed import seed_overview

_CHAPTER_RE = re.compile(r'^\s*(chapter\s+\w+|part\s+\w+|\d+\.\s)', re.IGNORECASE | re.MULTILINE)


class ConfirmedBibleError(RuntimeError):
    """Raised when drafting would clobber a bible a human already approved."""


def segment_into_chapters(text: str, max_chars: int = 20000) -> List[Dict[str, Any]]:
    """Split book text into large spans for long-context reading.

    Prefers real chapter markers; falls back to size-based windows so a span is
    never an arbitrary 3000-char chunk. Returns [{index, title, text}].
    """
    if not text:
        return []
    marks = [m.start() for m in _CHAPTER_RE.finditer(text)]
    spans: List[str] = []
    if len(marks) >= 2:
        bounds = marks + [len(text)]
        for i in range(len(marks)):
            spans.append(text[bounds[i]:bounds[i + 1]])
    else:
        spans = [text]

    # Further split any span that exceeds max_chars (keep spans large, not tiny).
    chapters: List[Dict[str, Any]] = []
    idx = 0
    for span in spans:
        span = span.strip()
        if not span:
            continue
        if len(span) <= max_chars:
            pieces = [span]
        else:
            pieces = [span[i:i + max_chars] for i in range(0, len(span), max_chars)]
        for piece in pieces:
            first_line = piece.strip().splitlines()[0][:60] if piece.strip() else f"Span {idx + 1}"
            chapters.append({"index": idx, "title": first_line, "text": piece})
            idx += 1
    return chapters


def bible_to_campaign_rules(bible: Dict[str, Any]) -> Dict[str, Any]:
    """Map a world-bible's signature systems into a campaign_rules block."""
    systems = bible.get("signature_systems", []) or []
    return {
        "description": f"{bible.get('name', 'This world')} runs on its own systems — follow them exactly.",
        "signature_systems": list(systems),
        "tone": bible.get("tone", ""),
    }


def draft_ruleset_from_bible(bible: Dict[str, Any], progression_model: str = "milestone",
                             kit: str = "custom", attributes: List[str] = None,
                             **progression_config) -> Dict[str, Any]:
    """Auto-draft a World Kit ruleset.json from a world-bible.

    progression_model is chosen by the importer / human (default milestone, the
    safest book-native option). Resolution defaults to the universal d20-vs-dc core.
    `kit` is the machine-readable router: 'dnd5e' unlocks the D&D mechanics skills
    and the spell-caster agent, and the importer sets it ONLY when the book
    actually is a D&D module; every other book stays 'custom'.
    """
    progression = {"model": progression_model}
    progression.update(progression_config)
    agents = ["monster-manual", "rules-master", "loot-dropper", "gear-master", "npc-builder"]
    if kit == "dnd5e":
        agents.append("spell-caster")
    return {
        "name": bible.get("name", "Imported World"),
        "kit": kit,
        "stat_schema": {"attributes": list(attributes or []), "vitals": ["hp"]},
        "progression": progression,
        "resolution": {"model": "d20-vs-dc"},
        "active_agents": agents,
        "rules_doc": "rules.md",
    }


def draft_voice(style: str, sample_passages: List[str], source_text: str,
                vocab: List[str] = None) -> Dict[str, Any]:
    """Build a world-bible `voice` block for an imported book, GROUNDED in the source.

    The GM narrates in the author's voice only if the bible carries it (surfaced by
    `get_full_context`). To keep the voice faithful (not invented), sample passages
    are kept ONLY when they appear verbatim in the source text — so an imported
    book's voice is real excerpts of that author's prose, not paraphrase.
    """
    src = source_text or ""
    grounded = [p.strip() for p in (sample_passages or [])
                if p and p.strip() and p.strip() in src]
    return {
        "style": (style or "").strip(),
        "sample_passages": grounded,
        "vocab": [v.strip() for v in (vocab or []) if v and v.strip()],
    }


def log_token_estimate(text: str, label: str = "import") -> int:
    """Observable (never a cap) token estimate, emitted to stderr."""
    approx = len(text or "") // 4
    print(f"[{label}] ~{approx} tokens ({len(text or '')} chars)", file=sys.stderr)
    return approx


# --- the import chain: bible -> ruleset -> campaign_rules ---
#
# The split is deliberate. This module writes only what the SOURCE can prove: the
# chapter map, the verbatim-filtered voice block, and the skeleton keys
# validate_bible requires. The creative fields (tone, themes, factions, geography,
# signature_systems) are the MODEL's authorship during /import, merged in by
# re-running the same verb. Everything stays `confirmed: false` until a human
# approves it, which is what the WorldBible confirm gate reads.

_SKELETON = (
    ("tone", ""),
    ("themes", []),
    ("factions", {"nodes": [], "edges": []}),
    ("geography", {"nodes": [], "edges": []}),
    ("signature_systems", []),
    # Named-thing roster the GM scans before inventing a name. Populated by a
    # later ticket; each entry is {"name": str, "note": str}.
    ("index", {"npcs": [], "locations": [], "items": [], "monsters": []}),
)


def _bible_path(campaign_dir) -> Path:
    return Path(campaign_dir) / "world-bible.json"


def load_bible(campaign_dir) -> Dict[str, Any]:
    """Read a campaign's world-bible.json, or raise with the step that writes it."""
    path = _bible_path(campaign_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"no world-bible.json in {campaign_dir} — run `gm-extract.sh draft-bible` first")
    return json.loads(path.read_text(encoding="utf-8"))


def draft_bible(campaign_dir, name: str = None, voice: Dict[str, Any] = None,
                fields: Dict[str, Any] = None) -> Dict[str, Any]:
    """Draft (or refresh) an unconfirmed world-bible.json from the campaign's source text.

    Idempotent: re-running merges `name` / `voice` / `fields` into the existing
    draft, preserving anything already authored, and scaffolds an empty `index`
    (npcs/locations/items/monsters) for the named-thing roster. Refuses to touch
    a bible a human has confirmed (ConfirmedBibleError).
    """
    cdir = Path(campaign_dir)
    path = _bible_path(cdir)
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    # Absent flag == confirmed (the WorldBible rule): hand-authored and legacy
    # bibles are never overwritten by a draft pass.
    if existing and existing.get("confirmed", True):
        raise ConfirmedBibleError(
            f"world-bible.json in {campaign_dir} is confirmed — refusing to redraft it")

    src_path = cdir / "source" / "current-document.txt"
    if not src_path.exists():
        legacy = cdir / "current-document.txt"  # pre-source/ campaigns
        if legacy.exists():
            src_path = legacy
        else:
            raise FileNotFoundError(
                f"no source/current-document.txt in {campaign_dir} — run `gm-extract.sh prepare` first")
    source = src_path.read_text(encoding="utf-8", errors="replace")
    log_token_estimate(source, label="draft-bible")

    bible = dict(existing)
    bible["name"] = name or bible.get("name") or cdir.name
    for key, default in _SKELETON:
        bible.setdefault(key, copy.deepcopy(default))
    if fields:
        bible.update(fields)
    if voice is not None:
        bible["voice"] = draft_voice(
            style=voice.get("style", ""),
            sample_passages=voice.get("sample_passages", []),
            source_text=source,
            vocab=voice.get("vocab", []),
        )
    else:
        bible.setdefault("voice", draft_voice("", [], source))
    bible["confirmed"] = False

    path.write_text(json.dumps(bible, indent=2, ensure_ascii=False), encoding="utf-8")
    return bible


def write_ruleset(campaign_dir, progression_model: str = "milestone", kit: str = "custom",
                  attributes: List[str] = None, force: bool = False,
                  **progression_config) -> Dict[str, Any]:
    """Draft the World Kit from the bible and write it to ruleset.json."""
    path = Path(campaign_dir) / "ruleset.json"
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists — pass --force to redraft it")
    ruleset = draft_ruleset_from_bible(load_bible(campaign_dir), progression_model=progression_model,
                                       kit=kit, attributes=attributes, **progression_config)
    path.write_text(json.dumps(ruleset, indent=2, ensure_ascii=False), encoding="utf-8")
    return ruleset


def write_campaign_rules(campaign_dir) -> Dict[str, Any]:
    """Map the bible's signature systems into campaign-overview.json's campaign_rules."""
    rules = bible_to_campaign_rules(load_bible(campaign_dir))
    seed_overview(campaign_dir, campaign_rules=rules)
    return rules


INDEX_BUCKETS = ("npcs", "locations", "items", "monsters")


def write_index(campaign_dir, index: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a WORLD INDEX into the bible (the light import pass, not the census).

    Merges `index` into the bible's existing `index`, keyed by four buckets
    (npcs/locations/items/monsters). Each entry is reduced to `{name, note}`;
    nameless entries are DROPPED and names are deduped case-insensitively (first
    note wins, a later note fills a blank one). Writes back to world-bible.json
    without touching any other field or the confirm flag.
    """
    bible = load_bible(campaign_dir)
    existing = bible.get("index") or {}
    out: Dict[str, Any] = {}
    for bucket in INDEX_BUCKETS:
        seen: Dict[str, Dict[str, str]] = {}
        for entry in list(existing.get(bucket, []) or []) + list((index or {}).get(bucket, []) or []):
            if not isinstance(entry, dict):
                continue
            name = (entry.get("name") or "").strip()
            if not name:
                continue  # drop nameless typed extras
            note = (entry.get("note") or "").strip()
            key = name.lower()
            if key not in seen:
                seen[key] = {"name": name, "note": note}
            elif note and not seen[key]["note"]:
                seen[key]["note"] = note
        out[bucket] = list(seen.values())
    bible["index"] = out
    _bible_path(campaign_dir).write_text(
        json.dumps(bible, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def write_systems(campaign_dir, systems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Persist executable signature systems onto the kit (ruleset.json `systems`).

    Each kept entry is `{primitive, name, config}` — an instantiation of a
    game_core primitive (named_track / price_roll / reaction_roll /
    guarded_payoff). Malformed entries (no primitive or no name) are dropped.
    Requires an existing ruleset.json (run `draft-ruleset` first).
    """
    path = Path(campaign_dir) / "ruleset.json"
    if not path.exists():
        raise FileNotFoundError(
            f"no ruleset.json in {campaign_dir} — run `gm-extract.sh draft-ruleset` first")
    ruleset = json.loads(path.read_text(encoding="utf-8"))
    clean = []
    for s in (systems or []):
        if isinstance(s, dict) and s.get("primitive") and s.get("name"):
            clean.append({"primitive": s["primitive"], "name": s["name"],
                          "config": s.get("config") or {}})
    ruleset["systems"] = clean
    path.write_text(json.dumps(ruleset, indent=2, ensure_ascii=False), encoding="utf-8")
    return clean


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Book Bible import chain")
    sub = parser.add_subparsers(dest="action", required=True)

    p_bible = sub.add_parser("draft-bible", help="draft/refresh an unconfirmed world-bible.json")
    p_bible.add_argument("campaign_dir")
    p_bible.add_argument("--name", help="the world's name (defaults to the campaign folder)")
    p_bible.add_argument("--voice-json", help='{"style":...,"sample_passages":[...],"vocab":[...]}')
    p_bible.add_argument("--fields-json", help="JSON object of creative fields (tone/themes/factions/...)")

    p_kit = sub.add_parser("draft-ruleset", help="draft ruleset.json from the bible")
    p_kit.add_argument("campaign_dir")
    p_kit.add_argument("--kit", default="custom", help="'dnd5e' only when the book IS a D&D module")
    p_kit.add_argument("--progression-model", default="milestone",
                       choices=["milestone", "xp-levels", "resource-axis"])
    p_kit.add_argument("--attributes", help="comma-separated stat schema attributes")
    p_kit.add_argument("--progression-json", help="extra progression config (e.g. resource/tiers)")
    p_kit.add_argument("--force", action="store_true", help="overwrite an existing ruleset.json")

    p_rules = sub.add_parser("campaign-rules", help="write campaign_rules into campaign-overview.json")
    p_rules.add_argument("campaign_dir")

    p_index = sub.add_parser("write-index",
                             help="persist a WORLD INDEX into the bible (the light import pass)")
    p_index.add_argument("campaign_dir")
    p_index.add_argument("--index-json", required=True,
                         help='{"npcs":[{"name":..,"note":..}],"locations":[...],"items":[...],"monsters":[...]}')

    p_sys = sub.add_parser("write-systems",
                           help="persist executable signature systems onto the kit (ruleset.json)")
    p_sys.add_argument("campaign_dir")
    p_sys.add_argument("--systems-json", required=True,
                       help='[{"primitive":"named_track","name":"Menace","config":{"max":6,"thresholds":[...]}}]')

    args = parser.parse_args()

    try:
        if args.action == "draft-bible":
            bible = draft_bible(
                args.campaign_dir,
                name=args.name,
                voice=json.loads(args.voice_json) if args.voice_json else None,
                fields=json.loads(args.fields_json) if args.fields_json else None,
            )
            idx = bible.get("index", {})
            idx_counts = ", ".join(f"{len(idx.get(b, []))} {b}"
                                   for b in ("npcs", "locations", "items", "monsters"))
            print(f"world-bible.json drafted: {bible['name']} "
                  f"(index: {idx_counts}; "
                  f"{len(bible['voice']['sample_passages'])} verbatim passages, confirmed=False)")
        elif args.action == "draft-ruleset":
            ruleset = write_ruleset(
                args.campaign_dir,
                progression_model=args.progression_model,
                kit=args.kit,
                attributes=[a.strip() for a in args.attributes.split(",") if a.strip()]
                if args.attributes else None,
                force=args.force,
                **(json.loads(args.progression_json) if args.progression_json else {}),
            )
            print(f"ruleset.json drafted: {ruleset['name']} | kit: {ruleset['kit']} "
                  f"| attrs: {ruleset['stat_schema']['attributes']} "
                  f"| agents: {ruleset['active_agents']}")
        elif args.action == "write-index":
            idx = write_index(args.campaign_dir, json.loads(args.index_json))
            counts = ", ".join(f"{len(idx.get(b, []))} {b}" for b in INDEX_BUCKETS)
            print(f"world index written: {counts}")
        elif args.action == "write-systems":
            sysv = write_systems(args.campaign_dir, json.loads(args.systems_json))
            print(f"kit systems written: {', '.join(s['name'] for s in sysv) or '(none)'}")
        else:
            rules = write_campaign_rules(args.campaign_dir)
            print(f"campaign_rules written: {len(rules['signature_systems'])} signature systems")
    except (ConfirmedBibleError, FileNotFoundError, FileExistsError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
