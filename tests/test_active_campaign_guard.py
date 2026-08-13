"""Tests for startup-active-campaign-guard: campaigns on disk, none active.

`world-state/active-campaign.txt` is what every tool resolves state through. When
it is missing, `WORLD_STATE_DIR` (tools/common.sh) is empty — sourcing survives
(see test_bootstrap_no_campaign.py), but a state verb used to hand the Python
layer an empty path and print a traceback. The wrappers now guard instead, and
the failure names the two commands that fix it.

These run the real wrappers against the real repo, so the fixture moves
world-state/active-campaign.txt aside and puts it back in teardown.
"""

import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
ACTIVE_FILE = PROJECT_ROOT / "world-state" / "active-campaign.txt"

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
def no_active_campaign():
    """Deactivate the live campaign for the duration of a test, then restore it."""
    saved = ACTIVE_FILE.read_text() if ACTIVE_FILE.exists() else None
    if saved is not None:
        ACTIVE_FILE.unlink()
    try:
        yield
    finally:
        if saved is not None:
            ACTIVE_FILE.write_text(saved)
        elif ACTIVE_FILE.exists():
            ACTIVE_FILE.unlink()


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
