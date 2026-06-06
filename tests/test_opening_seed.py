"""Tests for opening-beat-seed: start a fresh import at the book's opening."""

import json
from pathlib import Path

from lib.opening_seed import seed_opening
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
