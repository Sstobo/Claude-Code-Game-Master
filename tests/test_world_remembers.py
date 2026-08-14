"""Tests for recall-pushed-into-context.

CampaignMemory is a complete long-term memory with, until now, zero automated
readers: recall fired only if the GM thought to ask, which requires already
suspecting there is something to remember. These assert the harness now asks on
the GM's behalf using the scene as the query, and that a broken or absent memory
never costs the brief.
"""

import json
from pathlib import Path

from lib.campaign_memory import CampaignMemory
from lib.session_manager import SessionManager

CAMPAIGN = "dungeon-crawler-carl"


def _campaign_dir(world):
    return Path(world) / "campaigns" / CAMPAIGN


def _current_location(world):
    overview = json.loads((_campaign_dir(world) / "campaign-overview.json").read_text())
    return overview.get("player_position", {}).get("current_location")


def test_open_debts_reach_the_scene_unasked(dcc_world):
    """The promise made in session 3 surfaces in session 11 with no recall call."""
    CampaignMemory(dcc_world).add_arc(
        "The party bargained their way out of the Warehouse.",
        who_matters=["Mordecai"],
        open_debts=["Carl owes Mordecai a favor for the loaner gear"],
    )
    ctx = SessionManager(dcc_world).get_full_context()
    assert "OPEN DEBT" in ctx
    assert "owes Mordecai a favor" in ctx


def test_scene_seeds_the_recall_query(dcc_world):
    """History about where we are gets volunteered."""
    mem = CampaignMemory(dcc_world)
    location = _current_location(dcc_world)
    mem.add_arc(f"A deal went badly wrong at {location}, and someone remembers it.")
    mem.refresh()

    ctx = SessionManager(dcc_world).get_full_context()
    assert "THE WORLD REMEMBERS" in ctx
    assert "went badly wrong" in ctx


def test_missing_memory_file_still_builds_context(dcc_world):
    path = _campaign_dir(dcc_world) / "campaign-memory.json"
    if path.exists():
        path.unlink()
    ctx = SessionManager(dcc_world).get_full_context()
    assert "=== SESSION CONTEXT ===" in ctx


def test_corrupt_memory_file_still_builds_context(dcc_world):
    """A bad index degrades to re-gathering the log, never to a traceback."""
    (_campaign_dir(dcc_world) / "campaign-memory.json").write_text(
        "{ this is not json", encoding="utf-8"
    )
    ctx = SessionManager(dcc_world).get_full_context()
    assert "=== SESSION CONTEXT ===" in ctx
    assert "YOUR WORLD'S RULES" in ctx  # the brief completed, not truncated mid-build


def test_block_absent_when_there_is_no_history(dcc_world):
    """Nothing remembered and no debts -> no empty heading."""
    (_campaign_dir(dcc_world) / "campaign-memory.json").write_text(
        json.dumps({"entries": [], "arcs": []}), encoding="utf-8"
    )
    (_campaign_dir(dcc_world) / "session-log.md").write_text("", encoding="utf-8")
    (_campaign_dir(dcc_world) / "facts.json").write_text("{}", encoding="utf-8")
    ctx = SessionManager(dcc_world).get_full_context()
    assert "THE WORLD REMEMBERS" not in ctx


def test_recall_does_not_echo_previously_on(dcc_world):
    """A summary already printed above must not be repeated in the block."""
    mem = CampaignMemory(dcc_world)
    mem.refresh()
    sm = SessionManager(dcc_world)
    summaries = sm._recent_session_summaries(n=3)
    if not summaries:
        return  # fixture has no completed sessions; nothing to echo
    remembered, _debts, _held = sm._world_remembers(
        _current_location(dcc_world), already_shown=summaries)
    for s in summaries:
        assert s.strip() not in remembered
