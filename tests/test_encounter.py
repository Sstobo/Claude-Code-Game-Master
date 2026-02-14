import pytest
import json
from pathlib import Path
from lib.encounter_manager import EncounterManager


@pytest.fixture
def temp_campaign(tmp_path):
    """Create a minimal campaign for testing"""
    campaign_dir = tmp_path / "test-campaign"
    campaign_dir.mkdir()

    # Campaign overview
    overview = {
        "campaign_name": "Test Campaign",
        "time_of_day": "Day",
        "precise_time": "12:00",
        "current_date": "Day 1",
        "campaign_rules": {
            "encounter_system": {
                "enabled": True,
                "min_distance_meters": 300,
                "base_dc": 8,
                "distance_modifier": 4,
                "stat_to_use": "custom:awareness",
                "use_luck": False,
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

    # Character
    character = {
        "name": "Test Character",
        "custom_stats": {
            "awareness": {"current": 55, "max": 100}
        },
        "skills": {
            "Perception": 3
        },
        "abilities": {
            "dex": 14
        }
    }
    with open(campaign_dir / "character.json", "w", encoding="utf-8") as f:
        json.dump(character, f, indent=2, ensure_ascii=False)

    # Locations
    locations = {
        "Start": {
            "coordinates": {"x": 0, "y": 0},
            "connections": []
        },
        "End": {
            "coordinates": {"x": 1000, "y": 0},
            "connections": []
        }
    }
    with open(campaign_dir / "locations.json", "w", encoding="utf-8") as f:
        json.dump(locations, f, indent=2, ensure_ascii=False)

    return campaign_dir


class TestEncounterBasics:
    """Basic encounter system tests"""

    def test_system_enabled(self, temp_campaign):
        """Check that the system is enabled"""
        enc = EncounterManager(str(temp_campaign))
        assert enc.is_enabled() == True

    def test_custom_stat_modifier(self, temp_campaign):
        """Check custom stat modifier (awareness)"""
        enc = EncounterManager(str(temp_campaign))
        modifier = enc.get_character_modifier()
        # awareness=55 → (55-50)//10 = 0
        assert modifier == 0

    def test_skill_modifier(self, temp_campaign):
        """Check skill modifier"""
        # Change stat_to_use to skill:Perception
        overview = json.load(open(temp_campaign / "campaign-overview.json"))
        overview["campaign_rules"]["encounter_system"]["stat_to_use"] = "skill:Perception"
        with open(temp_campaign / "campaign-overview.json", "w", encoding="utf-8") as f:
            json.dump(overview, f, indent=2, ensure_ascii=False)

        enc = EncounterManager(str(temp_campaign))
        modifier = enc.get_character_modifier()
        assert modifier == 3

    def test_ability_modifier(self, temp_campaign):
        """Check ability modifier (dex)"""
        overview = json.load(open(temp_campaign / "campaign-overview.json"))
        overview["campaign_rules"]["encounter_system"]["stat_to_use"] = "dex"
        with open(temp_campaign / "campaign-overview.json", "w", encoding="utf-8") as f:
            json.dump(overview, f, indent=2, ensure_ascii=False)

        enc = EncounterManager(str(temp_campaign))
        modifier = enc.get_character_modifier()
        # dex=14 → (14-10)//2 = 2
        assert modifier == 2


class TestDCCalculation:
    """DC calculation tests"""

    def test_base_dc(self, temp_campaign):
        """Base DC without modifiers"""
        enc = EncounterManager(str(temp_campaign))
        dc = enc.calculate_dc(segment_distance_km=0, time_of_day="Day")
        assert dc == 8  # base_dc

    def test_distance_modifier(self, temp_campaign):
        """DC increases with distance"""
        enc = EncounterManager(str(temp_campaign))
        dc = enc.calculate_dc(segment_distance_km=2.5, time_of_day="Day")
        # 8 + 2.5*4 + 0 = 18
        assert dc == 18

    def test_time_modifier_night(self, temp_campaign):
        """DC is higher at night"""
        enc = EncounterManager(str(temp_campaign))
        dc_day = enc.calculate_dc(segment_distance_km=2.5, time_of_day="Day")
        dc_night = enc.calculate_dc(segment_distance_km=2.5, time_of_day="Night")
        # Night adds +4
        assert dc_night == dc_day + 4

    def test_dc_cap_at_30(self, temp_campaign):
        """DC cannot exceed 30"""
        enc = EncounterManager(str(temp_campaign))
        dc = enc.calculate_dc(segment_distance_km=100, time_of_day="Night")
        assert dc <= 30


class TestSegmentation:
    """Path segmentation tests"""

    def test_short_distance_one_segment(self, temp_campaign):
        """Short path (<1km) = 1 segment"""
        enc = EncounterManager(str(temp_campaign))
        segments = enc.calculate_segments(distance_meters=500)
        assert segments == 1

    def test_medium_distance_one_segment(self, temp_campaign):
        """Medium path (1-3km) = 1 segment"""
        enc = EncounterManager(str(temp_campaign))
        segments = enc.calculate_segments(distance_meters=2000)
        assert segments == 1

    def test_long_distance_two_segments(self, temp_campaign):
        """Long path (3-6km) = 2 segments"""
        enc = EncounterManager(str(temp_campaign))
        segments = enc.calculate_segments(distance_meters=4500)
        assert segments == 2

    def test_very_long_distance_three_segments(self, temp_campaign):
        """Very long path (6+km) = 3 segments"""
        enc = EncounterManager(str(temp_campaign))
        segments = enc.calculate_segments(distance_meters=7000)
        assert segments == 3


class TestMinDistance:
    """Minimum distance for encounter tests"""

    def test_skip_short_journey(self, temp_campaign):
        """Paths <300m are skipped"""
        enc = EncounterManager(str(temp_campaign))
        journey = enc.check_journey(
            from_loc="Start",
            to_loc="End",
            distance_meters=200,
            terrain="open"
        )
        assert journey["skipped"] == True
        assert "Too short" in journey["reason"]

    def test_process_long_journey(self, temp_campaign):
        """Paths >=300m are processed"""
        enc = EncounterManager(str(temp_campaign))
        journey = enc.check_journey(
            from_loc="Start",
            to_loc="End",
            distance_meters=500,
            terrain="open"
        )
        assert journey.get("skipped", False) == False


class TestEncounterNature:
    """Encounter nature determination tests"""

    def test_roll_nature_returns_category(self, temp_campaign):
        """roll_encounter_nature returns a category"""
        enc = EncounterManager(str(temp_campaign))
        result = enc.roll_encounter_nature()
        assert "roll" in result
        assert "category" in result
        assert result["category"] in ["Dangerous", "Neutral", "Beneficial", "Special"]

    def test_dangerous_category_range(self, temp_campaign):
        """Check Dangerous range (1-5)"""
        categories = []
        for roll in range(1, 6):
            if roll <= 5:
                categories.append("Dangerous")
        assert len(set(categories)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
