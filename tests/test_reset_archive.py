"""Tests for gm-reset.sh archiving and non-interactive safety.

`archive` used to claim it saved the world to a git branch, but world-state/campaigns/*
is gitignored, so the branch was empty and the reset was a real data loss. It now
copies the campaign directory to world-state/archive/<campaign>-<timestamp>/.

These tests run against a throwaway world-state under tmp_path: the fixture builds
a whole base dir (campaigns/ + active-campaign.txt) and points
GM_WORLD_STATE_BASE at it, so the wrappers, the managers and the archive all
operate there. The live world-state is never read or written — an interrupted or
parallel run cannot de-select the player's campaign.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from lib.combat_manager import CombatManager
from lib.player_manager import PlayerManager

ROOT = Path(__file__).resolve().parent.parent
RESET_COMMAND_DOC = ROOT / ".claude" / "commands" / "reset.md"
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
    "fallen/Dead Guy.json": '{"name": "Dead Guy"}\n',
    "plots.json": '{"The Heist": {"status": "active"}}\n',
    "items.json": '{"Rope": {"name": "Rope"}}\n',
    "campaign-memory.json": '{"entries": [{"summary": "we fought"}]}\n',
    "combat_state.json":
        '{"active": true, "round": 3, "turn_index": 0,'
        ' "combatants": [{"name": "Bandit", "hp_current": 4, "hp_max": 11,'
        ' "ac": 12, "conditions": [], "initiative": 14, "side": "enemy"}]}\n',
    "threat-clocks.json": '{"Doom": {"filled": 2, "segments": 6}}\n',
    "world-tick-log.json": '{"ticks": []}\n',
    "loremaster-cache.json": '{"The Pit": {"brief": "dark"}}\n',
    # Source, world and kit — reset must leave these alone.
    "world-bible.json": '{"voice": "grim"}\n',
    "world-seed.json": '{"premise": "a test world"}\n',
    "ruleset.json": '{"kit": "test-kit"}\n',
    "rules.md": "# House rules\n",
    "chronicler.json": '{"artist": "Astreus"}\n',
    "metadata.json": '{"title": "The Book"}\n',
    "current-document.txt": "chapter one\n",
    "chunks/chunk-0001.txt": "a passage\n",
    "vectors/chroma.sqlite3": "not-really-a-db\n",
    "images/scene.png": "not-really-a-png\n",
}

# What reset must clear, and what it must keep — "keeps the SOURCE, the WORLD
# and the KIT, clears the STORY".
CLEARED_FILES = [
    "character.json", "plots.json", "items.json", "campaign-memory.json",
    "combat_state.json", "threat-clocks.json", "world-tick-log.json",
    "loremaster-cache.json",
]
CLEARED_DIRS = ["saves", "fallen", "characters"]
KEPT = [
    "world-bible.json", "world-seed.json",
    "ruleset.json", "rules.md", "chronicler.json", "metadata.json",
    "current-document.txt", "chunks/chunk-0001.txt", "vectors/chroma.sqlite3",
    "images/scene.png",
]


def snapshot(directory: Path, skip: str = None) -> dict:
    """Map of relative path -> bytes, for byte-identical comparison."""
    return {
        str(p.relative_to(directory)): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file() and not (skip and str(p.relative_to(directory)).startswith(skip))
    }


def set_active_campaign(world: Path, text: str) -> None:
    """Point active-campaign.txt at a campaign atomically (sidecar + os.replace),
    so an interrupted test can never leave a half-written pointer behind."""
    active_file = world / "active-campaign.txt"
    sidecar = active_file.with_name(active_file.name + ".pytest-tmp")
    sidecar.write_text(text, encoding="utf-8")
    os.replace(sidecar, active_file)


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
def world(isolated_world_state):
    """The throwaway world-state base every tool in this module resolves to."""
    return isolated_world_state


@pytest.fixture
def archive(world):
    return world / "archive"


@pytest.fixture
def fixture_campaign(world):
    """A disposable campaign, active for the duration of the test."""
    campaign_dir = world / "campaigns" / FIXTURE_NAME
    for rel, body in FIXTURE_FILES.items():
        path = campaign_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    set_active_campaign(world, FIXTURE_NAME + "\n")
    return campaign_dir


def test_archive_copies_campaign_and_restores_byte_identical(fixture_campaign, archive):
    original = snapshot(fixture_campaign)
    snapshot_without_vectors = snapshot(fixture_campaign, skip="vectors/")

    result = run_reset("archive", "--yes")
    assert result.returncode == 0, result.stderr

    archives = list(archive.glob(f"{FIXTURE_NAME}-*"))
    assert len(archives) == 1, f"expected one archive dir, got {archives}"
    archive_dir = archives[0]

    # Everything but vectors/ — the index is rebuilt from chunks/, not archived.
    assert snapshot(archive_dir) == snapshot_without_vectors
    assert not (archive_dir / "vectors").exists()

    # The reset really cleared the live campaign (that's why the copy matters).
    assert (fixture_campaign / "npcs.json").read_text(encoding="utf-8").strip() == "{}"
    assert not (fixture_campaign / "character.json").exists()

    # Restoring from the archive brings the campaign back exactly — the live
    # vectors/ survived the reset, so the restored campaign is playable.
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


def test_reset_without_tty_and_without_yes_aborts(fixture_campaign, archive):
    before = snapshot(fixture_campaign)

    for action in ("archive", "hard"):
        result = run_reset(action)
        assert result.returncode != 0, f"{action} should refuse without a tty"
        assert "--yes" in (result.stderr + result.stdout)

    assert snapshot(fixture_campaign) == before
    assert not list(archive.glob(f"{FIXTURE_NAME}-*"))


def test_hard_reset_with_yes_clears_without_archiving(fixture_campaign, archive):
    result = run_reset("hard", "--yes")
    assert result.returncode == 0, result.stderr

    assert (fixture_campaign / "facts.json").read_text(encoding="utf-8").strip() == "{}"
    assert not (fixture_campaign / "character.json").exists()
    assert not list(archive.glob(f"{FIXTURE_NAME}-*")), "hard reset must not archive"


@pytest.mark.parametrize("action", ["archive", "hard"])
def test_reset_clears_every_story_file(fixture_campaign, action):
    assert run_reset(action, "--yes").returncode == 0

    for rel in CLEARED_FILES:
        assert not (fixture_campaign / rel).exists(), f"{rel} survived {action} reset"
    for rel in CLEARED_DIRS:
        directory = fixture_campaign / rel
        assert not directory.exists() or not any(directory.iterdir()), \
            f"{rel}/ still has content after {action} reset"


@pytest.mark.parametrize("action", ["archive", "hard"])
def test_reset_keeps_the_source_and_the_kit(fixture_campaign, action):
    kept_before = {rel: (fixture_campaign / rel).read_bytes() for rel in KEPT}

    assert run_reset(action, "--yes").returncode == 0

    for rel, body in kept_before.items():
        assert (fixture_campaign / rel).exists(), f"{rel} was destroyed by {action} reset"
        assert (fixture_campaign / rel).read_bytes() == body


@pytest.mark.parametrize("action", ["archive", "hard"])
def test_reset_ends_any_active_combat(fixture_campaign, world, action):
    # Managers take the world-state BASE dir; active-campaign.txt points at the fixture.
    assert CombatManager(str(world)).is_active(), "fixture should start mid-fight"

    assert run_reset(action, "--yes").returncode == 0

    assert not CombatManager(str(world)).is_active(), \
        "initiative and enemy HP leaked into the fresh story"


def test_archive_of_an_empty_campaign_dir_fails_without_resetting(world):
    """nullglob makes an empty copy loop look successful — it must not."""
    empty = world / "campaigns" / f"{FIXTURE_NAME}-empty"
    empty.mkdir(parents=True)
    set_active_campaign(world, empty.name + "\n")

    result = run_reset("archive", "--yes")
    assert result.returncode != 0, "an empty archive must not report success"
    assert "world unchanged" in (result.stderr + result.stdout).lower()


def test_preview_is_read_only(fixture_campaign):
    before = snapshot(fixture_campaign)

    result = run_reset("preview")
    assert result.returncode == 0, result.stderr
    assert snapshot(fixture_campaign) == before


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_failed_archive_copy_leaves_campaign_untouched(fixture_campaign, archive):
    before = snapshot(fixture_campaign)

    archive.mkdir(parents=True, exist_ok=True)
    original_mode = archive.stat().st_mode
    archive.chmod(0o555)  # can't create the timestamped subdir inside
    try:
        result = run_reset("archive", "--yes")
    finally:
        archive.chmod(original_mode)

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
    # The promised scope must match what reset_world actually does.
    for name in ("plots", "items", "combat state", "threat clocks", "saves"):
        assert name in doc.lower(), f"reset.md never says {name} is cleared"
    for name in ("ruleset.json", "chunks/", "vectors/", "world-bible.json", "world-seed.json"):
        assert name in doc, f"reset.md never says {name} is kept"


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


def test_the_live_world_state_is_never_touched(fixture_campaign, world):
    """Isolation itself: a full archive+reset cycle leaves the player's
    active-campaign.txt and campaigns/ listing bit-for-bit unchanged."""
    live = ROOT / "world-state"
    live_active = live / "active-campaign.txt"
    before = live_active.read_bytes() if live_active.exists() else None
    before_mtime = live_active.stat().st_mtime_ns if live_active.exists() else None
    before_campaigns = sorted(p.name for p in (live / "campaigns").iterdir()) \
        if (live / "campaigns").is_dir() else []

    assert run_reset("archive", "--yes").returncode == 0

    after = live_active.read_bytes() if live_active.exists() else None
    assert after == before
    if before_mtime is not None:
        assert live_active.stat().st_mtime_ns == before_mtime
    after_campaigns = sorted(p.name for p in (live / "campaigns").iterdir()) \
        if (live / "campaigns").is_dir() else []
    assert after_campaigns == before_campaigns
    assert not (live / "archive").exists() or \
        not list((live / "archive").glob(f"{FIXTURE_NAME}-*"))
