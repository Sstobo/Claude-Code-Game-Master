
import json

from lib.session_manager import SessionManager


def make_world_state(tmp_path, overview_extra=None, with_character=True):
    ws = tmp_path / "world-state"
    camp = ws / "campaigns" / "test-campaign"
    camp.mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("test-campaign")

    overview = {
        "campaign_name": "Test Campaign",
        "time_of_day": "Day",
        "current_date": "Day 1",
        "current_character": "Hero",
    }
    if overview_extra:
        overview.update(overview_extra)
    (camp / "campaign-overview.json").write_text(
        json.dumps(overview, ensure_ascii=False)
    )

    if with_character:
        character = {
            "name": "Hero",
            "level": 1,
            "hp": {"current": 20, "max": 20},
            "gold": 100,
        }
        (camp / "character.json").write_text(
            json.dumps(character, ensure_ascii=False)
        )

    (camp / "locations.json").write_text("{}")
    (camp / "npcs.json").write_text("{}")
    (camp / "facts.json").write_text("{}")
    (camp / "consequences.json").write_text("{}")

    return str(ws), camp


class TestMoveParty:
    def test_move_updates_current_location(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        result = mgr.move_party("Tavern")
        assert result["current_location"] == "Tavern"

    def test_move_records_previous_location(self, tmp_path):
        ws, camp = make_world_state(tmp_path, overview_extra={
            "player_position": {"current_location": "Forest"}
        })
        mgr = SessionManager(ws)
        result = mgr.move_party("Castle")
        assert result["previous_location"] == "Forest"

    def test_move_persists_to_campaign_file(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.move_party("Dungeon")
        data = json.loads((camp / "campaign-overview.json").read_text())
        assert data["player_position"]["current_location"] == "Dungeon"

    def test_move_updates_character_location(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.move_party("Marketplace")
        char = json.loads((camp / "character.json").read_text())
        assert char["current_location"] == "Marketplace"

    def test_move_auto_creates_location_in_locations_json(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.move_party("New Place")
        locations = json.loads((camp / "locations.json").read_text())
        assert "New Place" in locations

    def test_move_creates_bidirectional_connection(self, tmp_path):
        ws, camp = make_world_state(tmp_path, overview_extra={
            "player_position": {"current_location": "Town"}
        })
        locs = {"Town": {"connections": [], "position": "center", "description": ""}}
        (camp / "locations.json").write_text(json.dumps(locs))

        mgr = SessionManager(ws)
        mgr.move_party("Forest")

        locations = json.loads((camp / "locations.json").read_text())
        town_connections = [c["to"] for c in locations["Town"].get("connections", [])]
        assert "Forest" in town_connections
        forest_connections = [c["to"] for c in locations["Forest"].get("connections", [])]
        assert "Town" in forest_connections


class TestGetContext:
    def test_get_full_context_returns_string(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        ctx = mgr.get_full_context()
        assert isinstance(ctx, str)
        assert len(ctx) > 0

    def test_get_full_context_contains_campaign_name(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        ctx = mgr.get_full_context()
        assert "Test Campaign" in ctx

    def test_get_full_context_contains_character_info(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        ctx = mgr.get_full_context()
        assert "Hero" in ctx

    def test_get_status_returns_dict(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        status = mgr.get_status()
        assert isinstance(status, dict)
        assert "locations_count" in status
        assert "npcs_count" in status


class TestSessionStartEnd:
    def test_start_session_returns_summary(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        summary = mgr.start_session()
        assert isinstance(summary, dict)
        assert "timestamp" in summary

    def test_start_session_creates_log(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.start_session()
        log = camp / "session-log.md"
        assert log.exists()
        assert "Session Started:" in log.read_text()

    def test_end_session_logs_summary(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.start_session()
        mgr.end_session("Fought dragons and won")
        log = (camp / "session-log.md").read_text()
        assert "Fought dragons and won" in log

    def test_session_count_increments(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = SessionManager(ws)
        mgr.start_session()
        assert mgr._get_session_number() == 1
        mgr.start_session()
        assert mgr._get_session_number() == 2
