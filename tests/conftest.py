import pytest
import json
from pathlib import Path


@pytest.fixture
def minimal_campaign(tmp_path):
    """
    Minimal campaign setup for basic tests
    """
    campaign_dir = tmp_path / "minimal-campaign"
    campaign_dir.mkdir()

    overview = {
        "campaign_name": "Minimal Test",
        "time_of_day": "Day",
        "precise_time": "12:00",
        "current_date": "Day 1"
    }
    with open(campaign_dir / "campaign-overview.json", "w", encoding="utf-8") as f:
        json.dump(overview, f, indent=2, ensure_ascii=False)

    return campaign_dir


@pytest.fixture
def stalker_campaign(tmp_path):
    """
    STALKER-like campaign with custom stats and time effects
    """
    campaign_dir = tmp_path / "stalker-campaign"
    campaign_dir.mkdir()

    overview = {
        "campaign_name": "STALKER Test",
        "time_of_day": "Morning",
        "precise_time": "08:00",
        "current_date": "April 15th, 2012",
        "current_character": "Stalker",
        "campaign_rules": {
            "time_effects": {
                "enabled": True,
                "rules": [
                    {"stat": "hunger", "per_hour": -2, "min": 0, "max": 100},
                    {"stat": "thirst", "per_hour": -3, "min": 0, "max": 100},
                    {"stat": "radiation", "per_hour": -1, "min": 0, "max": 500}
                ]
            },
            "encounter_system": {
                "enabled": True,
                "min_distance_meters": 300,
                "base_dc": 8,
                "distance_modifier": 4,
                "stat_to_use": "custom:awareness",
                "time_dc_modifiers": {
                    "Morning": 0,
                    "Day": 0,
                    "Evening": 2,
                    "Night": 4
                }
            }
        }
    }
    with open(campaign_dir / "campaign-overview.json", "w", encoding="utf-8") as f:
        json.dump(overview, f, indent=2, ensure_ascii=False)

    character = {
        "name": "Stalker",
        "speed_kmh": 4,
        "hp": {"current": 25, "max": 25},
        "custom_stats": {
            "hunger": {"current": 80, "max": 100},
            "thirst": {"current": 70, "max": 100},
            "radiation": {"current": 0, "max": 500},
            "awareness": {"current": 55, "max": 100}
        },
        "skills": {
            "Survival": 3,
            "Perception": 3
        },
        "abilities": {
            "dex": 14,
            "wis": 12
        }
    }
    with open(campaign_dir / "character.json", "w", encoding="utf-8") as f:
        json.dump(character, f, indent=2, ensure_ascii=False)

    locations = {
        "Cordon": {
            "coordinates": {"x": 0, "y": 0},
            "diameter_meters": 100,
            "connections": [
                {
                    "to": "Junkyard",
                    "distance_meters": 2000,
                    "bearing": 0,
                    "terrain": "open"
                }
            ]
        },
        "Junkyard": {
            "coordinates": {"x": 0, "y": 2000},
            "diameter_meters": 300,
            "connections": [
                {
                    "to": "Cordon",
                    "distance_meters": 2000,
                    "bearing": 180,
                    "terrain": "open"
                }
            ]
        }
    }
    with open(campaign_dir / "locations.json", "w", encoding="utf-8") as f:
        json.dump(locations, f, indent=2, ensure_ascii=False)

    return campaign_dir
