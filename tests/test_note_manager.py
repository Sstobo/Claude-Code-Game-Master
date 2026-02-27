import pytest
import json
from pathlib import Path
from lib.note_manager import NoteManager


def make_world_state(tmp_path, facts=None):
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "test-campaign"
    camp.mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("test-campaign")

    overview = {
        "campaign_name": "Test Campaign",
        "time_of_day": "Day",
        "current_date": "Day 1",
    }
    (camp / "campaign-overview.json").write_text(
        json.dumps(overview, ensure_ascii=False)
    )

    if facts is not None:
        (camp / "facts.json").write_text(json.dumps(facts, ensure_ascii=False))

    return str(ws), camp


class TestAddFact:
    def test_add_fact_returns_true(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        result = mgr.add_fact("session_events", "Party arrived at the tavern")
        assert result is True

    def test_add_fact_persists_to_file(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        mgr.add_fact("plot_local", "The mayor is corrupt")
        data = json.loads((camp / "facts.json").read_text())
        assert "plot_local" in data
        assert len(data["plot_local"]) == 1
        assert data["plot_local"][0]["fact"] == "The mayor is corrupt"

    def test_add_fact_creates_category(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        mgr.add_fact("new_category", "Some fact")
        data = json.loads((camp / "facts.json").read_text())
        assert "new_category" in data

    def test_add_multiple_facts_same_category(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        mgr.add_fact("session_events", "Fact one")
        mgr.add_fact("session_events", "Fact two")
        data = json.loads((camp / "facts.json").read_text())
        assert len(data["session_events"]) == 2

    def test_add_fact_includes_timestamp(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        mgr.add_fact("session_events", "Timestamped fact")
        data = json.loads((camp / "facts.json").read_text())
        entry = data["session_events"][0]
        assert "timestamp" in entry

    def test_add_fact_to_different_categories(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        mgr.add_fact("plot_local", "Local plot")
        mgr.add_fact("plot_world", "World event")
        data = json.loads((camp / "facts.json").read_text())
        assert "plot_local" in data
        assert "plot_world" in data


class TestGetFacts:
    def test_get_all_facts_returns_dict(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        result = mgr.get_facts()
        assert isinstance(result, dict)

    def test_get_facts_by_category(self, tmp_path):
        facts = {
            "session_events": [{"fact": "Event A", "timestamp": "2024-01-01"}],
            "plot_local": [{"fact": "Plot B", "timestamp": "2024-01-01"}],
        }
        ws, camp = make_world_state(tmp_path, facts=facts)
        mgr = NoteManager(ws)
        result = mgr.get_facts("session_events")
        assert "session_events" in result
        assert "plot_local" not in result

    def test_get_facts_unknown_category_returns_empty(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        result = mgr.get_facts("nonexistent_category")
        assert result == {"nonexistent_category": []}

    def test_get_all_returns_all_categories(self, tmp_path):
        facts = {
            "cat_a": [{"fact": "A", "timestamp": "2024"}],
            "cat_b": [{"fact": "B", "timestamp": "2024"}],
        }
        ws, camp = make_world_state(tmp_path, facts=facts)
        mgr = NoteManager(ws)
        result = mgr.get_facts()
        assert "cat_a" in result
        assert "cat_b" in result

    def test_get_facts_reflects_added(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        mgr.add_fact("npc_relations", "Grimjaw trusts the party")
        result = mgr.get_facts("npc_relations")
        facts_in_cat = result["npc_relations"]
        assert any(e["fact"] == "Grimjaw trusts the party" for e in facts_in_cat)


class TestListCategories:
    def test_list_categories_empty(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        result = mgr.list_categories()
        assert result == []

    def test_list_categories_after_add(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        mgr.add_fact("session_events", "Something happened")
        mgr.add_fact("plot_world", "Dragon seen")
        categories = mgr.list_categories()
        assert "session_events" in categories
        assert "plot_world" in categories

    def test_list_categories_no_duplicates(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = NoteManager(ws)
        mgr.add_fact("events", "Fact 1")
        mgr.add_fact("events", "Fact 2")
        categories = mgr.list_categories()
        assert categories.count("events") == 1
