"""Tests for identity-first-onboarding: canon / original / nameless → open-schema char."""

from lib.identity_onboarding import IdentityOnboarding
from lib.character_schema import is_open_schema


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
    reloaded = onb.json_ops.load_json("character.json")
    assert reloaded["identity"]["name"] == "Kira"
