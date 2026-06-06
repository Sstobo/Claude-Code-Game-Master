"""Tests for session-identity-metadata: pair-based session count + structured footer."""

from pathlib import Path

from lib.session_manager import SessionManager


def _log(dcc_world):
    return Path(dcc_world) / "campaigns" / "dungeon-crawler-carl" / "session-log.md"


def test_session_number_uses_pairs_not_raw_starts(dcc_world):
    text = _log(dcc_world).read_text(encoding="utf-8")
    ended = text.count("### Session Ended:")
    started = text.count("## Session Started:")
    expected = ended + (1 if started > ended else 0)
    n = SessionManager(dcc_world)._get_session_number()
    assert n == expected
    # The pre-fix bug counted raw starts (DCC had ~20 starts for ~13 sessions).
    assert n < started


def test_end_writes_structured_footer(dcc_world):
    SessionManager(dcc_world).end_session(
        "Tested ending.", cliffhanger="A shadow moves at the door.",
        open_threads=["Find the key", "Warn the village"])
    text = _log(dcc_world).read_text(encoding="utf-8")
    assert "**Cliffhanger:** A shadow moves at the door." in text
    assert "**Open threads:** Find the key; Warn the village" in text
    assert "**Session:**" in text and "**Location:**" in text


def test_cliffhanger_and_threads_surface_in_context(dcc_world):
    sm = SessionManager(dcc_world)
    sm.end_session("done", cliffhanger="The door creaks open.", open_threads=["Escape the dungeon"])
    ctx = sm.get_full_context()
    assert "WHERE WE PAUSED: The door creaks open." in ctx
    assert "OPEN THREADS: Escape the dungeon" in ctx


def test_legacy_log_without_footer_still_works(dcc_world):
    # Before any structured end, context still assembles (best-effort cliffhanger).
    assert "PREVIOUSLY ON" in SessionManager(dcc_world).get_full_context()
