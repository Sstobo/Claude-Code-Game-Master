"""Tests for persist-path-hotfixes.

Three unrelated leaks on the persist path, fixed together:

1. `gm-note.sh` / `gm-time.sh` resolved both their Python module and `world-state`
   against the caller's working directory, so they blew up (and dropped a stray
   `world-state/` behind them) whenever the GM ran them from anywhere but the
   project root.
2. `modify_hp` happily healed and damaged a corpse.
3. `get_xp_status` — a read verb — rewrote `character.json` on every call.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
ACTIVE_FILE = PROJECT_ROOT / "world-state" / "active-campaign.txt"
FIXTURE_CAMPAIGN = Path(__file__).parent / "fixtures" / "world-state" / "campaigns" / "dungeon-crawler-carl"

sys.path.insert(0, str(PROJECT_ROOT / "lib"))
from player_manager import PlayerManager  # noqa: E402


@pytest.fixture
def live_fixture_campaign():
    """Install a throwaway copy of the DCC fixture as the live active campaign.

    The wrappers read `world-state/` under the project root, not a tmp dir, so a
    test that runs the real scripts has to put its campaign there. The name is
    test-only and the previous active campaign is restored in teardown.
    """
    name = "test-persist-path-hotfixes"
    dest = PROJECT_ROOT / "world-state" / "campaigns" / name
    saved = ACTIVE_FILE.read_text() if ACTIVE_FILE.exists() else None

    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(FIXTURE_CAMPAIGN, dest)
    ACTIVE_FILE.write_text(name + "\n")
    try:
        yield dest
    finally:
        shutil.rmtree(dest, ignore_errors=True)
        if saved is not None:
            ACTIVE_FILE.write_text(saved)
        elif ACTIVE_FILE.exists():
            ACTIVE_FILE.unlink()


def _run_from(cwd, *args):
    return subprocess.run(
        ["bash", str(PROJECT_ROOT / args[0]), *args[1:]],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=180,
    )


# --- 1. the wrappers work from any working directory --------------------------

@pytest.mark.parametrize("argv", [
    ("tools/gm-note.sh", "categories"),
    ("tools/gm-time.sh", "Dusk", "16th day of Harvestmoon"),
], ids=["gm-note", "gm-time"])
def test_wrapper_runs_from_foreign_cwd(live_fixture_campaign, tmp_path, argv):
    result = _run_from(tmp_path, *argv)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "No module named" not in result.stderr
    assert "No active campaign" not in result.stdout + result.stderr
    # The old failure mode also littered a world-state/ tree in the caller's cwd.
    assert not (tmp_path / "world-state").exists()


def test_gm_time_persists_to_the_campaign_from_foreign_cwd(live_fixture_campaign, tmp_path):
    assert _run_from(tmp_path, "tools/gm-time.sh", "Dusk", "Day of Ash").returncode == 0
    overview = json.loads((live_fixture_campaign / "campaign-overview.json").read_text())
    assert overview["time_of_day"] == "Dusk"
    assert overview["current_date"] == "Day of Ash"


# --- 2. a corpse neither takes damage nor heals --------------------------------

def _dead_pc(world_state_dir):
    mgr = PlayerManager(world_state_dir)
    assert mgr.kill_character("Tandy", cause="crushed by the Iron Tangle")["success"]
    return mgr


def test_healing_a_corpse_is_refused(dcc_world, capsys):
    mgr = _dead_pc(dcc_world)
    result = mgr.modify_hp("Tandy", +10)

    assert result["success"] is False
    assert result["status"] == "dead"
    assert "dead" in capsys.readouterr().out.lower()

    char = mgr.get_player("Tandy")
    assert char["hp"]["current"] == 0
    assert char["status"] == "dead"


def test_damaging_a_corpse_is_refused(dcc_world):
    mgr = _dead_pc(dcc_world)
    assert mgr.modify_hp("Tandy", -5)["success"] is False

    char = mgr.get_player("Tandy")
    assert char["hp"]["current"] == 0
    assert char["status"] == "dead"


def test_kill_still_works_through_the_guard(dcc_world):
    mgr = PlayerManager(dcc_world)
    result = mgr.kill_character("Tandy", cause="the Iron Tangle")
    assert result["success"] and result["status"] == "dead"
    assert mgr.get_player("Tandy")["hp"]["current"] == 0


def test_dying_gate_still_fires_for_the_living(dcc_world):
    mgr = PlayerManager(dcc_world)
    assert mgr.modify_hp("Tandy", -999)["success"]
    assert mgr.get_player("Tandy")["status"] == "dying"
    assert mgr.modify_hp("Tandy", +5)["success"]
    assert mgr.get_player("Tandy")["status"] == "alive"


# --- 3. get_xp_status is read-only ---------------------------------------------

def test_get_xp_status_does_not_write(dcc_world):
    character_file = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl" / "character.json"

    # Legacy plain-integer XP: the shape _normalize_xp rewrites in memory, so a
    # status call that still saved would rewrite the file.
    char = json.loads(character_file.read_text())
    char["xp"] = 7315
    character_file.write_text(json.dumps(char, indent=2))
    before = hashlib.sha256(character_file.read_bytes()).hexdigest()

    status = PlayerManager(dcc_world).get_xp_status("Tandy")

    assert status["current_xp"] == 7315
    assert hashlib.sha256(character_file.read_bytes()).hexdigest() == before
