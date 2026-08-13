"""Tests for cap-extraction-30: the importance ranking behind entity tiering.

The cap no longer deletes — it marks everything below the top-N `background: true`
(see test_extraction_tiering.py). These tests cover the ranking itself: who lands
above the line. `cap_type` returns (entities, background_names).
"""

import json

from lib.extraction_cap import (
    cap_type,
    cap_campaign,
    importance_score,
    plot_reference_names,
)


def test_plot_referenced_entity_survives_over_high_mention_noise():
    # "Walkon" is mentioned a lot but referenced by no plot; "Hero" is plot-referenced.
    entities = {f"Filler{i}": {} for i in range(40)}
    entities["Hero"] = {}        # plot-referenced, low raw mentions
    entities["Walkon"] = {}      # high mentions, no plot ref
    corpus = ("walkon " * 500) + ("filler0 " * 10) + "hero"
    plot_refs = {"hero"}
    entities, background = cap_type(entities, "npcs", corpus, plot_refs, limit=30)
    active = [n for n, e in entities.items() if not e.get("background")]
    assert len(active) == 30
    assert "Hero" in active, "plot-referenced entity must never be backgrounded"
    assert "Hero" not in background


def test_party_member_survives():
    entities = {f"X{i}": {} for i in range(35)}
    entities["Sidekick"] = {"is_party_member": True}
    entities, background = cap_type(entities, "npcs", "", set(), limit=30)
    assert entities["Sidekick"].get("background") is None


def test_nothing_backgrounded_when_under_limit():
    entities = {f"X{i}": {} for i in range(10)}
    entities, background = cap_type(entities, "npcs", "", set(), limit=30)
    assert background == []
    assert all(not e.get("background") for e in entities.values())


def test_plots_rank_main_over_optional():
    plots = {f"side{i}": {"type": "side"} for i in range(40)}
    plots["MainArc"] = {"type": "main"}
    plots["Optional1"] = {"type": "optional"}
    plots, background = cap_type(plots, "plots", "", set(), limit=30)
    assert plots["MainArc"].get("background") is None
    assert "Optional1" in background  # weakest type, displaced by 30 'side' plots


def test_exactly_limit_active():
    entities = {f"X{i}": {} for i in range(100)}
    entities, background = cap_type(entities, "items", "corpus", set(), limit=30)
    assert len(entities) - len(background) == 30


def test_plot_reference_names_normalizes():
    plots = {"P": {"npcs": ["Princess Donut"], "locations": ["Station 81 (hub)"]}}
    refs = plot_reference_names(plots)
    assert "donut" in refs          # title stripped
    assert "station 81" in refs     # parenthetical stripped


def test_cap_campaign_writes_tiered_files(tmp_path):
    cdir = tmp_path / "camp"
    (cdir / "chunks").mkdir(parents=True)
    (cdir / "chunks" / "chunk_000.txt").write_text("carl donut " * 20)
    npcs = {f"N{i}": {} for i in range(50)}
    npcs["Carl"] = {}
    (cdir / "npcs.json").write_text(json.dumps(npcs))
    (cdir / "plots.json").write_text(json.dumps({"P": {"type": "main", "npcs": ["Carl"]}}))
    report = cap_campaign(str(cdir), limit=30)
    saved = json.loads((cdir / "npcs.json").read_text())
    assert len(saved) == 51                      # every extracted NPC still on disk
    assert saved["Carl"].get("background") is None  # plot-referenced -> active
    assert report["npcs"]["active"] == 30
    assert len(report["npcs"]["background"]) == 21
