"""QA eval for READY THREADS surfacing (Part 4 of the plot-weaver feature).

A seeded thread is DORMANT (invisible to STORY THREADS) until it becomes relevant.
get_full_context must actively nudge the GM the moment a dormant thread's linked NPC
is present (or its clock matures) — otherwise a seeded thread sleeps forgotten.
"""

import json
from pathlib import Path

from lib.session_manager import SessionManager


def _paths(world_dir):
    active = (Path(world_dir) / "active-campaign.txt").read_text().strip()
    base = Path(world_dir) / "campaigns" / active
    return base / "plots.json", base / "npcs.json"


def _seed_plot(pp, name, status, npcs=None, locations=None):
    plots = json.loads(pp.read_text()) if pp.exists() else {}
    plots[name] = {"type": "mystery", "status": status,
                   "description": "the wench knows the caravan route",
                   "npcs": npcs or [], "locations": locations or [],
                   "objectives": [], "events": []}
    pp.write_text(json.dumps(plots))


def _place_npc(npp, name, location):
    npcs = json.loads(npp.read_text()) if npp.exists() else {}
    npcs[name] = {"description": "a test face", "attitude": "neutral",
                  "tags": {"locations": [location], "quests": []}}
    npp.write_text(json.dumps(npcs))


def test_dormant_thread_surfaces_when_linked_npc_present(dcc_world):
    pp, npp = _paths(dcc_world)
    loc = SessionManager(dcc_world)._get_current_location()
    _place_npc(npp, "Testificate", loc)
    _seed_plot(pp, "Hidden Bargain", "dormant", npcs=["Testificate"])
    ctx = SessionManager(dcc_world).get_full_context()
    assert "READY THREADS" in ctx
    assert "Hidden Bargain" in ctx and "Testificate is here" in ctx


def test_no_surface_when_linked_npc_absent(dcc_world):
    pp, npp = _paths(dcc_world)
    _place_npc(npp, "Faraway", "A Place That Is Not Here At All")
    _seed_plot(pp, "Sleeping Thread", "dormant", npcs=["Faraway"])
    ctx = SessionManager(dcc_world).get_full_context()
    i = ctx.find("READY THREADS")
    ready = ctx[i:] if i >= 0 else ""
    assert "Sleeping Thread" not in ready, "a thread whose NPC isn't present must not surface"


def test_active_plot_never_in_ready_threads(dcc_world):
    pp, npp = _paths(dcc_world)
    loc = SessionManager(dcc_world)._get_current_location()
    _place_npc(npp, "Active Face", loc)
    _seed_plot(pp, "Active Quest", "active", npcs=["Active Face"])
    ctx = SessionManager(dcc_world).get_full_context()
    i = ctx.find("READY THREADS")
    ready = ctx[i:] if i >= 0 else ""
    assert "Active Quest" not in ready, "only DORMANT plots surface as ready"
