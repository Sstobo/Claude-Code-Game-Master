"""Tests for identity-first-onboarding: canon / original / nameless → open-schema char."""

import json

from lib.campaign_manager import CampaignManager
from lib.character_schema import is_open_schema
from lib.identity_onboarding import IdentityOnboarding
from lib.opening_seed import seed_opening
from lib.player_manager import PlayerManager


def test_canon_lifts_party_member_sheet(dcc_world):
    char = IdentityOnboarding(dcc_world).from_canon("Carl")
    assert char is not None and char["origin"] == "canon"
    assert char["identity"]["name"] == "Carl"
    assert is_open_schema(char)
    # Carl is a party member -> stats lifted from the sheet
    assert isinstance(char["attributes"], dict)


def test_canon_lifts_voice_for_non_party_npc(dcc_world):
    char = IdentityOnboarding(dcc_world).from_canon("Mordecai")
    assert char is not None
    assert char["voice"]  # Mordecai has canonical context lines
    assert is_open_schema(char)


def test_canon_unknown_npc_returns_none(dcc_world):
    assert IdentityOnboarding(dcc_world).from_canon("Nobody McGhost") is None


def test_original_infers_minimal(dcc_world):
    char = IdentityOnboarding(dcc_world).original("Vex", concept="a thief with a debt")
    assert char["identity"]["name"] == "Vex"
    assert char["identity"]["concept"] == "a thief with a debt"
    assert char["attributes"] == {} and is_open_schema(char)


def test_nameless_has_zero_required_mechanics(dcc_world):
    char = IdentityOnboarding(dcc_world).nameless()
    assert char["origin"] == "nameless"
    assert char["attributes"] == {} and is_open_schema(char)


def test_characters_have_independent_vitals(dcc_world):
    # Regression: shared nested hp dict aliasing across characters.
    onb = IdentityOnboarding(dcc_world)
    a = onb.original("A")
    b = onb.nameless()
    a["vitals"]["hp"]["current"] = 5
    assert b["vitals"]["hp"]["current"] == 10, "characters must not share a vitals dict"


def test_build_dispatches_and_saves(dcc_world):
    onb = IdentityOnboarding(dcc_world)
    char = onb.build("original", name="Kira", concept="a pilot")
    assert onb.save_character(char) is True
    # character.json is persisted in the canonical FLAT shape (save_character
    # runs to_flat), so the reloaded sheet has top-level keys, not identity.*.
    reloaded = onb.json_ops.load_json("character.json")
    assert reloaded["name"] == "Kira"
    assert reloaded["concept"] == "a pilot"


def test_onboard_reseeds_opening_without_a_separate_set(isolated_world_state):
    """import / /new-game persist via onboard; the opening must match that PC."""
    from tests.test_opening_seed import PIRATE_PLOT, _setup_two_arcs

    cm = CampaignManager()
    cdir = cm.create("Hyboria", "Hyboria")
    assert cm.set_active("Hyboria")
    _setup_two_arcs(cdir)
    seed_opening(str(cdir), timestamp="2026-01-01T00:00:00Z")

    result = IdentityOnboarding().onboard(
        "original", name="Conan", concept="pirate-era sailor on the Black Coast",
    )
    assert result["success"]

    ov = json.loads((cdir / "campaign-overview.json").read_text())
    assert ov["current_character"] == "Conan"
    assert ov.get("opening_matched_to_pc") is True
    assert ov["player_position"]["current_location"] == "The Tigress"
    hook = ov.get("opening_hook") or {}
    assert hook.get("location") == "The Tigress"
    assert hook.get("plot") == PIRATE_PLOT
    assert "Black Coast" in (hook.get("hook") or "")

    # A later set must not rewrite a PC-matched opening.
    ov["player_position"]["current_location"] = "WRONG"
    (cdir / "campaign-overview.json").write_text(json.dumps(ov), encoding="utf-8")
    assert PlayerManager().set_current_player("Conan")
    ov = json.loads((cdir / "campaign-overview.json").read_text())
    assert ov["player_position"]["current_location"] == "WRONG"


def test_onboard_replace_does_not_reseed_when_opening_already_matched(isolated_world_state):
    """Death hand-off: --replace must not rewrite a PC-matched opening."""
    from tests.test_opening_seed import KING_PLOT, PIRATE_PLOT, _setup_two_arcs

    cm = CampaignManager()
    cdir = cm.create("Hyboria", "Hyboria")
    assert cm.set_active("Hyboria")
    _setup_two_arcs(cdir)
    seed_opening(str(cdir), timestamp="2026-01-01T00:00:00Z")

    first = IdentityOnboarding().onboard(
        "original", name="Conan", concept="pirate-era sailor on the Black Coast",
    )
    assert first["success"]

    ov = json.loads((cdir / "campaign-overview.json").read_text())
    assert ov.get("opening_matched_to_pc") is True
    plots_before = json.loads((cdir / "plots.json").read_text())
    log_before = (cdir / "session-log.md").read_text()

    ov["player_position"]["current_location"] = "WRONG"
    (cdir / "campaign-overview.json").write_text(json.dumps(ov), encoding="utf-8")

    result = IdentityOnboarding().onboard(
        "original", name="Valeria", concept="a thief of Aquilonia", replace=True,
    )
    assert result["success"]

    ov = json.loads((cdir / "campaign-overview.json").read_text())
    plots = json.loads((cdir / "plots.json").read_text())
    log = (cdir / "session-log.md").read_text()
    assert ov["current_character"] == "Valeria"
    assert ov.get("opening_matched_to_pc") is True
    assert ov["player_position"]["current_location"] == "WRONG"
    assert plots[PIRATE_PLOT]["status"] == plots_before[PIRATE_PLOT]["status"]
    assert plots[KING_PLOT]["status"] == plots_before[KING_PLOT]["status"]
    assert log == log_before
