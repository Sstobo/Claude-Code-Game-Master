"""Tests for gm-md-slim: gm.md sheds templates, checklists, and pre-rolled stories."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _gm_md():
    return (ROOT / ".claude" / "commands" / "gm.md").read_text(encoding="utf-8")


BOX_DRAWING = "╔┌═║╚╗╝│─"


def test_gm_md_has_no_box_drawing_chars():
    text = _gm_md()
    for ch in BOX_DRAWING:
        assert ch not in text, f"gm.md must not contain box-drawing char {ch!r}"


def test_gm_md_one_shot_has_no_pre_rolled_story():
    text = _gm_md()
    lower = text.lower()
    assert "d6" not in lower or "scenario" not in lower
    assert "1-2:" not in text
    assert "Rescue mission" not in text
    assert "Monster hunt" not in text
    assert "Treasure hunt" not in text
    assert "3-5 encounters" not in text
    assert "skip extensive" not in lower
    assert "start fast and stay tight" in lower
    assert "player's appetite" in lower


def test_gm_md_create_character_has_no_ascii_art_mandate():
    text = _gm_md()
    lower = text.lower()
    assert "ascii art" not in lower
    assert "ascii-art" not in lower
    assert "emoji decoration" not in lower
    assert "phone-friendly" in lower


def test_gm_md_startup_has_no_mental_model_checklist():
    text = _gm_md()
    assert "Build Mental Model" not in text
    assert "WHERE is the party?" not in text
    assert "Step 1:" in text
    assert "Step 2:" in text
    assert "Step 4" not in text
