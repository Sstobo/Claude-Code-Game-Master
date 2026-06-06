"""Tests for item-correctness: cursed flag, type taxonomy, value field."""

import json
from lib.item_fixup import fix_cursed, fix_type, fix_value, fix_items, run_fixup


def test_lore_curse_without_mechanical_penalty_is_cleared():
    # Scavenger-crossbow case: cursed lore, but mechanics are pure upside.
    item = {"cursed": True, "mechanics": "Scales damage with party size; female-only wielder."}
    assert fix_cursed(item) is True
    assert item["cursed"] is False


def test_real_mechanical_penalty_keeps_cursed():
    item = {"cursed": True, "mechanics": "You take 1d6 damage each turn; cannot be removed."}
    assert fix_cursed(item) is False
    assert item["cursed"] is True


def test_wondrous_reclassified_by_keyword():
    key = {"type": "wondrous", "name": "Steam Engineer's Key", "description": "opens the engine"}
    portal = {"type": "wondrous", "name": "Subspace Portal", "description": "a portal device"}
    box = {"type": "wondrous", "name": "Platinum Big Daddy Box", "description": "a loot box"}
    coupon = {"type": "wondrous", "name": "PVP Coupon", "description": "a voucher"}
    fix_type(key); fix_type(portal); fix_type(box); fix_type(coupon)
    assert key["type"] == "key"
    assert portal["type"] == "portal"
    assert box["type"] == "lootbox"
    assert coupon["type"] == "coupon"


def test_known_type_not_touched():
    item = {"type": "weapon", "name": "Sword"}
    assert fix_type(item) is False
    assert item["type"] == "weapon"


def test_non_price_value_moved_to_mechanics_and_nulled():
    item = {"value": "contains 3 potions and a gold ring", "mechanics": ""}
    assert fix_value(item) is True
    assert item["value"] == ""
    assert "Contents/notes" in item["mechanics"]


def test_real_price_kept():
    item = {"value": "50 gp"}
    assert fix_value(item) is False
    assert item["value"] == "50 gp"


def test_run_fixup_writes(tmp_path):
    (tmp_path / "items.json").write_text(json.dumps({
        "Crossbow": {"cursed": True, "type": "weapon", "mechanics": "party-scaling upside"},
        "Big Box": {"type": "wondrous", "name": "Gold Box", "description": "a loot box"},
    }))
    r = run_fixup(str(tmp_path))
    saved = json.loads((tmp_path / "items.json").read_text())
    assert saved["Crossbow"]["cursed"] is False
    assert saved["Big Box"]["type"] == "lootbox"
    assert "Crossbow" in r["cursed_cleared"]
