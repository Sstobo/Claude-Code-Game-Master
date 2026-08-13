"""Tests for gm-reset.sh archiving and non-interactive safety.

`archive` used to claim it saved the world to a git branch, but world-state/campaigns/*
is gitignored, so the branch was empty and the reset was a real data loss. It now
copies the campaign directory to world-state/archive/<campaign>-<timestamp>/.

These tests run against a throwaway fixture campaign under world-state/campaigns/;
the live campaigns (and active-campaign.txt) are saved and restored.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RESET_COMMAND_DOC = ROOT / ".claude" / "commands" / "reset.md"
CAMPAIGNS = ROOT / "world-state" / "campaigns"
ARCHIVE = ROOT / "world-state" / "archive"
ACTIVE_FILE = ROOT / "world-state" / "active-campaign.txt"
FIXTURE_NAME = "pytest-reset-fixture"

FIXTURE_FILES = {
    "npcs.json": '{"Grim": {"name": "Grim", "mood": "wary"}}\n',
    "locations.json": '{"The Pit": {"name": "The Pit"}}\n',
    "facts.json": '{"f1": {"fact": "The door is barred"}}\n',
    "consequences.json": '{"active": [], "resolved": []}\n',
    "campaign-overview.json": '{"campaign_name": "Reset Fixture", "session_count": 3}\n',
    "session-log.md": "# Campaign Session Log\n\nSession 1 happened.\n",
    "character.json": '{"name": "Testarossa", "hp": {"current": 9, "max": 12}}\n',
    "saves/snapshot.json": '{"saved": true}\n',
}


def snapshot(directory: Path) -> dict:
    """Map of relative path -> bytes, for byte-identical comparison."""
    return {
        str(p.relative_to(directory)): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def run_reset(*args, stdin=subprocess.DEVNULL):
    return subprocess.run(
        ["bash", "tools/gm-reset.sh", *args],
        cwd=ROOT, capture_output=True, text=True, stdin=stdin,
    )


def git_branches() -> str:
    return subprocess.run(
        ["git", "branch", "--list"], cwd=ROOT, capture_output=True, text=True
    ).stdout


def git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout


@pytest.fixture
def fixture_campaign():
    """A disposable campaign made active for the duration of the test."""
    campaign_dir = CAMPAIGNS / FIXTURE_NAME
    assert not campaign_dir.exists(), f"stale fixture campaign at {campaign_dir}"
    for rel, body in FIXTURE_FILES.items():
        path = campaign_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    previous_active = ACTIVE_FILE.read_text(encoding="utf-8") if ACTIVE_FILE.exists() else None
    ACTIVE_FILE.write_text(FIXTURE_NAME + "\n", encoding="utf-8")

    yield campaign_dir

    shutil.rmtree(campaign_dir, ignore_errors=True)
    for stale in ARCHIVE.glob(f"{FIXTURE_NAME}-*"):
        shutil.rmtree(stale, ignore_errors=True)
    if ARCHIVE.exists() and not any(ARCHIVE.iterdir()):
        ARCHIVE.rmdir()
    if previous_active is None:
        ACTIVE_FILE.unlink(missing_ok=True)
    else:
        ACTIVE_FILE.write_text(previous_active, encoding="utf-8")


def test_archive_copies_campaign_and_restores_byte_identical(fixture_campaign):
    original = snapshot(fixture_campaign)

    result = run_reset("archive", "--yes")
    assert result.returncode == 0, result.stderr

    archives = list(ARCHIVE.glob(f"{FIXTURE_NAME}-*"))
    assert len(archives) == 1, f"expected one archive dir, got {archives}"
    archive_dir = archives[0]

    assert snapshot(archive_dir) == original

    # The reset really cleared the live campaign (that's why the copy matters).
    assert (fixture_campaign / "npcs.json").read_text(encoding="utf-8").strip() == "{}"
    assert not (fixture_campaign / "character.json").exists()

    # Restoring from the archive brings the campaign back exactly.
    shutil.copytree(archive_dir, fixture_campaign, dirs_exist_ok=True)
    assert snapshot(fixture_campaign) == original

    # The recovery instructions must point at the real archive.
    assert str(archive_dir) in result.stdout


def test_archive_touches_no_git_state(fixture_campaign):
    branches_before, head_before = git_branches(), git_head()

    assert run_reset("archive", "--yes").returncode == 0

    assert git_branches() == branches_before
    assert git_head() == head_before
    assert "archive/" not in git_branches()


def test_reset_without_tty_and_without_yes_aborts(fixture_campaign):
    before = snapshot(fixture_campaign)

    for action in ("archive", "hard"):
        result = run_reset(action)
        assert result.returncode != 0, f"{action} should refuse without a tty"
        assert "--yes" in (result.stderr + result.stdout)

    assert snapshot(fixture_campaign) == before
    assert not list(ARCHIVE.glob(f"{FIXTURE_NAME}-*"))


def test_hard_reset_with_yes_clears_without_archiving(fixture_campaign):
    result = run_reset("hard", "--yes")
    assert result.returncode == 0, result.stderr

    assert (fixture_campaign / "facts.json").read_text(encoding="utf-8").strip() == "{}"
    assert not (fixture_campaign / "character.json").exists()
    assert not list(ARCHIVE.glob(f"{FIXTURE_NAME}-*")), "hard reset must not archive"


def test_preview_is_read_only(fixture_campaign):
    before = snapshot(fixture_campaign)

    result = run_reset("preview")
    assert result.returncode == 0, result.stderr
    assert snapshot(fixture_campaign) == before


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_failed_archive_copy_leaves_campaign_untouched(fixture_campaign):
    before = snapshot(fixture_campaign)

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    original_mode = ARCHIVE.stat().st_mode
    ARCHIVE.chmod(0o555)  # can't create the timestamped subdir inside
    try:
        result = run_reset("archive", "--yes")
    finally:
        ARCHIVE.chmod(original_mode)

    assert result.returncode != 0, "a failed archive must not report success"
    assert "world unchanged" in (result.stderr + result.stdout).lower()
    assert snapshot(fixture_campaign) == before


def test_reset_command_doc_matches_the_real_mechanism():
    doc = RESET_COMMAND_DOC.read_text(encoding="utf-8")
    assert "git checkout" not in doc
    assert "archive/[branch-name]" not in doc
    assert "git branch" not in doc
    # The documented invocations must survive the tty gate the GM runs under.
    assert "gm-reset.sh archive --yes" in doc
    assert "gm-reset.sh hard --yes" in doc
    assert "world-state/archive/" in doc


def test_campaign_delete_rejects_flag_as_campaign_name(fixture_campaign):
    result = subprocess.run(
        ["bash", "tools/gm-campaign.sh", "delete", "--yes"],
        cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL,
    )
    assert result.returncode != 0
    assert "Usage:" in (result.stdout + result.stderr)
    assert fixture_campaign.exists()


def test_campaign_delete_without_tty_and_without_yes_aborts(fixture_campaign):
    result = subprocess.run(
        ["bash", "tools/gm-campaign.sh", "delete", FIXTURE_NAME],
        cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL,
    )
    assert result.returncode != 0
    assert "--yes" in (result.stderr + result.stdout)
    assert fixture_campaign.exists()


def test_campaign_delete_with_yes_completes(fixture_campaign):
    result = subprocess.run(
        ["bash", "tools/gm-campaign.sh", "delete", FIXTURE_NAME, "--yes"],
        cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 0, result.stderr
    assert not fixture_campaign.exists()
