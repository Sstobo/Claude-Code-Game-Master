"""Tests for import-extraction-repair: one slug rule, one campaign directory.

A campaign name reaches the filesystem through three paths — campaign creation
(CampaignManager), extraction (AgentExtractor), and the shell wrappers (the
`slugify` CLI verb). They must all agree, or an import writes its extraction into
a directory the campaign tools never look at. The slug must also never be empty:
`gm-extract.sh clean` joins it onto the campaigns root before an rm -rf.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from lib.agent_extractor import AgentExtractor
from lib.campaign_manager import CampaignManager

REPO_ROOT = Path(__file__).resolve().parent.parent

TRICKY_NAMES = [
    ("Baldur's Gate: Book 1", "baldur-s-gate-book-1"),
    ("Hack  &  Slash", "hack-slash"),
    ("Curse of Strahd v2.0", "curse-of-strahd-v2-0"),
]


def slugify_cli(name: str, cwd: Path) -> str:
    """The path a shell wrapper takes (tools/gm-extract.sh campaign_slug)."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "lib" / "campaign_manager.py"), "slugify", name],
        capture_output=True, text=True, check=True, cwd=str(cwd),
    )
    return result.stdout.strip()


@pytest.mark.parametrize("name,expected", TRICKY_NAMES)
def test_all_three_slug_paths_land_in_one_directory(name, expected, tmp_path):
    world_state = tmp_path / "world-state"

    manager = CampaignManager(str(world_state))
    campaign_path = manager.create(name, campaign_name=name)
    assert campaign_path is not None
    assert campaign_path.name == expected

    # Extraction must reuse the directory campaign creation already made.
    extractor = AgentExtractor(str(world_state), campaign_name=name)
    assert extractor.extraction_dir.name == expected

    assert slugify_cli(name, cwd=tmp_path) == expected

    campaigns = sorted(p.name for p in (world_state / "campaigns").iterdir())
    assert campaigns == [expected], "the name must land in exactly one directory"

    # The Step 2 switch resolves the DISPLAY name to that same directory.
    assert manager.set_active(name) is True
    assert manager.get_active() == expected


@pytest.mark.parametrize("name", ["龍の伝説", "!!!", "...", " "])
def test_names_without_ascii_alphanumerics_still_get_a_usable_slug(name, tmp_path):
    slug = CampaignManager._slugify(name)
    assert slug, "an empty slug would resolve to the campaigns root"
    assert slug == CampaignManager._slugify(name), "must be deterministic"
    assert slug == slugify_cli(name, cwd=tmp_path)

    # Usable as a real directory, and distinct per name.
    manager = CampaignManager(str(tmp_path / "world-state"))
    campaign_path = manager.create(name, campaign_name=name)
    assert campaign_path is not None and campaign_path.name == slug


def test_distinct_non_ascii_names_do_not_collide():
    assert CampaignManager._slugify("龍の伝説") != CampaignManager._slugify("鬼の伝説")


def isolated_tools(tmp_path: Path) -> Path:
    """A throwaway PROJECT_ROOT so `gm-extract.sh clean` (which rm -rf's) can be
    exercised for real without pointing at the live world-state. common.sh derives
    every path from the script's own location, so copying tools/ and symlinking
    lib/ relocates the whole tool."""
    (tmp_path / "tools").mkdir()
    for script in ("common.sh", "gm-extract.sh"):
        shutil.copy(REPO_ROOT / "tools" / script, tmp_path / "tools" / script)
    (tmp_path / "lib").symlink_to(REPO_ROOT / "lib")
    return tmp_path / "tools" / "gm-extract.sh"


def run_clean(script: Path, name: str) -> subprocess.CompletedProcess:
    # cwd stays the repo so `uv run python` resolves this project's environment.
    return subprocess.run(
        ["bash", str(script), "clean", name],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


def test_gm_extract_clean_cannot_wipe_the_campaigns_root(tmp_path):
    """`clean` rm -rf's its target, so a name it cannot slug must never resolve to
    campaigns/ itself — that would delete every campaign."""
    script = isolated_tools(tmp_path)
    manager = CampaignManager(str(tmp_path / "world-state"))
    manager.create("Keeper", campaign_name="Keeper")

    result = run_clean(script, "龍の伝説")
    keeper = tmp_path / "world-state" / "campaigns" / "keeper"
    assert keeper.is_dir(), f"clean destroyed a bystander campaign:\n{result.stdout}{result.stderr}"
    assert (tmp_path / "world-state" / "campaigns").is_dir()


def test_gm_extract_clean_still_removes_the_named_campaign(tmp_path):
    """The root guard must not block the legitimate case."""
    script = isolated_tools(tmp_path)
    manager = CampaignManager(str(tmp_path / "world-state"))
    manager.create("Baldur's Gate: Book 1", campaign_name="Baldur's Gate: Book 1")
    manager.create("Keeper", campaign_name="Keeper")

    result = run_clean(script, "Baldur's Gate: Book 1")
    campaigns = tmp_path / "world-state" / "campaigns"
    assert not (campaigns / "baldur-s-gate-book-1").exists(), result.stdout + result.stderr
    assert (campaigns / "keeper").is_dir()


def test_gm_extract_fails_loudly_when_the_slug_helper_cannot_run(tmp_path):
    """A broken interpreter/lib must produce a message and a non-zero exit, not a
    silent mid-command death (and must not touch any campaign)."""
    script = isolated_tools(tmp_path)
    manager = CampaignManager(str(tmp_path / "world-state"))
    manager.create("Keeper", campaign_name="Keeper")
    (tmp_path / "lib").unlink()  # campaign_manager.py is now unreachable

    result = run_clean(script, "Keeper")
    assert result.returncode != 0
    assert "could not derive a campaign slug" in result.stderr
    assert (tmp_path / "world-state" / "campaigns" / "keeper").is_dir()


@pytest.mark.parametrize("legacy_dir,display_name", [
    ("baldur's-gate", "Baldur's Gate"),
    ("curse_of_strahd", "Curse of Strahd"),
])
def test_legacy_slug_directories_still_resolve(legacy_dir, display_name, tmp_path):
    """Folders created by the older, looser slug rule must stay reachable — the
    fix resolves them in place rather than renaming anything on disk."""
    world_state = tmp_path / "world-state"
    manager = CampaignManager(str(world_state))
    (world_state / "campaigns" / legacy_dir).mkdir(parents=True)

    assert manager.set_active(display_name) is True
    assert manager.get_active() == legacy_dir
    assert manager.get_campaign_path(display_name) == world_state / "campaigns" / legacy_dir
    # Resolution must not create or rename directories.
    assert sorted(p.name for p in (world_state / "campaigns").iterdir()) == [legacy_dir]


def test_new_slug_directory_wins_over_a_legacy_sibling(tmp_path):
    """When both spellings exist, the current rule's directory is authoritative."""
    world_state = tmp_path / "world-state"
    manager = CampaignManager(str(world_state))
    (world_state / "campaigns" / "baldur's-gate").mkdir(parents=True)
    (world_state / "campaigns" / "baldur-s-gate").mkdir(parents=True)

    assert manager._resolve_name("Baldur's Gate") == "baldur-s-gate"


@pytest.mark.parametrize("lookup", ["Keeper", "KEEPER", "keeper/"])
def test_resolution_returns_the_canonical_on_disk_spelling(lookup, tmp_path):
    """macOS matches case variants on the filesystem, so a plain is_dir() check
    echoed "Keeper" back for the on-disk "keeper" — the wrong spelling then
    reaches env vars and case-sensitive comparisons. A trailing slash echoed the
    same way."""
    world_state = tmp_path / "world-state"
    manager = CampaignManager(str(world_state))
    manager.create("Keeper", campaign_name="Keeper")

    assert manager._resolve_name(lookup) == "keeper"


def test_sanitize_name_does_not_stem_the_campaign_name(tmp_path):
    """A dotted campaign name keeps its suffix — stemming split it into two dirs."""
    extractor = AgentExtractor(str(tmp_path / "world-state"))
    assert extractor._sanitize_name("Curse of Strahd v2.0") == "curse-of-strahd-v2-0"
    assert extractor._sanitize_name("Curse of Strahd v2.0") == CampaignManager._slugify(
        "Curse of Strahd v2.0"
    )
