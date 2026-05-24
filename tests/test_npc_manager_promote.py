"""Regression: promote_to_party_member must not stomp an existing sheet."""
import json
from pathlib import Path

import pytest

from lib import npc_manager


@pytest.fixture
def carl_with_sheet(tmp_path):
    """A campaign dir with Carl as a previously-demoted party member."""
    campaign_dir = tmp_path / "world-state" / "campaigns" / "test-campaign"
    campaign_dir.mkdir(parents=True)
    ws = tmp_path / "world-state"
    (ws / "active-campaign.txt").write_text("test-campaign")
    (campaign_dir / "campaign-overview.json").write_text(
        json.dumps({"campaign_name": "T", "current_character": "PC"})
    )
    npcs = {
        "Carl": {
            "description": "demoted veteran",
            "attitude": "friendly",
            "is_party_member": False,
            "character_sheet": {
                "hp": {"current": 3, "max": 25},
                "ac": 18,
                "level": 5,
                "race": "Dwarf",
                "class": "Cleric",
                "stats": {"str": 12, "dex": 10, "con": 14,
                          "int": 10, "wis": 16, "cha": 10},
                "saves": {"str": 0, "dex": 0, "con": 0,
                          "int": 0, "wis": 0, "cha": 0},
                "skills": {}, "attack_bonus": 4, "damage": "1d8",
                "equipment": ["mace", "shield"],
                "features": [], "conditions": [], "xp": 6500,
            },
        }
    }
    (campaign_dir / "npcs.json").write_text(json.dumps(npcs))
    return str(ws), campaign_dir


def test_promote_preserves_existing_sheet(carl_with_sheet):
    ws, campaign_dir = carl_with_sheet
    mgr = npc_manager.NPCManager(world_state_dir=ws)
    assert mgr.promote_to_party_member("Carl") is True
    npcs = json.loads((campaign_dir / "npcs.json").read_text())
    sheet = npcs["Carl"]["character_sheet"]
    assert sheet["hp"] == {"current": 3, "max": 25}
    assert sheet["level"] == 5
    assert sheet["equipment"] == ["mace", "shield"]
