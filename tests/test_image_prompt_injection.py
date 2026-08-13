"""Appearance injection must fire even when the prompt names the character.

Regression: the old guard skipped injection when the character's NAME appeared
in the prompt — the natural way to write a beat brief — so recurring characters
drifted off-model.
"""

import json
from pathlib import Path

from lib.image_gen import inject_appearances


def _campaign_with_appearance(dcc_world):
    campaign = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl"
    char_path = campaign / "character.json"
    char = json.loads(char_path.read_text())
    char["visual_appearance"] = {
        "sex": "male", "age": "late 20s", "race": "Human", "species": "human",
        "hair": "short brown", "face": "stubbled", "eyes": "brown",
        "clothing": "boxer shorts", "gear": "barefoot, spiked gauntlet",
        "demeanor": "scrappy", "size": "average build",
    }
    char_path.write_text(json.dumps(char))
    return campaign, char["name"]


def test_injects_even_when_prompt_names_the_character(dcc_world):
    campaign, name = _campaign_with_appearance(dcc_world)
    prompt = f"{name} swings a club at the Terror Clown"
    out = inject_appearances(prompt, [name], campaign)
    assert "Character (render exactly):" in out
    assert "boxer shorts" in out


def test_injection_is_idempotent(dcc_world):
    campaign, name = _campaign_with_appearance(dcc_world)
    once = inject_appearances("a battle scene", [name], campaign)
    twice = inject_appearances(once, [name], campaign)
    assert once == twice


def test_unknown_character_injects_nothing(dcc_world):
    campaign, _ = _campaign_with_appearance(dcc_world)
    prompt = "a quiet vista"
    assert inject_appearances(prompt, ["Nobody Real"], campaign) == prompt
