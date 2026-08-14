"""Tests for minor-entity-stubs-taxonomy."""

import json
from lib.minor_stubs import stub_missing_npcs, validate_plot_types, run_stubs


def test_unresolved_plot_npc_gets_stubbed():
    npcs = {"Carl": {}}
    plots = {"P": {"npcs": ["Carl", "Ji-Hoon"]}}
    report = stub_missing_npcs(npcs, plots)
    assert "Ji-Hoon" in npcs
    assert npcs["Ji-Hoon"]["source"] == "auto-stub"
    assert plots["P"]["npcs"] == ["Carl", "Ji-Hoon"]
    assert "Ji-Hoon" in report["stubbed"]


def test_resolvable_ref_canonicalized_not_stubbed():
    npcs = {"Donut": {}}
    plots = {"P": {"npcs": ["Princess Donut"]}}
    report = stub_missing_npcs(npcs, plots)
    assert plots["P"]["npcs"] == ["Donut"]      # canonicalized, not stubbed
    assert report["stubbed"] == []
    assert "Princess Donut" not in npcs


def test_optional_type_is_valid_and_kept():
    plots = {"Court": {"type": "optional"}}
    report = validate_plot_types(plots)
    assert plots["Court"]["type"] == "optional"   # documented enum value
    assert report["reclassified"] == []


def test_threat_and_mystery_survive_untouched():
    plots = {"Siege": {"type": "threat"}, "Whodunit": {"type": "mystery"}}
    report = validate_plot_types(plots)
    assert plots["Siege"]["type"] == "threat"
    assert plots["Whodunit"]["type"] == "mystery"
    assert report["reclassified"] == []


def test_known_synonym_maps_to_canonical_type():
    plots = {
        "Errand": {"type": "quest"},
        "Rivalry": {"type": "conflict"},
        "Ambush": {"type": "Random Encounter"},
        "Riddles": {"type": "mysteries"},
    }
    validate_plot_types(plots)
    assert plots["Errand"]["type"] == "side"
    assert plots["Rivalry"]["type"] == "threat"
    assert plots["Ambush"]["type"] == "side"       # case-insensitive, multi-word
    assert plots["Riddles"]["type"] == "mystery"


def test_unknown_type_falls_back_to_side_with_warning(capsys):
    plots = {"Weird": {"type": "epilogue"}, "Blank": {}}
    validate_plot_types(plots)
    assert plots["Weird"]["type"] == "side"
    assert plots["Blank"]["type"] == "side"
    assert "epilogue" in capsys.readouterr().err


def test_run_stubs_makes_all_plot_npcs_resolve(tmp_path):
    (tmp_path / "npcs.json").write_text(json.dumps({"Carl": {}}))
    (tmp_path / "plots.json").write_text(json.dumps({"P": {"npcs": ["Carl", "Elle McGib"], "type": "main"}}))
    run_stubs(str(tmp_path))
    npcs = json.loads((tmp_path / "npcs.json").read_text())
    plots = json.loads((tmp_path / "plots.json").read_text())
    # every plot.npcs ref now exists as a key
    for ref in plots["P"]["npcs"]:
        assert ref in npcs


def test_diacritic_parenthetical_reuses_existing_with_alias():
    npcs = {"Belit": {}}
    plots = {"P": {"npcs": ["Bêlit (long qualifier)"]}}
    report = stub_missing_npcs(npcs, plots)
    assert report["stubbed"] == []
    assert "Bêlit (long qualifier)" not in npcs
    assert plots["P"]["npcs"] == ["Belit"]
    assert npcs["Belit"]["aliases"] == ["Bêlit (long qualifier)"]
