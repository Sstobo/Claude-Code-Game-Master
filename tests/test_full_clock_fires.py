"""Tests for full-clock-fires.

A threat clock stores what happens when the countdown runs out. At runtime that
text was only ever echoed in a print, so a filled clock was a line the GM might
notice rather than a beat that arrived. These assert it fires into the
consequence engine exactly once.
"""

from lib.consequence_manager import ConsequenceManager
from lib.threat_clocks import ThreatClockManager

DOOM = "The floor collapses and the level is lost."


def _active(world):
    data = ConsequenceManager(world).json_ops.load_json("consequences.json") or {}
    return [c.get("consequence", "") for c in data.get("active", [])]


def _fired(world, needle=DOOM):
    return [c for c in _active(world) if needle in c]


def test_filling_a_clock_fires_its_consequence(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Floor Collapse", 2, consequence=DOOM)
    m.advance("Floor Collapse")
    assert _fired(dcc_world) == []  # not full yet

    m.advance("Floor Collapse")
    fired = _fired(dcc_world)
    assert len(fired) == 1
    assert "[Clock — Floor Collapse]" in fired[0]


def test_a_full_clock_does_not_fire_twice(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Floor Collapse", 1, consequence=DOOM)
    m.advance("Floor Collapse")
    m.advance("Floor Collapse")
    m.advance("Floor Collapse")
    m.tick_time_clocks()
    assert len(_fired(dcc_world)) == 1


def test_time_ticks_fire_the_clock_they_fill(dcc_world):
    m = ThreatClockManager(dcc_world)
    m.add_clock("Pulse", 1, advance_on="time", consequence=DOOM)
    m.tick_time_clocks()
    assert len(_fired(dcc_world)) == 1
    m.tick_time_clocks()
    assert len(_fired(dcc_world)) == 1


def test_clock_without_a_consequence_fires_nothing(dcc_world):
    m = ThreatClockManager(dcc_world)
    before = len(_active(dcc_world))
    m.add_clock("Quiet Countdown", 1)
    m.advance("Quiet Countdown")
    assert len(_active(dcc_world)) == before


def test_reset_below_full_lets_it_fire_again(dcc_world):
    """A recurring countdown must be able to run out more than once."""
    m = ThreatClockManager(dcc_world)
    m.add_clock("Pulse", 1, consequence=DOOM)
    m.advance("Pulse")
    assert len(_fired(dcc_world)) == 1

    clocks = m._load()
    clocks["Pulse"]["current"] = 0
    m.json_ops.save_json(m.clocks_file, clocks)
    m.advance("Pulse")
    assert len(_fired(dcc_world)) == 2


def test_cli_add_accepts_a_consequence(dcc_world):
    """add_clock always took one; the parser could not pass it."""
    m = ThreatClockManager(dcc_world)
    m.add_clock("Seeded", 3, consequence=DOOM, linked_plot="The Descent")
    stored = m.get_clocks()["Seeded"]
    assert stored["consequence"] == DOOM
    assert stored["linked_plot"] == "The Descent"


def test_firing_keeps_stdout_parseable(dcc_world, capsys):
    """The fire happens inside advance/tick-time, whose --json output is parsed."""
    m = ThreatClockManager(dcc_world)
    m.add_clock("Doom", 1, consequence=DOOM)
    capsys.readouterr()
    m.advance("Doom")
    out = capsys.readouterr()
    assert out.out.strip() == "", f"fire leaked onto stdout: {out.out!r}"
    assert "[Clock — Doom]" in out.err
