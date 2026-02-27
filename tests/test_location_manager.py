
import json

from lib.location_manager import LocationManager


def make_world_state(tmp_path, locations=None):
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

    locs = locations if locations is not None else {}
    (camp / "locations.json").write_text(json.dumps(locs, ensure_ascii=False))

    return str(ws), camp


class TestAddLocation:
    def test_add_creates_entry(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = LocationManager(ws)
        result = mgr.add_location("Tavern", "center of town")
        assert result is True
        locs = json.loads((camp / "locations.json").read_text())
        assert "Tavern" in locs

    def test_add_stores_position(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = LocationManager(ws)
        mgr.add_location("Forest", "north of town")
        locs = json.loads((camp / "locations.json").read_text())
        assert locs["Forest"]["position"] == "north of town"

    def test_add_initializes_connections_as_empty(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = LocationManager(ws)
        mgr.add_location("Cave", "east")
        locs = json.loads((camp / "locations.json").read_text())
        assert locs["Cave"]["connections"] == []

    def test_add_duplicate_returns_false(self, tmp_path):
        ws, camp = make_world_state(tmp_path, locations={"Tavern": {"position": "town", "connections": []}})
        mgr = LocationManager(ws)
        result = mgr.add_location("Tavern", "somewhere")
        assert result is False


class TestConnectLocations:
    def test_connect_creates_bidirectional_links(self, tmp_path):
        locs = {
            "Tavern": {"position": "town", "connections": [], "description": ""},
            "Dungeon": {"position": "south", "connections": [], "description": ""},
        }
        ws, camp = make_world_state(tmp_path, locations=locs)
        mgr = LocationManager(ws)
        result = mgr.connect_locations("Tavern", "Dungeon", "road south")
        assert result is True

        data = json.loads((camp / "locations.json").read_text())
        tavern_targets = [c["to"] for c in data["Tavern"]["connections"]]
        dungeon_targets = [c["to"] for c in data["Dungeon"]["connections"]]
        assert "Dungeon" in tavern_targets
        assert "Tavern" in dungeon_targets

    def test_connect_stores_path(self, tmp_path):
        locs = {
            "A": {"position": "west", "connections": [], "description": ""},
            "B": {"position": "east", "connections": [], "description": ""},
        }
        ws, camp = make_world_state(tmp_path, locations=locs)
        mgr = LocationManager(ws)
        mgr.connect_locations("A", "B", "secret passage")
        data = json.loads((camp / "locations.json").read_text())
        conn = data["A"]["connections"][0]
        assert conn["path"] == "secret passage"

    def test_connect_nonexistent_location_returns_false(self, tmp_path):
        locs = {"A": {"position": "west", "connections": [], "description": ""}}
        ws, camp = make_world_state(tmp_path, locations=locs)
        mgr = LocationManager(ws)
        result = mgr.connect_locations("A", "Ghost Town", "road")
        assert result is False

    def test_connect_duplicate_returns_false(self, tmp_path):
        locs = {
            "A": {"position": "west", "connections": [{"to": "B", "path": "road"}], "description": ""},
            "B": {"position": "east", "connections": [], "description": ""},
        }
        ws, camp = make_world_state(tmp_path, locations=locs)
        mgr = LocationManager(ws)
        result = mgr.connect_locations("A", "B", "another road")
        assert result is False


class TestGetLocation:
    def test_get_returns_location_data(self, tmp_path):
        locs = {"Tavern": {"position": "town", "connections": [], "description": "A cozy place"}}
        ws, camp = make_world_state(tmp_path, locations=locs)
        mgr = LocationManager(ws)
        result = mgr.get_location("Tavern")
        assert result is not None
        assert result["position"] == "town"

    def test_get_nonexistent_returns_none(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = LocationManager(ws)
        result = mgr.get_location("Nowhere")
        assert result is None


class TestListLocations:
    def test_list_returns_all_names(self, tmp_path):
        locs = {
            "Tavern": {"position": "town", "connections": []},
            "Forest": {"position": "north", "connections": []},
            "Castle": {"position": "east", "connections": []},
        }
        ws, camp = make_world_state(tmp_path, locations=locs)
        mgr = LocationManager(ws)
        result = mgr.list_locations()
        assert set(result) == {"Tavern", "Forest", "Castle"}

    def test_list_empty_when_no_locations(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = LocationManager(ws)
        result = mgr.list_locations()
        assert result == []

    def test_list_after_add(self, tmp_path):
        ws, camp = make_world_state(tmp_path)
        mgr = LocationManager(ws)
        mgr.add_location("New Place", "somewhere")
        result = mgr.list_locations()
        assert "New Place" in result
