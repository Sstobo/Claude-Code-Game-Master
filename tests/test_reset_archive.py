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

from lib.combat_manager import CombatManager
from lib.player_manager import PlayerManager

ROOT = Path(__file__).resolve().parent.parent
RESET_COMMAND_DOC = ROOT / ".claude" / "commands" / "reset.md"
WORLD_STATE = str(ROOT / "world-state")
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


def set_active_campaign(text: str) -> None:
    """Point active-campaign.txt at a campaign atomically (sidecar + os.replace),
    so an interrupted test can never leave a half-written pointer behind."""
    sidecar = ACTIVE_FILE.with_name(ACTIVE_FILE.name + ".pytest-tmp")
    sidecar.write_text(text, encoding="utf-8")
    os.replace(sidecar, ACTIVE_FILE)


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
    set_active_campaign(FIXTURE_NAME + "\n")

    yield campaign_dir

    shutil.rmtree(campaign_dir, ignore_errors=True)
    for stale in ARCHIVE.glob(f"{FIXTURE_NAME}-*"):
        shutil.rmtree(stale, ignore_errors=True)
    if ARCHIVE.exists() and not any(ARCHIVE.iterdir()):
        ARCHIVE.rmdir()
    if previous_active is None:
        ACTIVE_FILE.unlink(missing_ok=True)
    else:
        set_active_campaign(previous_active)


def test_archive_copies_campaign_and_restores_byte_identical(fixture_campaign):
    original = snapshot(fixture_campaign)
    snapshot_without_vectors = snapshot(fixture_campaign, skip="vectors/")

    result = run_reset("archive", "--yes")
    assert result.returncode == 0, result.stderr

    archives = list(ARCHIVE.glob(f"{FIXTURE_NAME}-*"))
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
def test_reset_ends_any_active_combat(fixture_campaign, action):
    # Managers take the world-state BASE dir; active-campaign.txt points at the fixture.
    assert CombatManager(WORLD_STATE).is_active(), "fixture should start mid-fight"

    assert run_reset(action, "--yes").returncode == 0

    assert not CombatManager(WORLD_STATE).is_active(), \
        "initiative and enemy HP leaked into the fresh story"


@pytest.mark.parametrize("action", ["archive", "hard"])
def test_reset_clears_the_legacy_characters_dir(fixture_campaign, action):
    """Pre-character.json campaigns keep sheets in characters/ — still story state."""
    (fixture_campaign / "character.json").unlink()
    legacy = fixture_campaign / "characters"
    legacy.mkdir()
    (legacy / "testarossa.json").write_text(
        '{"name": "Testarossa", "level": 4}\n', encoding="utf-8"
    )
    assert PlayerManager(WORLD_STATE).list_players()

    assert run_reset(action, "--yes").returncode == 0

    assert not PlayerManager(WORLD_STATE).list_players(), \
        "legacy sheets survived the reset"


def test_archive_of_an_empty_campaign_dir_fails_without_resetting():
    """nullglob makes an empty copy loop look successful — it must not.

    Self-contained on purpose: it needs its own empty campaign rather than the
    fixture one, so it saves and restores active-campaign.txt itself and leaves
    the real active campaign untouched even when run alone.
    """
    previous_active = ACTIVE_FILE.read_text(encoding="utf-8") if ACTIVE_FILE.exists() else None
    empty = CAMPAIGNS / f"{FIXTURE_NAME}-empty"
    empty.mkdir(parents=True, exist_ok=True)
    set_active_campaign(empty.name + "\n")
    try:
        result = run_reset("archive", "--yes")
        assert result.returncode != 0, "an empty archive must not report success"
        assert "world unchanged" in (result.stderr + result.stdout).lower()
    finally:
        shutil.rmtree(empty, ignore_errors=True)
        for stale in ARCHIVE.glob(f"{empty.name}-*"):
            shutil.rmtree(stale, ignore_errors=True)
        if previous_active is None:
            ACTIVE_FILE.unlink(missing_ok=True)
        else:
            set_active_campaign(previous_active)


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
