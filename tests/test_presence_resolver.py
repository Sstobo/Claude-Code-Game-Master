"""Tests for presence-resolver-unification.

One who-is-here helper (party OR exact location tag); one entity resolver.
Scene presence must not go through substring search_npcs_by_tag.
"""

import ast
import json
import os
import subprocess
from pathlib import Path

import pytest

from lib.consequence_manager import ConsequenceManager
from lib.entity_manager import npcs_present
from lib.scene_context import SceneContext
from lib.search import WorldSearcher
from lib.session_manager import SessionManager

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "lib"
LOC = "The Inn"
INNER = "The Inner Sanctum"


@pytest.fixture
def presence_world(isolated_world_state):
    """Tiny campaign: tagged NPC, untagged party member, substring trap."""
    camp = isolated_world_state / "campaigns" / "presence-camp"
    camp.mkdir(parents=True)
    (isolated_world_state / "active-campaign.txt").write_text("presence-camp\n")
    (camp / "npcs.json").write_text(json.dumps({
        "Mara": {
            "description": "Keeps the tap.",
            "tags": {"locations": [LOC]},
            "aliases": ["The Barkeep"],
            "context": ["What'll it be?"],
        },
        "Pip": {
            "description": "An untagged companion.",
            "is_party_member": True,
            "tags": {"locations": []},
        },
        "Voss": {
            "description": "Lives where a prefix would lie.",
            "tags": {"locations": [INNER]},
        },
    }))
    (camp / "locations.json").write_text(json.dumps({
        LOC: {"description": "A taproom.", "aliases": ["The Public House"]},
        INNER: {"description": "A sealed chapel."},
    }))
    (camp / "campaign-overview.json").write_text(json.dumps({
        "name": "Presence Camp",
        "player_position": {"current_location": LOC},
        "time_of_day": "dusk",
    }))
    (camp / "consequences.json").write_text(json.dumps({"active": [], "resolved": []}))
    return str(isolated_world_state)


def _doors(world):
    """Names present according to session, SceneContext.build, and tick_from_session."""
    sm = SessionManager(world)
    npcs = sm.json_ops.load_json("npcs.json") or {}
    session = {name for name, _ in sm._present_npcs(npcs, LOC)}
    scene = set(SceneContext(world).build(LOC)["world"]["npcs_present"])
    captured = {}
    cm = ConsequenceManager(world)
    cm.tick = lambda world_state, limit=2: captured.update(present=world_state["present_npcs"]) or []
    cm.tick_from_session()
    return session, scene, set(captured["present"])


def test_single_presence_and_resolution_implementations():
    callers = ("session_manager.py", "consequence_manager.py", "scene_context.py")
    for name in callers:
        text = (LIB / name).read_text(encoding="utf-8")
        assert "npcs_present(" in text, f"{name} must call npcs_present"
        assert "loc_l in locs" not in text, f"{name} still has a copied presence loop"
    scene = (LIB / "scene_context.py").read_text(encoding="utf-8")
    assert "search_npcs_by_tag" not in scene

    tree = ast.parse((LIB / "entity_manager.py").read_text(encoding="utf-8"))
    defs = [n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "npcs_present"]
    assert defs == ["npcs_present"]

    search = ast.parse((LIB / "search.py").read_text(encoding="utf-8"))
    cls = next(n for n in search.body if isinstance(n, ast.ClassDef) and n.name == "WorldSearcher")
    for method in ("get_npc", "get_location"):
        fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method)
        called = [n.func.id for n in ast.walk(fn)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        assert "resolve_entity_name" in called, f"{method} must call resolve_entity_name"


def test_doors_agree_tagged_party_alias_and_substring_trap(presence_world):
    session, scene, tick = _doors(presence_world)
    assert session == scene == tick
    assert {"Mara", "Pip"} <= session          # tagged NPC + untagged party
    assert "Voss" not in session               # "The Inn" is not "The Inner Sanctum"
    assert WorldSearcher(presence_world).get_npc("The Barkeep") is not None
    assert WorldSearcher(presence_world).get_location("The Public House") is not None


def test_tag_search_stays_substring_discovery(presence_world):
    hits = WorldSearcher(presence_world).search_npcs_by_tag("locations", LOC)
    assert "Mara" in hits
    assert "Voss" in hits                      # substring: Inn ⊂ Inner Sanctum
    assert "Pip" not in hits                   # party is presence, not tag-search
    npcs = json.loads(
        (Path(presence_world) / "campaigns" / "presence-camp" / "npcs.json").read_text()
    )
    assert "Voss" not in npcs_present(npcs, LOC)


def test_alias_status_wrapper_and_context_presence(presence_world):
    env = {**os.environ, "GM_WORLD_STATE_BASE": presence_world}
    status = subprocess.run(
        ["bash", str(ROOT / "tools" / "gm-npc.sh"), "status", "The Barkeep"],
        cwd=str(ROOT), capture_output=True, text=True, env=env, timeout=60,
    )
    assert status.returncode == 0, status.stdout + status.stderr
    assert "Keeps the tap" in status.stdout

    ctx = subprocess.run(
        ["bash", str(ROOT / "tools" / "gm-context.sh"), "--json"],
        cwd=str(ROOT), capture_output=True, text=True, env=env, timeout=60,
    )
    assert ctx.returncode == 0, ctx.stdout + ctx.stderr
    present = json.loads(ctx.stdout)["data"]["world"]["npcs_present"]
    assert "Mara" in present
    assert "Pip" in present
    assert "Voss" not in present
