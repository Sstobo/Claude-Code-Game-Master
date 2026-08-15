"""QA eval for world-index-import-swarm: the write_index persistence helper.

The extractor swarm runs at /import time (Agent-tool subagents); this helper is
the code that persists their assembled roster into the bible. Adversarial on the
reduce rules: dedup case-insensitively, drop nameless, first note wins / blank
filled, merge with an existing index, touch no other bible field.
"""

import json

from lib import book_bible


def _campaign(tmp_path):
    cdir = tmp_path / "campaigns" / "wtest"
    cdir.mkdir(parents=True)
    (cdir / "world-bible.json").write_text(json.dumps({
        "name": "W", "voice": {}, "confirmed": False,
        "index": {"npcs": [], "locations": [], "items": [], "monsters": []},
    }), encoding="utf-8")
    return cdir


def test_dedups_drops_nameless_and_persists(tmp_path):
    cdir = _campaign(tmp_path)
    out = book_bible.write_index(cdir, {
        "npcs": [
            {"name": "Yara", "note": "The dread priest."},
            {"name": "yara", "note": "dup, different case"},
            {"name": "", "note": "nameless — dropped"},
            {"name": "  ", "note": "whitespace name — dropped"},
        ],
        "locations": [{"name": "The Tower of the Elephant", "note": "green stone"}],
        "items": [],
        "monsters": [{"name": "Yag-kosha", "note": ""}],
    })
    assert [e["name"] for e in out["npcs"]] == ["Yara"], "case-insensitive dedup + drop nameless"
    assert out["npcs"][0]["note"] == "The dread priest.", "first note wins over the dup"
    assert [e["name"] for e in out["locations"]] == ["The Tower of the Elephant"]
    assert [e["name"] for e in out["monsters"]] == ["Yag-kosha"]

    on_disk = json.loads((cdir / "world-bible.json").read_text(encoding="utf-8"))
    assert on_disk["index"] == out
    assert on_disk["name"] == "W" and on_disk["confirmed"] is False, "other fields untouched"


def test_merges_with_existing_and_fills_blank_note(tmp_path):
    cdir = _campaign(tmp_path)
    book_bible.write_index(cdir, {"npcs": [{"name": "Conan", "note": ""}],
                                  "locations": [], "items": [], "monsters": []})
    out = book_bible.write_index(cdir, {"npcs": [{"name": "Conan", "note": "A reaver."}],
                                        "locations": [], "items": [], "monsters": []})
    assert [e["name"] for e in out["npcs"]] == ["Conan"], "merge, not duplicate"
    assert out["npcs"][0]["note"] == "A reaver.", "later note fills the earlier blank"
