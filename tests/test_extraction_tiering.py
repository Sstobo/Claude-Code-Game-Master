"""Tests for extraction tiering: the import keeps the whole book, ranks it, and
never invents a placeholder for someone it already extracted.

The pipeline used to delete every entity below the top-30, then paper over the
resulting dangling references with generic stubs — pre-making the creative
decision of who exists in the world. Now the cap TIERS (active vs
`background: true`, same file), reconcile stubs any place the book names rather
than dropping it on a shape heuristic, and stubbing is reserved for names
extraction genuinely never produced.

Fixtures are hermetic tmp_path campaigns; no live campaign is read or written.
"""

import json

import pytest

from lib.entity_enhancer import EntityEnhancer
from lib.extraction_cap import cap_campaign, cap_type, plot_type_weight
from lib.integrity_gate import run_gate
from lib.json_ops import JsonOperations
from lib.location_reconcile import FACT_CATEGORY, reconcile, run_reconcile
from lib.minor_stubs import run_stubs
from lib.npc_manager import NPCManager
from lib.plot_manager import PlotManager
from lib.search import WorldSearcher
from lib.session_manager import SessionManager

LIMIT = 30
# 7 words: the old heuristic dropped anything over six.
LONG_PLACE = "the flooded hall beneath the collapsed east stair"


@pytest.fixture
def book(tmp_path):
    """A 44-NPC extraction: 2 plot-referenced leads, 42 walk-ons of decaying fame.

    Walk-on mention counts descend, so the tier boundary is deterministic:
    Walkon00 is the most-mentioned, Walkon41 the least.
    """
    cdir = tmp_path / "camp"
    (cdir / "chunks").mkdir(parents=True)

    npcs = {"Carl": {"name": "Carl"}, "Donut": {"name": "Donut"}}
    for i in range(42):
        npcs[f"Walkon{i:02d}"] = {"name": f"Walkon{i:02d}"}

    corpus = ["carl donut "]
    for i in range(42):
        corpus.append(f"walkon{i:02d} " * (100 - i))
    (cdir / "chunks" / "chunk_000.txt").write_text("".join(corpus))

    locations = {"The Hub": {"name": "The Hub", "connections": []}}
    plots = {
        "The Long Descent": {
            "type": "main",
            "npcs": ["Carl", "Donut", "Walkon41", "Elle McGib"],
            "locations": ["The Hub", LONG_PLACE],
        }
    }
    (cdir / "npcs.json").write_text(json.dumps(npcs))
    (cdir / "locations.json").write_text(json.dumps(locations))
    (cdir / "plots.json").write_text(json.dumps(plots))
    return cdir


def _load(cdir, name):
    return json.loads((cdir / name).read_text())


def test_nothing_is_deleted_by_the_cap(book):
    before = set(_load(book, "npcs.json"))
    cap_campaign(str(book), limit=LIMIT)
    assert set(_load(book, "npcs.json")) == before


def test_top_n_active_rest_background(book):
    report = cap_campaign(str(book), limit=LIMIT)
    npcs = _load(book, "npcs.json")

    active = [n for n, e in npcs.items() if not e.get("background")]
    background = [n for n, e in npcs.items() if e.get("background") is True]
    assert len(active) == LIMIT
    assert len(background) == len(npcs) - LIMIT
    assert report["npcs"]["active"] == LIMIT
    assert sorted(report["npcs"]["background"]) == sorted(background)

    # The plot-referenced cast is active even when the source barely names them.
    assert "Carl" in active and "Donut" in active
    # Walkon41 is the least-mentioned NPC, but a plot references it -> active.
    assert "Walkon41" in active
    assert "Walkon39" in background


def test_cap_is_idempotent(book):
    cap_campaign(str(book), limit=LIMIT)
    first = _load(book, "npcs.json")
    cap_campaign(str(book), limit=LIMIT)
    assert _load(book, "npcs.json") == first


def test_no_placeholder_invented_for_an_extracted_npc(book):
    cap_campaign(str(book), limit=LIMIT)
    run_stubs(str(book))
    npcs = _load(book, "npcs.json")

    # Walkon41 was extracted (and would have been dropped by the old cap):
    # it must still be the real entity, not a generic auto-stub over its grave.
    assert npcs["Walkon41"].get("source") != "auto-stub"
    for name in ("Carl", "Donut"):
        assert npcs[name].get("source") != "auto-stub"
    stubbed = [n for n, e in npcs.items() if e.get("source") == "auto-stub"]
    assert stubbed == ["Elle McGib"]


def test_never_extracted_plot_name_still_gets_a_stub(book):
    cap_campaign(str(book), limit=LIMIT)
    report = run_stubs(str(book))
    npcs = _load(book, "npcs.json")
    assert "Elle McGib" in npcs
    assert npcs["Elle McGib"]["source"] == "auto-stub"
    assert report["stubbed"] == ["Elle McGib"]


def test_background_npc_reference_resolves_through_the_gate(book):
    """A background entity is a valid resolution target — strict must pass."""
    cap_campaign(str(book), limit=LIMIT)
    npcs = _load(book, "npcs.json")
    plots = _load(book, "plots.json")
    plots["Rumour Mill"] = {"type": "side", "npcs": ["Walkon39"], "locations": ["The Hub"]}
    (book / "plots.json").write_text(json.dumps(plots))
    assert npcs["Walkon39"]["background"] is True

    run_reconcile(str(book))
    run_stubs(str(book))
    report = run_gate(str(book), strict=True)          # raises SystemExit(1) on unresolved
    assert report["unresolved"] == []
    assert _load(book, "plots.json")["Rumour Mill"]["npcs"] == ["Walkon39"]


def test_long_place_reference_survives_as_a_low_confidence_stub(book):
    run_reconcile(str(book))
    locations = _load(book, "locations.json")
    assert LONG_PLACE in locations, "a 7-word place name must not be dropped on word count"
    stub = locations[LONG_PLACE]
    assert stub["low_confidence"] is True
    # wired both ways to the hub, so it is reachable in play
    assert stub["connections"][0]["to"] == "The Hub"
    assert any(c["to"] == LONG_PLACE for c in locations["The Hub"]["connections"])
    assert _load(book, "plots.json")["The Long Descent"]["locations"] == ["The Hub", LONG_PLACE]


def test_slashed_and_unknown_names_are_stubbed_not_dropped():
    locations = {"Hub": {"connections": []}}
    npcs = {"Bob": {"tags": {"locations": ["Skull Empire / dungeon (location unknown)"]}}}
    report = reconcile(npcs, locations, {})
    assert report["dropped"] == []
    assert "Skull Empire / dungeon (location unknown)" in locations
    assert npcs["Bob"]["tags"]["locations"] == ["Skull Empire / dungeon (location unknown)"]


# Real Conan geography that a rule-phrase test misreads as prose: "upper level",
# "lower level", " via ". A plot or tag reference to any of these is a place.
REAL_PLACES = [
    "The Upper Level of the Tower of the Elephant",
    "The Lower Level Vault",
    "Kandahar via the Zhaibar Pass",
]


@pytest.mark.parametrize("place", REAL_PLACES)
def test_rule_phrase_shaped_place_names_survive_as_stubs(place):
    locations = {"Hub": {"connections": []}}
    npcs = {"Conan": {"tags": {"locations": [place]}}}
    plots = {"P": {"locations": [place]}}
    report = reconcile(npcs, locations, plots)
    assert report["dropped"] == [], f"{place!r} is a place, not routing prose"
    assert locations[place]["low_confidence"] is True
    assert plots["P"]["locations"] == [place]
    assert npcs["Conan"]["tags"]["locations"] == [place]


RULE_PROSE = "Transfer stations ending in 1"


def test_rule_prose_is_dropped_as_a_connection_target(tmp_path):
    (tmp_path / "locations.json").write_text(
        json.dumps({"Hub": {"connections": [{"to": RULE_PROSE}]}})
    )
    report = run_reconcile(str(tmp_path))
    locations = json.loads((tmp_path / "locations.json").read_text())
    assert report["dropped"] == [RULE_PROSE]
    assert RULE_PROSE not in locations
    assert locations["Hub"]["connections"] == []      # dead edge pruned

    facts = json.loads((tmp_path / "facts.json").read_text())
    assert any(RULE_PROSE in f["fact"] for f in facts[FACT_CATEGORY])


def test_the_same_string_is_a_place_when_a_plot_names_it():
    """A plot naming somewhere is the book saying it exists — stub, never drop."""
    locations = {"Hub": {"connections": []}}
    plots = {"P": {"locations": [RULE_PROSE]}}
    report = reconcile({}, locations, plots)
    assert report["dropped"] == []
    assert locations[RULE_PROSE]["low_confidence"] is True


def test_threat_and_mystery_plots_outrank_optional_in_the_cap():
    plots = {f"side{i}": {"type": "side"} for i in range(LIMIT)}
    plots["Siege"] = {"type": "threat"}
    plots["Whodunit"] = {"type": "mystery"}
    plots["Sidequest"] = {"type": "optional"}
    plots, background = cap_type(plots, "plots", "", set(), limit=LIMIT)
    assert plots["Siege"].get("background") is None
    assert plots["Whodunit"].get("background") is None
    assert "Sidequest" in background        # weakest type, displaced by 30 'side' plots


def test_extractor_synonyms_rank_at_their_canonical_weight():
    """`validate_plot_types` runs AFTER the cap, so the cap must map synonyms itself.

    An agent that typed "main quest" wrote the spine; ranking it raw drops the
    book's main arc below a take-it-or-leave-it errand.
    """
    assert plot_type_weight("main quest") == plot_type_weight("main")
    assert plot_type_weight("conflict") == plot_type_weight("threat")
    assert plot_type_weight("danger") == plot_type_weight("threat")
    # an unknown or blank type ranks where validate_plot_types will file it
    assert plot_type_weight("epilogue") == plot_type_weight("side")
    assert plot_type_weight("") == plot_type_weight("side")

    plots = {f"opt{i}": {"type": "optional"} for i in range(LIMIT)}
    plots["The Spine"] = {"type": "main quest"}
    plots["Errand"] = {"type": "optional"}
    plots, background = cap_type(plots, "plots", "", set(), limit=LIMIT)
    assert plots["The Spine"].get("background") is None
    assert "The Spine" not in background
    assert "Errand" in background


def test_background_entities_are_out_of_scope_for_batch_enhancement(book):
    """`gm-enhance.sh batch` costs a RAG round-trip per entity — tiering must bound it."""
    cap_campaign(str(book), limit=LIMIT)
    npcs = _load(book, "npcs.json")

    # __new__ + json_ops only: list_unenhanced reads files, and a real
    # EntityEnhancer would bootstrap an active campaign and a vector store.
    enhancer = EntityEnhancer.__new__(EntityEnhancer)
    enhancer.json_ops = JsonOperations(str(book))
    listed = {e["name"] for e in enhancer.list_unenhanced("npc")}

    active = {n for n, e in npcs.items() if not e.get("background")}
    background = {n for n, e in npcs.items() if e.get("background")}
    assert listed == active
    assert not (listed & background)


def test_promoting_a_party_member_clears_the_background_tier(tmp_path):
    world = tmp_path / "world-state"
    (world / "campaigns" / "camp").mkdir(parents=True)
    (world / "active-campaign.txt").write_text("camp")
    (world / "campaigns" / "camp" / "npcs.json").write_text(
        json.dumps({"Mordecai": {"name": "Mordecai", "background": True}})
    )
    mgr = NPCManager(world_state_dir=str(world))
    assert mgr.promote_to_party_member("Mordecai") is True

    npcs = json.loads((world / "campaigns" / "camp" / "npcs.json").read_text())
    assert "background" not in npcs["Mordecai"]        # active by definition
    assert npcs["Mordecai"]["is_party_member"] is True


def _world_with_plots(tmp_path, plots):
    world = tmp_path / "world-state"
    (world / "campaigns" / "camp").mkdir(parents=True)
    (world / "active-campaign.txt").write_text("camp")
    (world / "campaigns" / "camp" / "plots.json").write_text(json.dumps(plots))
    return world


TIERED_PLOTS = {
    "The Spine": {"type": "main", "status": "active"},
    "The Siege": {"type": "threat", "status": "active"},
    "The Errand": {"type": "side", "status": "active"},
    "Tavern Gossip": {"type": "side", "status": "active", "background": True},
    "A Rumour": {"type": "side", "status": "active", "background": True},
    "Old Debt": {"type": "personal", "status": "active", "background": True},
}


def test_scene_context_story_threads_skip_background_plots(tmp_path):
    """Background plots are real, but they are not what the scene is about."""
    world = _world_with_plots(tmp_path, TIERED_PLOTS)
    threads = SessionManager(str(world))._active_plot_threads(limit=None)

    assert len(threads) == 3
    named = " ".join(threads)
    for live in ("The Spine", "The Siege", "The Errand"):
        assert live in named
    for held in ("Tavern Gossip", "A Rumour", "Old Debt"):
        assert held not in named


def test_plot_threads_output_discloses_the_background_count(tmp_path):
    """The GM has to know they exist, or tiering reads as data loss."""
    world = _world_with_plots(tmp_path, TIERED_PLOTS)
    pm = PlotManager(str(world))
    out = pm.format_threads(pm.get_active_threads())

    assert "+3 background plots" in out
    assert "The Spine" in out
    assert "Tavern Gossip" not in out


def test_tag_gate_decides_presence_not_the_tier(tmp_path):
    """A background NPC is present iff tagged here — the same bar an active one clears."""
    world = tmp_path / "world-state"
    (world / "campaigns" / "camp").mkdir(parents=True)
    (world / "active-campaign.txt").write_text("camp")
    (world / "campaigns" / "camp" / "npcs.json").write_text(json.dumps({
        "Tagged Walkon": {"background": True, "tags": {"locations": ["The Hub"]}},
        "Untagged Walkon": {"background": True, "tags": {"locations": []}},
        "Tagged Lead": {"tags": {"locations": ["The Hub"]}},
        "Elsewhere Lead": {"tags": {"locations": ["Far Shore"]}},
    }))
    present = WorldSearcher(str(world)).search_npcs_by_tag("locations", "The Hub")

    assert set(present) == {"Tagged Walkon", "Tagged Lead"}
    assert "Untagged Walkon" not in present    # tiering leaks nothing into the scene
    assert "Elsewhere Lead" not in present
