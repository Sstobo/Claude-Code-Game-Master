"""Tests for claudemd-lean-core-router: lean CLAUDE.md + mechanics/craft/framework Skills.

CLAUDE.md was swapped to the lean core (the 1227-line original is in git history).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALL_SKILLS = ["dm-combat", "dm-spellcasting", "dm-conditions", "dm-levelup",
              "dm-dungeon", "dm-craft", "dm-skills", "dm-social"]


def _claude_md():
    return (ROOT / "CLAUDE.md").read_text(encoding="utf-8")


def test_claude_md_is_lean():
    text = _claude_md()
    assert len(text.splitlines()) < 320, "CLAUDE.md should be the lean core now"
    assert "LEAN CORE" in text


def test_lean_core_keeps_always_on_essentials():
    text = _claude_md()
    assert "## The Core Loop" in text
    assert "Persist" in text
    assert "Action Router" in text
    assert "Golden Rules" in text


def test_lean_core_routes_to_all_skills_not_inline_tables():
    text = _claude_md()
    for skill in ALL_SKILLS:
        assert skill in text, f"CLAUDE.md must route to {skill}"
    assert "25,000" not in text  # no inline XP-by-CR table


def test_lean_core_keeps_load_bearing_sections():
    # The audit's must-restore-inline items.
    text = _claude_md()
    assert "Movement" in text
    assert "Output Format" in text
    assert "Auto Memory Policy" in text
    assert "uv run python" in text
    assert "Search Guide" in text


def test_all_skills_exist_with_frontmatter():
    for name in ALL_SKILLS:
        p = ROOT / ".claude" / "skills" / name / "SKILL.md"
        assert p.exists(), f"missing skill {name}"
        assert f"name: {name}" in p.read_text(encoding="utf-8")


def test_craft_skill_preserves_the_soul():
    text = (ROOT / ".claude" / "skills" / "dm-craft" / "SKILL.md").read_text(encoding="utf-8")
    assert "Yes, and" in text and "Persist before narrating" in text
