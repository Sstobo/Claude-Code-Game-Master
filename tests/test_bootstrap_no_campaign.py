"""Tests for bootstrap-set-e-guard: no-active-campaign must not kill tools under `set -e`.

`get_campaign_dir` (tools/common.sh) returns 1 when no campaign is active. Every
wrapper sources common.sh, so `WORLD_STATE_DIR=$(get_campaign_dir)` inherits that
status — and in a `set -e` wrapper (gm-extract.sh, gm-worldgen.sh) the script died
at the source line, before printing anything. First-run bootstrap is exactly the
no-campaign case, so the guard is what makes import/create reachable at all.

These run the real wrappers against the real repo, so the fixture moves
world-state/active-campaign.txt aside and puts it back in teardown.
"""

import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
ACTIVE_FILE = PROJECT_ROOT / "world-state" / "active-campaign.txt"


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


def test_common_sh_survives_set_e(no_active_campaign):
    """The guard itself: sourcing common.sh under `set -e` must not abort the shell."""
    result = _run("-e", "-c", "source tools/common.sh; echo SOURCED_OK")
    assert result.returncode == 0
    assert "SOURCED_OK" in result.stdout


@pytest.mark.parametrize(
    "argv",
    [
        ("tools/gm-extract.sh",),
        ("tools/gm-extract.sh", "list"),
        ("tools/gm-worldgen.sh",),
        ("tools/gm-campaign.sh", "list"),
        ("tools/gm-session.sh", "context"),
    ],
)
def test_no_tool_dies_silently(no_active_campaign, argv):
    """No wrapper may exit non-zero without printing a diagnostic first."""
    result = _run(*argv)
    output = result.stdout + result.stderr
    assert output.strip(), f"{argv} produced no output (exit {result.returncode})"


def test_active_campaign_file_restored(no_active_campaign):
    """Guard the fixture: inside the test the file is gone, teardown puts it back."""
    assert not ACTIVE_FILE.exists()
