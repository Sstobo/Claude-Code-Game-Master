"""Tests for opening-beat-seed: place the PC; do not fabricate a session."""

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


def _fake_opening_block(ts="2026-01-01T00:00:00Z", hook="You wake on a train.", loc="The Iron Tangle", plot="Escape"):
    return (
        f"<!-- opening-seed -->\n"
        f"## Session Started: {ts}\n\n"
        f"### Session Ended: {ts}\n"
        f"Opening scene. {hook}\n\n"
        f"**Session:** 0\n"
        f"**Location:** {loc}\n"
        f"**Cliffhanger:** {hook}\n"
        f"**Open threads:** {plot}\n\n"
        f"---\n\n"
        f"<!-- /opening-seed -->\n"
    )


def _legacy_opening_block(ts="2026-01-01T00:00:00Z"):
    return (
        f"## Session Started: {ts}\n\n"
        f"### Session Ended: {ts}\n"
        f"Opening scene. You wake on a moving train.\n\n"
        f"**Session:** 0\n"
        f"**Location:** The Iron Tangle\n"
        f"**Cliffhanger:** You wake on a moving train.\n"
        f"**Open threads:** Escape\n\n"
        f"---\n"
    )


def _assert_no_fake_session(log: str):
    assert "<!-- opening-seed -->" not in log
    assert "Opening scene." not in log
    # A real later session may still have ### Session Ended; the seed must not plant one.
    if "### Session Ended:" in log:
        assert "Opening scene." not in log


def _assert_opening_hook(ov, *, location, plot, fragment):
    hook = ov.get("opening_hook") or {}
    assert hook.get("location") == location
    assert hook.get("plot") == plot
    assert fragment in (hook.get("hook") or "")


def _opening_facts(cdir):
    p = Path(cdir) / "facts.json"
    if not p.exists():
        return []
    facts = json.loads(p.read_text())
    bucket = facts.get("plot_local") or []
    out = []
    for item in bucket:
        txt = item.get("fact", "") if isinstance(item, dict) else str(item)
        if str(txt).startswith("Opening (not yet played):"):
            out.append(txt)
    return out


def test_sets_position_and_opening_hook_without_fake_session(tmp_path):
    _setup(tmp_path)
    r = seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    assert r["seeded"] and r["opening_location"] == "The Iron Tangle"

    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    assert ov["player_position"]["current_location"] == "The Iron Tangle"
    assert ov["player_position"]["arrival_time"] == "x"   # preserved
    _assert_opening_hook(ov, location="The Iron Tangle", plot="Escape", fragment="moving train")

    plots = json.loads((tmp_path / "plots.json").read_text())
    assert plots["Escape"].get("status") != "active"
    assert not any(
        isinstance(e, dict) and "Opening beat:" in str(e.get("event", ""))
        for e in (plots["Escape"].get("events") or [])
    )

    log = (tmp_path / "session-log.md").read_text()
    _assert_no_fake_session(log)
    assert "### Session Ended:" not in log
    facts = _opening_facts(tmp_path)
    assert len(facts) == 1
    assert "Opening (not yet played):" in facts[0]
    assert "moving train" in facts[0]


def test_seed_does_not_stamp_opening_beat(tmp_path):
    _setup(tmp_path)
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    plots = json.loads((tmp_path / "plots.json").read_text())
    events = plots["Escape"].get("events") or []
    beats = [e for e in events if isinstance(e, dict) and "Opening beat:" in str(e.get("event", ""))]
    assert beats == []
    assert plots["Escape"].get("status") != "active"
    assert len(_opening_facts(tmp_path)) == 1


def test_strips_marked_and_legacy_fake_session(tmp_path):
    _setup(tmp_path)
    real = (
        "## Session Started: 2026-02-01T00:00:00Z\n\n"
        "### Session Ended: 2026-02-01T00:00:00Z\n"
        "A real session the player played.\n\n"
        "**Session:** 1\n\n---\n"
    )
    (tmp_path / "session-log.md").write_text(_fake_opening_block() + real)
    seed_opening(str(tmp_path))
    log = (tmp_path / "session-log.md").read_text()
    _assert_no_fake_session(log)
    assert "A real session the player played." in log
    assert "<!-- opening-seed -->" not in log

    (tmp_path / "session-log.md").write_text(_legacy_opening_block() + real)
    seed_opening(str(tmp_path))
    log = (tmp_path / "session-log.md").read_text()
    _assert_no_fake_session(log)
    assert "A real session the player played." in log
    assert "Opening scene." not in log


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

    ov = json.loads((camp / "campaign-overview.json").read_text())
    assert ov["player_position"]["current_location"] == "The Iron Tangle"
    _assert_opening_hook(ov, location="The Iron Tangle", plot="Escape", fragment="moving train")
    # Fixture pre-set status active — the seed must not add an Opening beat on top.
    plots = json.loads((camp / "plots.json").read_text())
    events = plots["Escape"].get("events") or []
    assert not any(isinstance(e, dict) and "Opening beat:" in str(e.get("event", "")) for e in events)

    ctx = SessionManager(dcc_world).get_full_context()
    assert "The Iron Tangle" in ctx
    assert "moving train above station 80" in ctx
    assert "Opening (not yet played):" in ctx
    # Available (non-closed) plots already render; fixture status is active.
    assert "[main] Escape" in ctx
    assert "Opening scene." not in ctx
    assert "**Cliffhanger:**" not in ctx
    assert "WHERE WE PAUSED:" not in ctx
    log = (camp / "session-log.md").read_text()
    _assert_no_fake_session(log)


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


def test_reseed_updates_location_and_hook_atomically(tmp_path):
    _setup_two_arcs(tmp_path)
    (tmp_path / "session-log.md").write_text(_fake_opening_block(
        loc="The Scarlet Citadel", plot=KING_PLOT, hook="King Conan rides.",
    ))
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    assert ov["player_position"]["current_location"] == "The Scarlet Citadel"
    assert json.loads((tmp_path / "plots.json").read_text())[KING_PLOT]["status"] == "available"
    _assert_opening_hook(ov, location="The Scarlet Citadel", plot=KING_PLOT, fragment="Scarlet Citadel")

    r = reseed_opening(str(tmp_path), _belit(), timestamp="2026-01-02T00:00:00Z")
    assert r["seeded"] and r["first_plot"] == PIRATE_PLOT
    assert r["opening_location"] == "The Tigress"

    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    plots = json.loads((tmp_path / "plots.json").read_text())
    log = (tmp_path / "session-log.md").read_text()

    assert ov["player_position"]["current_location"] == "The Tigress"
    assert ov["player_position"]["arrival_time"] == "x"  # preserved
    assert ov.get("opening_matched_to_pc") is True
    _assert_opening_hook(ov, location="The Tigress", plot=PIRATE_PLOT, fragment="Black Coast")
    assert plots[PIRATE_PLOT]["status"] == "available"
    assert plots[KING_PLOT]["status"] == "available"
    _assert_no_fake_session(log)
    assert "### Session Ended:" not in log
    assert log.count("## Session Started:") == 0
    facts = _opening_facts(tmp_path)
    assert len(facts) == 1
    assert "Black Coast" in facts[0]
    assert "Scarlet Citadel" not in facts[0]


def test_reseed_does_not_activate_a_plot(tmp_path):
    _setup_two_arcs(tmp_path)
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    reseed_opening(str(tmp_path), _belit(), timestamp="2026-01-02T00:00:00Z")

    plots = json.loads((tmp_path / "plots.json").read_text())
    assert _active_plots(plots) == []
    assert plots[KING_PLOT]["status"] == "available"
    assert plots[PIRATE_PLOT]["status"] == "available"


def test_pirate_era_pc_selects_pirate_plot_not_king(tmp_path):
    _setup_two_arcs(tmp_path)
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    assert not ov.get("opening_matched_to_pc"), "provisional seed must not mark the opening PC-matched"
    r = reseed_opening(str(tmp_path), _belit(), timestamp="2026-01-02T00:00:00Z")
    assert r["first_plot"] == PIRATE_PLOT
    assert r["opening_location"] == "The Tigress"
    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    assert ov.get("opening_matched_to_pc") is True
    _assert_opening_hook(ov, location="The Tigress", plot=PIRATE_PLOT, fragment="Black Coast")


def test_conan_pirate_era_selects_queen_not_citadel(tmp_path):
    """PC named Conan listed on the king-era plot must not beat pirate-era overlap."""
    _setup_two_arcs(tmp_path)
    seed_opening(str(tmp_path), timestamp="2026-01-01T00:00:00Z")
    r = reseed_opening(str(tmp_path), _conan_pirate(), timestamp="2026-01-02T00:00:00Z")
    assert r["first_plot"] == PIRATE_PLOT
    assert r["opening_location"] == "The Tigress"
    plots = json.loads((tmp_path / "plots.json").read_text())
    assert plots[KING_PLOT]["status"] == "available"
    assert plots[PIRATE_PLOT]["status"] == "available"
    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    _assert_opening_hook(ov, location="The Tigress", plot=PIRATE_PLOT, fragment="Black Coast")


def test_import_then_set_character_opening_matches(isolated_world_state):
    """Criterion: import → create/set character → opening hook matches the PC."""
    cm = CampaignManager()
    cdir = cm.create("Hyboria", "Hyboria")
    assert cdir is not None
    assert cm.set_active("Hyboria")
    _setup_two_arcs(cdir)

    seed_opening(str(cdir), timestamp="2026-01-01T00:00:00Z")
    plots = json.loads((cdir / "plots.json").read_text())
    assert plots[KING_PLOT]["status"] == "available", "provisional seed must not activate spine[0]"
    ov = json.loads((cdir / "campaign-overview.json").read_text())
    _assert_opening_hook(ov, location="The Scarlet Citadel", plot=KING_PLOT, fragment="Scarlet Citadel")

    (cdir / "character.json").write_text(json.dumps(_belit()), encoding="utf-8")
    assert PlayerManager().set_current_player("Belit")

    ov = json.loads((cdir / "campaign-overview.json").read_text())
    plots = json.loads((cdir / "plots.json").read_text())
    log = (cdir / "session-log.md").read_text()
    assert ov["current_character"] == "Belit"
    assert ov.get("opening_matched_to_pc") is True
    assert ov["player_position"]["current_location"] == "The Tigress"
    _assert_opening_hook(ov, location="The Tigress", plot=PIRATE_PLOT, fragment="Black Coast")
    assert plots[PIRATE_PLOT]["status"] == "available"
    assert plots[KING_PLOT]["status"] == "available"
    assert _active_plots(plots) == []
    _assert_no_fake_session(log)


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
    _assert_opening_hook(ov, location="The Tigress", plot=PIRATE_PLOT, fragment="Black Coast")
    assert plots[PIRATE_PLOT]["status"] == "available"
    assert plots[KING_PLOT]["status"] == "available"


def test_onboard_reseeds_opening_to_match_pc(isolated_world_state):
    """The real product path: onboard writes current_character and re-seeds."""
    cm = CampaignManager()
    cdir = cm.create("Hyboria", "Hyboria")
    assert cm.set_active("Hyboria")
    _setup_two_arcs(cdir)
    seed_opening(str(cdir), timestamp="2026-01-01T00:00:00Z")
    assert json.loads((cdir / "plots.json").read_text())[KING_PLOT]["status"] == "available"

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
    _assert_opening_hook(ov, location="The Tigress", plot=PIRATE_PLOT, fragment="Black Coast")
    assert plots[PIRATE_PLOT]["status"] == "available"
    assert plots[KING_PLOT]["status"] == "available"
    assert _active_plots(plots) == []
    _assert_no_fake_session(log)


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
