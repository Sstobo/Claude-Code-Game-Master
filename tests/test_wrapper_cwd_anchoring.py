"""Every wrapper works from any working directory.

The managers default to the relative path "world-state", so before `common.sh`
took over the anchoring each wrapper resolved the campaign against whatever
directory the caller happened to be in: `cd /tmp && bash <repo>/tools/gm-player.sh
show` reported no active campaign and left a stray `/tmp/world-state/` behind.
`gm-note.sh` and `gm-time.sh` were spot-fixed with their own `cd` (guarded by
tests/test_persist_path_hotfixes.py); the fix now lives in `common.sh`, so this
file is the bind for the ~25 wrappers that inherit it.

`common.sh` also keeps `CALLER_PWD`, because moving to the project root would
otherwise break `gm-extract.sh prepare <document>`, the one verb taking a path
argument. That verb resolves a relative path against TWO anchors in order —
`CALLER_PWD` (what a human typed at their own prompt) and then `PROJECT_ROOT`
(what a tool emitted, e.g. a `world-state/campaigns/<name>/authored-canon.md`
binder) — and only then reports it missing. Both directions are bound below,
plus the tie.

GM_WORLD_STATE_BASE is pinned at a tmp tree throughout, so nothing here can read
or write the player's live campaign — and the `prepare` tests, which run a
manager that used to ignore the pin, assert the live tree is untouched after.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
LIVE_ACTIVE_FILE = PROJECT_ROOT / "world-state" / "active-campaign.txt"
FIXTURE_CAMPAIGN = Path(__file__).parent / "fixtures" / "world-state" / "campaigns" / "dungeon-crawler-carl"


def _live_campaign():
    """The live active campaign's name, if there is one on this machine.

    The unpinned test below is the only one that reaches the live tree, and only
    to read it. On a fresh clone there is no `world-state/` at all, so the test
    is skipped rather than allowed to create one."""
    if not LIVE_ACTIVE_FILE.exists():
        return None
    name = LIVE_ACTIVE_FILE.read_text().strip()
    return name if name and (PROJECT_ROOT / "world-state" / "campaigns" / name).is_dir() else None


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


@pytest.fixture
def project_root_scratch():
    """A throwaway directory INSIDE the project root, removed afterwards.

    The second anchor can only be exercised by a path that resolves from the
    project root, and the one tree already there is the player's live
    world-state, which these tests may not write to. So they name a file here
    instead, by a genuine forward `<dir>/<file>` path — the shape a tool emits."""
    scratch = Path(tempfile.mkdtemp(prefix="tmp-cwd-anchoring-", dir=PROJECT_ROOT))
    try:
        yield scratch
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


@pytest.fixture
def live_world_state_untouched():
    """The live world-state, before and after, must be the same tree.

    `prepare` is the one verb here that builds an AgentExtractor, and that
    manager took the relative default `world-state` — which, after common.sh's
    `cd`, IS the developer's live tree, whatever GM_WORLD_STATE_BASE said. These
    tests wrote whole campaigns into it. The wrapper now passes
    `--world-state "$WORLD_STATE_BASE"`, and this is what holds that."""
    live = PROJECT_ROOT / "world-state"

    def snapshot():
        if not live.exists():
            return None
        return sorted(str(p.relative_to(live)) for p in live.glob("*")) + \
            sorted(str(p.relative_to(live)) for p in live.glob("campaigns/*"))

    before = snapshot()
    yield
    assert snapshot() == before, "the run created or removed something in the LIVE world-state"


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
    ("tools/gm-consequence.sh", "list-resolved"),
    ("tools/gm-location.sh", "list"),
    ("tools/gm-overview.sh",),
    # `check <name>` is this wrapper's read verb. A bare `list` is not one of its
    # actions, and its arg-count guard exits before `require_active_campaign` —
    # so the run never reached the campaign resolution this test is about.
    ("tools/gm-condition.sh", "check", "Tandy"),
    ("tools/gm-extract.sh", "list"),
    ("tools/gm-image.sh", "chronicler"),
]


@pytest.mark.parametrize("argv", READ_VERBS, ids=[a[0].split("/")[-1] for a in READ_VERBS])
def test_read_verb_runs_from_a_foreign_cwd(active_fixture_campaign, foreign_cwd, argv):
    result = _run_from(foreign_cwd, *argv)
    out = result.stdout + result.stderr

    # Whatever a wrapper decides to do, it must not have decided it because it
    # was looking at the wrong tree. Every verb here is a real read verb of its
    # wrapper, so a clean exit is part of the guarantee: without it a wrapper
    # that failed for any reason at all still "passed" the checks below.
    assert result.returncode == 0, out
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


@pytest.mark.skipif(
    _live_campaign() is None,
    reason="needs a live active campaign to run the wrappers unpinned",
)
def test_a_world_state_in_the_caller_cwd_is_never_the_one_resolved(foreign_cwd, monkeypatch):
    """The actual regression bind.

    GM_WORLD_STATE_BASE is an ABSOLUTE path, so the pin every test above relies
    on keeps them passing even with `cd "$PROJECT_ROOT"` deleted from common.sh
    — the manager never gets to fall back to its relative default. Unpinned is
    the shape the GM runs in, and the failure is a wrapper picking up whatever
    `world-state/` happens to sit next to the caller.

    So: plant a decoy tree in the caller's cwd and require it to be ignored.
    `gm-campaign.sh list` only reads, so the live tree it correctly resolves to
    instead is not modified — asserted below, bytes and mtime.
    """
    live_name = _live_campaign()
    decoy = foreign_cwd / "world-state" / "campaigns" / "decoy-campaign-cwd-anchoring"
    decoy.mkdir(parents=True)
    (decoy / "campaign-overview.json").write_text('{"name": "Decoy"}')
    (foreign_cwd / "world-state" / "active-campaign.txt").write_text(decoy.name + "\n")
    monkeypatch.delenv("GM_WORLD_STATE_BASE", raising=False)
    before = LIVE_ACTIVE_FILE.read_bytes()
    before_mtime = LIVE_ACTIVE_FILE.stat().st_mtime_ns

    result = _run_from(foreign_cwd, "tools/gm-campaign.sh", "list")
    out = result.stdout + result.stderr

    assert result.returncode == 0, out
    # Ignoring the decoy is only half of it: a run that listed nothing at all
    # would satisfy that on its own. The live tree is the one it must have read.
    assert live_name in out, out
    assert decoy.name not in out, out
    assert LIVE_ACTIVE_FILE.read_bytes() == before
    assert LIVE_ACTIVE_FILE.stat().st_mtime_ns == before_mtime


# --- CALLER_PWD: path arguments still mean what the user typed ----------------

def test_extract_prepare_finds_a_relative_document_from_a_foreign_cwd(
    isolated_world_state, foreign_cwd, live_world_state_untouched
):
    """`prepare` takes a path the user gives relative to THEIR directory. The
    move to the project root must not turn that into a not-found. Whether the
    run then succeeds depends on the optional RAG extras, so getting past file
    resolution is the whole assertion."""
    (foreign_cwd / "module.txt").write_text("The tavern is on fire.\n")

    result = _run_from(foreign_cwd, "tools/gm-extract.sh", "prepare", "module.txt", "cwd-anchoring-doc")

    assert "File not found" not in result.stdout + result.stderr, result.stdout + result.stderr


def test_extract_prepare_finds_a_project_root_relative_document(
    isolated_world_state, foreign_cwd, project_root_scratch, live_world_state_untouched
):
    """A tool that emits a path relative to the PROJECT ROOT — the directory
    every wrapper now `cd`s to — can feed that string straight to `prepare`
    (e.g. a `world-state/campaigns/<name>/authored-canon.md` binder). Resolving
    relatives against CALLER_PWD alone broke that from every cwd but the repo
    root, so `prepare` tries the caller's directory first and the project root
    second.

    The path here has the same forward `<dir>/authored-canon.md` shape such a
    tool emits, and names the file only when read from the project root."""
    canon = project_root_scratch / "authored-canon.md"
    canon.write_text("The spires of Vaeltheon burn green at dusk.\n")
    root_relative = f"{project_root_scratch.name}/{canon.name}"
    assert not (foreign_cwd / root_relative).exists(), "the path must not also resolve from the caller's cwd"

    result = _run_from(foreign_cwd, "tools/gm-extract.sh", "prepare", root_relative, "cwd-anchoring-canon")

    # Whether the run then succeeds depends on the optional RAG extras; getting
    # past file resolution is the whole assertion.
    assert "File not found" not in result.stdout + result.stderr, result.stdout + result.stderr
    if result.returncode == 0:
        # With the extras present the run wrote a campaign, and it belongs to the
        # PINNED tree — the other half of what the live-tree guard asserts.
        assert (isolated_world_state / "campaigns" / "cwd-anchoring-canon").is_dir()


def test_extract_prepare_prefers_the_callers_copy_when_both_anchors_have_one(
    isolated_world_state, foreign_cwd, project_root_scratch, live_world_state_untouched
):
    """The tie, and the reason the order is not arbitrary: the same relative path
    names a file under BOTH anchors. A path typed at a prompt means the typist's
    file, so the caller's copy wins and the project root is only the fallback."""
    relative = f"{project_root_scratch.name}/authored-canon.md"
    (project_root_scratch / "authored-canon.md").write_text("the project root's copy\n")
    (foreign_cwd / project_root_scratch.name).mkdir()
    (foreign_cwd / relative).write_text("the caller's copy\n")

    result = _run_from(foreign_cwd, "tools/gm-extract.sh", "prepare", relative, "cwd-anchoring-tie")
    out = result.stdout + result.stderr

    # `prepare` echoes the path it resolved to, which is the whole answer here.
    assert f"Preparing document for extraction: {foreign_cwd / relative}" in out, out
    assert str(PROJECT_ROOT / relative) not in out, out


def test_extract_prepare_still_reports_a_genuinely_missing_document(
    isolated_world_state, foreign_cwd, live_world_state_untouched
):
    """The negative control: two anchors must not make every path exist. Without
    it the tests above would pass on a check that never fails. The message names
    both places it looked, so a wrong-anchor mistake is readable from it."""
    result = _run_from(foreign_cwd, "tools/gm-extract.sh", "prepare", "no-such-module.txt")
    out = result.stdout + result.stderr

    assert result.returncode != 0
    assert "File not found" in out
    assert str(foreign_cwd / "no-such-module.txt") in out, out
    assert str(PROJECT_ROOT / "no-such-module.txt") in out, out
