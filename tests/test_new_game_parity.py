"""/new-game must open a world as alive as /import does.

An authored world used to open dead: no plots.json (so STORY THREADS was empty),
no story spine, no threat clocks, a null starting location and an empty rules
block. These cover the parity — consolidation carries the axes' authored plots
into plots.json, and the same four passes an import runs turn them into an arc,
live pressure, a place to stand and a rules block.

Everything runs against a throwaway world-state under tmp_path via the
GM_WORLD_STATE_BASE seam, never a live campaign.
"""

import json

import pytest

from lib.book_bible import write_campaign_rules
from lib.campaign_manager import CampaignManager
from lib.clock_seed import seed_from_campaign
from lib.identity_onboarding import IdentityOnboarding
from lib.opening_seed import seed_opening
from lib.player_manager import PlayerManager
from lib.plot_spine import apply_spine
from lib.schemas import PLOT_TYPES
from lib.world_author import WorldAuthor

CAMPAIGN = "Drowned Coast"

BIBLE = {
    "name": "The Drowned Coast",
    "tone": "salt-bitten sword-and-sorcery",
    "themes": ["debt to the sea", "kings who cannot swim"],
    "voice": {"style": "terse, muscular, sensory", "vocab": ["tide-oath"], "sample_passages": []},
    "factions": {"nodes": [{"name": "The Tide-Oathed"}], "edges": []},
    "geography": {"nodes": [{"name": "Kelp Harbour"}], "edges": []},
    "signature_systems": ["Tide-oaths: every spell is a debt the sea collects"],
    "confirmed": False,
}

# The geography axis authors places and no plots — the backward-compat case.
GEOGRAPHY_AXIS = {
    "locations": {
        "Kelp Harbour": {
            "position": "the last dry quay on the drowned coast",
            "connections": [{"to": "The Weeping Stair", "path": "a barnacled causeway"}],
            "description": "Rope, rot and salt; the tide line climbs the doors each year.",
        },
        "The Weeping Stair": {
            "position": "cut into the cliff above the harbour",
            "connections": [{"to": "Kelp Harbour", "path": "the causeway"}],
            "description": "Nine hundred steps that run with seawater in dry weather.",
        },
    },
    "facts": {"geography": ["The coast has drowned three cities in living memory."]},
}

# The factions axis authors the conflicts — a main spine plot and a threat whose
# description names an explicit countdown (which is what seeds a clock).
FACTIONS_AXIS = {
    "npcs": {
        "Harl the Tide-Oathed": {
            "description": "A priest who sold his voice to the tide and wants it back.",
            "attitude": "suspicious",
            "tags": {"locations": ["Kelp Harbour"], "quests": []},
        }
    },
    "plots": {
        "The Tide-Oath Comes Due": {
            "type": "main",
            "description": "Harl's oath matures and the sea has come to collect the harbour with it.",
            "npcs": ["Harl the Tide-Oathed"],
            "locations": ["Kelp Harbour"],
            "status": "active",
        },
        "The Ninth Tide": {
            "type": "threat",
            "description": "In 9 days the ninth tide crests the Weeping Stair and the harbour collapse begins.",
            "npcs": [],
            "locations": ["The Weeping Stair"],
            "status": "active",
            "consequences": "Kelp Harbour drowns with everyone still in it.",
        },
    },
    "facts": {"plot_local": ["The harbourmaster is hiding the tide charts."]},
}


@pytest.fixture
def authored_campaign(isolated_world_state):
    """A tmp campaign holding a bible plus two axes' authored contributions."""
    cm = CampaignManager()
    cdir = cm.create(CAMPAIGN, CAMPAIGN)
    assert cdir is not None
    assert cm.set_active(CAMPAIGN)

    (cdir / "world-bible.json").write_text(json.dumps(BIBLE), encoding="utf-8")
    authored = cdir / "authored"
    authored.mkdir()
    (authored / "geography.json").write_text(json.dumps(GEOGRAPHY_AXIS), encoding="utf-8")
    (authored / "factions.json").write_text(json.dumps(FACTIONS_AXIS), encoding="utf-8")
    return cdir


def _ground(base, cdir):
    """Phase E's chain: consolidate, then the four passes /import runs."""
    report = WorldAuthor().consolidate()
    write_campaign_rules(cdir)
    spine = apply_spine(cdir)
    clocks = seed_from_campaign(str(base), cdir)
    opening = seed_opening(cdir)
    return report, spine, clocks, opening


def _read(cdir, name):
    return json.loads((cdir / name).read_text(encoding="utf-8"))


def test_consolidation_carries_typed_plots_into_plots_json(authored_campaign):
    report = WorldAuthor().consolidate()

    assert report["plots"] == 2
    plots = _read(authored_campaign, "plots.json")
    assert set(plots) == {"The Tide-Oath Comes Due", "The Ninth Tide"}
    for name, plot in plots.items():
        assert plot["type"] in PLOT_TYPES
        assert plot["name"] == name
        assert plot["status"] == "active"
    assert plots["The Tide-Oath Comes Due"]["type"] == "main"
    assert plots["The Ninth Tide"]["type"] == "threat"
    assert plots["The Tide-Oath Comes Due"]["npcs"] == ["Harl the Tide-Oathed"]
    # The facts/locations/npcs merges are untouched by the new one.
    assert report["locations"] == 2 and report["npcs"] == 1 and report["facts"] == 2


def test_an_axis_with_no_plots_still_consolidates(authored_campaign):
    """Backward compat: the geography axis emits no `plots` key at all."""
    (authored_campaign / "authored" / "factions.json").unlink()

    report = WorldAuthor().consolidate()

    assert report["files"] == 1 and report["plots"] == 0
    assert report["locations"] == 2
    assert not (authored_campaign / "plots.json").exists()  # never clobbered with {}


def test_consolidation_is_idempotent_for_plots(authored_campaign):
    WorldAuthor().consolidate()
    plots = _read(authored_campaign, "plots.json")
    plots["The Ninth Tide"]["status"] = "completed"
    (authored_campaign / "plots.json").write_text(json.dumps(plots), encoding="utf-8")

    report = WorldAuthor().consolidate()

    assert report["plots"] == 0
    assert _read(authored_campaign, "plots.json")["The Ninth Tide"]["status"] == "completed"


def test_an_authored_world_opens_alive(isolated_world_state, authored_campaign):
    report, spine, clocks, opening = _ground(isolated_world_state, authored_campaign)

    # Plots exist and are typed — STORY THREADS has something to show.
    assert report["plots"] == 2

    # A story spine, ordered from the main plots.
    assert spine["arc"] == ["The Tide-Oath Comes Due"]
    assert _read(authored_campaign, "campaign-overview.json")["story_spine"]["arc"]

    # Live pressure: the 9-day countdown became a real threat clock.
    assert clocks["seeded"] >= 1
    seeded = _read(authored_campaign, "threat-clocks.json")
    assert seeded
    clock = seeded[clocks["clocks"][0]["name"]]
    assert clock["max"] == 9 and clock["linked_plot"] == "The Ninth Tide"

    # A place to stand, and a hook to offer — not a started plot.
    assert opening["seeded"] is True
    overview = _read(authored_campaign, "campaign-overview.json")
    assert overview["player_position"]["current_location"] == "Kelp Harbour"
    hook = overview.get("opening_hook") or {}
    assert hook.get("location") == "Kelp Harbour"
    assert hook.get("plot") == "The Tide-Oath Comes Due"

    # The rules block the GM reads every beat, derived from the bible.
    assert overview["campaign_rules"]["signature_systems"] == BIBLE["signature_systems"]


def test_first_set_current_player_reseeds_opening(isolated_world_state, authored_campaign):
    """Phase E's seed-opening is provisional; set reseeds while opening_matched_to_pc is unset."""
    _ground(isolated_world_state, authored_campaign)

    plots = _read(authored_campaign, "plots.json")
    plots["The Salt-Road Bargain"] = {
        "type": "main",
        "description": "A pirate charter signed in blood on the salt-road.",
        "npcs": ["Belit"],
        "locations": ["The Weeping Stair"],
        "status": "available",
    }
    (authored_campaign / "plots.json").write_text(json.dumps(plots), encoding="utf-8")
    ov = _read(authored_campaign, "campaign-overview.json")
    ov["story_spine"]["arc"] = ["The Tide-Oath Comes Due", "The Salt-Road Bargain"]
    ov["current_character"] = None
    (authored_campaign / "campaign-overview.json").write_text(json.dumps(ov), encoding="utf-8")
    assert not ov.get("opening_matched_to_pc")

    (authored_campaign / "character.json").write_text(json.dumps({
        "name": "Belit", "level": 1, "hp": {"current": 10, "max": 10},
        "aliases": ["Queen of the Black Coast"],
        "concept": "pirate queen signing a salt-road charter",
    }), encoding="utf-8")

    assert PlayerManager().set_current_player("Belit")

    ov = _read(authored_campaign, "campaign-overview.json")
    assert ov["current_character"] == "Belit"
    assert ov.get("opening_matched_to_pc") is True
    assert ov["player_position"]["current_location"] == "The Weeping Stair"
    hook = ov.get("opening_hook") or {}
    assert hook.get("location") == "The Weeping Stair"
    assert hook.get("plot") == "The Salt-Road Bargain"
    assert "salt-road" in (hook.get("hook") or "").lower()


def test_onboard_reseeds_authored_world_opening(isolated_world_state, authored_campaign):
    """/new-game handoff is onboard, not set — the opening must match that PC."""
    _ground(isolated_world_state, authored_campaign)

    plots = _read(authored_campaign, "plots.json")
    plots["The Salt-Road Bargain"] = {
        "type": "main",
        "description": "A pirate charter signed in blood on the salt-road.",
        "npcs": ["Belit"],
        "locations": ["The Weeping Stair"],
        "status": "available",
    }
    (authored_campaign / "plots.json").write_text(json.dumps(plots), encoding="utf-8")
    ov = _read(authored_campaign, "campaign-overview.json")
    ov["story_spine"]["arc"] = ["The Tide-Oath Comes Due", "The Salt-Road Bargain"]
    (authored_campaign / "campaign-overview.json").write_text(json.dumps(ov), encoding="utf-8")

    result = IdentityOnboarding().onboard(
        "original", name="Belit", concept="pirate queen signing a salt-road charter",
    )
    assert result["success"]

    ov = _read(authored_campaign, "campaign-overview.json")
    assert ov["current_character"] == "Belit"
    assert ov.get("opening_matched_to_pc") is True
    assert ov["player_position"]["current_location"] == "The Weeping Stair"
    hook = ov.get("opening_hook") or {}
    assert hook.get("location") == "The Weeping Stair"
    assert hook.get("plot") == "The Salt-Road Bargain"
    assert "salt-road" in (hook.get("hook") or "").lower()
