"""Tests for bootstrap-set-e-guard: no-active-campaign must not kill tools under `set -e`.

`get_campaign_dir` (tools/common.sh) returns 1 when no campaign is active. Every
wrapper sources common.sh, so `WORLD_STATE_DIR=$(get_campaign_dir)` inherits that
status — and in a `set -e` wrapper (gm-extract.sh) the script died
at the source line, before printing anything. First-run bootstrap is exactly the
no-campaign case, so the guard is what makes import/create reachable at all.

gm-extract.sh had the same silent death from a second cause (gm-extract-silent-cat):
every verb open-coded `campaign_name=$(cat active-campaign.txt 2>/dev/null)`, whose
exit status under `set -e` killed the script with no output. Those sites now route
through require_campaign/campaign_dir, so the tests below assert the diagnostic
text, not merely that something was printed.

These run the real wrappers, but never against the live world-state: every test
sets GM_WORLD_STATE_BASE to an empty tree under tmp_path, which IS the
no-active-campaign state. The player's active-campaign.txt is never read, moved
or deleted.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

NO_CAMPAIGN_DIAGNOSTIC = "No campaign specified and no active campaign found."


@pytest.fixture
def no_active_campaign(isolated_world_state):
    """The no-campaign state, built under tmp_path rather than taken from the live tree."""
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


def test_common_sh_survives_set_e(no_active_campaign):
    """The guard itself: sourcing common.sh under `set -e` must not abort the shell."""
    result = _run("-e", "-c", "source tools/common.sh; echo SOURCED_OK")
    assert result.returncode == 0
    assert "SOURCED_OK" in result.stdout


def test_common_sh_takes_its_base_from_the_environment(no_active_campaign):
    """The seam every test here relies on: the env var, not PROJECT_ROOT, decides."""
    result = _run("-c", "source tools/common.sh; echo $WORLD_STATE_BASE")
    assert result.returncode == 0
    assert result.stdout.strip() == str(no_active_campaign)


def test_common_sh_falls_back_to_the_repo_when_unset(no_active_campaign):
    """Unset, behavior is what it always was: the repo's own world-state."""
    env = {k: v for k, v in os.environ.items() if k != "GM_WORLD_STATE_BASE"}
    result = subprocess.run(
        ["bash", "-c", "source tools/common.sh; echo $WORLD_STATE_BASE"],
        cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == str(PROJECT_ROOT / "world-state")


@pytest.mark.parametrize(
    "argv",
    [
        ("tools/gm-extract.sh",),
        ("tools/gm-extract.sh", "list"),
        ("tools/gm-campaign.sh", "list"),
        ("tools/gm-session.sh", "context"),
    ],
)
def test_no_tool_dies_silently(no_active_campaign, argv):
    """No wrapper may exit non-zero without printing a diagnostic first."""
    result = _run(*argv)
    output = result.stdout + result.stderr
    assert output.strip(), f"{argv} produced no output (exit {result.returncode})"


@pytest.mark.parametrize("verb", ["validate", "normalize", "cap", "archive"])
def test_extract_verbs_needing_a_campaign_fail_loudly(no_active_campaign, verb):
    """The raw-cat sites: each of these verbs needs a campaign and had none, so it
    must name the problem and the fix — not exit 1 with an empty terminal."""
    result = _run("tools/gm-extract.sh", verb)
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"{verb} should not succeed without a campaign"
    assert NO_CAMPAIGN_DIAGNOSTIC in output, f"{verb} exited {result.returncode} with: {output!r}"
    assert "gm-campaign.sh switch" in output, f"{verb} did not name the fix: {output!r}"


def test_wrappers_never_touch_the_live_world_state(no_active_campaign):
    """Guard the isolation: the live pointer is not read, moved or written, and
    everything the wrappers do lands under tmp_path."""
    live_active = PROJECT_ROOT / "world-state" / "active-campaign.txt"
    before = live_active.read_bytes() if live_active.exists() else None
    before_mtime = live_active.stat().st_mtime_ns if live_active.exists() else None

    _run("tools/gm-session.sh", "context")
    _run("tools/gm-campaign.sh", "list")

    after = live_active.read_bytes() if live_active.exists() else None
    assert after == before
    if before_mtime is not None:
        assert live_active.stat().st_mtime_ns == before_mtime
    assert not (no_active_campaign / "active-campaign.txt").exists()


def _isolated_extract(tmp_path: Path) -> Path:
    """A throwaway PROJECT_ROOT — common.sh derives every path from the script's own
    location, so copying tools/ and symlinking lib/ moves the whole tool off the live
    world-state."""
    (tmp_path / "tools").mkdir()
    for script in ("common.sh", "gm-extract.sh"):
        shutil.copy(PROJECT_ROOT / "tools" / script, tmp_path / "tools" / script)
    (tmp_path / "lib").symlink_to(PROJECT_ROOT / "lib")
    return tmp_path / "tools" / "gm-extract.sh"


def _isolated_env(tmp_path: Path, **extra) -> dict:
    """Environment pinning the base dir to this tmp_path, so an exported
    GM_WORLD_STATE_BASE in the ambient shell cannot reach these tests either."""
    return {**os.environ, "GM_WORLD_STATE_BASE": str(tmp_path / "world-state"), **extra}


def test_clean_is_idempotent_for_a_campaign_that_is_not_there(tmp_path):
    """`clean` removes a directory; a directory that is already gone is the job done,
    not an error. Only this verb gets that pass — the rest still fail hard."""
    script = _isolated_extract(tmp_path)
    (tmp_path / "world-state" / "campaigns" / "keeper").mkdir(parents=True)

    result = subprocess.run(
        ["bash", str(script), "clean", "No Such Book"],
        cwd=PROJECT_ROOT, env=_isolated_env(tmp_path),
        capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "not found" in output, output
    assert (tmp_path / "world-state" / "campaigns" / "keeper").is_dir(), output


def test_a_broken_resolver_that_still_prints_cannot_produce_a_path(tmp_path):
    """campaign_dir must judge success by exit status, not by "something reached
    stdout" — otherwise a failing interpreter's junk becomes a path that `clean`
    then rm -rf's."""
    script = _isolated_extract(tmp_path)
    (tmp_path / "world-state" / "campaigns" / "keeper").mkdir(parents=True)

    # find_python (common.sh) prefers `uv`, so a `uv` earlier on PATH is the whole
    # interpreter: this one prints to stdout and then fails, like a broken venv.
    stub_bin = tmp_path / "stub-bin"
    stub_bin.mkdir()
    stub_uv = stub_bin / "uv"
    stub_uv.write_text("#!/bin/bash\necho 'keeper-but-actually-junk'\nexit 1\n")
    stub_uv.chmod(0o755)

    result = subprocess.run(
        ["bash", str(script), "clean", "Keeper"],
        cwd=PROJECT_ROOT,
        env=_isolated_env(tmp_path, PATH=f"{stub_bin}:{os.environ['PATH']}"),
        capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "could not derive a campaign slug" in output, output
    assert (tmp_path / "world-state" / "campaigns" / "keeper").is_dir(), output


@pytest.mark.parametrize("name", ["../rag", "..", ".", "/tmp", "campaigns/keeper"])
def test_clean_refuses_a_path_instead_of_a_campaign_name(tmp_path, name):
    """`clean "../rag"` used to rm -rf world-state/rag: resolution returns an exact
    folder match verbatim, and campaigns/../rag IS a directory. Slugging made that
    impossible by stripping slashes; resolving has to refuse paths outright. This is
    a loud refusal, not the idempotent no-such-campaign exit."""
    script = _isolated_extract(tmp_path)
    world_state = tmp_path / "world-state"
    (world_state / "campaigns" / "keeper").mkdir(parents=True)
    (world_state / "rag").mkdir()

    result = subprocess.run(
        ["bash", str(script), "clean", name],
        cwd=PROJECT_ROOT, env=_isolated_env(tmp_path),
        capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "not a path" in output, output
    assert (world_state / "rag").is_dir(), f"clean escaped campaigns/:\n{output}"
    assert (world_state / "campaigns" / "keeper").is_dir(), output
    assert (world_state / "campaigns").is_dir(), output


def test_resolve_refuses_names_that_leave_the_campaigns_directory(tmp_path):
    """The same refusal one layer down, where every other caller (set_active,
    delete, get_campaign_path) reaches it: a name only resolves when it is a direct
    child of campaigns/."""
    world_state = tmp_path / "world-state"
    (world_state / "campaigns" / "keeper").mkdir(parents=True)
    (world_state / "rag").mkdir()

    def resolve(name):
        return subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "lib" / "campaign_manager.py"),
             "resolve", name, "--world-state", str(world_state)],
            capture_output=True, text=True, timeout=120,
        )

    for name in ["../rag", "", str(world_state / "rag")]:
        result = resolve(name)
        assert result.returncode == 3, f"{name!r} resolved to {result.stdout!r}"
        assert not result.stdout.strip(), f"{name!r} printed {result.stdout!r}"

    # The refusal must not cost the normal paths: exact, display name, legacy folder.
    (world_state / "campaigns" / "curse_of_strahd").mkdir()
    for name, expected in [("keeper", "keeper"), ("Curse of Strahd", "curse_of_strahd"),
                           ("curse_of_strahd", "curse_of_strahd")]:
        result = resolve(name)
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.strip() == expected


def test_legacy_campaign_directory_is_reachable_from_extract_verbs(tmp_path):
    """A folder named under the older slug rule (curse_of_strahd) is what
    `gm-campaign.sh switch` writes to active-campaign.txt. gm-extract.sh used to
    re-slugify that name to curse-of-strahd and report a real campaign as missing;
    it now resolves against what is on disk.

    Runs in a throwaway PROJECT_ROOT so the live world-state is never touched.
    """
    script = _isolated_extract(tmp_path)
    (tmp_path / "world-state" / "campaigns" / "curse_of_strahd" / "extracted").mkdir(parents=True)
    env = _isolated_env(tmp_path)

    switched = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "lib" / "campaign_manager.py"), "switch", "Curse of Strahd"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120,
    )
    assert switched.returncode == 0, switched.stdout + switched.stderr
    assert (tmp_path / "world-state" / "active-campaign.txt").read_text() == "curse_of_strahd"

    result = subprocess.run(
        ["bash", str(script), "normalize"],
        cwd=PROJECT_ROOT,  # so `uv run python` resolves this project's environment
        env=env, capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "curse_of_strahd" in output, output
    assert "not found" not in output, output
