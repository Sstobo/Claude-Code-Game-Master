#!/usr/bin/env python3
"""
Tests for Firearms Combat Resolver
Uses isolated fake campaigns with tmp_path fixture
"""

import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from firearms_resolver import FirearmsCombatResolver, format_combat_output


@pytest.fixture
def fake_campaign(tmp_path):
    """Create a minimal fake campaign with firearms system"""
    world_state = tmp_path / "world-state"
    campaigns_dir = world_state / "campaigns"
    campaign_dir = campaigns_dir / "test-campaign"
    campaign_dir.mkdir(parents=True)

    active_campaign_file = world_state / "active-campaign.txt"
    active_campaign_file.write_text("test-campaign")

    character_data = {
        "name": "Test Stalker",
        "class": "Сталкер",
        "subclass": "Стрелок",
        "level": 5,
        "hp": {"current": 40, "max": 40},
        "abilities": {"str": 12, "dex": 16, "con": 14, "int": 10, "wis": 12, "cha": 8},
        "proficiency_bonus": 3,
        "xp": {"current": 1000, "next_level": 2000}
    }

    campaign_overview = {
        "name": "Test Campaign",
        "current_character": "Test Stalker",
        "current_location": "Test Zone",
        "current_time": "Day",
        "campaign_rules": {
            "firearms_system": {
                "weapons": {
                    "AK-74": {
                        "damage": "2d8+2",
                        "pen": 6,
                        "rpm": 650,
                        "ammo_type": "5.45x39mm"
                    }
                },
                "fire_modes": {
                    "full_auto": {
                        "penalty_per_shot": -2,
                        "penalty_per_shot_sharpshooter": -1
                    }
                }
            }
        }
    }

    (campaign_dir / "character.json").write_text(json.dumps(character_data, indent=2))
    (campaign_dir / "campaign-overview.json").write_text(json.dumps(campaign_overview, indent=2))

    return world_state


def test_resolver_initialization(fake_campaign):
    """Test that resolver loads campaign correctly"""
    resolver = FirearmsCombatResolver(str(fake_campaign))

    assert resolver.character["name"] == "Test Stalker"
    assert resolver.character["subclass"] == "Стрелок"
    assert resolver.campaign_rules["firearms_system"]["weapons"]["AK-74"]["damage"] == "2d8+2"


def test_attack_bonus_calculation(fake_campaign):
    """Test attack bonus calculation with sharpshooter subclass"""
    resolver = FirearmsCombatResolver(str(fake_campaign))

    attack_bonus = resolver._get_attack_bonus()
    dex_mod = (16 - 10) // 2
    prof_bonus = 3
    subclass_bonus = 2

    expected = dex_mod + prof_bonus + subclass_bonus
    assert attack_bonus == expected


def test_is_sharpshooter(fake_campaign):
    """Test sharpshooter detection"""
    resolver = FirearmsCombatResolver(str(fake_campaign))
    assert resolver._is_sharpshooter() is True


def test_rpm_calculation(fake_campaign):
    """Test rounds-per-D&D-round calculation"""
    resolver = FirearmsCombatResolver(str(fake_campaign))

    ak74_rpm = 650
    rounds_per_6_seconds = resolver._calculate_rounds_per_dnd_round(ak74_rpm)

    expected = int((650 / 60) * 6)
    assert rounds_per_6_seconds == expected


def test_pen_vs_prot_scaling(fake_campaign):
    """Test penetration vs protection damage scaling"""
    resolver = FirearmsCombatResolver(str(fake_campaign))

    assert resolver._apply_pen_vs_prot(100, pen=10, prot=5) == 100
    assert resolver._apply_pen_vs_prot(100, pen=5, prot=12) == 25
    assert resolver._apply_pen_vs_prot(100, pen=6, prot=8) == 50


def test_full_auto_combat_basic(fake_campaign):
    """Test basic full-auto combat resolution"""
    resolver = FirearmsCombatResolver(str(fake_campaign))

    targets = [
        {"name": "Snork", "ac": 12, "hp": 15, "prot": 2}
    ]

    result = resolver.resolve_full_auto("AK-74", ammo_available=10, targets=targets)

    assert result["weapon"] == "AK-74"
    assert result["shots_fired"] == 10
    assert result["ammo_remaining"] == 0
    assert result["base_attack"] > 0
    assert result["is_sharpshooter"] is True
    assert len(result["targets"]) == 1


def test_full_auto_multi_target(fake_campaign):
    """Test full-auto combat with multiple targets"""
    resolver = FirearmsCombatResolver(str(fake_campaign))

    targets = [
        {"name": "Snork A", "ac": 12, "hp": 15, "prot": 2},
        {"name": "Snork B", "ac": 12, "hp": 15, "prot": 2},
        {"name": "Snork C", "ac": 12, "hp": 15, "prot": 2}
    ]

    result = resolver.resolve_full_auto("AK-74", ammo_available=30, targets=targets)

    assert result["shots_fired"] == 30
    assert len(result["targets"]) == 3

    total_shots = sum(t["shots"] for t in result["targets"])
    assert total_shots == 30


def test_combat_output_formatting(fake_campaign):
    """Test combat result output formatting"""
    resolver = FirearmsCombatResolver(str(fake_campaign))

    targets = [
        {"name": "Snork", "ac": 12, "hp": 15, "prot": 2}
    ]

    result = resolver.resolve_full_auto("AK-74", ammo_available=5, targets=targets)
    output = format_combat_output(result)

    assert "FIREARMS COMBAT RESOLVER" in output
    assert "AK-74" in output
    assert "Snork" in output
    assert "XP Gained:" in output


def test_character_update_after_combat(fake_campaign):
    """Test character XP update after combat"""
    resolver = FirearmsCombatResolver(str(fake_campaign))

    initial_xp = resolver.character["xp"]["current"]

    targets = [
        {"name": "Snork", "ac": 12, "hp": 1, "prot": 0}
    ]

    result = resolver.resolve_full_auto("AK-74", ammo_available=5, targets=targets)

    if result["enemies_killed"] > 0:
        resolver.update_character_after_combat(result["shots_fired"], result["total_xp"])

        updated_char = resolver.player_mgr.get_player("Test Stalker")
        assert updated_char["xp"]["current"] > initial_xp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
