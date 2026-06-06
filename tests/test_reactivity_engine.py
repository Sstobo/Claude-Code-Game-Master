"""Tests for reactivity-engine.

check_pending(world_state) evaluates triggers against the scene and returns only
the consequences that FIRE (annotated with a match_reason, capped, sorted),
auto-archiving expired ones. check_pending() with no args stays the legacy
raw-active accessor.
"""

import json
from pathlib import Path

from lib.consequence_manager import ConsequenceManager


def _consq_path(dcc_world):
    return Path(dcc_world) / "campaigns" / "dungeon-crawler-carl" / "consequences.json"


def test_legacy_accessor_returns_active_list(dcc_world):
    pending = ConsequenceManager(dcc_world).check_pending()
    assert isinstance(pending, list) and len(pending) == 3  # fixture active count


def test_on_location_fires_with_reason(dcc_world):
    fired = ConsequenceManager(dcc_world).check_pending(
        {"location": "Floor 4 - The Over City", "time": "day", "present_npcs": []}, limit=10)
    ids = {c["id"] for c in fired}
    assert "c3e61742" in ids  # Sheol: on_location -> "Floor 4"
    assert all("match_reason" in c for c in fired)


def test_on_time_fires(dcc_world):
    fired = ConsequenceManager(dcc_world).check_pending(
        {"location": "Village", "time": "night falls", "present_npcs": []}, limit=10)
    assert "a36a02f6" in {c["id"] for c in fired}  # Nightstalker: on_time -> "night"


def test_on_npc_fires(dcc_world):
    fired = ConsequenceManager(dcc_world).check_pending(
        {"location": "Inn", "time": "day", "present_npcs": ["a friendly trader"]}, limit=10)
    assert "b5aeefab" in {c["id"] for c in fired}  # Squeeks: on_npc -> "friendly"


def test_nothing_fires_when_no_match(dcc_world):
    fired = ConsequenceManager(dcc_world).check_pending(
        {"location": "Nowhere", "time": "noon", "present_npcs": ["Bob"], "events": []}, limit=10)
    assert fired == []


def test_cap_limits_results(dcc_world):
    cm = ConsequenceManager(dcc_world)
    ws = {"location": "Floor 4", "time": "night", "present_npcs": [], "events": []}
    assert len(cm.check_pending(ws, limit=10)) >= 2  # Sheol + Nightstalker both match
    assert len(cm.check_pending(ws, limit=1)) == 1


def test_expired_consequence_is_archived_not_fired(dcc_world):
    cm = ConsequenceManager(dcc_world)
    cm.add_consequence("temp ward", "soon", trigger_type="on_location",
                       match="Cave", expiry="Cave")
    fired = cm.check_pending({"location": "Dark Cave", "time": "day", "present_npcs": []}, limit=10)
    assert all(c["consequence"] != "temp ward" for c in fired), "expired must not fire"
    data = json.loads(_consq_path(dcc_world).read_text(encoding="utf-8"))
    assert any(c.get("consequence") == "temp ward" for c in data["resolved"]), "expired must be archived"
    assert all(c.get("consequence") != "temp ward" for c in data["active"]), "expired removed from active"
