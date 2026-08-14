"""Tests for the onboard wrapper: bash tools/gm-player.sh onboard <mode> --json.

The fixture campaign already plays Tandy, so every successful path here passes
--replace — which is itself the guard being tested.
"""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _onboard(dcc_world, *args):
    """Drive the real wrapper against a hermetic world-state tree."""
    return subprocess.run(
        ["bash", str(ROOT / "tools" / "gm-player.sh"), "onboard", *args],
        capture_output=True, text=True,
        env={**os.environ, "GM_WORLD_STATE_BASE": str(dcc_world)},
    )


def _campaign_dir(dcc_world):
    return Path(dcc_world) / "campaigns" / "dungeon-crawler-carl"


def _load(dcc_world, filename):
    return json.loads((_campaign_dir(dcc_world) / filename).read_text())


def test_nameless_envelope_and_flat_character(dcc_world):
    r = _onboard(dcc_world, "nameless", "--replace", "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["ok"] is True and d["data"]["name"] == "A nameless traveler"

    saved = _load(dcc_world, "character.json")
    # Canonical FLAT shape on disk: top-level keys, never identity/vitals sections.
    assert "identity" not in saved and "vitals" not in saved
    for key in ("name", "level", "hp", "ac", "stats", "origin"):
        assert key in saved
    assert saved["origin"] == "nameless"


def test_refuses_to_clobber_an_existing_pc(dcc_world):
    r = _onboard(dcc_world, "nameless", "--json")
    assert r.returncode == 1
    d = json.loads(r.stdout)
    assert d["ok"] is False
    assert "Tandy" in d["error"] and "--replace" in d["error"]
    # The sitting PC is untouched.
    assert _load(dcc_world, "character.json")["name"] == "Tandy"


def test_replace_archives_the_outgoing_pc(dcc_world):
    r = _onboard(dcc_world, "original", "Vex", "a thief with a debt", "--replace", "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["ok"] is True

    archived = list((_campaign_dir(dcc_world) / "fallen").glob("tandy-*.json"))
    assert archived, "the outgoing sheet must land in fallen/ like become() does"
    assert json.loads(archived[0].read_text())["name"] == "Tandy"

    saved = _load(dcc_world, "character.json")
    assert saved["name"] == "Vex" and saved["concept"] == "a thief with a debt"


def test_onboard_sets_current_character_on_the_overview(dcc_world):
    r = _onboard(dcc_world, "original", "Vex", "--replace", "--json")
    assert r.returncode == 0, r.stderr
    assert _load(dcc_world, "campaign-overview.json")["current_character"] == "Vex"


def test_canon_resolves_alias_aware_and_flags_the_npc(dcc_world):
    r = _onboard(dcc_world, "canon", "mordecai", "--replace", "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    # Lowercase input resolves to the canonical npcs.json key, and that key is the PC's name.
    assert d["ok"] is True and d["data"]["name"] == "Mordecai"
    assert d["data"]["voice"], "canon mode carries the NPC's context lines as voice"

    saved = _load(dcc_world, "character.json")
    assert saved["origin"] == "canon"
    # A canon figure who died in the book takes the helm alive.
    assert saved["status"] == "alive"
    assert "died_at" not in saved and "cause" not in saved

    npc = _load(dcc_world, "npcs.json")["Mordecai"]
    assert npc["is_player_character"] is True
    assert npc["is_party_member"] is False and npc["became_pc"] is True


def test_canon_unknown_npc_errors(dcc_world):
    r = _onboard(dcc_world, "canon", "Nobody McGhost", "--replace", "--json")
    assert r.returncode == 1
    d = json.loads(r.stdout)
    assert d["ok"] is False and "Nobody McGhost" in d["error"]


def test_canon_rejects_a_third_positional(dcc_world):
    r = _onboard(dcc_world, "canon", "Mordecai", "a rat with a clipboard", "--replace", "--json")
    assert r.returncode == 1
    assert json.loads(r.stdout)["ok"] is False


def test_human_mode_prints_a_summary_line(dcc_world):
    r = _onboard(dcc_world, "original", "Kira", "--replace")
    assert r.returncode == 0, r.stderr
    assert "Kira" in r.stdout
