"""Tests for longterm-memory: recall over campaign history + tiered memoir + provenance."""

import json
import os
import subprocess
from pathlib import Path

from lib.campaign_memory import CampaignMemory

ROOT = Path(__file__).resolve().parent.parent
_TOKEN = "zephyrstone"


def _seed_matching_entries(dcc_world, n=8):
    """Write n keyword-matching entries so top-k caps are observable."""
    m = CampaignMemory(dcc_world)
    entries = [
        {"text": f"{_TOKEN} fragment {i} recovered from the vault.",
         "provenance": "our-story", "source": "facts:session_events", "tier": "archive"}
        for i in range(n)
    ]
    m.json_ops.save_json("campaign-memory.json", {"entries": entries, "arcs": []})
    return m


def _gm_recall(dcc_world, *args):
    return subprocess.run(
        ["bash", str(ROOT / "tools" / "gm-recall.sh"), *args],
        capture_output=True, text=True,
        env={**os.environ, "GM_WORLD_STATE_BASE": str(dcc_world)},
    )


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


def test_arc_entry_persists_and_leads_the_memoir(dcc_world):
    m = CampaignMemory(dcc_world)
    m.add_arc("Carl skinned the Terror Clown and the dungeon noticed.",
              who_matters=["Grimaldi"], open_debts=["Grimaldi wants revenge"])
    mem = m.memoir()
    assert "Terror Clown" in mem["arc_summary"]
    assert "Grimaldi" in mem["arc_summary"]
    assert mem["arc_entries"] == 1


def test_refresh_preserves_arcs_and_indexes_them(dcc_world):
    m = CampaignMemory(dcc_world)
    m.add_arc("The party freed the dragon from the circus.")
    m.refresh()
    assert len(m.arcs()) == 1  # refresh must not clobber arcs
    hits = m.recall("dragon circus", top_k=10)
    assert any(e.get("source") == "arc" for e in hits)


def test_recall_falls_back_to_keyword_without_rag_deps(dcc_world):
    # In this test env sentence_transformers is absent, so this exercises the
    # keyword path end to end; with deps installed it exercises the semantic path.
    m = CampaignMemory(dcc_world)
    m.refresh()
    hits = m.recall("alliance Tutorial Guild Hall")
    assert hits, "recall must return something on a matching query"


def test_recall_default_top_k_is_five(dcc_world):
    m = _seed_matching_entries(dcc_world, n=8)
    hits = m.recall(_TOKEN)
    assert len(hits) == 5


def test_recall_top_k_eight(dcc_world):
    m = _seed_matching_entries(dcc_world, n=8)
    hits = m.recall(_TOKEN, top_k=8)
    assert len(hits) == 8


def test_gm_recall_wrapper_default_top_k_is_five(dcc_world):
    _seed_matching_entries(dcc_world, n=8)
    r = _gm_recall(dcc_world, "recall", _TOKEN)
    assert r.returncode == 0, r.stdout + r.stderr
    assert len(json.loads(r.stdout)) == 5


def test_gm_recall_wrapper_top_k_eight(dcc_world):
    _seed_matching_entries(dcc_world, n=8)
    r = _gm_recall(dcc_world, "recall", _TOKEN, "--top-k", "8")
    assert r.returncode == 0, r.stdout + r.stderr
    assert len(json.loads(r.stdout)) == 8
