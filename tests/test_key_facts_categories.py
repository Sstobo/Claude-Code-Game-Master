"""Tests for key-facts-reads-choices.

gm-note.sh advertises player_choices and npc_relations; KEY FACTS read only the
three plot_* categories, so the two categories holding what the player DID were
write-only. These assert every advertised category now has a reader.
"""

import re
from pathlib import Path

from lib.note_manager import NoteManager
from lib.session_manager import SessionManager

WRAPPER = Path(__file__).parent.parent / "tools" / "gm-note.sh"


def test_player_choices_reach_the_scene(dcc_world):
    NoteManager(dcc_world).add_fact("player_choices", "Carl spared the goblin scribe")
    ctx = SessionManager(dcc_world).get_full_context()
    assert "spared the goblin scribe" in ctx


def test_npc_relations_reach_the_scene(dcc_world):
    NoteManager(dcc_world).add_fact("npc_relations", "Mordecai now owes Carl a favor")
    ctx = SessionManager(dcc_world).get_full_context()
    assert "owes Carl a favor" in ctx


def test_plot_facts_still_reach_the_scene(dcc_world):
    NoteManager(dcc_world).add_fact("plot_local", "The stairwell is braced open")
    ctx = SessionManager(dcc_world).get_full_context()
    assert "stairwell is braced open" in ctx


def test_every_advertised_category_has_a_reader(dcc_world):
    """No category may be a write-only hole: KEY FACTS reads it, or recall does."""
    help_text = WRAPPER.read_text(encoding="utf-8")
    advertised = set()
    for line in help_text.splitlines():
        if "Categories:" in line or (advertised and line.strip().startswith('"')):
            advertised.update(re.findall(r"\b[a-z]+_[a-z]+\b", line))
        elif advertised:
            advertised.update(re.findall(r"\b[a-z]+_[a-z]+\b", line))
            break
    assert advertised, "could not parse advertised categories from gm-note.sh"

    sm = SessionManager(dcc_world)
    read_by_key_facts = set(sm.KEY_FACT_CATEGORIES)
    for cat in advertised - read_by_key_facts:
        # Reachable through campaign memory, which gathers every facts category.
        NoteManager(dcc_world).add_fact(cat, f"a distinctive {cat} fact about zzyzx")
    from lib.campaign_memory import CampaignMemory
    entries = CampaignMemory(dcc_world).gather()
    sources = {e.get("source", "") for e in entries}
    for cat in advertised - read_by_key_facts:
        assert f"facts:{cat}" in sources, f"{cat} is advertised but nothing reads it"
