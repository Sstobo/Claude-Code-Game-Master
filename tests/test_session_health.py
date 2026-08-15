"""Session-health staleness scan — pure computation over loaded state."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from session_manager import SessionManager  # noqa: E402

H = SessionManager._health_summary


def test_all_quiet():
    assert H(5, {}, {}, {}) == []


def test_threads_stalest_and_filters():
    plots = {
        "The Sunken Pact": {"status": "active", "events": [{"session_number": 2}]},
        "Fresh Lead":      {"status": "active", "events": [{"session_number": 8}]},
        "Old News":        {"status": "resolved", "events": [{"session_number": 1}]},  # closed, skip
        "Deep Lore":       {"status": "active", "background": True},                    # background, skip
    }
    lines = H(8, plots, {}, {})
    assert lines == ['Threads: 2 open · stalest "The Sunken Pact" untouched 6 sessions']


def test_clocks_due_only_when_full():
    clocks = {
        "Siege": {"current": 4, "max": 4},   # due
        "Plague": {"current": 1, "max": 6},  # not due
    }
    lines = H(3, {}, clocks, {})
    assert lines == ["Clocks: 1 at a due beat (Siege) — resolve or advance the fiction"]


def test_pending_consequences_dict_and_list():
    assert H(1, {}, {}, {"active": [{"id": 1}], "pending": [{"id": 2}]}) == \
        ["Pending consequences: 2 waiting on a trigger"]
    assert H(1, {}, {}, [{"id": 1}]) == ["Pending consequences: 1 waiting on a trigger"]


def test_stale_npcs_term():
    lines = H(1, {}, {}, {}, stale_npcs={"Astreus": 5, "Bram": 3})
    assert lines == ['Canon drift: 2 NPC(s) need re-grounding (worst "Astreus", 5 beats) — gm-npc.sh stale']


def test_drift_map():
    from npc_manager import NPCManager
    npcs = {
        "Astreus": {"events": [1, 2, 3, 4, 5], "canon_checked_at": 1},  # drift 4
        "Bram":    {"events": [1, 2], "canon_checked_at": 2},           # drift 0, omit
        "Cid":     {"events": [1, 2, 3]},                               # no watermark -> drift 3
    }
    assert NPCManager._drift_map(npcs) == {"Astreus": 4, "Cid": 3}


if __name__ == "__main__":
    test_all_quiet()
    test_threads_stalest_and_filters()
    test_clocks_due_only_when_full()
    test_pending_consequences_dict_and_list()
    test_stale_npcs_term()
    test_drift_map()
    print("ok")
