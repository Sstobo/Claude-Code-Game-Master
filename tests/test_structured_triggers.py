"""Tests for structured-trigger-schema.

Consequences gain optional structured triggers (trigger_type/match/expiry) that
the reactivity engine can fire and expire on, additively — legacy free-text
consequences still load and round-trip unchanged.
"""

import json
from pathlib import Path

from lib.consequence_manager import ConsequenceManager


def _consq_path(dcc_world):
    return Path(dcc_world) / "campaigns" / "dungeon-crawler-carl" / "consequences.json"


def test_add_with_structured_trigger(dcc_world):
    cm = ConsequenceManager(dcc_world)
    cid = cm.add_consequence("Guards search the market", "next day",
                             trigger_type="on_location", match="Market", expiry="day 5")
    assert cid
    data = json.loads(_consq_path(dcc_world).read_text(encoding="utf-8"))
    new = next(c for c in data["active"] if c["id"] == cid)
    assert new["trigger_type"] == "on_location"
    assert new["match"] == "Market"
    assert new["expiry"] == "day 5"
    # free-text trigger + description still preserved
    assert new["trigger"] == "next day"
    assert new["consequence"] == "Guards search the market"


def test_legacy_add_omits_structured_fields(dcc_world):
    cm = ConsequenceManager(dcc_world)
    cid = cm.add_consequence("plain consequence", "someday")
    data = json.loads(_consq_path(dcc_world).read_text(encoding="utf-8"))
    new = next(c for c in data["active"] if c["id"] == cid)
    assert "trigger_type" not in new and "match" not in new and "expiry" not in new


def test_fixture_exercises_all_trigger_types_and_a_legacy(dcc_world):
    data = json.loads(_consq_path(dcc_world).read_text(encoding="utf-8"))
    items = data.get("active", []) + data.get("pending", [])
    types = {c.get("trigger_type") for c in items if c.get("trigger_type")}
    assert {"on_location", "on_npc", "on_time", "on_event"}.issubset(types)
    assert any("trigger_type" not in c for c in items), "expected a legacy free-text consequence too"


def test_existing_consequences_round_trip(dcc_world):
    pending = ConsequenceManager(dcc_world).check_pending()
    assert all("consequence" in c and "trigger" in c for c in pending)


def test_expiry_matches_whole_words_not_substrings(dcc_world):
    # Regression: --expiry "dawn" must not self-archive at a place named Dawnhollow.
    cm = ConsequenceManager(dcc_world)
    cid = cm.add_consequence("ambush at first light", "when dawn comes",
                             trigger_type="on_time", match="dawn", expiry="dawn")
    hollow = {"location": "Dawnhollow", "time": "midnight", "present_npcs": [], "events": []}
    assert not cm._is_expired({"expiry": "dawn"}, hollow)
    still_active = [c["id"] for c in cm.check_pending(hollow, limit=10)] + \
                   [c["id"] for c in cm.check_pending()]
    assert cid in still_active

    at_dawn = {"location": "camp", "time": "dawn", "present_npcs": [], "events": []}
    assert cm._is_expired({"expiry": "dawn"}, at_dawn)
