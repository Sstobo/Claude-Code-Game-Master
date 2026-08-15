"""QA eval for world-index-schema-context.

Proves the net-new behavior: the WORLD INDEX block reaches the model via
get_full_context when the bible carries an index, stays absent when it does
not, and validate_bible accepts a well-formed index while rejecting malformed
ones. Adversarial: each assertion would fail on a plausible real bug (empty
header emitted, notes dropped, malformed index silently accepted).
"""

import json
from pathlib import Path

from lib.session_manager import SessionManager
from lib.world_bible import validate_bible


def _bible_path(world_dir: str) -> Path:
    base = Path(world_dir)
    active = (base / "active-campaign.txt").read_text().strip()
    return base / "campaigns" / active / "world-bible.json"


def _write_index(world_dir: str, index) -> None:
    p = _bible_path(world_dir)
    bible = json.loads(p.read_text()) if p.exists() else {}
    bible["index"] = index
    p.write_text(json.dumps(bible))


def test_index_block_surfaces_in_context(dcc_world):
    _write_index(dcc_world, {
        "npcs": [{"name": "Yara", "note": "The dread priest of the Elephant Tower."}],
        "locations": [{"name": "The Tower of the Elephant", "note": "A tower of green stone."}],
        "items": [],
        "monsters": [{"name": "Yag-kosha", "note": "An alien captive of the tower."}],
    })
    ctx = SessionManager(dcc_world).get_full_context()
    assert "WORLD INDEX" in ctx, "index block must reach the model"
    assert "Yara" in ctx and "dread priest" in ctx, "npc name + note must render"
    assert "The Tower of the Elephant" in ctx, "location entry must render"
    assert "Yag-kosha" in ctx, "monster entry must render"


def test_empty_index_emits_no_header(dcc_world):
    _write_index(dcc_world, {"npcs": [], "locations": [], "items": [], "monsters": []})
    assert "WORLD INDEX" not in SessionManager(dcc_world).get_full_context()


def test_absent_index_emits_no_header(dcc_world):
    p = _bible_path(dcc_world)
    if p.exists():
        bible = json.loads(p.read_text())
        bible.pop("index", None)
        p.write_text(json.dumps(bible))
    assert "WORLD INDEX" not in SessionManager(dcc_world).get_full_context()


def test_validate_accepts_good_and_absent_index():
    base = {
        "name": "X", "voice": {}, "tone": "t", "themes": [],
        "factions": {"nodes": [], "edges": []},
        "geography": {"nodes": [], "edges": []},
        "signature_systems": [],
    }
    ok, _ = validate_bible(dict(base))  # absent index
    assert ok, "absent index must validate"
    good = dict(base, index={"npcs": [{"name": "A", "note": "b"}],
                             "locations": [], "items": [], "monsters": []})
    ok, errs = validate_bible(good)
    assert ok, f"good index must validate, got {errs}"


def test_validate_rejects_malformed_index():
    base = {
        "name": "X", "voice": {}, "tone": "t", "themes": [],
        "factions": {"nodes": [], "edges": []},
        "geography": {"nodes": [], "edges": []},
        "signature_systems": [],
    }
    missing_note = dict(base, index={"npcs": [{"name": "A"}], "locations": [],
                                     "items": [], "monsters": []})
    ok, _ = validate_bible(missing_note)
    assert not ok, "entry missing 'note' must fail validation"

    non_list = dict(base, index={"npcs": {"name": "A", "note": "b"}, "locations": [],
                                 "items": [], "monsters": []})
    ok, _ = validate_bible(non_list)
    assert not ok, "non-list bucket must fail validation"
