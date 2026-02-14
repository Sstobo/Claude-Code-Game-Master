#!/usr/bin/env python3
"""
Integration test: auto-time calculation on movement
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from session_manager import SessionManager
from location_manager import LocationManager
from player_manager import PlayerManager


@pytest.fixture
def temp_campaign():
    """Create temporary campaign with time effects enabled"""
    temp_dir = tempfile.mkdtemp()
    campaign_dir = Path(temp_dir) / "world-state" / "campaigns" / "test-auto-time"
    campaign_dir.mkdir(parents=True)

    # Active campaign marker
    active_file = Path(temp_dir) / "world-state" / "active-campaign.txt"
    active_file.parent.mkdir(parents=True, exist_ok=True)
    active_file.write_text("test-auto-time")

    # Campaign overview with time effects
    campaign_data = {
        "name": "Test Auto Time",
        "campaign_name": "Test Auto Time",
        "current_character": "Stalker",
        "time_of_day": "Morning",
        "current_date": "1st day",
        "precise_time": "08:00",
        "player_position": {
            "current_location": "Start"
        },
        "campaign_rules": {
            "time_effects": {
                "enabled": True,
                "rules": [
                    {"stat": "hunger", "per_hour": -2},
                    {"stat": "thirst", "per_hour": -3},
                    {"stat": "radiation", "per_hour": -1}
                ]
            }
        }
    }
    (campaign_dir / "campaign-overview.json").write_text(
        json.dumps(campaign_data, indent=2, ensure_ascii=False)
    )

    # Locations with distance_meters
    locations_data = {
        "Start": {
            "position": "Origin",
            "connections": [
                {
                    "to": "Finish",
                    "path": "2km east",
                    "distance_meters": 2000
                }
            ],
            "description": "Starting point"
        },
        "Finish": {
            "position": "Destination",
            "connections": [
                {
                    "to": "Start",
                    "path": "2km west",
                    "distance_meters": 2000
                }
            ],
            "description": "End point"
        }
    }
    (campaign_dir / "locations.json").write_text(
        json.dumps(locations_data, indent=2, ensure_ascii=False)
    )

    # Character with speed and custom stats
    character_data = {
        "name": "Stalker",
        "level": 1,
        "class": "Ranger",
        "race": "Human",
        "hp": {"current": 20, "max": 20},
        "ac": 15,
        "xp": 0,
        "gold": 100,
        "speed_kmh": 4.0,
        "custom_stats": {
            "hunger": {"current": 80, "max": 100, "min": 0},
            "thirst": {"current": 70, "max": 100, "min": 0},
            "radiation": {"current": 20, "max": 500, "min": 0}
        }
    }
    (campaign_dir / "character.json").write_text(
        json.dumps(character_data, indent=2, ensure_ascii=False)
    )

    # Empty files
    for fname in ["npcs.json", "facts.json", "consequences.json", "items.json", "plots.json"]:
        (campaign_dir / fname).write_text("{}")

    (campaign_dir / "session-log.md").write_text("# Session Log\n")

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def test_auto_time_on_move(temp_campaign):
    """Test that moving automatically advances time and updates custom stats"""
    campaign_dir = Path(temp_campaign) / "world-state" / "campaigns" / "test-auto-time"
    session_mgr = SessionManager(str(campaign_dir), require_active_campaign=False)

    # Initial state
    campaign = session_mgr.json_ops.load_json("campaign-overview.json")
    assert campaign['precise_time'] == "08:00"
    assert campaign['time_of_day'] == "Morning"

    character = session_mgr.json_ops.load_json("character.json")
    initial_hunger = character['custom_stats']['hunger']['current']
    initial_thirst = character['custom_stats']['thirst']['current']
    initial_radiation = character['custom_stats']['radiation']['current']

    # Move from Start to Finish (2000m at 4 km/h = 0.5 hours = 30 minutes)
    result = session_mgr.move_party("Finish")

    assert result['previous_location'] == "Start"
    assert result['current_location'] == "Finish"
    assert result['travel_hours'] == 0.5

    # Check time updated
    campaign = session_mgr.json_ops.load_json("campaign-overview.json")
    assert campaign['precise_time'] == "08:30"
    assert campaign['time_of_day'] == "Morning"

    # Check custom stats updated (effects: hunger -2/h, thirst -3/h, radiation -1/h)
    # 0.5h elapsed: hunger -1, thirst -1 (int(-1.5) = -1), radiation -0 (int(-0.5) = 0)
    character = session_mgr.json_ops.load_json("character.json")
    assert character['custom_stats']['hunger']['current'] == initial_hunger - 1  # 80 - 1 = 79
    assert character['custom_stats']['thirst']['current'] == initial_thirst - 1  # 70 - 1 = 69 (int(-1.5) = -1)
    assert character['custom_stats']['radiation']['current'] == initial_radiation  # 20 - 0 = 20 (int(-0.5) = 0)


def test_no_time_change_without_distance(temp_campaign):
    """Test that movement without distance_meters doesn't change time"""
    campaign_dir = Path(temp_campaign) / "world-state" / "campaigns" / "test-auto-time"
    session_mgr = SessionManager(str(campaign_dir), require_active_campaign=False)
    loc_mgr = LocationManager(str(campaign_dir), require_active_campaign=False)

    # Add location without distance
    loc_mgr.add_location("NoDistance", "Somewhere")
    loc_mgr.connect_locations("Start", "NoDistance", "magic portal")

    # Get initial time
    campaign = session_mgr.json_ops.load_json("campaign-overview.json")
    initial_time = campaign['precise_time']

    # Move
    result = session_mgr.move_party("NoDistance")

    assert result['travel_hours'] == 0.0

    # Time should NOT change
    campaign = session_mgr.json_ops.load_json("campaign-overview.json")
    assert campaign['precise_time'] == initial_time


def test_time_of_day_updates(temp_campaign):
    """Test that time_of_day changes based on precise_time"""
    campaign_dir = Path(temp_campaign) / "world-state" / "campaigns" / "test-auto-time"
    session_mgr = SessionManager(str(campaign_dir), require_active_campaign=False)

    # Manually set time to 11:30 (Morning)
    campaign = session_mgr.json_ops.load_json("campaign-overview.json")
    campaign['precise_time'] = "11:30"
    session_mgr.json_ops.save_json("campaign-overview.json", campaign)

    # Move (0.5 hours = 30 min) -> should cross into Day (12:00)
    result = session_mgr.move_party("Finish")

    campaign = session_mgr.json_ops.load_json("campaign-overview.json")
    assert campaign['precise_time'] == "12:00"
    assert campaign['time_of_day'] == "Day"
