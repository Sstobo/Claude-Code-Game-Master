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
    ("tools/gm-worldgen.sh", "consolidate"),
]

USAGE_ONLY = [
    ("tools/gm-session.sh",),
    ("tools/gm-enhance.sh",),
    ("tools/gm-worldgen.sh",),
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
    assert "No active campaign" in output
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


def test_worldgen_guards_flag_only_invocation(no_active_campaign):
    """A leading flag is not a campaign name — the guard must still fire."""
    result = _run("tools/gm-worldgen.sh", "consolidate", "--json")
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "No active campaign" in output
    assert "Traceback" not in output


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
