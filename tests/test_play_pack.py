"""Play pack: primer in context, stage writes a room, from-book writes one name."""

import json
from pathlib import Path

from lib.play_pack import (
    apply_stage,
    empty_pack,
    from_book,
    load_pack,
    normalize_pack,
    pack_is_set,
    render_primer,
    save_pack,
)
from lib.session_manager import SessionManager


def _campaign(tmp_path):
    cdir = tmp_path / "world-state" / "campaigns" / "packtest"
    cdir.mkdir(parents=True)
    (cdir / "campaign-overview.json").write_text(json.dumps({
        "campaign_name": "Pack Test",
        "player_position": {"current_location": None},
    }))
    (cdir / "npcs.json").write_text("{}")
    (cdir / "locations.json").write_text("{}")
    return cdir


def test_empty_pack_renders_nothing():
    assert render_primer(empty_pack()) == ""
    assert pack_is_set(normalize_pack({})) is False


def test_filled_pack_renders_primer():
    block = render_primer({
        "whose_story": "Bêlit",
        "room": "The Tigress",
        "present": ["Bêlit", "N'Yaga"],
        "exits": ["the Black Coast"],
        "hook": "A sail on the horizon.",
        "offstage": ["Stygia"],
        "primer": "They came to meet the queen of the Black Coast.",
    })
    assert "--- PRIMER ---" in block
    assert "The Tigress" in block
    assert "Bêlit" in block
    assert "Stygia" in block
    assert "A sail on the horizon." in block
    assert "from-book" in block


def test_save_pack_sets_position_and_does_not_fake_a_session(tmp_path):
    cdir = _campaign(tmp_path)
    save_pack(cdir, {"room": "The Maul", "hook": "A knife in the dark."})
    pack = load_pack(cdir)
    assert pack["room"] == "The Maul"
    overview = json.loads((cdir / "campaign-overview.json").read_text())
    assert overview["player_position"]["current_location"] == "The Maul"
    assert overview["opening_hook"]["hook"] == "A knife in the dark."
    assert not (cdir / "session-log.md").exists()


def test_pack_closes_reseed_latch(tmp_path):
    """The pack is the matched opening, so it closes the reseed latch. Handoffs
    (`set_current_player` / `onboard`) only call reseed_opening while this flag
    is falsy — closing it here stops a later death-swap from teleporting the PC
    onto a mid-campaign plot's location."""
    cdir = _campaign(tmp_path)
    save_pack(cdir, {"room": "The Tigress", "hook": "A sail on the horizon."})
    overview = json.loads((cdir / "campaign-overview.json").read_text())
    assert overview["opening_matched_to_pc"] is True


def test_context_omits_primer_when_pack_empty(dcc_world):
    ctx = SessionManager(dcc_world).get_full_context()
    assert "--- PRIMER ---" not in ctx


def test_context_includes_primer_when_pack_set(dcc_world):
    root = Path(dcc_world)
    cdir = root / "campaigns" / "dungeon-crawler-carl"
    save_pack(cdir, {
        "whose_story": "Carl",
        "room": "The saferoom",
        "hook": "The collapse clock is ticking.",
        "present": ["Donut"],
        "offstage": ["Floor 2"],
    })
    ctx = SessionManager(dcc_world).get_full_context()
    assert "--- PRIMER ---" in ctx
    assert "The saferoom" in ctx
    assert "The collapse clock is ticking." in ctx
    assert "Donut" in ctx
    assert "Floor 2" in ctx
    assert "### Session Ended" not in ctx


def test_stage_writes_room_people_exits_only(tmp_path):
    cdir = _campaign(tmp_path)
    save_pack(cdir, {
        "room": "The Bedchamber",
        "present": ["Ascalante"],
        "exits": ["the corridor"],
        "hook": "They mean to knife the king.",
        "primer": "Night in Tarantia.",
    })
    result = apply_stage(cdir)
    assert result["ok"] is True
    locs = json.loads((cdir / "locations.json").read_text())
    npcs = json.loads((cdir / "npcs.json").read_text())
    assert set(locs) == {"The Bedchamber", "the corridor"}
    assert set(npcs) == {"Ascalante"}
    assert npcs["Ascalante"]["tags"]["locations"] == ["The Bedchamber"]
    assert any(
        c.get("to") == "the corridor" and c.get("path") == "visible from here"
        for c in locs["The Bedchamber"]["connections"]
    )


def test_from_book_writes_one_npc(tmp_path):
    cdir = _campaign(tmp_path)
    r = from_book(cdir, "Valeria", kind="npc", description="A sheathed sword and a hard grin.")
    assert r == {"ok": True, "kind": "npc", "name": "Valeria"}
    npcs = json.loads((cdir / "npcs.json").read_text())
    assert list(npcs) == ["Valeria"]
    assert "hard grin" in npcs["Valeria"]["description"]
    again = from_book(cdir, "Valeria", kind="npc", description="nope")
    assert again["ok"] is False
    assert list(json.loads((cdir / "npcs.json").read_text())) == ["Valeria"]


def test_from_book_writes_one_location(tmp_path):
    cdir = _campaign(tmp_path)
    r = from_book(cdir, "The Tower of the Elephant", kind="location",
                  description="A spire over Arenjun.")
    assert r["ok"] is True
    locs = json.loads((cdir / "locations.json").read_text())
    assert list(locs) == ["The Tower of the Elephant"]
