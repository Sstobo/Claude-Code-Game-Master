"""Whole-campaign saves: versioned snapshots, legacy partial restore, autosave rotation."""

import json
from pathlib import Path

from lib.session_manager import SessionManager

CAMPAIGN = "dungeon-crawler-carl"


def _camp(dcc_world) -> Path:
    return Path(dcc_world) / "campaigns" / CAMPAIGN


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _seed_extra_state(camp: Path) -> None:
    """Files the DCC fixture omits — must still round-trip when present."""
    _write(camp / "threat-clocks.json", {
        "Floor Collapse": {"current": 2, "max": 4, "advance_on": "event"},
    })
    _write(camp / "campaign-memory.json", {"entries": [{"text": "we escaped floor 1"}]})
    _write(camp / "chronicler.json", {"name": "Astreus", "style": "ink"})
    _write(camp / "world-tick-log.json", {"ticks": [{"id": "t1"}]})
    _write(camp / "combat_state.json", {
        "active": True, "round": 3, "combatants": [{"name": "Goblin", "hp_current": 4}],
    })
    _write(camp / "fallen" / "tandy-archive.json", {"name": "Tandy", "status": "dead"})
    _write(camp / "loremaster-cache.json", {"The Inn": {"brief": "derived, skip me"}})


def _snapshot_from_save(sm: SessionManager, filename: str) -> dict:
    return _load(sm.saves_dir / filename)["snapshot"]


def _disk_value(camp: Path, key: str):
    if key == "characters":
        return _load(camp / "character.json")
    path = camp / key
    if key.endswith(".md"):
        return path.read_text(encoding="utf-8")
    return _load(path)


def test_round_trip_restores_every_snapshotted_file(dcc_world):
    camp = _camp(dcc_world)
    _seed_extra_state(camp)
    sm = SessionManager(dcc_world)

    filename = sm.create_save("checkpoint")
    save = _load(sm.saves_dir / filename)
    assert save["save_version"] == SessionManager.SAVE_VERSION
    snapshot = save["snapshot"]

    assert "plots.json" in snapshot
    assert "items.json" in snapshot
    assert "threat-clocks.json" in snapshot
    assert "combat_state.json" in snapshot
    assert "fallen/tandy-archive.json" in snapshot
    assert "characters" in snapshot
    assert "loremaster-cache.json" not in snapshot
    assert not any(k.startswith("saves/") for k in snapshot)

    # Mutate live state after the snapshot.
    plots = _load(camp / "plots.json")
    first_plot = next(iter(plots))
    plots[first_plot]["status"] = "MUTATED"
    _write(camp / "plots.json", plots)

    clocks = _load(camp / "threat-clocks.json")
    clocks["Floor Collapse"]["current"] = 99
    _write(camp / "threat-clocks.json", clocks)

    items = _load(camp / "items.json")
    items["__mutated__"] = {"name": "not in snapshot"}
    _write(camp / "items.json", items)

    npcs = _load(camp / "npcs.json")
    npcs["__mutated__"] = {"description": "anachronism"}
    _write(camp / "npcs.json", npcs)

    char = _load(camp / "character.json")
    char["hp"] = {"current": 1, "max": char.get("hp", {}).get("max", 1)}
    _write(camp / "character.json", char)

    (camp / "session-log.md").write_text("# MUTATED LOG\n", encoding="utf-8")

    assert sm.restore_save("checkpoint")

    for key, expected in snapshot.items():
        actual = _disk_value(camp, key)
        if key == "characters":
            assert actual == expected["character"]
        else:
            assert actual == expected, f"{key} did not round-trip"


def test_legacy_restore_warns_what_was_not_covered(dcc_world, capsys):
    camp = _camp(dcc_world)
    _seed_extra_state(camp)
    sm = SessionManager(dcc_world)

    legacy = {
        "name": "old-world",
        "created": "2026-01-01T00:00:00+00:00",
        "session_number": 1,
        "snapshot": {
            "campaign_overview": _load(camp / "campaign-overview.json"),
            "npcs": _load(camp / "npcs.json"),
            "locations": _load(camp / "locations.json"),
            "facts": _load(camp / "facts.json"),
            "consequences": _load(camp / "consequences.json"),
            "characters": {"character": _load(camp / "character.json")},
        },
    }
    (sm.saves_dir / "20260101-000000-old-world.json").write_text(
        json.dumps(legacy, indent=2), encoding="utf-8")

    npcs_after = _load(camp / "npcs.json")
    npcs_after["__present_time__"] = {"description": "should revert"}
    _write(camp / "npcs.json", npcs_after)

    plots_after = _load(camp / "plots.json")
    plots_after["__present_time__"] = {"status": "should stay mixed"}
    _write(camp / "plots.json", plots_after)

    capsys.readouterr()
    assert sm.restore_save("old-world")
    out = capsys.readouterr().out
    assert "WARNING" in out and "Partial restore" in out
    assert "plots.json" in out
    assert "items.json" in out
    assert "threat-clocks.json" in out

    restored_npcs = _load(camp / "npcs.json")
    assert "__present_time__" not in restored_npcs
    mixed_plots = _load(camp / "plots.json")
    assert "__present_time__" in mixed_plots


def test_autosaves_rotate_and_named_saves_persist(dcc_world):
    sm = SessionManager(dcc_world)
    sm.get_iso_timestamp = lambda: "20260814-153000"

    for _ in range(10):
        sm.create_save("autosave")
    sm.create_save("before-boss")

    autosaves = sm._autosave_files()
    named = [p for p in sm.saves_dir.glob("*.json") if "before-boss" in p.name]

    assert len(autosaves) <= SessionManager.AUTOSAVE_KEEP
    assert len(autosaves) == SessionManager.AUTOSAVE_KEEP
    assert len(named) == 1

    newest = sm._find_save("autosave")
    assert newest is not None
    assert newest == autosaves[-1]
    assert newest.name != named[0].name


def test_missing_files_are_omitted_not_stubbed(dcc_world):
    camp = _camp(dcc_world)
    assert not (camp / "threat-clocks.json").exists()
    sm = SessionManager(dcc_world)
    snapshot = _snapshot_from_save(sm, sm.create_save("thin"))
    assert "threat-clocks.json" not in snapshot
    assert "combat_state.json" not in snapshot
    assert "loremaster-cache.json" not in snapshot
    assert snapshot.get("plots.json") != {}
