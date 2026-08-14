"""Every wrapper works from any working directory.

The managers default to the relative path "world-state", so before `common.sh`
took over the anchoring each wrapper resolved the campaign against whatever
directory the caller happened to be in: `cd /tmp && bash <repo>/tools/gm-player.sh
show` reported no active campaign and left a stray `/tmp/world-state/` behind.
`gm-note.sh` and `gm-time.sh` were spot-fixed with their own `cd` (guarded by
tests/test_persist_path_hotfixes.py); the fix now lives in `common.sh`, so this
file is the bind for the ~25 wrappers that inherit it.

`common.sh` also keeps `CALLER_PWD`, because moving to the project root would
otherwise break the one verb that takes a path the user typed relative to their
own directory: `gm-extract.sh prepare <document>`.

GM_WORLD_STATE_BASE is pinned at a tmp tree throughout, so nothing here can read
or write the player's live campaign.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURE_CAMPAIGN = Path(__file__).parent / "fixtures" / "world-state" / "campaigns" / "dungeon-crawler-carl"


@pytest.fixture
def active_fixture_campaign(isolated_world_state):
    """A throwaway copy of the DCC fixture, active inside the tmp world-state."""
    name = "test-wrapper-cwd-anchoring"
    shutil.copytree(FIXTURE_CAMPAIGN, isolated_world_state / "campaigns" / name)
    (isolated_world_state / "active-campaign.txt").write_text(name + "\n")
    return isolated_world_state / "campaigns" / name


@pytest.fixture
def foreign_cwd(tmp_path):
    """A directory that is neither the project root nor the world-state, so a
    wrapper that resolves anything against the caller's cwd is caught here."""
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()
    return cwd


def _run_from(cwd, *args):
    return subprocess.run(
        ["bash", str(PROJECT_ROOT / args[0]), *args[1:]],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=300,
    )


# A read verb per wrapper: enough to make it source common.sh, resolve the
# campaign and reach its manager, without writing anything.
READ_VERBS = [
    ("tools/gm-player.sh", "show"),
    ("tools/gm-npc.sh", "list"),
    ("tools/gm-session.sh", "status"),
    ("tools/gm-note.sh", "categories"),
    ("tools/gm-search.sh", "carl", "--world-only"),
    ("tools/gm-plot.sh", "threads"),
    ("tools/gm-campaign.sh", "list"),
    ("tools/gm-clock.sh", "list"),
    ("tools/gm-consequence.sh", "list"),
    ("tools/gm-location.sh", "list"),
    ("tools/gm-overview.sh",),
    ("tools/gm-condition.sh", "list"),
    ("tools/gm-extract.sh", "list"),
    ("tools/gm-image.sh", "chronicler"),
]


@pytest.mark.parametrize("argv", READ_VERBS, ids=[a[0].split("/")[-1] for a in READ_VERBS])
def test_read_verb_runs_from_a_foreign_cwd(active_fixture_campaign, foreign_cwd, argv):
    result = _run_from(foreign_cwd, *argv)
    out = result.stdout + result.stderr

    # Whatever a wrapper decides to do, it must not have decided it because it
    # was looking at the wrong tree.
    assert "No active campaign" not in out, out
    assert "No module named" not in out, out
    assert not (foreign_cwd / "world-state").exists(), f"{argv[0]} littered a world-state/ in the caller's cwd"


def test_gm_time_persists_to_the_pinned_campaign_from_a_foreign_cwd(active_fixture_campaign, foreign_cwd):
    """The write side of the same guarantee, with the per-wrapper `cd` removed."""
    import json

    result = _run_from(foreign_cwd, "tools/gm-time.sh", "Dusk", "Day of Ash")
    assert result.returncode == 0, result.stdout + result.stderr

    overview = json.loads((active_fixture_campaign / "campaign-overview.json").read_text())
    assert overview["time_of_day"] == "Dusk"
    assert not (foreign_cwd / "world-state").exists()


def test_a_world_state_in_the_caller_cwd_is_never_the_one_resolved(foreign_cwd, monkeypatch):
    """The actual regression bind.

    GM_WORLD_STATE_BASE is an ABSOLUTE path, so the pin every test above relies
    on keeps them passing even with `cd "$PROJECT_ROOT"` deleted from common.sh
    — the manager never gets to fall back to its relative default. Unpinned is
    the shape the GM runs in, and the failure is a wrapper picking up whatever
    `world-state/` happens to sit next to the caller.

    So: plant a decoy tree in the caller's cwd and require it to be ignored.
    `gm-campaign.sh list` only reads, so the live tree it correctly resolves to
    instead is not modified.
    """
    decoy = foreign_cwd / "world-state" / "campaigns" / "decoy-campaign-cwd-anchoring"
    decoy.mkdir(parents=True)
    (decoy / "campaign-overview.json").write_text('{"name": "Decoy"}')
    (foreign_cwd / "world-state" / "active-campaign.txt").write_text(decoy.name + "\n")
    monkeypatch.delenv("GM_WORLD_STATE_BASE", raising=False)

    result = _run_from(foreign_cwd, "tools/gm-campaign.sh", "list")

    assert decoy.name not in result.stdout + result.stderr, result.stdout + result.stderr


# --- CALLER_PWD: path arguments still mean what the user typed ----------------

def test_extract_prepare_finds_a_relative_document_from_a_foreign_cwd(isolated_world_state, foreign_cwd):
    """`prepare` takes a path the user gives relative to THEIR directory. The
    move to the project root must not turn that into a not-found. Whether the
    run then succeeds depends on the optional RAG extras, so getting past file
    resolution is the whole assertion."""
    (foreign_cwd / "module.txt").write_text("The tavern is on fire.\n")

    result = _run_from(foreign_cwd, "tools/gm-extract.sh", "prepare", "module.txt", "cwd-anchoring-doc")

    assert "File not found" not in result.stdout + result.stderr, result.stdout + result.stderr


def test_extract_prepare_still_reports_a_genuinely_missing_document(isolated_world_state, foreign_cwd):
    """The negative control: resolving against CALLER_PWD must not make every
    path exist. Without it the test above would pass on a broken check."""
    result = _run_from(foreign_cwd, "tools/gm-extract.sh", "prepare", "no-such-module.txt")

    assert result.returncode != 0
    assert "File not found" in result.stdout + result.stderr
