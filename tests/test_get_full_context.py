"""Characterization tests for SessionManager.get_full_context — seam #1.

These snapshot the CURRENT (post-cleanup) behavior so later reimagining tickets
(story-spine-context, untruncate-campaign-rules, ...) can change it deliberately
and see exactly what moved. They also lock in the consequence-display fix.
"""

from lib.session_manager import SessionManager


def _context(dcc_world):
    ctx = SessionManager(dcc_world).get_full_context()
    assert isinstance(ctx, str) and ctx, "get_full_context must return a non-empty string"
    return ctx


def test_context_includes_active_character(dcc_world):
    assert "Tandy" in _context(dcc_world)


def test_context_has_pending_consequences_section(dcc_world):
    assert "PENDING CONSEQUENCES" in _context(dcc_world)


def test_action_menu_defaults_on_and_surfaces_in_context(dcc_world):
    sm = SessionManager(dcc_world)
    assert sm.get_preferences().get("action_menu") is True
    assert "action menu ON" in sm.get_full_context()


def test_action_menu_off_changes_play_style_line(dcc_world):
    sm = SessionManager(dcc_world)
    sm.set_preference("action_menu", False)
    # Persisted and re-read by a fresh manager (proves it lives in the overview).
    assert SessionManager(dcc_world).get_preferences().get("action_menu") is False
    ctx = SessionManager(dcc_world).get_full_context()
    assert "action menu OFF" in ctx
    assert "action menu ON" not in ctx


def test_action_menu_on_is_a_few_numbered_not_exactly_three(dcc_world):
    ctx = _context(dcc_world)
    assert "action menu ON" in ctx
    assert "a few numbered" in ctx
    assert "exactly 3" not in ctx


def test_choices_on_confirmation_has_no_digit_option_count(dcc_world, capsys, monkeypatch):
    """The choices CLI confirmation must not re-inject a numeric option cap."""
    import sys
    import lib.session_manager as sm_mod

    monkeypatch.setattr(sys, "argv", ["session_manager.py", "choices", "on"])
    monkeypatch.setattr(sm_mod, "SessionManager", lambda: SessionManager(dcc_world))
    sm_mod.main()
    out = capsys.readouterr().out
    assert "a few numbered" in out
    assert "3 numbered" not in out


def test_adaptive_pacing_sets_no_numeric_cap(dcc_world):
    ctx = _context(dcc_world)
    assert "at most one new world development" not in ctx.lower()
    assert "NEVER convert a failure" not in ctx


def test_failure_line_is_one_informing_sentence(dcc_world):
    failure_lines = [ln for ln in _context(dcc_world).splitlines() if ln.startswith("Failure:")]
    assert len(failure_lines) == 1
    assert failure_lines[0].count(".") == 1
    assert "failure should cost something" in failure_lines[0].lower()
    assert "NEVER" not in failure_lines[0]


def test_tight_pacing_keeps_opt_in_cap(dcc_world):
    sm = SessionManager(dcc_world)
    sm.set_preference("beat_length", "tight")
    ctx = SessionManager(dcc_world).get_full_context()
    assert "AT MOST ONE new world development" in ctx


def test_pending_consequences_render_real_text_not_unknown(dcc_world):
    """Regression guard for the consequence-display bug.

    The pre-cleanup code iterated the wrong structure and read non-existent
    fields, so every consequence rendered as 'Unknown' (or the section showed
    '(none)'). Real consequence text must appear and the 'Unknown' sentinel
    must not.
    """
    ctx = _context(dcc_world)
    assert any(name in ctx for name in ("Squeeks", "Nightstalker", "Mongo", "Sheol")), (
        "expected at least one real DCC consequence to surface"
    )
    # The bug rendered each consequence as "[id] Unknown -> triggers: ...".
    assert "Unknown -> triggers" not in ctx


def test_context_includes_campaign_rules_block(dcc_world):
    """DCC's bespoke rules should be present (untruncate-campaign-rules will
    later assert they are present IN FULL; here we just pin that they appear)."""
    ctx = _context(dcc_world)
    assert any(
        rule in ctx for rule in ("loot_box_system", "audience_system", "interview_system")
    ), "expected DCC campaign_rules to appear in the context"
