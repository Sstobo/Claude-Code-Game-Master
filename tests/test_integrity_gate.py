"""Tests for import-integrity-gate: canonicalize cross-refs, fail on unresolved."""

import json
import pytest

from lib.integrity_gate import canonicalize, run_gate


def test_donut_reference_canonicalized_and_aliased():
    npcs = {"Donut": {}, "Carl": {}}
    plots = {"P1": {"npcs": ["Princess Donut", "Carl"], "locations": []}}
    report = canonicalize(npcs, {}, plots)
    # plot ref rewritten to the real key
    assert plots["P1"]["npcs"] == ["Donut", "Carl"]
    # variant recorded as an alias on the target
    assert "Princess Donut" in npcs["Donut"]["aliases"]
    assert any(r["to"] == "Donut" for r in report["rewritten"])


def test_location_connection_and_tag_canonicalized():
    locations = {
        "Station 435 (End of the Line)": {"connections": [{"to": "Sirin Station 81"}]},
        "Sirin Station 81": {"connections": [{"to": "station 435 (end of line)"}]},
    }
    npcs = {"Bob": {"location_tags": ["sirin station 81"]}}
    report = canonicalize(npcs, locations, {})
    assert locations["Sirin Station 81"]["connections"][0]["to"] == "Station 435 (End of the Line)"
    assert npcs["Bob"]["location_tags"] == ["Sirin Station 81"]


def test_unresolved_reference_is_reported():
    npcs = {"Carl": {}}
    plots = {"P": {"npcs": ["Carl", "Ghostface"], "locations": []}}
    report = canonicalize(npcs, {}, plots)
    assert len(report["unresolved"]) == 1
    assert report["unresolved"][0]["ref"] == "Ghostface"


def test_strict_gate_fails_on_unresolved(tmp_path):
    (tmp_path / "npcs.json").write_text(json.dumps({"Carl": {}}))
    (tmp_path / "plots.json").write_text(json.dumps({"P": {"npcs": ["Nobody"], "locations": []}}))
    with pytest.raises(SystemExit) as exc:
        run_gate(str(tmp_path), strict=True)
    assert exc.value.code == 1


def test_no_strict_returns_report_without_raising(tmp_path):
    (tmp_path / "npcs.json").write_text(json.dumps({"Carl": {}}))
    (tmp_path / "plots.json").write_text(json.dumps({"P": {"npcs": ["Nobody"], "locations": []}}))
    report = run_gate(str(tmp_path), strict=False)
    assert len(report["unresolved"]) == 1


def test_clean_refs_pass_strict_and_persist(tmp_path):
    (tmp_path / "npcs.json").write_text(json.dumps({"Donut": {}}))
    (tmp_path / "plots.json").write_text(json.dumps({"P": {"npcs": ["Princess Donut"], "locations": []}}))
    report = run_gate(str(tmp_path), strict=True)  # must NOT raise: Princess Donut resolves
    saved = json.loads((tmp_path / "plots.json").read_text())
    assert saved["P"]["npcs"] == ["Donut"]
    assert report["unresolved"] == []
    assert report["near_duplicates"] == []


def test_near_duplicate_keys_are_reported():
    npcs = {"Belit": {}, "Bêlit": {}}
    report = canonicalize(npcs, {}, {})
    assert report["unresolved"] == []
    assert len(report["near_duplicates"]) == 1
    finding = report["near_duplicates"][0]
    assert finding["kind"] == "npc"
    assert finding["normalized"] == "belit"
    assert set(finding["keys"]) == {"Belit", "Bêlit"}


def test_strict_gate_fails_on_near_duplicates(tmp_path):
    (tmp_path / "npcs.json").write_text(json.dumps({"Belit": {}, "Bêlit": {}}))
    with pytest.raises(SystemExit) as exc:
        run_gate(str(tmp_path), strict=True)
    assert exc.value.code == 1
