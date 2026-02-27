#!/usr/bin/env python3
"""
Tests for encounter engine module.
Uses tmp_path for isolated campaign directories.
"""

import pytest
import json
import sys
from pathlib import Path

# Add PROJECT_ROOT to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MODULE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MODULE_ROOT / "lib"))

from encounter_engine import EncounterEngine


@pytest.fixture
def campaign_dir(tmp_path):
    """Create a temporary campaign directory with minimal setup"""
    campaign = tmp_path / "test-campaign"
    campaign.mkdir()

    # Create campaign-overview.json
    overview = {
        "name": "Test Campaign",
        "campaign_rules": {
            "encounter_system": {
                "enabled": True,
                "min_distance_meters": 300,
                "base_dc": 16,
                "distance_modifier": 2,
                "stat_to_use": "stealth",
                "use_luck": False,
                "time_dc_modifiers": {
                    "Morning": 0,
                    "Day": 0,
                    "Evening": 2,
                    "Night": 4
                }
            }
        },
        "time_of_day": "Day",
        "precise_time": "12:00"
    }
    with open(campaign / "campaign-overview.json", "w") as f:
        json.dump(overview, f)

    # Create character.json
    character = {
        "name": "Test Hero",
        "abilities": {"dex": 14},
        "skills": {"stealth": 5},
        "custom_stats": {
            "awareness": {"current": 70, "min": 0, "max": 100}
        }
    }
    with open(campaign / "character.json", "w") as f:
        json.dump(character, f)

    # Create locations.json
    locations = {
        "Village": {
            "coordinates": {"x": 0, "y": 0},
            "connections": []
        },
        "Ruins": {
            "coordinates": {"x": 2000, "y": 0},
            "connections": []
        }
    }
    with open(campaign / "locations.json", "w") as f:
        json.dump(locations, f)

    return campaign


def test_is_enabled(campaign_dir):
    """Test checking if encounter system is enabled"""
    engine = EncounterEngine(str(campaign_dir))
    assert engine.is_enabled() is True


def test_disabled_system(campaign_dir):
    """Test system skip when disabled"""
    # Disable system
    overview_path = campaign_dir / "campaign-overview.json"
    with open(overview_path, "r") as f:
        overview = json.load(f)
    overview['campaign_rules']['encounter_system']['enabled'] = False
    with open(overview_path, "w") as f:
        json.dump(overview, f)

    engine = EncounterEngine(str(campaign_dir))
    assert engine.is_enabled() is False


def test_calculate_segments(campaign_dir):
    """Test segment calculation based on distance"""
    engine = EncounterEngine(str(campaign_dir))

    assert engine.calculate_segments(500) == 1    # < 1km
    assert engine.calculate_segments(1500) == 1   # 1-3km
    assert engine.calculate_segments(4000) == 2   # 3-6km
    assert engine.calculate_segments(7000) == 3   # > 6km


def test_calculate_dc(campaign_dir):
    """Test DC calculation with distance and time modifiers"""
    engine = EncounterEngine(str(campaign_dir))

    # Day (no time modifier)
    dc_day = engine.calculate_dc(1.5, "Day")
    assert dc_day == 16 + int(1.5 * 2) + 0  # base 16 + 3 + 0 = 19

    # Night (+4 modifier)
    dc_night = engine.calculate_dc(1.5, "Night")
    assert dc_night == 16 + int(1.5 * 2) + 4  # base 16 + 3 + 4 = 23

    # DC capped at 30
    dc_extreme = engine.calculate_dc(100.0, "Night")
    assert dc_extreme == 30


def test_get_character_modifier_skill(campaign_dir):
    """Test character modifier from D&D skill"""
    # Change config to use skill:stealth
    overview_path = campaign_dir / "campaign-overview.json"
    with open(overview_path, "r") as f:
        overview = json.load(f)
    overview['campaign_rules']['encounter_system']['stat_to_use'] = 'skill:stealth'
    with open(overview_path, "w") as f:
        json.dump(overview, f)

    engine = EncounterEngine(str(campaign_dir))
    modifier = engine.get_character_modifier()
    assert modifier == 5  # character has stealth: 5


def test_get_character_modifier_custom_stat(campaign_dir):
    """Test character modifier from custom stat"""
    # Change config to use custom:awareness
    overview_path = campaign_dir / "campaign-overview.json"
    with open(overview_path, "r") as f:
        overview = json.load(f)
    overview['campaign_rules']['encounter_system']['stat_to_use'] = 'custom:awareness'
    with open(overview_path, "w") as f:
        json.dump(overview, f)

    engine = EncounterEngine(str(campaign_dir))
    modifier = engine.get_character_modifier()
    # awareness: 70 → (70 - 50) // 10 = 2
    assert modifier == 2


def test_get_character_modifier_ability(campaign_dir):
    """Test character modifier from D&D ability"""
    overview_path = campaign_dir / "campaign-overview.json"
    with open(overview_path, "r") as f:
        overview = json.load(f)
    overview['campaign_rules']['encounter_system']['stat_to_use'] = 'dex'
    with open(overview_path, "w") as f:
        json.dump(overview, f)

    engine = EncounterEngine(str(campaign_dir))
    modifier = engine.get_character_modifier()
    # dex: 14 → (14 - 10) // 2 = 2
    assert modifier == 2


def test_roll_encounter_nature(campaign_dir):
    """Test encounter nature roll produces valid categories"""
    engine = EncounterEngine(str(campaign_dir))

    # Roll multiple times to check category assignment
    for _ in range(10):
        nature = engine.roll_encounter_nature()
        assert 'roll' in nature
        assert 'category' in nature
        assert nature['category'] in ["Dangerous", "Neutral", "Beneficial", "Special"]

        # Check category logic (based on roll)
        if nature['roll'] <= 5:
            assert nature['category'] == "Dangerous"
        elif nature['roll'] <= 10:
            assert nature['category'] == "Neutral"
        elif nature['roll'] <= 15:
            assert nature['category'] == "Beneficial"
        else:
            assert nature['category'] == "Special"


def test_check_journey_skipped_too_short(campaign_dir):
    """Test journey skip for distances below minimum"""
    engine = EncounterEngine(str(campaign_dir))

    journey = engine.check_journey("Village", "Ruins", 200, "open")

    assert journey['skipped'] is True
    assert 'Too short' in journey['reason']
    assert journey['total_encounters'] == 0


def test_check_journey_basic(campaign_dir):
    """Test basic journey with segments and checks"""
    engine = EncounterEngine(str(campaign_dir))

    journey = engine.check_journey("Village", "Ruins", 2000, "open")

    assert journey['skipped'] is False
    assert journey['total_distance_m'] == 2000
    assert len(journey['waypoints']) > 0

    # Check waypoint structure
    for wp in journey['waypoints']:
        assert 'segment' in wp
        assert 'check' in wp
        assert 'distance_traveled_m' in wp
        assert 'current_time' in wp
        assert 'can_turn_back' in wp


def test_waypoint_creation(campaign_dir):
    """Test waypoint location creation"""
    engine = EncounterEngine(str(campaign_dir))

    journey = {
        'total_distance_m': 2000,
        'terrain': 'forest'
    }

    waypoint_data = {
        'segment': 1,
        'check': {'total_segments': 2}
    }

    waypoint_name = engine.create_waypoint_location(
        "Village", "Ruins", waypoint_data, journey
    )

    # Check waypoint was created in locations.json
    locations_path = campaign_dir / "locations.json"
    with open(locations_path, "r") as f:
        locations = json.load(f)

    assert waypoint_name in locations
    waypoint = locations[waypoint_name]
    assert waypoint['is_waypoint'] is True
    assert waypoint['original_journey']['from'] == "Village"
    assert waypoint['original_journey']['to'] == "Ruins"


def test_waypoint_cleanup(campaign_dir):
    """Test waypoint removal after cleanup"""
    engine = EncounterEngine(str(campaign_dir))

    # Create waypoint
    journey = {'total_distance_m': 2000, 'terrain': 'forest'}
    waypoint_data = {'segment': 1, 'check': {'total_segments': 2}}
    waypoint_name = engine.create_waypoint_location(
        "Village", "Ruins", waypoint_data, journey
    )

    # Verify it exists
    assert engine.is_waypoint(waypoint_name) is True

    # Cleanup
    engine.cleanup_waypoint(waypoint_name)

    # Verify it's gone
    assert engine.is_waypoint(waypoint_name) is False


def test_is_waypoint(campaign_dir):
    """Test waypoint detection"""
    engine = EncounterEngine(str(campaign_dir))

    # Regular location is not a waypoint
    assert engine.is_waypoint("Village") is False

    # Create waypoint
    journey = {'total_distance_m': 2000, 'terrain': 'forest'}
    waypoint_data = {'segment': 1, 'check': {'total_segments': 2}}
    waypoint_name = engine.create_waypoint_location(
        "Village", "Ruins", waypoint_data, journey
    )

    # Now it is
    assert engine.is_waypoint(waypoint_name) is True


def test_get_waypoint_options(campaign_dir):
    """Test getting waypoint travel options"""
    engine = EncounterEngine(str(campaign_dir))

    journey = {'total_distance_m': 2000, 'terrain': 'forest'}
    waypoint_data = {'segment': 1, 'check': {'total_segments': 2}}
    waypoint_name = engine.create_waypoint_location(
        "Village", "Ruins", waypoint_data, journey
    )

    options = engine.get_waypoint_options(waypoint_name)

    assert options is not None
    assert 'forward' in options
    assert 'back' in options
    assert options['forward']['to'] == "Ruins"
    assert options['back']['to'] == "Village"


def test_format_journey_output_skipped(campaign_dir):
    """Test journey output formatting for skipped journey"""
    engine = EncounterEngine(str(campaign_dir))

    journey = {
        'skipped': True,
        'reason': 'Too short (< 300m)',
        'total_distance_m': 200,
        'total_time_min': 3,
        'from_location': 'Village',
        'to_location': 'Ruins'
    }

    output = engine.format_journey_output(journey)
    assert "Too short" in output
    assert "Village" in output
    assert "Ruins" in output


def test_format_journey_output_full(campaign_dir):
    """Test journey output formatting for full journey"""
    engine = EncounterEngine(str(campaign_dir))

    journey = engine.check_journey("Village", "Ruins", 2000, "forest")
    output = engine.format_journey_output(journey)

    assert "JOURNEY" in output
    assert "Village" in output
    assert "Ruins" in output
    assert "2000m" in output or "2.0km" in output
