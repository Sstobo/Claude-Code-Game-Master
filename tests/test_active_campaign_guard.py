"""Tests for startup-active-campaign-guard: campaigns on disk, none active.

`world-state/active-campaign.txt` is what every tool resolves state through. When
it is missing, `WORLD_STATE_DIR` (tools/common.sh) is empty — sourcing survives
(see test_bootstrap_no_campaign.py), but a state verb used to hand the Python
layer an empty path and print a traceback. The wrappers now guard instead, and
the failure names the two commands that fix it.

These run the real wrappers, but never against the live world-state: the fixture
builds the "campaigns on disk, none active" state under tmp_path and points
GM_WORLD_STATE_BASE at it. The player's active-campaign.txt is never touched.
"""

import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

# One state-reading verb per guarded wrapper.
STATE_VERBS = [
    ("tools/gm-session.sh", "context"),
    ("tools/gm-enhance.sh", "find", "Anyone"),
]

USAGE_ONLY = [
    ("tools/gm-session.sh",),
    ("tools/gm-enhance.sh",),
]


@pytest.fixture
def no_active_campaign(isolated_world_state):
    """A world-state with a campaign on disk but nothing selected — the exact
    state the guard exists for, built fresh under tmp_path."""
    (isolated_world_state / "campaigns" / "some-campaign").mkdir()
    assert not (isolated_world_state / "active-campaign.txt").exists()
    return isolated_world_state


def _run(*args):
    return subprocess.run(
        ["bash", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize("argv", STATE_VERBS, ids=lambda a: a[0])
def test_state_verb_refuses_without_active_campaign(no_active_campaign, argv):
    result = _run(*argv)
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"{argv} succeeded without a campaign: {output}"
    assert "No active campaign. This command needs one." in output
    assert "gm-campaign.sh list" in output
    assert "gm-campaign.sh switch" in output


@pytest.mark.parametrize("argv", STATE_VERBS, ids=lambda a: a[0])
def test_state_verb_prints_no_traceback(no_active_campaign, argv):
    result = _run(*argv)
    output = result.stdout + result.stderr
    assert "Traceback" not in output, f"{argv} leaked a traceback: {output}"


@pytest.mark.parametrize("argv", USAGE_ONLY, ids=lambda a: a[0])
def test_bare_usage_still_prints(no_active_campaign, argv):
    """Usage text is informational — it must survive with no campaign at all."""
    result = _run(*argv)
    output = result.stdout + result.stderr
    assert "Usage:" in output or "Commands:" in output, output
    assert "Traceback" not in output


def test_enhance_help_needs_no_campaign(no_active_campaign):
    result = _run("tools/gm-enhance.sh", "help")
    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_session_help_needs_no_campaign(no_active_campaign):
    result = _run("tools/gm-session.sh", "--help")
    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_session_typo_reports_the_typo_not_the_campaign(no_active_campaign):
    """A mistyped verb is a typo first — the guard must not shadow it."""
    result = _run("tools/gm-session.sh", "contxt")
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "Unknown action" in output
    assert "No active campaign" not in output


def test_session_unknown_action_names_every_dispatched_verb(no_active_campaign):
    """The guard's verb list and the message a typo gets are one variable, and
    every verb in it has a branch to reach — an omission here is how a real verb
    starts reporting itself as unknown."""
    script = (PROJECT_ROOT / "tools" / "gm-session.sh").read_text()
    declared = script.split('VALID_ACTIONS="', 1)[1].split('"', 1)[0].split()
    assert declared, "VALID_ACTIONS no longer parses"

    output = _run("tools/gm-session.sh", "contxt").stdout
    for verb in declared:
        assert verb in output, f"{verb} missing from the unknown-action message"
        assert f"\n    {verb})" in script, f"{verb} has no case branch"


def test_no_wrapper_local_guard_copies_remain():
    """The guard lives in common.sh only — wrapper-local copies drift out of sync
    with it, which is how the stale "/new-game or /import" wording survived.

    gm-extract.sh is exempt: its require_campaign is a name RESOLVER (it echoes
    the campaign an explicit argument or the active pointer names), not a copy of
    this guard.
    """
    result = subprocess.run(
        ["bash", "-c", 'grep -l "^require_campaign()" tools/*.sh || true'],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    offenders = [f for f in result.stdout.split() if f != "tools/gm-extract.sh"]
    assert offenders == [], f"wrapper-local guard copies left: {offenders}"


def test_the_guarded_run_stays_inside_tmp_path(no_active_campaign):
    """Isolation itself: the live pointer keeps its bytes and its mtime, and the
    wrappers wrote nothing new into the live tree."""
    live_active = PROJECT_ROOT / "world-state" / "active-campaign.txt"
    before = live_active.read_bytes() if live_active.exists() else None
    before_mtime = live_active.stat().st_mtime_ns if live_active.exists() else None

    for argv in STATE_VERBS:
        _run(*argv)

    after = live_active.read_bytes() if live_active.exists() else None
    assert after == before
    if before_mtime is not None:
        assert live_active.stat().st_mtime_ns == before_mtime
