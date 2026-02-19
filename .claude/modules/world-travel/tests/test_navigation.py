#!/usr/bin/env python3
"""
Tests for coordinate navigation module
"""

import pytest
import sys
import json
import math
from pathlib import Path

MODULE_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(MODULE_DIR))

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pathfinding import PathFinder
from path_intersect import check_path_intersection, find_route_with_waypoints


class TestPathFinder:
    """Test coordinate calculations and pathfinding"""

    def test_calculate_coordinates_north(self):
        """Test coordinate calculation for North direction"""
        pf = PathFinder()
        start = {"x": 0, "y": 0}
        result = pf.calculate_coordinates(start, 1000, 0)  # North, 1000m

        assert result["x"] == 0
        assert result["y"] == 1000

    def test_calculate_coordinates_east(self):
        """Test coordinate calculation for East direction"""
        pf = PathFinder()
        start = {"x": 0, "y": 0}
        result = pf.calculate_coordinates(start, 1000, 90)  # East, 1000m

        assert result["x"] == 1000
        assert result["y"] == 0

    def test_calculate_coordinates_northeast(self):
        """Test coordinate calculation for Northeast direction"""
        pf = PathFinder()
        start = {"x": 0, "y": 0}
        result = pf.calculate_coordinates(start, 1414, 45)  # NE, ~1414m

        # 45° gives equal x/y components (diagonal)
        assert abs(result["x"] - 1000) < 10  # ~707 * sqrt(2)
        assert abs(result["y"] - 1000) < 10

    def test_calculate_bearing(self):
        """Test bearing calculation"""
        pf = PathFinder()
        start = {"x": 0, "y": 0}
        north = {"x": 0, "y": 1000}
        east = {"x": 1000, "y": 0}

        assert pf.calculate_bearing(start, north) == 0.0  # North
        assert pf.calculate_bearing(start, east) == 90.0  # East

    def test_calculate_direct_distance(self):
        """Test Euclidean distance calculation"""
        pf = PathFinder()
        a = {"x": 0, "y": 0}
        b = {"x": 300, "y": 400}

        # 3-4-5 triangle: sqrt(300^2 + 400^2) = 500
        assert pf.calculate_direct_distance(a, b) == 500

    def test_bearing_to_compass(self):
        """Test compass direction conversion"""
        pf = PathFinder()

        ru, en = pf.bearing_to_compass(0)
        assert en == "N"

        ru, en = pf.bearing_to_compass(90)
        assert en == "E"

        ru, en = pf.bearing_to_compass(180)
        assert en == "S"

        ru, en = pf.bearing_to_compass(270)
        assert en == "W"

        ru, en = pf.bearing_to_compass(45)
        assert en == "NE"

    def test_is_bearing_blocked(self):
        """Test bearing blocking check"""
        pf = PathFinder()
        location_data = {
            "blocked_ranges": [
                {"from": 160, "to": 200, "reason": "Cliff"}
            ]
        }

        blocked, reason = pf.is_bearing_blocked(location_data, 180)
        assert blocked is True
        assert "Cliff" in reason

        blocked, _ = pf.is_bearing_blocked(location_data, 90)
        assert blocked is False

    def test_get_reverse_bearing(self):
        """Test reverse bearing calculation"""
        pf = PathFinder()

        assert pf.get_reverse_bearing(0) == 180
        assert pf.get_reverse_bearing(90) == 270
        assert pf.get_reverse_bearing(180) == 0
        assert pf.get_reverse_bearing(270) == 90


class TestPathIntersection:
    """Test path intersection detection"""

    def test_check_path_intersection_hit(self):
        """Test intersection detection when path passes through location"""
        locations = {
            "A": {"coordinates": {"x": 0, "y": 0}, "diameter_meters": 100},
            "B": {"coordinates": {"x": 1000, "y": 0}, "diameter_meters": 100},
            "C": {"coordinates": {"x": 500, "y": 50}, "diameter_meters": 150},  # Should intersect A-B
        }

        intersections = check_path_intersection("A", "B", locations)
        assert "C" in intersections

    def test_check_path_intersection_miss(self):
        """Test intersection detection when path doesn't hit location"""
        locations = {
            "A": {"coordinates": {"x": 0, "y": 0}, "diameter_meters": 100},
            "B": {"coordinates": {"x": 1000, "y": 0}, "diameter_meters": 100},
            "D": {"coordinates": {"x": 500, "y": 500}, "diameter_meters": 50},  # Should NOT intersect
        }

        intersections = check_path_intersection("A", "B", locations)
        assert "D" not in intersections

    def test_find_route_with_waypoints(self):
        """Test route finding with waypoint insertion"""
        locations = {
            "A": {"coordinates": {"x": 0, "y": 0}, "diameter_meters": 100},
            "B": {"coordinates": {"x": 2000, "y": 0}, "diameter_meters": 100},
            "C": {"coordinates": {"x": 500, "y": 50}, "diameter_meters": 150},
            "D": {"coordinates": {"x": 1500, "y": 50}, "diameter_meters": 150},
        }

        route = find_route_with_waypoints("A", "B", locations)

        # Route should pass through C and D (in order by distance from A)
        assert route[0] == "A"
        assert route[-1] == "B"
        assert "C" in route
        assert "D" in route
        assert route.index("C") < route.index("D")  # C comes before D


class TestNavigationIntegration:
    """Integration tests for navigation manager"""

    def test_navigation_manager_init(self, tmp_path):
        """Test NavigationManager initialization"""
        from navigation_manager import NavigationManager

        campaign_dir = tmp_path / "test_campaign"
        campaign_dir.mkdir()

        # Create minimal campaign files
        locations_file = campaign_dir / "locations.json"
        overview_file = campaign_dir / "campaign-overview.json"

        locations_file.write_text(json.dumps({
            "Origin": {
                "position": "Starting point",
                "coordinates": {"x": 0, "y": 0},
                "connections": []
            }
        }))

        overview_file.write_text(json.dumps({
            "campaign_name": "Test Campaign",
            "path_preferences": {}
        }))

        manager = NavigationManager(str(campaign_dir))
        assert manager is not None

    def test_add_location_with_coordinates(self, tmp_path):
        """Test adding location with auto-calculated coordinates"""
        from navigation_manager import NavigationManager

        campaign_dir = tmp_path / "test_campaign"
        campaign_dir.mkdir()

        locations_file = campaign_dir / "locations.json"
        overview_file = campaign_dir / "campaign-overview.json"

        locations_file.write_text(json.dumps({
            "Origin": {
                "position": "Starting point",
                "coordinates": {"x": 0, "y": 0},
                "connections": []
            }
        }))

        overview_file.write_text(json.dumps({
            "campaign_name": "Test Campaign",
            "path_preferences": {}
        }))

        manager = NavigationManager(str(campaign_dir))

        success, result = manager.add_location_with_coordinates(
            name="North Point",
            position="1km north of origin",
            from_location="Origin",
            bearing=0,
            distance=1000,
            terrain="open"
        )

        assert success is True
        assert result is not None
        assert result['coordinates']['x'] == 0
        assert result['coordinates']['y'] == 1000
        assert result['direction_abbr'] == "N"

    def test_block_unblock_direction(self, tmp_path):
        """Test blocking and unblocking directions"""
        from navigation_manager import NavigationManager

        campaign_dir = tmp_path / "test_campaign"
        campaign_dir.mkdir()

        locations_file = campaign_dir / "locations.json"
        overview_file = campaign_dir / "campaign-overview.json"

        locations_file.write_text(json.dumps({
            "Origin": {
                "position": "Starting point",
                "coordinates": {"x": 0, "y": 0},
                "connections": [],
                "blocked_ranges": []
            }
        }))

        overview_file.write_text(json.dumps({
            "campaign_name": "Test Campaign"
        }))

        manager = NavigationManager(str(campaign_dir))

        # Block south direction
        success = manager.block_direction("Origin", 160, 200, "Cliff edge")
        assert success is True

        # Verify block was added
        locations = json.loads(locations_file.read_text())
        assert len(locations["Origin"]["blocked_ranges"]) == 1
        assert locations["Origin"]["blocked_ranges"][0]["from"] == 160
        assert locations["Origin"]["blocked_ranges"][0]["to"] == 200
        assert locations["Origin"]["blocked_ranges"][0]["reason"] == "Cliff edge"

        # Unblock
        success = manager.unblock_direction("Origin", 160, 200)
        assert success is True

        # Verify block was removed
        locations = json.loads(locations_file.read_text())
        assert len(locations["Origin"]["blocked_ranges"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
