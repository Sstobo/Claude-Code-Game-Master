#!/usr/bin/env python3
"""Play pack — kit/primer/one room. The book stays the book.

campaign-overview.json.play_pack is the GM primer. stage() writes that room
into the journal. from_book() writes exactly one name when play walks toward it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

PACK_KEYS = (
    "whose_story",
    "room",
    "present",
    "exits",
    "hook",
    "offstage",
    "primer",
)


def empty_pack() -> Dict[str, Any]:
    return {
        "whose_story": "",
        "room": "",
        "present": [],
        "exits": [],
        "hook": "",
        "offstage": [],
        "primer": "",
    }


def normalize_pack(raw: Any) -> Dict[str, Any]:
    pack = empty_pack()
    if not isinstance(raw, dict):
        return pack
    pack["whose_story"] = str(raw.get("whose_story") or "")
    pack["room"] = str(raw.get("room") or "")
    pack["hook"] = str(raw.get("hook") or "")
    pack["primer"] = str(raw.get("primer") or "")
    for key in ("present", "exits", "offstage"):
        val = raw.get(key) or []
        if isinstance(val, str):
            val = [v.strip() for v in val.split(",") if v.strip()]
        pack[key] = [str(v).strip() for v in val if str(v).strip()]
    return pack


def pack_is_set(pack: Dict[str, Any]) -> bool:
    return bool(
        pack.get("room")
        or pack.get("hook")
        or pack.get("primer")
        or pack.get("whose_story")
        or pack.get("present")
    )


def render_primer(pack: Dict[str, Any]) -> str:
    pack = normalize_pack(pack)
    if not pack_is_set(pack):
        return ""
    lines = ["--- PRIMER ---"]
    if pack["whose_story"]:
        lines.append(f"Whose story: {pack['whose_story']}")
    if pack["room"]:
        lines.append(f"Room: {pack['room']}")
    if pack["present"]:
        lines.append(f"Here: {', '.join(pack['present'])}")
    if pack["exits"]:
        lines.append(f"Exits: {', '.join(pack['exits'])}")
    if pack["hook"]:
        lines.append(f"Hook: {pack['hook']}")
    if pack["offstage"]:
        lines.append(f"Offstage (do not build): {', '.join(pack['offstage'])}")
    if pack["primer"]:
        lines.append(pack["primer"])
    lines.append(
        "The book is the binder. New face or place: "
        "`bash tools/gm-playpack.sh from-book \"<name>\"` then RAG."
    )
    return "\n".join(lines)


def _overview_path(campaign_dir) -> Path:
    return Path(campaign_dir) / "campaign-overview.json"


def load_pack(campaign_dir) -> Dict[str, Any]:
    path = _overview_path(campaign_dir)
    if not path.exists():
        return empty_pack()
    data = json.loads(path.read_text(encoding="utf-8"))
    return normalize_pack(data.get("play_pack"))


def save_pack(campaign_dir, fields: Dict[str, Any]) -> Dict[str, Any]:
    path = _overview_path(campaign_dir)
    overview = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    pack = normalize_pack({**normalize_pack(overview.get("play_pack")), **fields})
    overview["play_pack"] = pack
    if pack["room"]:
        pos = overview.get("player_position") if isinstance(overview.get("player_position"), dict) else {}
        pos["current_location"] = pack["room"]
        overview["player_position"] = pos
        hook = overview.get("opening_hook") if isinstance(overview.get("opening_hook"), dict) else {}
        hook["location"] = pack["room"]
        hook["hook"] = pack["hook"] or hook.get("hook", "")
        overview["opening_hook"] = hook
        # The pack IS the matched opening — close the reseed latch so a later
        # handoff (death `become`, PC swap) never teleports the PC to a
        # mid-campaign plot's location. opening_seed.reseed_opening only fires
        # while this is falsy.
        overview["opening_matched_to_pc"] = True
    path.write_text(json.dumps(overview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return pack


def _load_json(cdir: Path, name: str) -> dict:
    path = cdir / name
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _save_json(cdir: Path, name: str, data: dict) -> None:
    (cdir / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _ensure_location(locations: dict, name: str, position: str, description: str = "") -> bool:
    if name in locations:
        if description and not (locations[name] or {}).get("description"):
            locations[name]["description"] = description
        return False
    locations[name] = {
        "name": name,
        "position": position,
        "description": description,
        "connections": [],
    }
    return True


def _connect(locations: dict, a: str, b: str, via: str) -> None:
    for src, dst in ((a, b), (b, a)):
        loc = locations.setdefault(src, {"name": src, "connections": []})
        conns = loc.setdefault("connections", [])
        if not any(isinstance(c, dict) and c.get("to") == dst for c in conns):
            conns.append({"to": dst, "path": via})


def apply_stage(campaign_dir, world_state_dir: Optional[str] = None) -> Dict[str, Any]:
    """Persist the pack's room, exits, and present NPCs into the journal."""
    cdir = Path(campaign_dir)
    pack = load_pack(cdir)
    if not pack["room"]:
        return {"ok": False, "error": "play_pack.room is empty"}

    locations = _load_json(cdir, "locations.json")
    npcs = _load_json(cdir, "npcs.json")
    created = {"location": pack["room"], "npcs": [], "exits": []}

    _ensure_location(
        locations, pack["room"],
        pack.get("whose_story") or "opening stage",
        pack["primer"] or pack["hook"],
    )
    for exit_name in pack["exits"]:
        if _ensure_location(locations, exit_name, f"exit from {pack['room']}"):
            created["exits"].append(exit_name)
        _connect(locations, pack["room"], exit_name, "visible from here")

    for name in pack["present"]:
        if name not in npcs:
            npcs[name] = {
                "name": name,
                "description": f"Present in {pack['room']}.",
                "attitude": "neutral",
                "tags": {"locations": [pack["room"]], "quests": []},
            }
            created["npcs"].append(name)
        else:
            tags = npcs[name].setdefault("tags", {})
            locs = tags.setdefault("locations", [])
            if pack["room"] not in locs:
                locs.append(pack["room"])

    _save_json(cdir, "locations.json", locations)
    _save_json(cdir, "npcs.json", npcs)
    return {"ok": True, **created, "pack": pack}


def from_book(
    campaign_dir,
    name: str,
    kind: str = "auto",
    description: str = "",
    attitude: str = "neutral",
    world_state_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Write exactly one journal entity. Description from caller or a RAG blurb."""
    cdir = Path(campaign_dir)
    name = (name or "").strip()
    if not name:
        return {"ok": False, "error": "name required"}

    kind = (kind or "auto").lower()
    if kind == "auto":
        kind = "location" if _looks_like_place(name) else "npc"

    blurb = (description or "").strip() or _rag_blurb(name, cdir) or (
        f"Named in the book; read the binder when they walk on. ({name})"
    )

    if kind == "location":
        locations = _load_json(cdir, "locations.json")
        if name in locations:
            return {"ok": False, "error": f"location '{name}' already exists", "kind": "location"}
        _ensure_location(locations, name, "from the book", blurb)
        _save_json(cdir, "locations.json", locations)
        return {"ok": True, "kind": "location", "name": name}

    npcs = _load_json(cdir, "npcs.json")
    if name in npcs:
        return {"ok": False, "error": f"npc '{name}' already exists", "kind": "npc"}
    npcs[name] = {
        "name": name,
        "description": blurb,
        "attitude": attitude or "neutral",
        "tags": {"locations": [], "quests": []},
    }
    _save_json(cdir, "npcs.json", npcs)
    return {"ok": True, "kind": "npc", "name": name}


def _looks_like_place(name: str) -> bool:
    n = name.lower()
    return any(w in n for w in (
        "the ", "house", "tower", "city", "inn", "road", "sea", "coast",
        "forest", "temple", "keep", "gate", "alley", "room", "deck",
    ))


def _rag_blurb(name: str, campaign_dir) -> str:
    """One or two source passages for a name. Empty if the binder is not indexed."""
    try:
        from rag.vector_store import CampaignVectorStore
        from rag.embedder import LocalEmbedder
        if not CampaignVectorStore.is_available():
            return ""
        store = CampaignVectorStore(str(campaign_dir))
        results = store.query_by_text(name, LocalEmbedder(), n_results=2)
        docs = results.get("documents") or []
        return " ".join(str(d)[:400] for d in docs if d).strip()
    except Exception:
        return ""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Play pack — primer, stage, from-book")
    parser.add_argument("campaign_dir")
    sub = parser.add_subparsers(dest="action", required=True)

    p_set = sub.add_parser("set")
    p_set.add_argument("--json", dest="fields_json", required=True)

    sub.add_parser("show")

    p_stage = sub.add_parser("stage")
    p_stage.add_argument("--world-state", default=None)

    p_fb = sub.add_parser("from-book")
    p_fb.add_argument("name")
    p_fb.add_argument("--kind", default="auto", choices=["auto", "npc", "location"])
    p_fb.add_argument("--description", default="")
    p_fb.add_argument("--attitude", default="neutral")
    p_fb.add_argument("--world-state", default=None)

    args = parser.parse_args()
    cdir = args.campaign_dir

    if args.action == "set":
        pack = save_pack(cdir, json.loads(args.fields_json))
        print(json.dumps(pack, indent=2, ensure_ascii=False))
    elif args.action == "show":
        pack = load_pack(cdir)
        print(json.dumps(pack, indent=2, ensure_ascii=False))
        block = render_primer(pack)
        if block:
            print()
            print(block)
    elif args.action == "stage":
        print(json.dumps(apply_stage(cdir, args.world_state), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(
            from_book(cdir, args.name, args.kind, args.description, args.attitude, args.world_state),
            indent=2, ensure_ascii=False,
        ))


if __name__ == "__main__":
    main()
