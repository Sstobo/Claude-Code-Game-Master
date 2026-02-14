import pytest
import json
from lib.time_manager import TimeManager


class TestCustomStats:
    """Custom stats tests"""

    def test_custom_stats_exist(self, stalker_campaign):
        """Check that custom stats load correctly"""
        char = json.load(open(stalker_campaign / "character.json"))
        assert "custom_stats" in char
        assert "hunger" in char["custom_stats"]
        assert "thirst" in char["custom_stats"]

    def test_custom_stat_structure(self, stalker_campaign):
        """Check custom_stats structure"""
        char = json.load(open(stalker_campaign / "character.json"))
        hunger = char["custom_stats"]["hunger"]
        assert "current" in hunger
        assert "max" in hunger
        assert hunger["current"] <= hunger["max"]


class TestTimeEffects:
    """Time effects on stats tests"""

    def test_time_effects_enabled(self, stalker_campaign):
        """Check that time_effects are enabled"""
        overview = json.load(open(stalker_campaign / "campaign-overview.json"))
        time_effects = overview["campaign_rules"]["time_effects"]
        assert time_effects["enabled"] == True

    def test_hunger_decreases_over_time(self, stalker_campaign):
        """Hunger decreases over time"""
        time_mgr = TimeManager(str(stalker_campaign), require_active_campaign=False)

        # Initial state
        char_before = json.load(open(stalker_campaign / "character.json"))
        hunger_before = char_before["custom_stats"]["hunger"]["current"]

        # 5 hours pass
        time_mgr.add_time_hours(5)

        # Check result
        char_after = json.load(open(stalker_campaign / "character.json"))
        hunger_after = char_after["custom_stats"]["hunger"]["current"]

        # Hunger should decrease: 80 - (5 * 2) = 70
        assert hunger_after == hunger_before - 10

    def test_thirst_decreases_faster_than_hunger(self, stalker_campaign):
        """Thirst decreases faster than hunger"""
        time_mgr = TimeManager(str(stalker_campaign), require_active_campaign=False)

        char_before = json.load(open(stalker_campaign / "character.json"))
        hunger_before = char_before["custom_stats"]["hunger"]["current"]
        thirst_before = char_before["custom_stats"]["thirst"]["current"]

        # 10 hours
        time_mgr.add_time_hours(10)

        char_after = json.load(open(stalker_campaign / "character.json"))
        hunger_after = char_after["custom_stats"]["hunger"]["current"]
        thirst_after = char_after["custom_stats"]["thirst"]["current"]

        hunger_delta = hunger_before - hunger_after
        thirst_delta = thirst_before - thirst_after

        # Thirst (-3/h) should decrease faster than hunger (-2/h)
        assert thirst_delta > hunger_delta

    def test_radiation_decreases_naturally(self, stalker_campaign):
        """Radiation naturally decays"""
        # Set initial radiation
        char = json.load(open(stalker_campaign / "character.json"))
        char["custom_stats"]["radiation"]["current"] = 100
        with open(stalker_campaign / "character.json", "w", encoding="utf-8") as f:
            json.dump(char, f, indent=2, ensure_ascii=False)

        time_mgr = TimeManager(str(stalker_campaign), require_active_campaign=False)
        time_mgr.add_time_hours(10)

        char_after = json.load(open(stalker_campaign / "character.json"))
        radiation_after = char_after["custom_stats"]["radiation"]["current"]

        # 100 - (10 * 1) = 90
        assert radiation_after == 90

    def test_stats_clamp_at_min(self, stalker_campaign):
        """Stats cannot drop below minimum"""
        # Set low hunger
        char = json.load(open(stalker_campaign / "character.json"))
        char["custom_stats"]["hunger"]["current"] = 5
        with open(stalker_campaign / "character.json", "w", encoding="utf-8") as f:
            json.dump(char, f, indent=2, ensure_ascii=False)

        time_mgr = TimeManager(str(stalker_campaign), require_active_campaign=False)
        time_mgr.add_time_hours(10)  # Should subtract 20, but clamps at 0

        char_after = json.load(open(stalker_campaign / "character.json"))
        hunger_after = char_after["custom_stats"]["hunger"]["current"]

        assert hunger_after == 0

    def test_stats_clamp_at_max(self, stalker_campaign):
        """Stats cannot exceed maximum"""
        char = json.load(open(stalker_campaign / "character.json"))
        char["custom_stats"]["hunger"]["current"] = 95
        with open(stalker_campaign / "character.json", "w", encoding="utf-8") as f:
            json.dump(char, f, indent=2, ensure_ascii=False)

        # Use player_manager to add (it should clamp)
        from lib.player_manager import PlayerManager
        player_mgr = PlayerManager(str(stalker_campaign), require_active_campaign=False)
        player_mgr.modify_custom_stat(stat="hunger", amount=+20)  # 95 + 20 = 115, but clamps at 100

        char_after = json.load(open(stalker_campaign / "character.json"))
        hunger_after = char_after["custom_stats"]["hunger"]["current"]

        assert hunger_after == 100


class TestPreciseTime:
    """Precise time tests"""

    def test_precise_time_format(self, stalker_campaign):
        """Check HH:MM format"""
        overview = json.load(open(stalker_campaign / "campaign-overview.json"))
        precise_time = overview["precise_time"]
        assert ":" in precise_time
        hours, minutes = precise_time.split(":")
        assert 0 <= int(hours) < 24
        assert 0 <= int(minutes) < 60

    def test_time_advances_correctly(self, stalker_campaign):
        """Time advances correctly"""
        time_mgr = TimeManager(str(stalker_campaign), require_active_campaign=False)

        # Was 08:00, add 2.5 hours → 10:30
        time_mgr.add_time_hours(2.5)

        overview = json.load(open(stalker_campaign / "campaign-overview.json"))
        precise_time = overview["precise_time"]

        assert precise_time == "10:30"

    def test_time_wraps_at_midnight(self, stalker_campaign):
        """Time wraps after 24:00"""
        time_mgr = TimeManager(str(stalker_campaign), require_active_campaign=False)

        # Was 08:00, add 20 hours → 04:00 next day
        time_mgr.add_time_hours(20)

        overview = json.load(open(stalker_campaign / "campaign-overview.json"))
        precise_time = overview["precise_time"]
        hours = int(precise_time.split(":")[0])

        assert hours == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
