"""Tests for threat-clocks-choice-beats: named segmented pressure clocks."""

import json
import os
import subprocess
from pathlib import Path

from lib.threat_clocks import ThreatClockManager
from lib.session_manager import SessionManager
from lib.time_manager import ticks_for_elapsed, ticks_from_duration

ROOT = Path(__file__).resolve().parent.parent


def _active(dcc_world):
    p = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl" / "consequences.json"
    return json.loads(p.read_text(encoding="utf-8")).get("active", [])


def _active(dcc_world):
    p = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl" / "consequences.json"
    return json.loads(p.read_text(encoding="utf-8")).get("active", [])


def test_filled_clock_is_a_pending_beat(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Doom", 2)
    assert m.pending_beats() == {}
    m.advance("Doom", 2)
    assert "Doom" in m.pending_beats()


def test_record_choice_writes_a_consequence(dcc_world):
    m = ThreatClockManager(dcc_world)
    cid = m.record_choice("Carry the WMD or run?", "Carry it yourself — irreversible",
                          trigger_type="on_location", match="Floor 4")
    assert cid
    texts = " ".join(c["consequence"] for c in _active(dcc_world))
    assert "Carry it yourself" in texts
    fork = next(c for c in _active(dcc_world) if "Carry it yourself" in c["consequence"])
    assert fork.get("trigger_type") == "on_location" and fork.get("match") == "Floor 4"


def test_add_advance_and_fill(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Floor Collapse", segments=4, advance_on="time")
    assert not m.is_full("Floor Collapse")
    m.advance("Floor Collapse", 3)
    assert not m.is_full("Floor Collapse")
    m.advance("Floor Collapse", 5)  # clamps at max
    c = m.get_clocks()["Floor Collapse"]
    assert c["current"] == 4
    assert m.is_full("Floor Collapse")
    assert "Floor Collapse" in m.full_clocks()


def test_advance_unknown_clock_returns_none(dcc_world):
    assert ThreatClockManager(dcc_world).advance("nope") is None


def test_remove_clock(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Doom", 6)
    assert m.remove_clock("Doom") is True
    assert "Doom" not in m.get_clocks()


def test_no_clocks_is_valid_tone_respecting(dcc_world):
    # A campaign that wants no doom clock simply has none.
    assert ThreatClockManager(dcc_world).get_clocks() == {}


def test_clocks_surface_in_session_context(dcc_world):
    ThreatClockManager(dcc_world).add_clock("Floor Collapse", segments=4)
    ThreatClockManager(dcc_world).advance("Floor Collapse", 2)
    ctx = SessionManager(dcc_world).get_full_context()
    assert "THREAT CLOCKS" in ctx
    assert "Floor Collapse" in ctx and "2/4" in ctx


def test_tick_time_advances_only_time_clocks(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Collapse", segments=3, advance_on="time")
    m.add_clock("Ritual", segments=3, advance_on="event")
    advanced = m.tick_time_clocks()
    assert "Collapse" in advanced and "Ritual" not in advanced
    assert m.get_clocks()["Collapse"]["current"] == 1
    assert m.get_clocks()["Ritual"]["current"] == 0


def test_tick_time_scales_with_ticks(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Siege", segments=10, advance_on="time")
    advanced = m.tick_time_clocks(3)
    assert "Siege" in advanced
    assert m.get_clocks()["Siege"]["current"] == 3


def test_duration_days_and_weeks_scale():
    assert ticks_from_duration("3 days") == 3
    assert ticks_from_duration("1 week") == 7
    assert ticks_from_duration("2 weeks") == 14
    assert ticks_for_elapsed(duration="3 days") == 3
    assert ticks_for_elapsed(ticks=3, duration="10 minutes") == 3  # explicit wins


def test_duration_minutes_and_default_are_one_tick():
    assert ticks_from_duration("10 minutes") == 1
    assert ticks_from_duration("2 hours") == 1
    assert ticks_from_duration("Dawn to Noon") == 1
    assert ticks_for_elapsed() == 1
    assert ticks_for_elapsed(ticks=1) == 1


def _gm_time(dcc_world, *args):
    return subprocess.run(
        ["bash", str(ROOT / "tools" / "gm-time.sh"), *args],
        capture_output=True, text=True,
        env={**os.environ, "GM_WORLD_STATE_BASE": str(dcc_world)},
    )


def test_gm_time_duration_advances_clocks_proportionally(dcc_world):
    ThreatClockManager(dcc_world).add_clock("Siege", segments=10, advance_on="time")
    r = _gm_time(dcc_world, "Noon", "Day 4", "--duration", "3 days")
    assert r.returncode == 0, r.stdout + r.stderr
    assert ThreatClockManager(dcc_world).get_clocks()["Siege"]["current"] == 3


def test_gm_time_default_still_ticks_one(dcc_world):
    ThreatClockManager(dcc_world).add_clock("Siege", segments=10, advance_on="time")
    r = _gm_time(dcc_world, "Noon", "Day 4")
    assert r.returncode == 0, r.stdout + r.stderr
    assert ThreatClockManager(dcc_world).get_clocks()["Siege"]["current"] == 1


def test_tick_time_stops_at_full(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Doom", segments=1, advance_on="time")
    m.tick_time_clocks()
    assert m.is_full("Doom")
    # A full clock is a pending beat, not a re-ticking counter.
    assert "Doom" not in m.tick_time_clocks()
