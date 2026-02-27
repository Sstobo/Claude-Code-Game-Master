import pytest
import json
from pathlib import Path
from lib.time_manager import TimeManager


def make_world_state(tmp_path, campaign_dir: Path) -> Path:
    """Wrap a campaign dir in the world-state/campaigns/<name>/ structure
    that CampaignManager expects, then return the world-state root."""
    ws = tmp_path / "world-state"
    campaigns = ws / "campaigns" / "test-campaign"
    campaigns.mkdir(parents=True)
    (ws / "active-campaign.txt").write_text("test-campaign")

    for fname in campaign_dir.iterdir():
        if fname.is_file():
            (campaigns / fname.name).write_bytes(fname.read_bytes())

    return ws


class TestCustomStats:
    """Custom stats structure tests (no TimeManager needed)"""

    def test_custom_stats_exist(self, stalker_campaign):
        char = json.loads((stalker_campaign / "character.json").read_text())
        assert "custom_stats" in char
        assert "hunger" in char["custom_stats"]
        assert "thirst" in char["custom_stats"]

    def test_custom_stat_structure(self, stalker_campaign):
        char = json.loads((stalker_campaign / "character.json").read_text())
        hunger = char["custom_stats"]["hunger"]
        assert "current" in hunger
        assert "max" in hunger
        assert hunger["current"] <= hunger["max"]


class TestTimeEffectsConfig:
    """Verify time_effects config in campaign_rules (no TimeManager needed)"""

    def test_time_effects_enabled(self, stalker_campaign):
        overview = json.loads((stalker_campaign / "campaign-overview.json").read_text())
        time_effects = overview["campaign_rules"]["time_effects"]
        assert time_effects["enabled"] is True

    def test_time_effects_rules_present(self, stalker_campaign):
        overview = json.loads((stalker_campaign / "campaign-overview.json").read_text())
        rules = overview["campaign_rules"]["time_effects"]["rules"]
        assert len(rules) > 0
        stats = [r["stat"] for r in rules]
        assert "hunger" in stats
        assert "thirst" in stats

    def test_thirst_drains_faster_than_hunger(self, stalker_campaign):
        overview = json.loads((stalker_campaign / "campaign-overview.json").read_text())
        rules = overview["campaign_rules"]["time_effects"]["rules"]
        by_stat = {r["stat"]: r for r in rules}
        hunger_rate = abs(by_stat["hunger"]["per_hour"])
        thirst_rate = abs(by_stat["thirst"]["per_hour"])
        assert thirst_rate > hunger_rate


class TestTimeManagerUpdateTime:
    """TimeManager.update_time() and get_time() tests"""

    def test_update_time_changes_time_of_day(self, stalker_campaign, tmp_path):
        ws = make_world_state(tmp_path, stalker_campaign)
        mgr = TimeManager(str(ws))
        result = mgr.update_time("Night", "April 15th, 2012")
        assert isinstance(result, dict) and result['elapsed'] == 0.0
        data = json.loads((ws / "campaigns" / "test-campaign" / "campaign-overview.json").read_text())
        assert data["time_of_day"] == "Night"

    def test_update_time_changes_date(self, stalker_campaign, tmp_path):
        ws = make_world_state(tmp_path, stalker_campaign)
        mgr = TimeManager(str(ws))
        mgr.update_time("Evening", "April 16th, 2012")
        data = json.loads((ws / "campaigns" / "test-campaign" / "campaign-overview.json").read_text())
        assert data["current_date"] == "April 16th, 2012"

    def test_get_time_returns_current_values(self, stalker_campaign, tmp_path):
        ws = make_world_state(tmp_path, stalker_campaign)
        mgr = TimeManager(str(ws))
        time_info = mgr.get_time()
        assert "time_of_day" in time_info
        assert "current_date" in time_info
        assert time_info["time_of_day"] == "Morning"
        assert time_info["current_date"] == "April 15th, 2012"

    def test_get_time_reflects_update(self, stalker_campaign, tmp_path):
        ws = make_world_state(tmp_path, stalker_campaign)
        mgr = TimeManager(str(ws))
        mgr.update_time("Dusk", "Day 2")
        time_info = mgr.get_time()
        assert time_info["time_of_day"] == "Dusk"
        assert time_info["current_date"] == "Day 2"

    def test_update_preserves_other_fields(self, stalker_campaign, tmp_path):
        ws = make_world_state(tmp_path, stalker_campaign)
        mgr = TimeManager(str(ws))
        mgr.update_time("Day", "April 15th, 2012")
        data = json.loads((ws / "campaigns" / "test-campaign" / "campaign-overview.json").read_text())
        assert "campaign_rules" in data
        assert "campaign_name" in data

    def test_no_active_campaign_raises(self, tmp_path):
        ws = tmp_path / "world-state"
        ws.mkdir()
        (ws / "campaigns").mkdir()
        with pytest.raises(RuntimeError, match="No active campaign"):
            TimeManager(str(ws))


class TestPreciseTime:
    """precise_time field in campaign-overview.json"""

    def test_precise_time_format(self, stalker_campaign):
        overview = json.loads((stalker_campaign / "campaign-overview.json").read_text())
        precise_time = overview["precise_time"]
        assert ":" in precise_time
        hours, minutes = precise_time.split(":")
        assert 0 <= int(hours) < 24
        assert 0 <= int(minutes) < 60

    def test_precise_time_initial_value(self, stalker_campaign):
        overview = json.loads((stalker_campaign / "campaign-overview.json").read_text())
        assert overview["precise_time"] == "08:00"

    def test_minimal_campaign_has_precise_time(self, minimal_campaign):
        overview = json.loads((minimal_campaign / "campaign-overview.json").read_text())
        assert "precise_time" in overview
        assert overview["precise_time"] == "12:00"
