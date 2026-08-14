"""KIT block in scene context; signature_systems render; campaign_rules fallback."""

import json

from lib.session_manager import SessionManager
from lib.world_kit import WorldKit


def _world(tmp_path, slug, ruleset, overview=None):
    world = tmp_path / "world-state"
    campaign = world / "campaigns" / slug
    campaign.mkdir(parents=True)
    (world / "active-campaign.txt").write_text(slug, encoding="utf-8")
    (campaign / "ruleset.json").write_text(json.dumps(ruleset), encoding="utf-8")
    (campaign / "campaign-overview.json").write_text(
        json.dumps(overview or {"name": slug}), encoding="utf-8"
    )
    return str(world)


def _kit_section(ctx: str) -> str:
    assert "--- KIT ---" in ctx
    rest = ctx.split("--- KIT ---", 1)[1]
    nxt = rest.find("\n--- ")
    return rest if nxt < 0 else rest[:nxt]


# --- scene context -----------------------------------------------------------

def test_dcc_context_kit_block_names_custom_d20_resource_axis(dcc_world):
    ctx = SessionManager(dcc_world).get_full_context()
    kit = _kit_section(ctx)
    assert "kit: custom" in kit
    assert "resolution: d20-vs-dc" in kit
    assert "progression: resource-axis" in kit
    assert "vitals: hp" in kit


def test_dnd5e_kit_named_in_context(tmp_path):
    world = _world(tmp_path, "realms", {
        "name": "Forgotten Realms",
        "kit": "dnd5e",
        "stat_schema": {"attributes": ["str"], "vitals": ["hp"]},
        "progression": {"model": "xp-levels"},
        "resolution": {"model": "d20-vs-dc"},
        "active_agents": [],
    })
    kit = _kit_section(SessionManager(world).get_full_context())
    assert "kit: dnd5e" in kit


def test_signature_systems_list_appear_in_world_rules(tmp_path):
    world = _world(tmp_path, "tide", {
        "name": "Tideworld",
        "kit": "custom",
        "progression": {"model": "milestone"},
        "resolution": {"model": "d20-vs-dc"},
        "signature_systems": [
            {"name": "Tide-oaths", "summary": "every spell is a debt the sea collects"},
        ],
    }, overview={"name": "tide", "campaign_rules": {"legacy_flavor": "should not win"}})
    ctx = SessionManager(world).get_full_context()
    assert "YOUR WORLD'S RULES" in ctx
    assert "Tide-oaths" in ctx
    assert "every spell is a debt the sea collects" in ctx
    assert "legacy_flavor" not in ctx


def test_signature_systems_dict_appear_in_world_rules(tmp_path):
    world = _world(tmp_path, "hyborian", {
        "name": "The Hyborian Age",
        "kit": "hyborian",
        "progression": {"model": "milestone"},
        "resolution": {"model": "d20-vs-dc"},
        "signature_systems": {
            "Blood-priced sorcery": "Casting costs HP; no spell slots",
        },
    })
    ctx = SessionManager(world).get_full_context()
    assert "YOUR WORLD'S RULES" in ctx
    assert "Blood-priced sorcery" in ctx
    assert "Casting costs HP" in ctx


def test_campaign_rules_fallback_when_no_signature_systems(tmp_path):
    world = _world(tmp_path, "legacy", {
        "name": "Old World",
        "kit": "custom",
        "progression": {"model": "milestone"},
        "resolution": {"model": "d20-vs-dc"},
    }, overview={
        "name": "legacy",
        "campaign_rules": {"loot_box_system": "award a distinctive zzyzx box"},
    })
    ctx = SessionManager(world).get_full_context()
    assert "YOUR WORLD'S RULES" in ctx
    assert "loot_box_system" in ctx
    assert "zzyzx" in ctx


def test_dcc_still_renders_campaign_rules(dcc_world):
    ctx = SessionManager(dcc_world).get_full_context()
    assert "loot_box_system" in ctx


def test_kit_block_skipped_when_worldkit_fails(dcc_world, monkeypatch):
    def boom(*_a, **_k):
        raise RuntimeError("no campaign")

    monkeypatch.setattr("lib.session_manager.WorldKit", boom)
    ctx = SessionManager(dcc_world).get_full_context()
    assert "--- KIT ---" not in ctx
    assert "SESSION CONTEXT" in ctx
    assert "loot_box_system" in ctx  # campaign_rules fallback still renders


# --- WorldKit accessors ------------------------------------------------------

def test_worldkit_accepts_dcc_world_dir(dcc_world):
    kit = WorldKit(dcc_world)
    assert kit.kit() == "custom"
    assert kit.resolution_model() == "d20-vs-dc"
    assert kit.progression_model() == "resource-axis"
    assert kit.skills() == []
    assert kit.signature_systems() == []


def test_signature_systems_normalizes_dict_form(tmp_path):
    world = _world(tmp_path, "conan", {
        "name": "The Hyborian Age",
        "signature_systems": {
            "Steel before sorcery": "mundane steel always works",
            "Blood-priced sorcery": {
                "summary": "casting costs HP",
                "rules": "no Vancian slots",
            },
        },
    })
    systems = WorldKit(world).signature_systems()
    by_name = {s["name"]: s for s in systems}
    assert by_name["Steel before sorcery"]["summary"] == "mundane steel always works"
    assert by_name["Blood-priced sorcery"]["summary"] == "casting costs HP"
    assert by_name["Blood-priced sorcery"]["rules"] == "no Vancian slots"


def test_signature_systems_normalizes_list_form(tmp_path):
    world = _world(tmp_path, "listy", {
        "name": "List World",
        "signature_systems": [
            {"name": "Tide-oaths", "summary": "debt the sea collects", "rules": "pay or drown"},
            "loot boxes",
        ],
    })
    systems = WorldKit(world).signature_systems()
    assert systems[0]["name"] == "Tide-oaths"
    assert systems[0]["summary"] == "debt the sea collects"
    assert systems[0]["rules"] == "pay or drown"
    assert systems[1] == {"name": "loot boxes", "summary": "loot boxes"}


def test_skills_from_list_or_empty(tmp_path):
    world = _world(tmp_path, "skilled", {
        "name": "Skilled",
        "skills": ["might", "guile"],
    })
    assert WorldKit(world).skills() == ["might", "guile"]
