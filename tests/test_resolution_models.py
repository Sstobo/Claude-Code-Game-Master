"""Tests for executable resolution models: the kit's declared `resolution.model`
actually changes how a check is rolled, instead of being a label nothing reads.

RNG is pinned by monkeypatching random.randint with a scripted sequence, so every
assertion is about the model's arithmetic, not about luck.
"""

import json
import random

import pytest

from lib import game_core as gc
from lib.world_kit import WorldKit


@pytest.fixture
def faces(monkeypatch):
    """Feed dice.py an exact sequence of die faces; returns the remaining queue."""
    queue = []

    def scripted(low, high):
        assert queue, "ran out of scripted die faces"
        face = queue.pop(0)
        assert low <= face <= high, f"scripted face {face} outside d{high}"
        return face

    monkeypatch.setattr(random, "randint", scripted)
    return queue


def _kit_world(tmp_path, ruleset):
    world = tmp_path / "world-state"
    campaign = world / "campaigns" / "kitworld"
    campaign.mkdir(parents=True)
    (world / "active-campaign.txt").write_text("kitworld", encoding="utf-8")
    (campaign / "ruleset.json").write_text(json.dumps(ruleset), encoding="utf-8")
    return str(world)


# --- d20-vs-dc: today's behavior, unchanged -----------------------------------

def test_d20_default_is_unchanged(faces):
    faces.append(14)
    r = gc.resolve_check(modifier=3, dc=15)
    assert r == {'die': 14, 'modifier': 3, 'total': 17, 'dc': 15,
                 'success': True, 'margin': 2, 'critical': None}


def test_d20_named_explicitly_matches_the_default(faces):
    faces.extend([9, 9])
    implicit = gc.resolve_check(modifier=2, dc=12)
    explicit = gc.resolve_check(modifier=2, dc=12, model="d20-vs-dc")
    assert implicit == explicit


def test_d20_crit_and_fumble(faces):
    faces.extend([20, 1])
    assert gc.resolve_check(model="d20-vs-dc")['critical'] == 'hit'
    assert gc.resolve_check(model="d20-vs-dc")['critical'] == 'miss'


def test_d20_advantage_keeps_the_higher_face(faces):
    faces.extend([4, 18])
    r = gc.resolve_check(modifier=1, dc=10, advantage="advantage", model="d20-vs-dc")
    assert r['die'] == 18 and r['total'] == 19


# --- 2d6-plus-mod --------------------------------------------------------------

def test_2d6_sums_both_dice_plus_the_modifier(faces):
    faces.extend([4, 5])
    r = gc.resolve_check(modifier=2, dc=10, model="2d6-plus-mod")
    assert r['die'] == 9 and r['total'] == 11 and r['success'] is True
    assert r['margin'] == 1 and r['critical'] is None


def test_2d6_crit_on_twelve_and_fumble_on_two(faces):
    faces.extend([6, 6, 1, 1])
    assert gc.resolve_check(model="2d6-plus-mod")['critical'] == 'hit'
    assert gc.resolve_check(model="2d6-plus-mod")['critical'] == 'miss'


def test_2d6_advantage_keeps_the_best_two_of_three(faces):
    faces.extend([2, 6, 5])
    r = gc.resolve_check(modifier=0, dc=10, advantage="advantage", model="2d6-plus-mod")
    assert r['die'] == 11        # 6 + 5, the 2 dropped


def test_2d6_never_rolls_a_d20(faces):
    faces.extend([3, 3])
    assert gc.resolve_check(model="2d6-plus-mod")['die'] == 6


# --- dice-pool -----------------------------------------------------------------

def test_pool_counts_fives_and_sixes_against_required_successes(faces):
    faces.extend([5, 2, 6, 1])
    r = gc.resolve_check(modifier=4, dc=2, model="dice-pool")
    assert r['die'] == 2 and r['total'] == 2 and r['modifier'] == 4
    assert r['success'] is True and r['margin'] == 0


def test_pool_falls_short_of_the_threshold(faces):
    faces.extend([1, 2, 3])
    r = gc.resolve_check(modifier=3, dc=2, model="dice-pool")
    assert r['die'] == 0 and r['success'] is False and r['critical'] == 'miss'


def test_pool_is_at_least_one_die(faces):
    faces.append(6)
    r = gc.resolve_check(modifier=0, dc=1, model="dice-pool")
    assert r['modifier'] == 1 and r['die'] == 1 and r['critical'] == 'hit'
    assert not faces, "a zero modifier must still roll exactly one die"


def test_pool_advantage_adds_a_die(faces):
    faces.extend([5, 5, 5])
    r = gc.resolve_check(modifier=2, dc=1, advantage="advantage", model="dice-pool")
    assert r['modifier'] == 3 and r['die'] == 3


def test_pool_target_face_comes_from_kit_params(faces):
    faces.extend([4, 4])
    lenient = gc.resolve_check(modifier=2, dc=1, model={"model": "dice-pool", "target": 4})
    assert lenient['die'] == 2
    faces.extend([4, 4])
    strict = gc.resolve_check(modifier=2, dc=1, model={"model": "dice-pool"})
    assert strict['die'] == 0


# --- unknown model -------------------------------------------------------------

def test_unknown_model_warns_by_name_and_falls_back_to_d20(faces, capsys):
    faces.append(11)
    r = gc.resolve_check(modifier=1, dc=10, model="fudge-ladder")
    warning = capsys.readouterr().err
    assert "fudge-ladder" in warning and "d20-vs-dc" in warning
    assert r['die'] == 11 and r['total'] == 12


def test_level_is_an_alias_for_xp_levels(capsys):
    p = gc.make_progression("level", thresholds=[100, 300])
    assert capsys.readouterr().err == ""       # a documented alias, not a typo
    assert p.name == "xp-levels"
    assert p.level(p.advance({}, xp=150)) == 2


def test_unknown_progression_model_warns_and_milestones(capsys):
    p = gc.make_progression("xp-level")          # the classic typo
    warning = capsys.readouterr().err
    assert "xp-level" in warning and "milestone" in warning
    assert p.name == "milestone"


def test_declared_progression_models_are_silent(capsys):
    for model in ("milestone", "xp-levels", "resource-axis", "level"):
        gc.make_progression(model)
    assert capsys.readouterr().err == ""


# --- contests run on the same model ---------------------------------------------

def test_opposed_check_defaults_to_d20(faces):
    faces.extend([15, 8])
    contest = gc.opposed_check(0, 0)
    assert contest == {'a': 15, 'b': 8, 'winner': 'a', 'margin': 7}


def test_opposed_check_on_2d6(faces):
    faces.extend([3, 4, 6, 6])
    contest = gc.opposed_check(0, 0, model="2d6-plus-mod")
    assert contest['a'] == 7 and contest['b'] == 12
    assert contest['winner'] == 'b' and contest['margin'] == 5


def test_opposed_check_on_a_pool_compares_success_counts(faces):
    faces.extend([5, 5, 1, 6, 1])
    contest = gc.opposed_check(3, 2, model="dice-pool")
    assert contest['a'] == 2 and contest['b'] == 1     # successes, not die totals
    assert contest['winner'] == 'a' and contest['margin'] == 1


def test_opposed_check_ties_go_to_neither(faces):
    faces.extend([1, 1, 1, 1])
    assert gc.opposed_check(2, 2, model="dice-pool")['winner'] == 'tie'


def test_kit_oppose_uses_the_declared_model(tmp_path, faces):
    kit = WorldKit(_kit_world(tmp_path, {"resolution": "2d6-plus-mod"}))
    faces.extend([6, 6, 1, 1])
    contest = kit.oppose(0, 0)
    assert contest['a'] == 12 and contest['b'] == 2 and contest['winner'] == 'a'


# --- the kit drives it ---------------------------------------------------------

def test_kit_normalizes_string_and_dict_resolution_syntax(tmp_path):
    terse = WorldKit(_kit_world(tmp_path / "a", {"resolution": "dice-pool"}))
    assert terse.resolution() == {"model": "dice-pool", "params": {}}

    full = WorldKit(_kit_world(tmp_path / "b", {
        "resolution": {"model": "dice-pool", "target": 4}}))
    assert full.resolution() == {"model": "dice-pool", "params": {"target": 4}}
    assert full.resolution_model() == "dice-pool"


def test_kit_resolve_uses_the_declared_model(tmp_path, faces):
    kit = WorldKit(_kit_world(tmp_path, {"resolution": {"model": "2d6-plus-mod"}}))
    faces.extend([6, 5])
    r = kit.resolve(modifier=1, dc=10)
    assert r['die'] == 11 and r['total'] == 12


def test_ruleset_less_campaign_still_rolls_d20(tmp_path, faces):
    world = tmp_path / "world-state"
    (world / "campaigns" / "bare").mkdir(parents=True)
    (world / "active-campaign.txt").write_text("bare", encoding="utf-8")
    faces.append(7)
    assert WorldKit(str(world)).resolve(modifier=0, dc=5)['die'] == 7
