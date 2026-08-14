"""Tests for alias-runtime-resolver: alias-aware entity name resolution."""

from lib.entity_aliases import normalize_entity_name, resolve_entity_name


def test_normalize_strips_title_paren_case():
    assert normalize_entity_name("Princess Donut") == "donut"
    assert normalize_entity_name("Station 435 (End of the Line)") == "station 435"
    assert normalize_entity_name("KING Rust") == "rust"


def test_normalize_folds_diacritics():
    assert normalize_entity_name("Bêlit") == normalize_entity_name("Belit") == "belit"


def test_diacritic_parenthetical_resolves():
    entities = {"Belit": {}}
    assert resolve_entity_name("Bêlit (long qualifier)", entities) == "Belit"


def test_reuse_descriptive_phrasing_prefix():
    from lib.entity_aliases import reuse_existing_key
    entities = {"The Scarlet Citadel": {}}
    assert reuse_existing_key(
        "The Scarlet Citadel and the pits beneath it", entities
    ) == "The Scarlet Citadel"


def test_pure_title_normalizes_empty():
    # "King" alone must not collapse onto every titled entity.
    assert normalize_entity_name("King") == ""
    assert normalize_entity_name("The") == ""


def test_princess_donut_resolves_to_donut():
    entities = {"Donut": {}, "Carl": {}, "Mordecai": {}}
    assert resolve_entity_name("Princess Donut", entities) == "Donut"


def test_parenthetical_drift_resolves():
    entities = {"Station 435 (End of the Line)": {}, "Desperado Club": {}}
    assert resolve_entity_name("Station 435 (end of line)", entities) == "Station 435 (End of the Line)"
    assert resolve_entity_name("Desperado Club (Station 131)", entities) == "Desperado Club"


def test_explicit_aliases_field():
    entities = {"Princess Donut": {"aliases": ["Donut", "Mongo's Mom"]}, "Carl": {}}
    assert resolve_entity_name("Donut", entities) == "Princess Donut"
    assert resolve_entity_name("mongo's mom", entities) == "Princess Donut"


def test_exact_and_case_paths_still_work():
    entities = {"Carl": {}, "Donut": {}}
    assert resolve_entity_name("Carl", entities) == "Carl"        # exact
    assert resolve_entity_name("carl", entities) == "Carl"        # case-insensitive


def test_pure_title_query_does_not_false_match():
    # "King" must NOT resolve to "King Rust" (would be a wrong link at the table).
    entities = {"King Rust": {}, "Donut": {}}
    assert resolve_entity_name("King", entities) is None


def test_unrelated_query_returns_none():
    entities = {"Donut": {}, "Carl": {}}
    assert resolve_entity_name("Hekla", entities) is None


def test_accepts_iterable_of_keys():
    # resolve works on a bare key list (no data map), used by import-time passes.
    keys = ["Station 435 (End of the Line)", "Sirin Station 81"]
    assert resolve_entity_name("station 435 (end of line)", keys) == "Station 435 (End of the Line)"


def test_review_drift_set_resolution_rate():
    # Representative slice of the review's broken cross-refs; require >=92% resolve.
    npc_keys = {"Donut": {}, "Carl": {}, "Mordecai": {}, "Katia": {}, "King Rust": {}}
    loc_keys = {
        "Station 435 (End of the Line)": {},
        "Desperado Club": {},
        "Sirin Station 81": {},
        "The Iron Tangle": {},
    }
    # Title / case / parenthetical drift — the resolver's scope. (Slash-vs-paren
    # rewrites with differing trailing words are deferred to connection-key-normalize.)
    drift = [
        ("Princess Donut", npc_keys),
        ("DONUT", npc_keys),
        ("Mordecai", npc_keys),
        ("King Rust", npc_keys),
        ("Station 435 (end of line)", loc_keys),
        ("Desperado Club (Station 131)", loc_keys),
        ("the iron tangle", loc_keys),
        ("Sirin Station 81", loc_keys),
    ]
    resolved = sum(1 for q, m in drift if resolve_entity_name(q, m) is not None)
    assert resolved / len(drift) >= 0.92, f"only {resolved}/{len(drift)} resolved"


def test_unify_location_tags_merges_and_deletes_legacy():
    from lib.tag_unify import unify_location_tags
    npcs = {
        "Mordecai": {"location_tags": ["Guild Hall", "safe zone"],
                     "tags": {"locations": ["Safe Zone"], "quests": []}},
        "Donut": {"tags": {"locations": ["Safe Zone"], "quests": []}},
        "Stubby": {"location_tags": ["The Pit"]},  # no tags dict at all
    }
    report = unify_location_tags(npcs)
    assert sorted(report["migrated"]) == ["Mordecai", "Stubby"]
    m = npcs["Mordecai"]
    assert "location_tags" not in m
    assert m["tags"]["locations"] == ["Safe Zone", "Guild Hall"]  # case-insensitive dedupe
    assert npcs["Stubby"]["tags"]["locations"] == ["The Pit"]
    assert "location_tags" not in npcs["Stubby"]
