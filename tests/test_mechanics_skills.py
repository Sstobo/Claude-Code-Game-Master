"""Tests for claudemd-extract-tables: mechanics tables moved to on-demand Skills."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ["dm-combat", "dm-spellcasting", "dm-conditions", "dm-levelup", "dm-dungeon"]


def test_each_mechanics_skill_exists_with_valid_frontmatter():
    for name in SKILLS:
        p = ROOT / ".claude" / "skills" / name / "SKILL.md"
        assert p.exists(), f"missing skill {name}"
        text = p.read_text(encoding="utf-8")
        assert text.startswith("---")
        assert f"name: {name}" in text
        assert "description:" in text


def test_claudemd_references_each_skill():
    # Post lean-core swap: the Action Router maps each action to its skill.
    cm = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Action Router" in cm
    for name in SKILLS:
        assert name in cm, f"CLAUDE.md must reference {name}"


def test_core_loop_remains_in_claudemd():
    cm = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    # The always-on essentials must NOT have been extracted.
    assert "## The Core Loop" in cm
    assert "persist" in cm.lower()
    assert "## Action Router" in cm


def test_combat_skill_has_xp_table():
    text = (ROOT / ".claude" / "skills" / "dm-combat" / "SKILL.md").read_text(encoding="utf-8")
    assert "XP by Challenge Rating" in text and "25,000" in text
