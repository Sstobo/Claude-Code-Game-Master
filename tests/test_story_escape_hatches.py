"""Tests for story-escape-hatches: the code informs the GM, it never vetoes the story.

Two doors out of a default that is otherwise right: `revive` reopens a death the
fiction walks back, and the two image locks can be skipped for the one beat where
the campaign's style or a character's stored look is deliberately wrong.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from lib.image_gen import build_prompt, save_chronicler
from lib.player_manager import PlayerManager

ROOT = Path(__file__).resolve().parent.parent


def _sheet(dcc_world):
    return json.loads(
        (Path(dcc_world) / "campaigns" / "dungeon-crawler-carl" / "character.json")
        .read_text(encoding="utf-8"))


def test_revive_reopens_a_death(dcc_world):
    mgr = PlayerManager(dcc_world)
    name = _sheet(dcc_world)["name"]

    mgr.kill_character(name, "crushed by the Iron Tangle")
    dead = _sheet(dcc_world)
    assert dead["status"] == "dead" and dead["cause"] == "crushed by the Iron Tangle"

    result = mgr.revive(name, hp=12, reason="the Sunken Priest paid her debt")
    assert result["success"] and result["current_hp"] == 12
    assert result["reason"] == "the Sunken Priest paid her debt"

    alive = _sheet(dcc_world)
    assert alive["status"] == "alive"
    assert alive["hp"]["current"] == 12
    assert "died_at" not in alive and "cause" not in alive
    assert alive["revived_reason"] == "the Sunken Priest paid her debt"

    # The corpse guard is gone: HP moves again, and a second death still lands.
    assert mgr.modify_hp(name, -3)["success"]
    assert _sheet(dcc_world)["hp"]["current"] == 9
    assert mgr.kill_character(name, "eaten")["success"]
    assert _sheet(dcc_world)["status"] == "dead"


def test_revive_defaults_to_one_hp_and_clamps_to_max(dcc_world):
    mgr = PlayerManager(dcc_world)
    name = _sheet(dcc_world)["name"]
    max_hp = _sheet(dcc_world)["hp"]["max"]

    mgr.kill_character(name, "fell")
    assert mgr.revive(name)["current_hp"] == 1

    mgr.kill_character(name, "fell again")
    assert mgr.revive(name, hp=max_hp + 500)["current_hp"] == max_hp

    # 0 (or below) must not produce a living character at 0 HP.
    mgr.kill_character(name, "fell once more")
    assert mgr.revive(name, hp=0)["current_hp"] == 1
    assert _sheet(dcc_world)["status"] == "alive"


def test_dying_again_clears_the_revival_stamps(dcc_world):
    """Death and revival are mutually exclusive; the last event wins."""
    mgr = PlayerManager(dcc_world)
    name = _sheet(dcc_world)["name"]

    mgr.kill_character(name, "crushed")
    mgr.revive(name, reason="the Sunken Priest paid her debt")
    mgr.kill_character(name, "crushed again")

    dead = _sheet(dcc_world)
    assert "revived_at" not in dead and "revived_reason" not in dead
    assert dead["cause"] == "crushed again"


def test_revive_refuses_a_name_that_is_not_the_sitting_pc(dcc_world):
    """Single-character mode ignores the name on load — a revive aimed at a hero
    archived to fallen/ must not silently hit whoever holds character.json."""
    mgr = PlayerManager(dcc_world)
    name = _sheet(dcc_world)["name"]
    mgr.kill_character(name, "crushed")

    result = mgr.revive("Some Fallen Hero", reason="a miracle")
    assert result["success"] is False
    assert name in result["error"] and "Some Fallen Hero" in result["error"]
    assert _sheet(dcc_world)["status"] == "dead"


def test_revive_on_a_living_character_is_refused(dcc_world):
    """Explicit refusal, not a silent no-op — a living PC's HP is never touched."""
    mgr = PlayerManager(dcc_world)
    name = _sheet(dcc_world)["name"]
    before = _sheet(dcc_world)["hp"]["current"]

    result = mgr.revive(name, reason="just in case")
    assert result["success"] is False
    assert result["error"] == "character is not dead"
    assert _sheet(dcc_world)["hp"]["current"] == before


def test_revive_json_envelope(dcc_world):
    PlayerManager(dcc_world).kill_character("Tandy", "crushed")
    r = subprocess.run(
        [sys.executable, str(ROOT / "lib" / "player_manager.py"), "revive", "Tandy",
         "--hp", "9", "--reason", "the loop reset", "--json"],
        capture_output=True, text=True, cwd=str(Path(dcc_world).parent), env={**os.environ},
    )
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["ok"] is True
    assert d["data"]["success"] is True and d["data"]["current_hp"] == 9


# --- image prompt locks -------------------------------------------------------

STYLE = "In the style of a Bayeux-tapestry embroidery but depicting a neon megacity"


def _campaign_with_style_and_appearance(dcc_world):
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
    save_chronicler(style=STYLE, campaign_dir=campaign)
    return campaign, char["name"]


def test_both_locks_fire_by_default(dcc_world):
    campaign, name = _campaign_with_style_and_appearance(dcc_world)
    out = build_prompt(f"{name} kicks in the door", [name], campaign)
    assert "boxer shorts" in out and STYLE in out


def test_no_appearance_lock_skips_only_the_appearance(dcc_world):
    campaign, name = _campaign_with_style_and_appearance(dcc_world)
    out = build_prompt(f"{name} transformed into a crow", [name], campaign,
                       appearance_lock=False)
    assert "boxer shorts" not in out
    assert STYLE in out


def test_no_style_lock_skips_only_the_style(dcc_world):
    campaign, name = _campaign_with_style_and_appearance(dcc_world)
    out = build_prompt(f"{name} dreams of the surface", [name], campaign,
                       style_lock=False)
    assert STYLE not in out
    assert "boxer shorts" in out


def test_both_locks_off_leaves_the_prompt_untouched(dcc_world):
    campaign, name = _campaign_with_style_and_appearance(dcc_world)
    prompt = f"{name} as a stained-glass saint"
    assert build_prompt(prompt, [name], campaign,
                        style_lock=False, appearance_lock=False) == prompt
