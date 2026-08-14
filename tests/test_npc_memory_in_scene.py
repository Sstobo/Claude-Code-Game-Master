"""Tests for npc-memory-in-scene.

Per-NPC history is written by `gm-npc.sh update` and was rendered only for party
members, while NPCs with no extracted dialogue were dropped from the scene brief
entirely. Both meant the shopkeeper you betrayed kept a perfect log that never
reached a scene. These assert presence no longer requires a voice, and that a
present NPC carries what they remember.
"""

import json
from pathlib import Path

from lib.npc_manager import NPCManager
from lib.session_manager import SessionManager

CAMPAIGN = "dungeon-crawler-carl"


def _npcs_path(world):
    return Path(world) / "campaigns" / CAMPAIGN / "npcs.json"


def _current_location(world):
    overview = json.loads(
        (Path(world) / "campaigns" / CAMPAIGN / "campaign-overview.json").read_text()
    )
    return overview.get("player_position", {}).get("current_location")


def _add_npc(world, name, *, events=None, context=None, mood=None):
    """Write an NPC tagged to the current location straight into npcs.json."""
    path = _npcs_path(world)
    npcs = json.loads(path.read_text(encoding="utf-8"))
    npcs[name] = {
        "description": "a local",
        "context": context or [],
        "events": [{"event": e, "timestamp": "2026-01-01T00:00:00Z"} for e in (events or [])],
        "tags": {"locations": [_current_location(world)], "quests": []},
    }
    if mood:
        npcs[name]["current_mood"] = mood
    path.write_text(json.dumps(npcs, indent=2), encoding="utf-8")


def test_voiceless_npc_is_still_present(dcc_world):
    """An NPC with no canonical dialogue must not vanish from the brief."""
    _add_npc(dcc_world, "Silent Bram", mood="wary")
    ctx = SessionManager(dcc_world).get_full_context()
    assert "Silent Bram" in ctx
    assert "wary" in ctx


def test_present_npc_carries_what_they_remember(dcc_world):
    _add_npc(dcc_world, "Grimnar", events=["insulted by the player", "refused them a room"])
    ctx = SessionManager(dcc_world).get_full_context()
    assert "Grimnar" in ctx
    assert "refused them a room" in ctx


def test_absent_npc_memory_stays_out_of_the_scene(dcc_world):
    """Memory is pushed for who is HERE — not the whole cast."""
    path = _npcs_path(dcc_world)
    npcs = json.loads(path.read_text(encoding="utf-8"))
    npcs["Faraway Sal"] = {
        "description": "somewhere else entirely",
        "events": [{"event": "owes the player a debt", "timestamp": "2026-01-01T00:00:00Z"}],
        "tags": {"locations": ["A Place The Party Is Not"], "quests": []},
    }
    path.write_text(json.dumps(npcs, indent=2), encoding="utf-8")

    ctx = SessionManager(dcc_world).get_full_context()
    assert "owes the player a debt" not in ctx


def test_party_history_is_not_duplicated(dcc_world):
    """Party members render their history once, in the party block."""
    mgr = NPCManager(dcc_world)
    party = [n for n, d in (mgr.json_ops.load_json("npcs.json") or {}).items()
             if isinstance(d, dict) and d.get("is_party_member")]
    assert party, "fixture must have a party member for this to mean anything"
    mgr.update_npc(party[0], "took a bolt meant for the player")

    ctx = SessionManager(dcc_world).get_full_context()
    assert ctx.count("took a bolt meant for the player") == 1


def test_context_read_does_not_mutate_npcs(dcc_world):
    _add_npc(dcc_world, "Grimnar", events=["insulted by the player"], context=["Get out."])
    before = _npcs_path(dcc_world).read_text(encoding="utf-8")
    SessionManager(dcc_world).get_full_context()
    assert _npcs_path(dcc_world).read_text(encoding="utf-8") == before
