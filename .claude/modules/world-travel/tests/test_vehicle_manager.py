#!/usr/bin/env python3
"""Tests for VehicleManager — dual-map transport system."""

import pytest
import sys
import json
from pathlib import Path


def _find_project_root() -> Path:
    for p in Path(__file__).parents:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("pyproject.toml not found")


PROJECT_ROOT = _find_project_root()
sys.path.insert(0, str(PROJECT_ROOT / "lib"))
sys.path.insert(0, str(PROJECT_ROOT / ".claude/modules/world-travel/lib"))

from vehicle_manager import VehicleManager


@pytest.fixture
def campaign_dir(tmp_path):
    d = tmp_path / "campaigns" / "test"
    d.mkdir(parents=True)

    locations = {
        "Sigma Spaceport": {
            "coordinates": {"x": 0, "y": 0},
            "connections": []
        },
        "Mantisk-7 Station": {
            "coordinates": {"x": 1000, "y": 0},
            "connections": []
        },
        "Far Station": {
            "coordinates": {"x": 50000, "y": 50000},
            "connections": []
        }
    }

    overview = {
        "player_position": {
            "current_location": "Sigma Spaceport"
        }
    }

    (d / "locations.json").write_text(json.dumps(locations), encoding="utf-8")
    (d / "campaign-overview.json").write_text(json.dumps(overview), encoding="utf-8")
    return d


def _load_locations(campaign_dir):
    return json.loads((campaign_dir / "locations.json").read_text(encoding="utf-8"))


def _load_overview(campaign_dir):
    return json.loads((campaign_dir / "campaign-overview.json").read_text(encoding="utf-8"))


def _setup_vehicle(campaign_dir):
    """Register a ship with two rooms at Sigma Spaceport."""
    vm = VehicleManager(str(campaign_dir))
    vm.register_vehicle("Sigma Spaceport", "ship-01", "corvette", "Bridge")
    vm.add_room("ship-01", "Bridge", None, "Sigma Spaceport", 0, 10)
    vm.add_room("ship-01", "Cargo Hold", None, "Bridge", 180, 5)
    return vm


class TestRegister:
    def test_register_vehicle_basic(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        result = vm.register_vehicle("Sigma Spaceport", "ship-01", "corvette", "Bridge")
        assert result is True

        locs = _load_locations(campaign_dir)
        v = locs["Sigma Spaceport"]["_vehicle"]
        assert v["vehicle_id"] == "ship-01"
        assert v["is_vehicle_anchor"] is True
        assert v["vehicle_type"] == "corvette"
        assert v["dock_room"] == "Bridge"

    def test_register_nonexistent_anchor(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        result = vm.register_vehicle("Nonexistent Place", "ship-01", "corvette", "Bridge")
        assert result is False

    def test_register_twice_same_id(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        vm.register_vehicle("Sigma Spaceport", "ship-01", "corvette", "Bridge")
        result = vm.register_vehicle("Sigma Spaceport", "ship-01", "corvette", "Bridge")
        assert result is True
        locs = _load_locations(campaign_dir)
        assert locs["Sigma Spaceport"]["_vehicle"]["vehicle_id"] == "ship-01"


class TestAddRoom:
    def test_add_room_calculates_coords(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        vm.register_vehicle("Sigma Spaceport", "ship-01", "corvette", "Bridge")
        result = vm.add_room("ship-01", "Bridge", None, "Sigma Spaceport", 0, 10)

        assert result["success"] is True
        assert result["coordinates"]["y"] == 10

    def test_add_room_creates_connection(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        vm.register_vehicle("Sigma Spaceport", "ship-01", "corvette", "Bridge")
        vm.add_room("ship-01", "Bridge", None, "Sigma Spaceport", 0, 10)

        locs = _load_locations(campaign_dir)
        from connection_utils import get_connection_between
        conn = get_connection_between("Sigma Spaceport", "Bridge", locs)
        assert conn is not None
        assert conn["terrain"] == "internal"

    def test_add_room_from_nonexistent(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        vm.register_vehicle("Sigma Spaceport", "ship-01", "corvette", "Bridge")
        result = vm.add_room("ship-01", "Bridge", None, "No Such Room", 0, 10)
        assert result["success"] is False


class TestBoarding:
    def test_board_goes_to_dock_room(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.board_vehicle("ship-01")
        assert result["success"] is True
        assert result["room"] == "Bridge"

    def test_board_custom_room(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.board_vehicle("ship-01", room="Cargo Hold")
        assert result["success"] is True
        assert result["room"] == "Cargo Hold"

    def test_board_sets_map_context_local(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        overview = _load_overview(campaign_dir)
        assert overview["player_position"]["map_context"] == "local"

    def test_board_sets_vehicle_id(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        overview = _load_overview(campaign_dir)
        assert overview["player_position"]["vehicle_id"] == "ship-01"

    def test_board_nonexistent_vehicle(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        result = vm.board_vehicle("nope")
        assert result["success"] is False


class TestExiting:
    def test_exit_goes_to_anchor(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        result = vm.exit_vehicle()
        assert result["success"] is True
        assert result["location"] == "Sigma Spaceport"

    def test_exit_sets_map_context_global(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        vm.exit_vehicle()
        overview = _load_overview(campaign_dir)
        assert overview["player_position"]["map_context"] == "global"

    def test_exit_clears_vehicle_id(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        vm.exit_vehicle()
        overview = _load_overview(campaign_dir)
        assert "vehicle_id" not in overview["player_position"]

    def test_exit_when_not_inside(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        result = vm.exit_vehicle()
        assert result["success"] is False


class TestInternalMovement:
    def test_move_internal_valid_room(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        result = vm.move_internal("Cargo Hold")
        assert result["success"] is True
        assert result["room"] == "Cargo Hold"

    def test_move_internal_wrong_vehicle_fail(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        result = vm.move_internal("Mantisk-7 Station")
        assert result["success"] is False

    def test_move_internal_updates_position(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        vm.move_internal("Cargo Hold")
        overview = _load_overview(campaign_dir)
        assert overview["player_position"]["current_location"] == "Cargo Hold"

    def test_move_internal_not_inside(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        result = vm.move_internal("Bridge")
        assert result["success"] is False

    def test_move_to_anchor(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01", room="Cargo Hold")
        result = vm.move_internal("Sigma Spaceport")
        assert result["success"] is True


class TestVehicleMovement:
    def test_move_vehicle_copies_coords(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.move_vehicle("ship-01", "Mantisk-7 Station")
        assert result["success"] is True

        locs = _load_locations(campaign_dir)
        assert locs["Sigma Spaceport"]["coordinates"]["x"] == 1000
        assert locs["Sigma Spaceport"]["coordinates"]["y"] == 0

    def test_move_vehicle_by_coords(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.move_vehicle("ship-01", None, x=500, y=300)
        assert result["success"] is True

        locs = _load_locations(campaign_dir)
        assert locs["Sigma Spaceport"]["coordinates"]["x"] == 500
        assert locs["Sigma Spaceport"]["coordinates"]["y"] == 300

    def test_rooms_move_with_anchor(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        locs_before = _load_locations(campaign_dir)
        room_y_before = locs_before["Bridge"]["coordinates"]["y"]

        vm.move_vehicle("ship-01", None, x=500, y=500)

        locs_after = _load_locations(campaign_dir)
        assert locs_after["Bridge"]["coordinates"]["x"] == 500
        assert locs_after["Bridge"]["coordinates"]["y"] == 500 + room_y_before

    def test_new_connections_built_by_proximity(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.move_vehicle("ship-01", "Mantisk-7 Station")
        assert "Mantisk-7 Station" in result["new_connections"]

    def test_no_nearby_locations(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.move_vehicle("ship-01", None, x=999999, y=999999)
        assert result["success"] is True
        assert result["new_connections"] == []

    def test_player_inside_status(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        result = vm.move_vehicle("ship-01", "Mantisk-7 Station")
        assert result["player_status"] == "inside"

    def test_player_outside_status(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.move_vehicle("ship-01", "Mantisk-7 Station")
        assert result["player_status"] == "outside"

    def test_nonexistent_vehicle(self, campaign_dir):
        vm = VehicleManager(str(campaign_dir))
        result = vm.move_vehicle("nope", "Mantisk-7 Station")
        assert result["success"] is False

    def test_old_connections_removed(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.move_vehicle("ship-01", "Mantisk-7 Station")
        vm.move_vehicle("ship-01", None, x=999999, y=999999)

        locs = _load_locations(campaign_dir)
        from connection_utils import get_connections
        conns = get_connections("Sigma Spaceport", locs)
        external = [c for c in conns if c["to"] not in ("Bridge", "Cargo Hold")]
        assert len(external) == 0


class TestMapData:
    def test_get_internal_map_data_filters_correctly(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        data = vm.get_internal_map_data("ship-01")
        assert "Sigma Spaceport" in data
        assert "Bridge" in data
        assert "Cargo Hold" in data
        assert "Mantisk-7 Station" not in data

    def test_global_locations_excluded(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        data = vm.get_internal_map_data("ship-01")
        for name in data:
            assert data[name].get("_vehicle", {}).get("vehicle_id") == "ship-01"


class TestListAndStatus:
    def test_list_vehicles(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.list_vehicles()
        assert len(result) == 1
        assert result[0]["vehicle_id"] == "ship-01"
        assert result[0]["vehicle_type"] == "corvette"
        assert result[0]["rooms_count"] == 2

    def test_get_status_specific(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.get_status("ship-01")
        assert result["vehicle_id"] == "ship-01"
        assert result["anchor"] == "Sigma Spaceport"
        assert "Bridge" in result["rooms"]
        assert "Cargo Hold" in result["rooms"]

    def test_get_status_all(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.get_status()
        assert len(result["vehicles"]) == 1


class TestEdgeCases:
    def test_backward_compat_no_map_context_field(self, campaign_dir):
        overview = _load_overview(campaign_dir)
        del overview["player_position"]["current_location"]
        (campaign_dir / "campaign-overview.json").write_text(
            json.dumps(overview), encoding="utf-8"
        )
        vm = VehicleManager(str(campaign_dir))
        status = vm._get_player_vehicle_status()
        assert status["map_context"] == "global"

    def test_board_when_already_inside(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.board_vehicle("ship-01")
        result = vm.board_vehicle("ship-01", room="Cargo Hold")
        assert result["success"] is True
        assert result["room"] == "Cargo Hold"

    def test_stationary_vehicle_cannot_move(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        locs = _load_locations(campaign_dir)
        locs["Sigma Spaceport"]["_vehicle"]["stationary"] = True
        (campaign_dir / "locations.json").write_text(json.dumps(locs), encoding="utf-8")
        result = vm.move_vehicle("ship-01", "Mantisk-7 Station")
        assert result["success"] is False
        assert "stationary" in result["error"]

    def test_non_stationary_vehicle_can_move(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        result = vm.move_vehicle("ship-01", "Mantisk-7 Station")
        assert result["success"] is True

    def test_multiple_vehicles_no_interference(self, campaign_dir):
        vm = _setup_vehicle(campaign_dir)
        vm.register_vehicle("Mantisk-7 Station", "ship-02", "freighter", "Cargo Bay")
        vm.add_room("ship-02", "Cargo Bay", None, "Mantisk-7 Station", 90, 15)

        vehicles = vm.list_vehicles()
        assert len(vehicles) == 2

        data1 = vm.get_internal_map_data("ship-01")
        data2 = vm.get_internal_map_data("ship-02")
        assert "Cargo Bay" not in data1
        assert "Bridge" not in data2
