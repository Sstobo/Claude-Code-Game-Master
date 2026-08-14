"""Tests for kit-driven progression on the PC sheet: a milestone world never grows
a phantom `xp` object, and the level ceiling comes from the kit's threshold table
rather than a hardcoded 20.

Every fixture world is built in tmp_path with its own active-campaign.txt, so the
repo's live world-state is never read or written.
"""

import json

import pytest

from lib.player_manager import PlayerManager

MILESTONE_RULESET = {
    "name": "The Long Road",
    "kit": "custom",
    "stat_schema": {"attributes": ["grit", "wits"], "vitals": ["hp", "resolve"]},
    "progression": {"model": "milestone"},
    "resolution": {"model": "2d6-plus-mod"},
    "active_agents": [],
}

# 11 thresholds -> levels 2..12, so this world tops out at 12, not 20.
TWELVE_LEVEL_RULESET = {
    "name": "Twelve Rungs",
    "kit": "custom",
    "stat_schema": {"attributes": ["grit"], "vitals": ["hp"]},
    "progression": {"model": "xp-levels",
                    "thresholds": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100]},
    "resolution": {"model": "d20-vs-dc"},
    "active_agents": [],
}

PILGRIM = {
    "name": "Pilgrim",
    "level": 1,
    "hp": {"current": 20, "max": 20},
    "stats": {"grit": 12, "wits": 14},
    "resolve": {"current": 3, "max": 3},
    "gold": 0,
}


def _world(tmp_path, slug, ruleset, character=PILGRIM):
    world = tmp_path / "world-state"
    campaign = world / "campaigns" / slug
    campaign.mkdir(parents=True)
    (world / "active-campaign.txt").write_text(slug, encoding="utf-8")
    if ruleset is not None:
        (campaign / "ruleset.json").write_text(json.dumps(ruleset), encoding="utf-8")
    if character is not None:
        (campaign / "character.json").write_text(json.dumps(character), encoding="utf-8")
    return world


def _sheet(world, slug):
    return json.loads((world / "campaigns" / slug / "character.json").read_text(encoding="utf-8"))


@pytest.fixture
def milestone_world(tmp_path):
    return _world(tmp_path, "long-road", MILESTONE_RULESET)


# --- a milestone sheet never grows an xp object --------------------------------

@pytest.mark.parametrize("tier", ["minor", "major", "legendary"])
def test_spectacle_award_writes_no_xp_object(milestone_world, tier):
    mgr = PlayerManager(str(milestone_world))
    assert mgr.award_spectacle("Pilgrim", tier)["success"]
    assert "xp" not in _sheet(milestone_world, "long-road")


def test_legendary_beat_ticks_the_milestone_counter(milestone_world):
    mgr = PlayerManager(str(milestone_world))
    result = mgr.award_spectacle("Pilgrim", "legendary", reason="talked the god down")
    assert result["milestone_total"] == 1
    sheet = _sheet(milestone_world, "long-road")
    assert sheet["milestone"] == 1 and "xp" not in sheet


def test_reading_level_status_writes_nothing(milestone_world):
    mgr = PlayerManager(str(milestone_world))
    status = mgr.get_xp_status("Pilgrim")
    assert status["current_xp"] == 0
    assert "xp" not in _sheet(milestone_world, "long-road")


def test_vitals_and_hp_changes_leave_xp_alone(milestone_world):
    mgr = PlayerManager(str(milestone_world))
    assert mgr.modify_vital(None, "resolve", -1)["current"] == 2
    assert mgr.modify_hp("Pilgrim", -5)["success"]
    assert "xp" not in _sheet(milestone_world, "long-road")


# --- the level ceiling is the kit's, not 20 ------------------------------------

def test_twelve_level_kit_reports_max_at_twelve(tmp_path):
    world = _world(tmp_path, "twelve", TWELVE_LEVEL_RULESET)
    mgr = PlayerManager(str(world))

    result = mgr.award_xp("Pilgrim", 1100)
    assert result["new_level"] == 12
    assert result["next_level_xp"] == "MAX"


def test_twelve_level_kit_still_reports_a_threshold_below_the_top(tmp_path):
    world = _world(tmp_path, "twelve", TWELVE_LEVEL_RULESET)
    mgr = PlayerManager(str(world))

    result = mgr.award_xp("Pilgrim", 1000)
    assert result["new_level"] == 11 and result["next_level_xp"] == 1100

    status = mgr.get_xp_status("Pilgrim")
    assert status["ready_to_level"] is False and status["xp_remaining"] == 100


def test_top_level_of_a_twelve_level_kit_is_not_ready_to_level(tmp_path):
    world = _world(tmp_path, "twelve", TWELVE_LEVEL_RULESET)
    mgr = PlayerManager(str(world))
    mgr.award_xp("Pilgrim", 1100)
    assert mgr.get_xp_status("Pilgrim")["ready_to_level"] is False


def test_default_table_still_caps_at_twenty(tmp_path):
    """No kit thresholds -> the 5e-shaped default table, whose top is level 20."""
    char = dict(PILGRIM, level=19, xp={"current": 305000, "next_level": 355000})
    world = _world(tmp_path, "default-kit", None, character=char)
    result = PlayerManager(str(world)).award_xp("Pilgrim", 50000)
    assert result["new_level"] == 20 and result["next_level_xp"] == "MAX"


# --- ruleset syntax the kit accepts must not crash the XP path -----------------

def test_bare_string_progression_does_not_break_xp_reads(tmp_path):
    """`"progression": "milestone"` is valid kit syntax; the sheet code reads the
    thresholds through the kit, so the shorthand cannot raise here."""
    world = _world(tmp_path, "terse", {
        "stat_schema": {"vitals": ["hp"]}, "progression": "milestone"})
    mgr = PlayerManager(str(world))

    assert mgr.get_xp_status("Pilgrim")["current_xp"] == 0
    assert mgr.award_spectacle("Pilgrim", "legendary")["milestone_total"] == 1
    assert "xp" not in _sheet(world, "terse")


def test_bare_string_xp_progression_still_levels(tmp_path):
    world = _world(tmp_path, "terse-xp", {"progression": "xp-levels"})
    result = PlayerManager(str(world)).award_xp("Pilgrim", 300)
    assert result["new_level"] == 2 and result["next_level_xp"] == 900


def test_level_alias_kit_gets_scaled_spectacle_xp(tmp_path):
    """"model": "level" is the documented alias for xp-levels — a spectacle beat on
    such a kit must award scaled XP, not fall through to a milestone tick."""
    world = _world(tmp_path, "alias", {
        "progression": {"model": "level", "thresholds": [100, 200]}})
    result = PlayerManager(str(world)).award_spectacle("Pilgrim", "major")

    assert result["xp_gained"] == 150 and result["new_level"] == 2
    sheet = _sheet(world, "alias")
    assert sheet["xp"]["current"] == 150 and "milestone" not in sheet


# --- a campaign with no ruleset at all -----------------------------------------

def test_ruleset_less_campaign_can_still_change_hp(tmp_path):
    """WorldKit's DEFAULT_RULESET declares ['hp'], so the vital is not refused."""
    world = _world(tmp_path, "bare", None)
    mgr = PlayerManager(str(world))

    assert mgr._kit_vitals() == ["hp"]
    result = mgr.modify_vital(None, "hp", -6)
    assert result["success"] and result["current"] == 14
    assert _sheet(world, "bare")["hp"]["current"] == 14


def test_ruleset_less_campaign_refuses_an_undeclared_vital(tmp_path):
    world = _world(tmp_path, "bare", None)
    assert PlayerManager(str(world)).modify_vital(None, "resolve", -1)["success"] is False


def test_ruleset_without_a_stat_schema_still_has_hp(tmp_path):
    """A ruleset that exists but declares no vitals is the same failure class as no
    ruleset at all — every world has a body."""
    world = _world(tmp_path, "schemaless", {"name": "Half-Authored", "kit": "custom"})
    mgr = PlayerManager(str(world))

    assert mgr._kit_vitals() == ["hp"]
    assert mgr.modify_vital(None, "hp", -6)["current"] == 14


def test_empty_declared_vitals_list_still_has_hp(tmp_path):
    world = _world(tmp_path, "emptyvitals", {
        "stat_schema": {"attributes": ["grit"], "vitals": []}})
    assert PlayerManager(str(world)).modify_vital(None, "hp", -1)["success"] is True
