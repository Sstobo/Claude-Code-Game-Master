"""Tests for missing-location-reconcile: stub or drop unresolved location refs."""

import json
from lib.location_reconcile import reconcile, run_reconcile, _is_stubbable


def test_stubbable_heuristic():
    assert _is_stubbable("Station 24")
    # a messy name is still a place — only prose that names no destination is not
    assert _is_stubbable("Skull Empire / dungeon (location unknown)")
    assert _is_stubbable("The Upper Level of the Tower of the Elephant")
    # routing prose fails only where it is routing prose: a connection target
    assert _is_stubbable("Transfer stations ending in 1")
    assert not _is_stubbable("Transfer stations ending in 1", is_connection=True)
    assert not _is_stubbable("")


def test_missing_plot_location_gets_stubbed_and_linked():
    locations = {"The Iron Tangle": {"connections": [{"to": "Red Line"}]}, "Red Line": {"connections": []}}
    plots = {"P": {"locations": ["Station 24"]}}
    report = reconcile({}, locations, plots)
    assert "Station 24" in locations, "missing structural location should be stubbed"
    assert "Station 24" in report["stubbed"]
    # bidirectional link to the hub (Iron Tangle has most connections)
    assert any(c["to"] == "Station 24" for c in locations["The Iron Tangle"]["connections"])
    assert locations["Station 24"]["connections"][0]["to"] == "The Iron Tangle"
    assert plots["P"]["locations"] == ["Station 24"]


def test_rule_prose_dropped_as_a_connection_target():
    locations = {"Hub": {"connections": [{"to": "Transfer stations ending in 1"}]}}
    report = reconcile({}, locations, {})
    assert "Transfer stations ending in 1" in report["dropped"]
    assert locations["Hub"]["connections"] == []      # dead edge removed
    assert "Transfer stations ending in 1" not in locations


def test_tag_reference_to_the_same_string_is_stubbed():
    """A tag says someone stands there, so it names a place — stub, never drop."""
    locations = {"Hub": {"connections": []}}
    npcs = {"Bob": {"location_tags": ["Transfer stations ending in 1"]}}
    report = reconcile(npcs, locations, {})
    assert report["dropped"] == []
    assert npcs["Bob"]["location_tags"] == ["Transfer stations ending in 1"]
    assert locations["Transfer stations ending in 1"]["low_confidence"] is True


def test_existing_reference_kept_via_alias():
    locations = {"Station 435 (End of the Line)": {"connections": []}}
    plots = {"P": {"locations": ["station 435 (end of line)"]}}
    report = reconcile({}, locations, plots)
    assert plots["P"]["locations"] == ["Station 435 (End of the Line)"]
    assert report["kept"] >= 1
    assert report["stubbed"] == []


def test_dead_connection_edge_to_rule_prose_is_removed():
    locations = {"Hub": {"connections": [{"to": "Any line from here"}]}}
    reconcile({}, locations, {})
    assert locations["Hub"]["connections"] == []   # edge to a non-destination pruned


def test_run_reconcile_writes_files(tmp_path):
    (tmp_path / "locations.json").write_text(json.dumps({"Hub": {"connections": []}}))
    (tmp_path / "plots.json").write_text(json.dumps({"P": {"locations": ["Station 72"]}}))
    report = run_reconcile(str(tmp_path))
    saved = json.loads((tmp_path / "locations.json").read_text())
    assert "Station 72" in saved
    assert report["stubbed"] == ["Station 72"]


def test_diacritic_parenthetical_reuses_existing_with_alias():
    locations = {"Belit": {"connections": []}}
    plots = {"P": {"locations": ["Bêlit (long qualifier)"]}}
    report = reconcile({}, locations, plots)
    assert report["stubbed"] == []
    assert "Bêlit (long qualifier)" not in locations
    assert plots["P"]["locations"] == ["Belit"]
    assert locations["Belit"]["aliases"] == ["Bêlit (long qualifier)"]


def test_descriptive_phrasing_reuses_existing_location():
    locations = {"The Scarlet Citadel": {"connections": []}}
    plots = {"P": {"locations": ["The Scarlet Citadel and the pits beneath it"]}}
    report = reconcile({}, locations, plots)
    assert report["stubbed"] == []
    assert report["dropped"] == []
    assert "The Scarlet Citadel and the pits beneath it" not in locations
    assert plots["P"]["locations"] == ["The Scarlet Citadel"]
    assert "The Scarlet Citadel and the pits beneath it" in locations["The Scarlet Citadel"]["aliases"]
