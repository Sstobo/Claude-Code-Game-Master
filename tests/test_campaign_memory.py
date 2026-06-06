"""Tests for longterm-memory: recall over campaign history + tiered memoir + provenance."""

from pathlib import Path

from lib.campaign_memory import CampaignMemory


def _log(dcc_world):
    return Path(dcc_world) / "campaigns" / "dungeon-crawler-carl" / "session-log.md"


def test_recall_surfaces_a_past_event(dcc_world):
    m = CampaignMemory(dcc_world)
    m.refresh()
    hits = m.recall("Remex soul crystal warehouse")
    assert hits and any("Remex" in h["text"] for h in hits)


def test_recall_filters_by_provenance(dcc_world):
    m = CampaignMemory(dcc_world)
    m.refresh()
    canon = m.recall("Prometheus dragon", provenance="book-canon")
    assert all(h["provenance"] == "book-canon" for h in canon)


def test_memoir_is_tiered_and_bounded(dcc_world):
    mem = CampaignMemory(dcc_world).memoir()
    assert mem["arc_summary"]
    assert isinstance(mem["recent"], list) and len(mem["recent"]) <= 3
    assert mem["archive_count"] >= 0 and mem["compressed_older"] >= 0


def test_refresh_writes_collection(dcc_world):
    m = CampaignMemory(dcc_world)
    n = m.refresh()
    assert n > 0
    data = m.json_ops.load_json("campaign-memory.json")
    assert "entries" in data and len(data["entries"]) == n


def test_session_log_is_not_mutated(dcc_world):
    before = _log(dcc_world).read_text(encoding="utf-8")
    m = CampaignMemory(dcc_world)
    m.refresh()
    m.recall("anything")
    m.memoir()
    assert _log(dcc_world).read_text(encoding="utf-8") == before  # canonical ledger untouched


def test_recall_empty_query_returns_nothing(dcc_world):
    assert CampaignMemory(dcc_world).recall("") == []
