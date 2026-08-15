"""Play-pack materialize dedupe — a descriptive stub and its later materialize
collapse to ONE npc record.

The bug: `apply_stage` keys a `present` entry by its full descriptive string
("Aratus the Kothian (a fat, boastful kidnapper up from Koth)"); a later
`from_book("Aratus")` guarded only by a bare `name in npcs` check never saw the
long stub and minted a second record. The fix routes both through the
bidirectional resolver so the short proper name survives and the long form is
recorded as an alias, tags preserved.
"""

import json

from lib.entity_aliases import resolve_or_merge_key
from lib.play_pack import apply_stage, from_book, save_pack


ARATUS_LONG = "Aratus the Kothian (a fat, boastful kidnapper up from Koth)"


def _campaign(tmp_path):
    cdir = tmp_path / "world-state" / "campaigns" / "dedupetest"
    cdir.mkdir(parents=True)
    (cdir / "campaign-overview.json").write_text(json.dumps({
        "campaign_name": "Dedupe Test",
        "player_position": {"current_location": None},
    }))
    (cdir / "npcs.json").write_text("{}")
    (cdir / "locations.json").write_text("{}")
    return cdir


def test_resolver_matches_short_query_onto_long_key():
    """Reverse direction of reuse_existing_key: a short proper name attaches to a
    longer descriptive key (this is what the bare exact-match guard missed)."""
    entities = {ARATUS_LONG: {}}
    assert resolve_or_merge_key("Aratus", entities) == ARATUS_LONG
    # ...and the descriptive->short direction still works.
    assert resolve_or_merge_key(ARATUS_LONG, {"Aratus": {}}) == "Aratus"
    # A genuinely different name matches nothing (no over-merge).
    assert resolve_or_merge_key("Yara", entities) is None


def test_stage_then_materialize_yields_one_record(tmp_path):
    cdir = _campaign(tmp_path)
    save_pack(cdir, {
        "room": "The Bedchamber",
        "present": [ARATUS_LONG],
        "hook": "A kidnapper up from Koth.",
    })
    stage = apply_stage(cdir)
    assert stage["ok"] is True
    # Stage created the descriptive stub keyed by its full string.
    npcs = json.loads((cdir / "npcs.json").read_text())
    assert list(npcs) == [ARATUS_LONG]
    assert npcs[ARATUS_LONG]["tags"]["locations"] == ["The Bedchamber"]

    # GM materializes the short proper name later.
    result = from_book(cdir, "Aratus", kind="npc",
                       description="A fat, boastful Kothian slaver.")
    assert result["ok"] is True
    assert result["name"] == "Aratus"

    npcs = json.loads((cdir / "npcs.json").read_text())
    # ONE record, keyed on the canonical short name.
    assert list(npcs) == ["Aratus"]
    rec = npcs["Aratus"]
    assert rec["name"] == "Aratus"
    # The long descriptive form is preserved as an alias.
    assert ARATUS_LONG in rec.get("aliases", [])
    # The stub's location tag survived the merge.
    assert rec["tags"]["locations"] == ["The Bedchamber"]
    # The stub blurb was upgraded by the richer materialize description.
    assert "boastful Kothian" in rec["description"]


def test_materialize_then_stage_yields_one_record(tmp_path):
    """Original bug's reverse order: materialize the short name first, then stage
    the descriptive present entry. Still ONE record, keyed short."""
    cdir = _campaign(tmp_path)
    from_book(cdir, "Aratus", kind="npc", description="A Kothian slaver.")
    save_pack(cdir, {"room": "The Bedchamber", "present": [ARATUS_LONG]})
    apply_stage(cdir)

    npcs = json.loads((cdir / "npcs.json").read_text())
    assert list(npcs) == ["Aratus"]
    assert ARATUS_LONG in npcs["Aratus"].get("aliases", [])
    assert npcs["Aratus"]["tags"]["locations"] == ["The Bedchamber"]


def test_descriptive_materialize_reuses_short_existing_key(tmp_path):
    """Reverse-direction guard: a descriptive from_book against a short existing
    key reuses the short key rather than spawning a near-dupe."""
    cdir = _campaign(tmp_path)
    from_book(cdir, "Aratus", kind="npc", description="A Kothian slaver.")
    result = from_book(cdir, ARATUS_LONG, kind="npc")
    assert result["ok"] is True
    assert result["name"] == "Aratus"

    npcs = json.loads((cdir / "npcs.json").read_text())
    assert list(npcs) == ["Aratus"]
    assert ARATUS_LONG in npcs["Aratus"].get("aliases", [])
    # A real description is never clobbered by the stub materialize.
    assert npcs["Aratus"]["description"] == "A Kothian slaver."


def test_different_name_still_creates_its_own_record(tmp_path):
    """No over-merge: an unrelated proper name gets its own record."""
    cdir = _campaign(tmp_path)
    save_pack(cdir, {"room": "The Bedchamber", "present": [ARATUS_LONG]})
    apply_stage(cdir)
    result = from_book(cdir, "Yara", kind="npc", description="A slave girl.")
    assert result["ok"] is True
    assert result["name"] == "Yara"

    npcs = json.loads((cdir / "npcs.json").read_text())
    assert set(npcs) == {ARATUS_LONG, "Yara"}


def test_short_name_never_corrupts_fleshed_longer_named_npc(tmp_path):
    """Regression: `from_book("Aram")` against a fleshed, DISTINCT "Aram Baksh"
    must NOT over-merge. The reverse token-prefix match ("Aram" prefixes "Aram
    Baksh") is a surname suffix, not an epithet — so the fleshed record survives
    intact and the short name becomes its own separate record.
    """
    cdir = _campaign(tmp_path)
    # Seed a fully-fleshed innkeeper — real description, own location tag, an event.
    (cdir / "npcs.json").write_text(json.dumps({
        "Aram Baksh": {
            "name": "Aram Baksh",
            "description": "A Zamorian innkeeper who rents rooms he does not expect his guests to leave.",
            "attitude": "greedy",
            "tags": {"locations": ["The Maul"], "quests": []},
            "events": ["Took the stranger's coin for a room in the Maul."],
        }
    }))

    result = from_book(cdir, "Aram", kind="npc",
                       description="A young Turanian guardsman new to the city watch.")
    assert result["ok"] is True
    # A DISTINCT record keyed on the short name — NOT re-keyed onto the fleshed one.
    assert result["name"] == "Aram"

    npcs = json.loads((cdir / "npcs.json").read_text())
    assert set(npcs) == {"Aram", "Aram Baksh"}

    # The fleshed record survived un-renamed, description / tags / events intact.
    baksh = npcs["Aram Baksh"]
    assert baksh["name"] == "Aram Baksh"
    assert baksh["description"].startswith("A Zamorian innkeeper")
    assert baksh["tags"]["locations"] == ["The Maul"]
    assert baksh["events"] == ["Took the stranger's coin for a room in the Maul."]

    # Neither is aliased onto the other — two separate identities.
    assert "Aram Baksh" not in npcs["Aram"].get("aliases", [])
    assert "Aram" not in baksh.get("aliases", [])
    # The new short record carries its own description.
    assert "Turanian guardsman" in npcs["Aram"]["description"]
