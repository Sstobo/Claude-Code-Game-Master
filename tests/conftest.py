"""Shared pytest fixtures.

The DCC campaign under tests/fixtures/world-state is the read-only golden
fixture. Each test gets a throwaway copy in a tmp dir so the managers (which can
write) never touch the checked-in fixture or any live campaign.
"""

import shutil
from pathlib import Path

import pytest

FIXTURE_WORLD_STATE = Path(__file__).parent / "fixtures" / "world-state"


@pytest.fixture
def isolated_world_state(tmp_path, monkeypatch):
    """An empty world-state tree under tmp_path, made the default for the test.

    GM_WORLD_STATE_BASE is what tools/common.sh and the Python base-dir default
    resolve to, so wrappers run via subprocess (which inherit the environment)
    and managers constructed without a directory both land here. Tests that
    exercise the real wrappers use this instead of mutating the live
    world-state — a killed or parallel run can no longer de-select the player's
    campaign or leave fixture campaigns behind.
    """
    base = tmp_path / "world-state"
    (base / "campaigns").mkdir(parents=True)
    monkeypatch.setenv("GM_WORLD_STATE_BASE", str(base))
    return base


@pytest.fixture
def dcc_world(tmp_path):
    """Return a path to a hermetic, writable copy of the DCC world-state.

    Point managers at this via their `world_state_dir` arg. active-campaign.txt
    selects the dungeon-crawler-carl campaign inside it.
    """
    dest = tmp_path / "world-state"
    shutil.copytree(FIXTURE_WORLD_STATE, dest)
    return str(dest)
