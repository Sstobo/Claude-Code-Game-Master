"""Entity-anchored memory: facts that NAME a present NPC surface under them.

A fact logged via gm-note.sh lands only in facts.json. If it names an NPC, that
memory used to die in the global log. `get_full_context` now re-attaches such
facts under the present NPC at READ time (no write-side coupling), de-duped
against PREVIOUSLY ON / world-remembers and the NPC's own events.

These tests mutate only the hermetic `dcc_world` copy (never the checked-in
fixture): they add a present NPC (tagged to the current location) plus facts,
then assert on SessionManager(dcc_world).get_full_context().
"""

import json
from pathlib import Path

from lib.session_manager import SessionManager


def _load(world, name):
    return json.loads((Path(world) / "campaigns" / "dungeon-crawler-carl" / name).read_text())


def _save(world, name, data):
    (Path(world) / "campaigns" / "dungeon-crawler-carl" / name).write_text(
        json.dumps(data, indent=2))


def _current_location(world):
    overview = _load(world, "campaign-overview.json")
    return overview.get("player_position", {}).get("current_location")


def _add_npc(world, name, location, events=None, aliases=None):
    npcs = _load(world, "npcs.json")
    npcs[name] = {
        "name": name,
        "is_party_member": False,
        "tags": {"locations": [location], "quests": []},
        "events": events or [],
    }
    if aliases is not None:
        npcs[name]["aliases"] = aliases
    _save(world, "npcs.json", npcs)


def _add_facts(world, category, texts):
    facts = _load(world, "facts.json")
    facts.setdefault(category, [])
    for t in texts:
        facts[category].append({"fact": t, "timestamp": "2026-08-15T00:00:00Z"})
    _save(world, "facts.json", facts)


def _npc_block(ctx, npc_name):
    """Lines belonging to one present-NPC entry (header -> next header/blank)."""
    lines = ctx.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(f"{npc_name}:") or ln.startswith(f"{npc_name} ("):
            start = i
            break
    assert start is not None, f"{npc_name} not rendered as a present NPC"
    block = []
    for ln in lines[start + 1:]:
        if ln and not ln.startswith("  "):  # next NPC header or new section
            break
        block.append(ln)
    return "\n".join(block)


def test_fact_naming_present_npc_surfaces_under_that_npc(dcc_world):
    loc = _current_location(dcc_world)
    fact = "Griselda's eyes flicked to the back door — she knows more than she lets on."
    _add_npc(dcc_world, "Griselda", loc)
    _add_facts(dcc_world, "npc_relations", [fact])

    ctx = SessionManager(dcc_world).get_full_context()
    block = _npc_block(ctx, "Griselda")
    assert "remembers:" in block, "expected a 'remembers:' sub-line under the NPC"
    assert fact in block, "the naming fact must appear under the present NPC"


def test_fact_naming_no_present_npc_is_not_attached(dcc_world):
    loc = _current_location(dcc_world)
    unrelated = "Zoltar the Unseen brooded in a tower far from any living soul."
    _add_npc(dcc_world, "Griselda", loc)
    _add_facts(dcc_world, "npc_relations", [unrelated])

    ctx = SessionManager(dcc_world).get_full_context()
    # It names nobody present, so it is on no NPC's 'remembers:' line.
    assert f"remembers: {unrelated}" not in ctx
    block = _npc_block(ctx, "Griselda")
    assert unrelated not in block


def test_word_boundary_substring_is_not_a_false_positive(dcc_world):
    loc = _current_location(dcc_world)
    banana = "The crawlers found a crate of Banana rations near the vending machine."
    _add_npc(dcc_world, "Ana", loc)
    _add_facts(dcc_world, "npc_relations", [banana])

    ctx = SessionManager(dcc_world).get_full_context()
    # "Ana" must not match inside "Banana".
    assert f"remembers: {banana}" not in ctx
    assert banana not in _npc_block(ctx, "Ana")


def test_fact_already_in_npc_events_is_not_shown_twice(dcc_world):
    loc = _current_location(dcc_world)
    dup = "Griselda swore an oath to the party in the smoke-filled hall."
    _add_npc(dcc_world, "Griselda", loc, events=[{"event": dup, "timestamp": "x"}])
    _add_facts(dcc_world, "npc_relations", [dup])

    ctx = SessionManager(dcc_world).get_full_context()
    block = _npc_block(ctx, "Griselda")
    # Rendered once by Recent/_recent_events, never a second time as 'remembers:'.
    assert f"remembers: {dup}" not in block


def test_common_leading_token_is_not_a_false_positive(dcc_world):
    """A multi-token NPC whose first token is a common word must NOT vacuum up
    ordinary lowercase prose that merely starts with that word."""
    loc = _current_location(dcc_world)
    rope = "the old rope frayed against the pier"
    door = "The red door creaked open on rusted hinges."
    _add_npc(dcc_world, "Old Man Withers", loc)
    _add_npc(dcc_world, "Red Sonja", loc)
    _add_facts(dcc_world, "world_events", [rope, door])

    ctx = SessionManager(dcc_world).get_full_context()
    # Neither fact names a real NPC, so it attaches under no one.
    assert f"remembers: {rope}" not in ctx
    assert f"remembers: {door}" not in ctx
    assert rope not in _npc_block(ctx, "Old Man Withers")
    assert rope not in _npc_block(ctx, "Red Sonja")
    assert door not in _npc_block(ctx, "Old Man Withers")
    assert door not in _npc_block(ctx, "Red Sonja")


def test_full_multiword_key_still_attaches(dcc_world):
    """A fact naming the whole NPC key still surfaces under that NPC."""
    loc = _current_location(dcc_world)
    fact = "Old Man Withers cursed the merchant who shorted him."
    _add_npc(dcc_world, "Old Man Withers", loc)
    _add_facts(dcc_world, "npc_relations", [fact])

    ctx = SessionManager(dcc_world).get_full_context()
    block = _npc_block(ctx, "Old Man Withers")
    assert "remembers:" in block
    assert fact in block


def test_alias_path_attaches(dcc_world):
    """A fact mentioning an explicit alias attaches under the NPC."""
    loc = _current_location(dcc_world)
    fact = "Aratus the Kothian bargained hard for the caravan's silk."
    _add_npc(dcc_world, "Aratus", loc, aliases=["Aratus the Kothian"])
    _add_facts(dcc_world, "npc_relations", [fact])

    ctx = SessionManager(dcc_world).get_full_context()
    block = _npc_block(ctx, "Aratus")
    assert "remembers:" in block
    assert fact in block
