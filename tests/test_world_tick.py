"""Tests for between-session-worldtick: off-screen developments + rollback.

The cap is advisory: every proposal applies, and overflow is warned rather than dropped.
"""

import json
from pathlib import Path

from lib.world_tick import WorldTick


def _active(dcc_world):
    p = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl" / "consequences.json"
    return json.loads(p.read_text(encoding="utf-8")).get("active", [])


DEVS = [
    {"text": "A rival crew claims Floor 3 territory", "trigger_type": "on_location", "match": "Floor 3"},
    {"text": "Mordecai sends word of a new threat", "trigger": "next visit"},
    {"text": "Viewer interest spikes around the party"},
    {"text": "An old ally resurfaces"},
    {"text": "A fifth development that exceeds the cap"},
]


def test_cap_is_enforced(dcc_world, capsys):
    applied = WorldTick(dcc_world).apply(DEVS, cap=3)
    assert len(applied) == 5
    texts = " ".join(c["consequence"] for c in _active(dcc_world))
    assert "rival crew" in texts and "fifth development" in texts
    err = capsys.readouterr().err
    assert "fifth development" in err
    assert "cap 3" in err


def test_disabled_is_a_noop_tone_respecting(dcc_world):
    before = len(_active(dcc_world))
    applied = WorldTick(dcc_world).apply(DEVS, enabled=False)
    assert applied == [] and len(_active(dcc_world)) == before


def test_tick_is_logged_and_rollbackable(dcc_world):
    wt = WorldTick(dcc_world)
    before = len(_active(dcc_world))
    wt.apply(DEVS, cap=2)
    assert len(_active(dcc_world)) == before + 5
    assert wt.history()  # provenance log
    assert wt.rollback_last() is True
    assert len(_active(dcc_world)) == before  # developments removed


def test_rollback_without_a_tick_is_safe(dcc_world):
    assert WorldTick(dcc_world).rollback_last() is False


def test_cli_apply_and_rollback(dcc_world, monkeypatch):
    # Smoke the CLI wiring end to end (json envelope, apply -> rollback).
    import json as _json
    import subprocess, sys as _sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    def run(*args):
        return subprocess.run(
            [_sys.executable, str(root / "lib" / "world_tick.py"), *args, "--json"],
            capture_output=True, text=True, cwd=str(Path(dcc_world).parent))
    r = run("apply", _json.dumps([{"text": "a rumor spreads", "trigger": "next visit to town"}]))
    assert r.returncode == 0, r.stderr
    out = _json.loads(r.stdout)
    assert out["ok"] and len(out["data"]["applied"]) == 1
    r = run("rollback")
    assert _json.loads(r.stdout)["data"]["rolled_back"] is True
