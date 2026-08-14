"""Tests for kit-aware-character-creation: create-character branches on the
active kit; non-dnd5e saves warn on the 10/10 HP fallback and do not require
5e race/class.
"""

import json
import re
from pathlib import Path

from lib.schemas import validate_character
from lib.world_kit import WorldKit

from tests.test_kit_vitals import (
    CONAN,
    HYBORIAN_RULESET,
    _make_world,
    _save,
    _sheet,
)

ROOT = Path(__file__).resolve().parent.parent
COMMAND = ROOT / ".claude" / "commands" / "create-character.md"
AGENT = ROOT / ".claude" / "agents" / "create-character.md"
VA_KEYS = (
    "sex", "age", "race", "species", "hair", "face", "eyes",
    "clothing", "gear", "demeanor", "size",
)

# Live Conan bug: ruleset has NO kit field → WorldKit.kit() == 'custom'.
CONAN_LIVE_RULESET = {k: v for k, v in HYBORIAN_RULESET.items() if k != "kit"}


def _cmd():
    return COMMAND.read_text(encoding="utf-8")


def _agent():
    return AGENT.read_text(encoding="utf-8")


def _section(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _generic(text):
    return _section(text, "## Generic spine", "## dnd5e branch")


def _dnd(text):
    return text[text.index("## dnd5e branch"):]


def _save_json_blobs(text):
    blobs = []
    for m in re.finditer(r"save-json '(\{.*?\})'", text):
        blobs.append(json.loads(m.group(1)))
    return blobs


def test_command_and_agent_have_generic_spine_and_dnd5e_branch():
    for text in (_cmd(), _agent()):
        assert "## Generic spine" in text
        assert "## dnd5e branch" in text
        assert "stat_schema" in _generic(text)
        assert "attributes" in _generic(text)
        assert "vitals" in _generic(text)
        generic = _generic(text).lower()
        assert "exactly" in generic or "dnd5e" in text.lower()


def test_generic_spine_never_mentions_5e_races_classes_or_spell_slots():
    for text in (_cmd(), _agent()):
        generic = _generic(text).lower()
        assert "spell slot" not in generic
        assert "spell slots" not in generic
        assert "hit die" not in generic
        assert "get_races.py" not in generic
        assert "get_classes.py" not in generic
        assert "get_spells.py" not in generic
        assert "cantrip" not in generic
        assert "standard array" not in generic
        assert "point buy" not in generic


def test_dnd5e_branch_keeps_race_class_spells_and_hit_die_hp():
    for text in (_cmd(), _agent()):
        dnd = _dnd(text)
        assert "get_races.py" in dnd
        assert "get_classes.py" in dnd
        assert "get_spells.py" in dnd
        assert "Hit Die max + Constitution" in dnd
        assert "Step 2 - Race" in dnd
        assert "Step 3 - Class" in dnd or "Step 4 - Background" in dnd


def test_hit_die_hp_is_gated_to_dnd5e_not_the_only_rule():
    for text in (_cmd(), _agent()):
        assert "Hit Die max + Constitution" in _dnd(text)
        assert "Hit Die max + Constitution" not in _generic(text)
        assert "does not derive HP" in _generic(text) or "Author HP" in _generic(text)


def test_no_ascii_art_or_ascii_interface_mandate():
    for text in (_cmd(), _agent()):
        lower = text.lower()
        assert "ascii interface" not in lower
        assert "ascii art" not in lower
        assert "ascii-art" not in lower
        assert "phone-friendly" in lower


def test_step_numbers_do_not_skip_2():
    for text in (_cmd(), _agent()):
        assert "Step 2 -" in text
        # Old bug: Step 1 - Introduction jumped to Step 3 - Background.
        intro = text.find("Step 1 - Introduction")
        assert intro != -1
        window = text[intro:intro + 600]
        assert "Step 2 -" in window
        assert not re.search(
            r"Step 1 - Introduction\s*\n\s*\n\s*\*?Step 3 - Background", text
        )


def test_save_json_examples_include_hp_and_visual_appearance():
    for text in (_cmd(), _agent()):
        blobs = _save_json_blobs(text)
        assert blobs, "expected at least one save-json JSON example"
        for blob in blobs:
            assert "hp" in blob, blob.keys()
            va = blob.get("visual_appearance")
            assert isinstance(va, dict), blob.keys()
            for key in VA_KEYS:
                assert key in va, key


def test_claude_md_death_protocol_routes_new_character_kit_aware():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    start = text.index("SWAP")
    swap = text[start:text.index("## Action Router", start)]
    assert "create-character" in swap
    assert "kit-aware" in swap.lower()
    assert "5e wizard" in swap.lower()


def test_gm_player_banner_is_kit_neutral():
    text = (ROOT / "tools" / "gm-player.sh").read_text(encoding="utf-8")
    assert "D&D Player Character Manager" not in text
    assert "Player Character management for D&D campaign" not in text
    assert "Player Character Manager" in text


def test_custom_kit_sheet_without_race_class_saves_and_validates(tmp_path):
    world = _make_world(tmp_path, "conan-live", CONAN_LIVE_RULESET)
    assert WorldKit(str(world)).kit() == "custom"

    payload = {
        "name": "Nameless",
        "level": 1,
        "attributes": {"might": 14, "guile": 11, "grit": 13},
        "hp": {"current": 20, "max": 20},
    }
    r = _save(world, payload)
    assert r.returncode == 0, r.stdout + r.stderr
    sheet = _sheet(world)
    ok, errs = validate_character(sheet, WorldKit(str(world)))
    assert ok, errs


def test_save_warnings_on_10_10_fallback(tmp_path):
    world = _make_world(tmp_path, "conan-live", CONAN_LIVE_RULESET)
    payload = {k: v for k, v in CONAN.items() if k != "hp"}
    # No race/class either — custom kit must not require them.
    payload.pop("race", None)
    payload.pop("class", None)
    r = _save(world, payload)
    assert r.returncode == 0, r.stdout + r.stderr
    result = json.loads(r.stdout)
    assert _sheet(world)["hp"] == {"current": 10, "max": 10}
    warnings = result["warnings"]
    assert isinstance(warnings, list) and warnings
    assert any("10/10" in w for w in warnings)


def test_dnd5e_still_requires_race_and_class(tmp_path):
    from tests.test_kit_vitals import DND5E_RULESET

    world = _make_world(tmp_path, "forgotten-realms", DND5E_RULESET)
    r = _save(world, {
        "name": "Thorin", "level": 1,
        "stats": {"str": 16, "dex": 12, "con": 15, "int": 10, "wis": 13, "cha": 8},
    })
    assert r.returncode == 1
    err = json.loads(r.stdout)
    assert "error" in err
    assert "race" in err["error"] or "class" in err["error"]
