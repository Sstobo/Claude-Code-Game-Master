"""Tests for opening-beat-seed: start a fresh import at the book's opening."""

import json
from pathlib import Path

from lib.campaign_manager import CampaignManager
from lib.identity_onboarding import IdentityOnboarding
from lib.opening_seed import reseed_opening, seed_opening
from lib.player_manager import PlayerManager
from lib.session_manager import SessionManager


def _setup(cdir):
    (cdir / "campaign-overview.json").write_text(json.dumps({
        "campaign_name": "T", "story_spine": {"arc": ["Escape"]},
        "player_position": {"current_location": "", "arrival_time": "x"},
    }))
    (cdir / "plots.json").write_text(json.dumps({
        "Escape": {"type": "main", "description": "You wake on a moving train above station 80. The floor collapses in 10 days.",
                   "locations": ["The Iron Tangle"]},
    }))
    (cdir / "locations.json").write_text(json.dumps({"The Iron Tangle": {"connections": []}}))


def test_sets_position_marks_beat_and_writes_log(tmp_path):
    _setup(tmp_path)
    r = seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    assert r["seeded"] and r["opening_location"] == "The Iron Tangle"

    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    assert ov["player_position"]["current_location"] == "The Iron Tangle"
    assert ov["player_position"]["arrival_time"] == "x"   # preserved

    plots = json.loads((tmp_path / "plots.json").read_text())
    assert plots["Escape"]["status"] == "active"
    assert any("Opening beat:" in e["event"] for e in plots["Escape"]["events"])

    log = (tmp_path / "session-log.md").read_text()
    assert "### Session Ended:" in log and "**Cliffhanger:**" in log


def test_idempotent_beat(tmp_path):
    _setup(tmp_path)
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    plots = json.loads((tmp_path / "plots.json").read_text())
    beats = [e for e in plots["Escape"]["events"] if "Opening beat:" in e["event"]]
    assert len(beats) == 1, "opening beat must not duplicate on re-run"


def test_no_spine_returns_not_seeded(tmp_path):
    (tmp_path / "campaign-overview.json").write_text(json.dumps({"campaign_name": "T"}))
    (tmp_path / "plots.json").write_text(json.dumps({"S": {"type": "side"}}))
    (tmp_path / "locations.json").write_text(json.dumps({}))
    r = seed_opening(str(tmp_path))
    assert r["seeded"] is False


def test_fresh_context_opens_on_book_opening(dcc_world):
    camp = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl"
    (camp / "campaign-overview.json").write_text(json.dumps({
        "campaign_name": "The Iron Tangle", "story_spine": {"arc": ["Escape"]},
        "player_position": {"current_location": ""},
    }))
    (camp / "plots.json").write_text(json.dumps({
        "Escape": {"type": "main", "status": "active", "sequence": 1,
                   "description": "You wake on a moving train above station 80.",
                   "locations": ["The Iron Tangle"]},
    }))
    (camp / "locations.json").write_text(json.dumps({"The Iron Tangle": {"connections": []}}))
    (camp / "session-log.md").write_text("")  # fresh, no prior sessions

    seed_opening(str(camp), timestamp="2026-01-01T00:00:00Z")

    ctx = SessionManager(dcc_world).get_full_context()
    assert "PREVIOUSLY ON" in ctx
    assert "moving train above station 80" in ctx
    assert "[main] Escape" in ctx


# --- re-seed once the PC exists ---------------------------------------------

KING_PLOT = "The Scarlet Citadel"
PIRATE_PLOT = "Queen of the Black Coast"


def _setup_two_arcs(cdir):
    """King-era spine[0] vs pirate-era spine[1] — the Conan import bug."""
    (cdir / "campaign-overview.json").write_text(json.dumps({
        "campaign_name": "Hyboria",
        "story_spine": {"arc": [KING_PLOT, PIRATE_PLOT]},
        "player_position": {"current_location": "", "arrival_time": "x"},
        "current_character": None,
    }))
    (cdir / "plots.json").write_text(json.dumps({
        KING_PLOT: {
            "type": "main",
            "description": "King Conan of Aquilonia rides to the Scarlet Citadel and loses five thousand knights.",
            "npcs": ["Conan"],
            "locations": ["The Scarlet Citadel"],
            "status": "available",
        },
        PIRATE_PLOT: {
            "type": "main",
            "description": "Pirate-era Conan sails with Belit, queen of the Black Coast, aboard the Tigress.",
            "npcs": ["Belit"],
            "locations": ["The Tigress"],
            "status": "available",
        },
    }))
    (cdir / "locations.json").write_text(json.dumps({
        "The Scarlet Citadel": {"connections": []},
        "The Tigress": {"connections": []},
    }))


def _belit():
    return {
        "name": "Belit",
        "aliases": ["Queen of the Black Coast"],
        "description": "pirate queen of the Black Coast",
        "level": 1,
        "hp": {"current": 10, "max": 10},
    }


def _conan_pirate():
    """The motivating Conan-import sheet: named Conan, pirate-era concept."""
    return {
        "name": "Conan",
        "concept": "pirate-era",
        "description": "pirate-era adventurer on the Black Coast",
        "level": 1,
        "hp": {"current": 10, "max": 10},
    }


def _active_plots(plots):
    return [n for n, p in plots.items() if isinstance(p, dict) and p.get("status") == "active"]


def test_reseed_updates_position_plot_and_log_atomically(tmp_path):
    _setup_two_arcs(tmp_path)
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    assert ov["player_position"]["current_location"] == "The Scarlet Citadel"
    assert json.loads((tmp_path / "plots.json").read_text())[KING_PLOT]["status"] == "active"

    r = reseed_opening(str(tmp_path), _belit(), timestamp="2026-01-02T00:00:00Z")
    assert r["seeded"] and r["first_plot"] == PIRATE_PLOT
    assert r["opening_location"] == "The Tigress"

    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    plots = json.loads((tmp_path / "plots.json").read_text())
    log = (tmp_path / "session-log.md").read_text()

    assert ov["player_position"]["current_location"] == "The Tigress"
    assert ov["player_position"]["arrival_time"] == "x"  # preserved
    assert ov.get("opening_matched_to_pc") is True
    assert plots[PIRATE_PLOT]["status"] == "active"
    assert "Opening scene." in log and "Black Coast" in log
    assert log.count("## Session Started:") == 1, "re-seed must replace the hook, not append a second one"


def test_reseed_leaves_exactly_one_plot_active(tmp_path):
    _setup_two_arcs(tmp_path)
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    reseed_opening(str(tmp_path), _belit(), timestamp="2026-01-02T00:00:00Z")

    plots = json.loads((tmp_path / "plots.json").read_text())
    assert _active_plots(plots) == [PIRATE_PLOT]
    assert plots[KING_PLOT]["status"] == "available"


def test_pirate_era_pc_selects_pirate_plot_not_king(tmp_path):
    _setup_two_arcs(tmp_path)
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    assert not ov.get("opening_matched_to_pc"), "provisional seed must not mark the opening PC-matched"
    r = reseed_opening(str(tmp_path), _belit(), timestamp="2026-01-02T00:00:00Z")
    assert r["first_plot"] == PIRATE_PLOT
    assert r["opening_location"] == "The Tigress"


def test_conan_pirate_era_selects_queen_not_citadel(tmp_path):
    """PC named Conan listed on the king-era plot must not beat pirate-era overlap."""
    _setup_two_arcs(tmp_path)
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    r = reseed_opening(str(tmp_path), _conan_pirate(), timestamp="2026-01-02T00:00:00Z")
    assert r["first_plot"] == PIRATE_PLOT
    assert r["opening_location"] == "The Tigress"
    plots = json.loads((tmp_path / "plots.json").read_text())
    assert plots[KING_PLOT]["status"] == "available"
    assert plots[PIRATE_PLOT]["status"] == "active"


def test_import_then_set_character_opening_matches(isolated_world_state):
    """Criterion: import → create/set character → opening beat matches the PC."""
    cm = CampaignManager()
    cdir = cm.create("Hyboria", "Hyboria")
    assert cdir is not None
    assert cm.set_active("Hyboria")
    _setup_two_arcs(cdir)

    seed_opening(str(cdir), timestamp="2026-01-01T00:00:00Z")
    plots = json.loads((cdir / "plots.json").read_text())
    assert plots[KING_PLOT]["status"] == "active", "provisional seed still opens on spine[0]"

    (cdir / "character.json").write_text(json.dumps(_belit()), encoding="utf-8")
    assert PlayerManager().set_current_player("Belit")

    ov = json.loads((cdir / "campaign-overview.json").read_text())
    plots = json.loads((cdir / "plots.json").read_text())
    log = (cdir / "session-log.md").read_text()
    assert ov["current_character"] == "Belit"
    assert ov.get("opening_matched_to_pc") is True
    assert ov["player_position"]["current_location"] == "The Tigress"
    assert plots[PIRATE_PLOT]["status"] == "active"
    assert plots[KING_PLOT]["status"] == "available"
    assert _active_plots(plots) == [PIRATE_PLOT]
    assert "Black Coast" in log
    assert log.count("## Session Started:") == 1


def test_set_reseeds_when_opening_not_yet_matched(isolated_world_state):
    """save-json path: current_character may already be filled; flag unset → reseed."""
    cm = CampaignManager()
    cdir = cm.create("Hyboria", "Hyboria")
    assert cm.set_active("Hyboria")
    _setup_two_arcs(cdir)
    seed_opening(str(cdir), timestamp="2026-01-01T00:00:00Z")

    (cdir / "character.json").write_text(json.dumps(_conan_pirate()), encoding="utf-8")
    ov = json.loads((cdir / "campaign-overview.json").read_text())
    ov["current_character"] = "Conan"
    (cdir / "campaign-overview.json").write_text(json.dumps(ov), encoding="utf-8")
    assert not ov.get("opening_matched_to_pc")

    assert PlayerManager().set_current_player("Conan")

    ov = json.loads((cdir / "campaign-overview.json").read_text())
    plots = json.loads((cdir / "plots.json").read_text())
    assert ov.get("opening_matched_to_pc") is True
    assert ov["player_position"]["current_location"] == "The Tigress"
    assert plots[PIRATE_PLOT]["status"] == "active"
    assert plots[KING_PLOT]["status"] == "available"


def test_onboard_reseeds_opening_to_match_pc(isolated_world_state):
    """The real product path: onboard writes current_character and re-seeds."""
    cm = CampaignManager()
    cdir = cm.create("Hyboria", "Hyboria")
    assert cm.set_active("Hyboria")
    _setup_two_arcs(cdir)
    seed_opening(str(cdir), timestamp="2026-01-01T00:00:00Z")
    assert json.loads((cdir / "plots.json").read_text())[KING_PLOT]["status"] == "active"

    result = IdentityOnboarding().onboard(
        "original", name="Conan", concept="pirate-era sailor on the Black Coast",
    )
    assert result["success"]

    ov = json.loads((cdir / "campaign-overview.json").read_text())
    plots = json.loads((cdir / "plots.json").read_text())
    log = (cdir / "session-log.md").read_text()
    assert ov["current_character"] == "Conan"
    assert ov.get("opening_matched_to_pc") is True
    assert ov["player_position"]["current_location"] == "The Tigress"
    assert plots[PIRATE_PLOT]["status"] == "active"
    assert plots[KING_PLOT]["status"] == "available"
    assert _active_plots(plots) == [PIRATE_PLOT]
    assert "Black Coast" in log or "Tigress" in log


def test_subsequent_set_does_not_reseed(isolated_world_state):
    cm = CampaignManager()
    cdir = cm.create("Hyboria", "Hyboria")
    assert cm.set_active("Hyboria")
    _setup_two_arcs(cdir)
    seed_opening(str(cdir), timestamp="2026-01-01T00:00:00Z")
    (cdir / "character.json").write_text(json.dumps(_belit()), encoding="utf-8")
    assert PlayerManager().set_current_player("Belit")

    ov = json.loads((cdir / "campaign-overview.json").read_text())
    assert ov.get("opening_matched_to_pc") is True
    ov["player_position"]["current_location"] = "WRONG"
    (cdir / "campaign-overview.json").write_text(json.dumps(ov), encoding="utf-8")

    assert PlayerManager().set_current_player("Belit")
    ov = json.loads((cdir / "campaign-overview.json").read_text())
    assert ov["player_position"]["current_location"] == "WRONG"
