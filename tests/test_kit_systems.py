"""QA eval for kit-systems-authoring.

The kit can instantiate executable signature-system primitives (a `systems`
block on ruleset.json), and get_full_context surfaces them as a ROLL-these block
distinct from the prose YOUR WORLD'S RULES. Adversarial: malformed entries
dropped, block absent when no systems, named_track config rendered.
"""

import json
from pathlib import Path

from lib.session_manager import SessionManager
from lib.world_kit import WorldKit


def _ruleset_path(world_dir: str) -> Path:
    base = Path(world_dir)
    active = (base / "active-campaign.txt").read_text().strip()
    return base / "campaigns" / active / "ruleset.json"


def _set_systems(world_dir: str, systems) -> None:
    p = _ruleset_path(world_dir)
    rs = json.loads(p.read_text()) if p.exists() else {}
    rs["systems"] = systems
    p.write_text(json.dumps(rs))


def test_worldkit_systems_getter_drops_malformed(dcc_world):
    _set_systems(dcc_world, [
        {"primitive": "named_track", "name": "Menace", "config": {"max": 6}},
        {"primitive": "price_roll", "name": "Sorcery's Price", "config": {}},
        {"name": "no primitive"},          # dropped
        {"primitive": "guarded_payoff"},    # dropped (no name)
        "junk",                              # dropped
    ])
    got = WorldKit(dcc_world).systems()
    assert [s["name"] for s in got] == ["Menace", "Sorcery's Price"]


def test_systems_block_surfaces_in_context(dcc_world):
    _set_systems(dcc_world, [
        {"primitive": "named_track", "name": "Menace",
         "config": {"max": 6, "thresholds": [{"at": 3, "consequence": "they fear you"},
                                             {"at": 6, "consequence": "the city hunts you"}]}},
    ])
    ctx = SessionManager(dcc_world).get_full_context()
    assert "SIGNATURE SYSTEMS (executable" in ctx, "the roll-these block must appear"
    assert "Menace (named_track)" in ctx
    assert "they fear you" in ctx and "the city hunts you" in ctx
    assert "named_track / price_roll / reaction_roll / guarded_payoff" in ctx


def test_no_systems_no_block(dcc_world):
    _set_systems(dcc_world, [])
    assert "SIGNATURE SYSTEMS (executable" not in SessionManager(dcc_world).get_full_context()


def test_write_systems_roundtrips_and_drops_malformed(dcc_world):
    from lib import book_bible
    active = (Path(dcc_world) / "active-campaign.txt").read_text().strip()
    cdir = str(Path(dcc_world) / "campaigns" / active)
    book_bible.write_systems(cdir, [
        {"primitive": "named_track", "name": "Dread", "config": {"max": 4}},
        {"name": "bad — no primitive"},   # dropped
        {"primitive": "price_roll"},        # dropped — no name
    ])
    got = WorldKit(dcc_world).systems()
    assert [s["name"] for s in got] == ["Dread"], "round-trips one, drops the malformed two"
    assert got[0]["config"] == {"max": 4}
