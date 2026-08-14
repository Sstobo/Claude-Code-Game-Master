"""Tests for reactivity-tick-wiring.

tick() fires matching consequences once per scene (last_fired_key annotates
already-fired matches rather than suppressing them) and re-arms when the scene
changes; tick_from_session() builds the world_state from campaign state. The
wrappers (gm-session.sh move, gm-time.sh) call this so firing is automatic, not
eyeballed.
"""

from lib.consequence_manager import ConsequenceManager


def test_tick_fires_then_dedups_same_scene(dcc_world):
    cm = ConsequenceManager(dcc_world)
    scene = {"location": "Floor 4", "time": "day", "present_npcs": [], "events": []}
    first = cm.tick(scene, limit=10)
    assert any(c["id"] == "c3e61742" for c in first["fired"])  # Sheol on_location Floor 4
    assert all("match_reason" in c for c in first["fired"])
    # Same scene again -> still reported, annotated already-fired, not re-stamped.
    second = cm.tick(scene, limit=10)
    assert any(c["id"] == "c3e61742" for c in second["already_fired"])
    assert all(c["id"] != "c3e61742" for c in second["fired"])
    sheol = next(c for c in second["already_fired"] if c["id"] == "c3e61742")
    assert sheol.get("already_fired") is True
    assert "match_reason" in sheol


def test_tick_rearms_on_scene_change(dcc_world):
    cm = ConsequenceManager(dcc_world)
    cm.tick({"location": "Floor 4", "time": "day", "present_npcs": []}, limit=10)
    # New scene (night) -> Nightstalker fires, and Sheol re-arms (different ctx key).
    third = cm.tick({"location": "Floor 4 ruins", "time": "night", "present_npcs": []}, limit=10)
    ids = {c["id"] for c in third["fired"]}
    assert "a36a02f6" in ids  # Nightstalker on_time night
    assert "c3e61742" in ids  # Sheol re-armed by changed scene


def test_tick_respects_limit(dcc_world):
    cm = ConsequenceManager(dcc_world)
    scene = {"location": "Floor 4", "time": "night", "present_npcs": []}
    result = cm.tick(scene, limit=1)
    assert len(result["fired"]) == 1
    # Floor 4 + night matches Sheol and Nightstalker; the rest are disclosed.
    assert len(result["disclosed"]) >= 1
    assert all("match_reason" in c for c in result["fired"] + result["disclosed"])


def test_tick_from_session_runs_against_campaign_state(dcc_world):
    # Reads current location/time from campaign-overview without error.
    result = ConsequenceManager(dcc_world).tick_from_session()
    assert isinstance(result, dict)
    assert "fired" in result and "disclosed" in result
    assert "already_fired" in result and "near_misses" in result
