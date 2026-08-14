"""Tests for party-promote-real-stats: promote copies npc.stats HP/AC, not 10/10."""

import json

from lib.npc_manager import NPCManager, PARTY_MEMBER_DEFAULTS


def _world(tmp_path, npcs):
    world = tmp_path / "world-state"
    (world / "campaigns" / "camp").mkdir(parents=True)
    (world / "active-campaign.txt").write_text("camp")
    (world / "campaigns" / "camp" / "npcs.json").write_text(json.dumps(npcs))
    return world


def _sheet(world, name):
    npcs = json.loads((world / "campaigns" / "camp" / "npcs.json").read_text())
    return npcs[name]["character_sheet"]


def test_promote_derives_hp_ac_from_existing_stats(tmp_path, capsys):
    world = _world(tmp_path, {
        "Belit": {
            "name": "Belit",
            "description": "Pirate queen",
            "stats": {
                "hp": 120, "ac": 15, "cr": 8,
                "difficulty": "boss", "statless": False,
            },
        }
    })
    assert NPCManager(world_state_dir=str(world)).promote_to_party_member("Belit")
    sheet = _sheet(world, "Belit")
    assert sheet["hp"] == {"current": 120, "max": 120}
    assert sheet["ac"] == 15
    assert sheet["class"] == PARTY_MEMBER_DEFAULTS["class"]
    assert sheet["level"] == PARTY_MEMBER_DEFAULTS["level"]
    assert sheet["stats"] == PARTY_MEMBER_DEFAULTS["stats"]
    out = capsys.readouterr().out
    assert "HP: 120/120" in out
    assert "AC: 15" in out
    assert "from npc.stats (stat-npcs proxy, difficulty boss)" in out


def test_promote_statless_uses_defaults_and_discloses(tmp_path, capsys):
    world = _world(tmp_path, {
        "Innkeep": {"name": "Innkeep", "stats": {"statless": True}},
    })
    assert NPCManager(world_state_dir=str(world)).promote_to_party_member("Innkeep")
    sheet = _sheet(world, "Innkeep")
    assert sheet["hp"] == {"current": 10, "max": 10}
    assert sheet["ac"] == 10
    out = capsys.readouterr().out
    assert "HP: 10/10" in out
    assert "defaults (NPC has no stats)" in out
