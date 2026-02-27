import pytest
import json
from pathlib import Path
from lib.consequence_manager import ConsequenceManager


def make_world_state(tmp_path, consequences=None):
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

    if consequences is not None:
        (camp / "consequences.json").write_text(
            json.dumps(consequences, ensure_ascii=False)
        )

    return str(ws), camp


class TestAddConsequence:
    def test_add_returns_id(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        cid = mgr.add_consequence("Guard reports the party", "next morning")
        assert isinstance(cid, str)
        assert len(cid) > 0

    def test_add_persists_to_file(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        mgr.add_consequence("Alarm triggered", "1 hour later")
        data = json.loads((camp / "consequences.json").read_text())
        assert len(data["active"]) == 1
        assert data["active"][0]["consequence"] == "Alarm triggered"

    def test_add_stores_trigger(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        mgr.add_consequence("Dragon wakes", "at dawn")
        data = json.loads((camp / "consequences.json").read_text())
        assert data["active"][0]["trigger"] == "at dawn"

    def test_add_multiple_consequences(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        mgr.add_consequence("Event A", "tomorrow")
        mgr.add_consequence("Event B", "next week")
        data = json.loads((camp / "consequences.json").read_text())
        assert len(data["active"]) == 2


class TestCheckPending:
    def test_check_returns_list(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        result = mgr.check_pending()
        assert isinstance(result, list)

    def test_check_empty_initially(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        result = mgr.check_pending()
        assert result == []

    def test_check_returns_added_consequence(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        mgr.add_consequence("Soldiers arrive", "next day")
        pending = mgr.check_pending()
        assert len(pending) == 1
        assert pending[0]["consequence"] == "Soldiers arrive"

    def test_check_returns_multiple(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        mgr.add_consequence("Event A", "tomorrow")
        mgr.add_consequence("Event B", "later")
        pending = mgr.check_pending()
        assert len(pending) == 2


class TestResolveConsequence:
    def test_resolve_returns_true(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        cid = mgr.add_consequence("Event to resolve", "now")
        result = mgr.resolve(cid)
        assert result is True

    def test_resolve_removes_from_active(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        cid = mgr.add_consequence("Removable event", "now")
        mgr.resolve(cid)
        pending = mgr.check_pending()
        assert len(pending) == 0

    def test_resolve_moves_to_resolved(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        cid = mgr.add_consequence("Archived event", "now")
        mgr.resolve(cid)
        resolved = mgr.list_resolved()
        assert len(resolved) == 1
        assert resolved[0]["consequence"] == "Archived event"

    def test_resolve_nonexistent_returns_false(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        result = mgr.resolve("deadbeef")
        assert result is False

    def test_resolve_only_target_consequence(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = ConsequenceManager(ws)
        cid1 = mgr.add_consequence("Keep this", "later")
        cid2 = mgr.add_consequence("Resolve this", "now")
        mgr.resolve(cid2)
        pending = mgr.check_pending()
        assert len(pending) == 1
        assert pending[0]["id"] == cid1
