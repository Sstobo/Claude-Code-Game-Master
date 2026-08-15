"""QA eval for kit-grit-dial (re-scoped).

The original premise — a hardcoded 5e death model in game_core to "branch" — was
wrong: game_core had only apply_harm/heal. This adds a kit-configurable lethality
CLASSIFIER (game_core.classify_harm) + WorldKit.lethality() so a grim world plays
lethal while the default stays 5e-faithful. Pure calculator; no death-save
ceremony (that's the caller's).
"""

import json
from pathlib import Path

from lib.game_core import classify_harm
from lib.world_kit import WorldKit


def test_death_saves_default_matches_5e():
    # drop to 0 but not massive overkill -> the dying gate, not death
    assert classify_harm(5, 20, 5)["outcome"] == "dying"
    # massive overkill (damage past 0 >= max HP) -> dead outright (5e massive damage)
    assert classify_harm(5, 20, 30)["outcome"] == "dead"          # overkill 25 >= 20
    # survivable hit
    assert classify_harm(20, 20, 5) == {"new_hp": 15, "outcome": "ok"}


def test_gritty_kills_at_zero_no_saves():
    assert classify_harm(5, 20, 5, {"model": "gritty"})["outcome"] == "dead"
    assert classify_harm(20, 20, 5, {"model": "gritty"})["outcome"] == "ok"


def test_lower_massive_threshold_is_more_lethal():
    # default: overkill 8 < 20 -> only dying
    assert classify_harm(5, 20, 13)["outcome"] == "dying"                     # overkill 8
    # kit lowers the massive-damage bar to 8 -> that same hit kills
    assert classify_harm(5, 20, 13, {"massive_damage_at": 8})["outcome"] == "dead"


def test_none_never_instant_kills():
    # huge damage, model 'none' -> still just the dying gate, no instant death
    assert classify_harm(5, 20, 100, {"model": "none"})["outcome"] == "dying"


def test_worldkit_lethality_default_and_override(dcc_world):
    assert WorldKit(dcc_world).lethality() == {"model": "death-saves"}, "absent -> 5e default"
    active = (Path(dcc_world) / "active-campaign.txt").read_text().strip()
    p = Path(dcc_world) / "campaigns" / active / "ruleset.json"
    rs = json.loads(p.read_text())
    rs["lethality"] = {"model": "gritty", "massive_damage_at": 10}
    p.write_text(json.dumps(rs))
    assert WorldKit(dcc_world).lethality() == {"model": "gritty", "massive_damage_at": 10}
