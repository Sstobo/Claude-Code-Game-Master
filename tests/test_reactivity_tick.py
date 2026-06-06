"""Tests for reactivity-tick-wiring.

tick() fires matching consequences once per scene (dedup via last_fired_key) and
re-arms when the scene changes; tick_from_session() builds the world_state from
campaign state. The wrappers (dm-session.sh move, dm-time.sh) call this so firing
is automatic, not eyeballed.
"""

from lib.consequence_manager import ConsequenceManager


def test_tick_fires_then_dedups_same_scene(dcc_world):
    cm = ConsequenceManager(dcc_world)
    scene = {"location": "Floor 4", "time": "day", "present_npcs": [], "events": []}
    first = cm.tick(scene, limit=10)
    assert any(c["id"] == "c3e61742" for c in first)  # Sheol on_location Floor 4
    assert all("match_reason" in c for c in first)
    # Same scene again -> already fired, does not re-fire.
    second = cm.tick(scene, limit=10)
    assert all(c["id"] != "c3e61742" for c in second)


def test_tick_rearms_on_scene_change(dcc_world):
    cm = ConsequenceManager(dcc_world)
    cm.tick({"location": "Floor 4", "time": "day", "present_npcs": []}, limit=10)
    # New scene (night) -> Nightstalker fires, and Sheol re-arms (different ctx key).
    third = cm.tick({"location": "Floor 4 ruins", "time": "night", "present_npcs": []}, limit=10)
    ids = {c["id"] for c in third}
    assert "a36a02f6" in ids  # Nightstalker on_time night
    assert "c3e61742" in ids  # Sheol re-armed by changed scene


def test_tick_respects_limit(dcc_world):
    cm = ConsequenceManager(dcc_world)
    scene = {"location": "Floor 4", "time": "night", "present_npcs": []}
    assert len(cm.tick(scene, limit=1)) == 1


def test_tick_from_session_runs_against_campaign_state(dcc_world):
    # Reads current location/time from campaign-overview without error.
    fired = ConsequenceManager(dcc_world).tick_from_session()
    assert isinstance(fired, list)
