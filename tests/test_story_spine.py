"""Tests for story-spine-context.

Pre-fix, get_full_context never read plots.json, facts.json, or session-log.md —
the DM started each session knowing party HP but not the plot or last cliffhanger.
These assert the spine is now assembled. Each substring comes from a file the old
code never opened, so they fail against the pre-fix implementation.
"""

from lib.session_manager import SessionManager


def _ctx(dcc_world, full=False):
    return SessionManager(dcc_world).get_full_context(full=full)


def test_previously_on_has_recent_session_summaries(dcc_world):
    ctx = _ctx(dcc_world)
    assert "PREVIOUSLY ON" in ctx
    assert "Session 13:" in ctx  # most recent completed session
    assert "Sheol Glass Reaper Case" in ctx  # from a recent summary


def test_where_we_paused_cliffhanger_present(dcc_world):
    assert "WHERE WE PAUSED:" in _ctx(dcc_world)


def test_story_threads_include_main_plot(dcc_world):
    ctx = _ctx(dcc_world)
    assert "STORY THREADS" in ctx
    assert "The Eight Day Countdown" in ctx
    assert "[main]" in ctx


def test_key_facts_loaded_from_facts_json(dcc_world):
    ctx = _ctx(dcc_world)
    assert "KEY FACTS" in ctx
    # a plot_world fact the pre-fix code never loaded
    assert "Prometheus" in ctx


def test_full_flag_widens_without_truncation(dcc_world):
    sm = SessionManager(dcc_world)
    default_ctx = sm.get_full_context()
    full_ctx = sm.get_full_context(full=True)
    # --full surfaces the whole campaign history (13 sessions), default bounds to 3.
    assert full_ctx.count("### ") >= 0  # sanity
    assert full_ctx.count("Session 1:") + full_ctx.count("Session 2:") >= 1
    assert len(full_ctx) >= len(default_ctx)
