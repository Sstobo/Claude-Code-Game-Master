
import json

from lib.player_manager import PlayerManager


def make_campaign(tmp_path, overview_extra=None, character=None):
    campaign_dir = tmp_path / "world-state" / "campaigns" / "test-campaign"
    campaign_dir.mkdir(parents=True)
    ws = tmp_path / "world-state"
    (ws / "active-campaign.txt").write_text("test-campaign")

    overview = {
        "campaign_name": "Test Campaign",
        "time_of_day": "Day",
        "current_date": "Day 1",
        "current_character": "Hero",
    }
    if overview_extra:
        overview.update(overview_extra)
    (campaign_dir / "campaign-overview.json").write_text(
        json.dumps(overview, ensure_ascii=False)
    )

    if character is None:
        character = {
            "name": "Hero",
            "level": 1,
            "hp": {"current": 20, "max": 20},
            "gold": 100,
            "xp": 0,
            "equipment": [],
        }
    (campaign_dir / "character.json").write_text(
        json.dumps(character, ensure_ascii=False)
    )

    return str(ws), campaign_dir


class TestModifyHp:
    def test_heal_increases_hp(self, tmp_path):
        ws, camp = make_campaign(tmp_path, character={
            "name": "Hero", "level": 1,
            "hp": {"current": 10, "max": 20},
            "gold": 0, "xp": 0, "equipment": [],
        })
        mgr = PlayerManager(ws)
        result = mgr.modify_hp("Hero", 5)
        assert result["success"] is True
        assert result["current_hp"] == 15

    def test_damage_decreases_hp(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_hp("Hero", -8)
        assert result["success"] is True
        assert result["current_hp"] == 12

    def test_hp_clamps_at_zero(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_hp("Hero", -999)
        assert result["current_hp"] == 0
        assert result["unconscious"] is True

    def test_hp_clamps_at_max(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_hp("Hero", +999)
        assert result["current_hp"] == 20

    def test_hp_persisted_to_file(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        mgr.modify_hp("Hero", -5)
        char = json.loads((camp / "character.json").read_text())
        assert char["hp"]["current"] == 15

    def test_bloodied_flag(self, tmp_path):
        ws, camp = make_campaign(tmp_path, character={
            "name": "Hero", "level": 1,
            "hp": {"current": 20, "max": 20},
            "gold": 0, "xp": 0, "equipment": [],
        })
        mgr = PlayerManager(ws)
        result = mgr.modify_hp("Hero", -16)
        assert result["bloodied"] is True

    def test_auto_detect_name_none(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_hp(None, -3)
        assert result["success"] is True
        assert result["current_hp"] == 17


class TestModifyGold:
    def test_add_gold(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_gold("Hero", 50)
        assert result["current_gold"] == 150

    def test_spend_gold(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_gold("Hero", -30)
        assert result["current_gold"] == 70

    def test_gold_clamps_at_zero_not_negative(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_gold("Hero", -9999)
        assert result["current_gold"] == 0

    def test_gold_show_without_amount(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_gold("Hero")
        assert result["success"] is True
        assert result["gold"] == 100

    def test_gold_persisted(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        mgr.modify_gold("Hero", +25)
        char = json.loads((camp / "character.json").read_text())
        assert char["gold"] == 125


class TestModifyInventory:
    def test_add_item(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_inventory("Hero", "add", "Iron Sword")
        assert result["success"] is True
        assert "Iron Sword" in result["equipment"]

    def test_remove_item(self, tmp_path):
        ws, camp = make_campaign(tmp_path, character={
            "name": "Hero", "level": 1,
            "hp": {"current": 20, "max": 20},
            "gold": 0, "xp": 0,
            "equipment": ["Iron Sword", "Shield"],
        })
        mgr = PlayerManager(ws)
        result = mgr.modify_inventory("Hero", "remove", "Iron Sword")
        assert result["success"] is True
        assert "Iron Sword" not in result["equipment"]
        assert "Shield" in result["equipment"]

    def test_remove_item_partial_match(self, tmp_path):
        ws, camp = make_campaign(tmp_path, character={
            "name": "Hero", "level": 1,
            "hp": {"current": 20, "max": 20},
            "gold": 0, "xp": 0,
            "equipment": ["Iron Sword"],
        })
        mgr = PlayerManager(ws)
        result = mgr.modify_inventory("Hero", "remove", "sword")
        assert result["success"] is True

    def test_remove_nonexistent_item(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.modify_inventory("Hero", "remove", "Nonexistent Item")
        assert result["success"] is False
        assert result.get("error") == "item_not_found"

    def test_list_inventory(self, tmp_path):
        ws, camp = make_campaign(tmp_path, character={
            "name": "Hero", "level": 1,
            "hp": {"current": 20, "max": 20},
            "gold": 0, "xp": 0,
            "equipment": ["Dagger", "Rope"],
        })
        mgr = PlayerManager(ws)
        result = mgr.modify_inventory("Hero", "list")
        assert result["success"] is True
        assert "Dagger" in result["equipment"]

    def test_inventory_persisted(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        mgr.modify_inventory("Hero", "add", "Magic Wand")
        char = json.loads((camp / "character.json").read_text())
        assert "Magic Wand" in char["equipment"]


class TestModifyXp:
    def test_xp_gained(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.award_xp("Hero", 150)
        assert result["success"] is True
        assert result["current_xp"] == 150
        assert result["xp_gained"] == 150

    def test_xp_level_up(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.award_xp("Hero", 300)
        assert result["level_up"] is True
        assert result["new_level"] == 2

    def test_xp_no_level_up_below_threshold(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        result = mgr.award_xp("Hero", 100)
        assert result["level_up"] is False
        assert result["new_level"] == 1

    def test_xp_persisted(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        mgr.award_xp("Hero", 200)
        char = json.loads((camp / "character.json").read_text())
        assert char["xp"]["current"] == 200


class TestGetPlayer:
    def test_get_player_returns_data(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        char = mgr.get_player("Hero")
        assert char is not None
        assert char["name"] == "Hero"

    def test_get_player_none_uses_active(self, tmp_path):
        ws, camp = make_campaign(tmp_path)
        mgr = PlayerManager(ws)
        char = mgr.get_player(None)
        assert char is not None
        assert char["name"] == "Hero"

    def test_get_player_no_active_character_returns_none(self, tmp_path):
        ws, camp = make_campaign(tmp_path, overview_extra={"current_character": None})
        (camp / "character.json").unlink()
        mgr = PlayerManager(ws)
        result = mgr.get_player(None)
        assert result is None
