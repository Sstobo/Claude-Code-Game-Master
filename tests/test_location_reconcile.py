"""Tests for missing-location-reconcile: stub or drop unresolved location refs."""

import json
from lib.location_reconcile import reconcile, run_reconcile, _is_stubbable


def test_stubbable_heuristic():
    assert _is_stubbable("Station 24")
    assert not _is_stubbable("Skull Empire / dungeon (location unknown)")
    assert not _is_stubbable("the upper level reached via the central stairwell after a long climb")


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


def test_descriptive_phrase_dropped_not_stubbed():
    locations = {"Hub": {"connections": []}}
    npcs = {"Bob": {"location_tags": ["Skull Empire / dungeon (location unknown)"]}}
    report = reconcile(npcs, locations, {})
    assert "Skull Empire / dungeon (location unknown)" in report["dropped"]
    assert npcs["Bob"]["location_tags"] == []        # dead ref removed
    assert "Skull Empire / dungeon (location unknown)" not in locations


def test_existing_reference_kept_via_alias():
    locations = {"Station 435 (End of the Line)": {"connections": []}}
    plots = {"P": {"locations": ["station 435 (end of line)"]}}
    report = reconcile({}, locations, plots)
    assert plots["P"]["locations"] == ["Station 435 (End of the Line)"]
    assert report["kept"] >= 1
    assert report["stubbed"] == []


def test_dead_connection_edge_to_droppable_is_removed():
    locations = {
        "Hub": {"connections": [{"to": "somewhere vague that cannot possibly be a real place name here"}]},
    }
    reconcile({}, locations, {})
    assert locations["Hub"]["connections"] == []   # unresolved+undroppable edge pruned


def test_run_reconcile_writes_files(tmp_path):
    (tmp_path / "locations.json").write_text(json.dumps({"Hub": {"connections": []}}))
    (tmp_path / "plots.json").write_text(json.dumps({"P": {"locations": ["Station 72"]}}))
    report = run_reconcile(str(tmp_path))
    saved = json.loads((tmp_path / "locations.json").read_text())
    assert "Station 72" in saved
    assert report["stubbed"] == ["Station 72"]
