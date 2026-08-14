"""Tests for claudemd-lean-core-router: lean CLAUDE.md + mechanics/craft/framework Skills.

CLAUDE.md was swapped to the lean core (the 1227-line original is in git history).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALL_SKILLS = ["gm-combat", "gm-spellcasting", "gm-conditions", "gm-levelup",
              "gm-dungeon", "gm-craft", "gm-skills", "gm-social"]


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


def test_lean_core_drops_beat_mandates():
    text = _claude_md()
    assert "exactly 3 numbered" not in text
    assert "AT MOST ONE new world development" not in text
    assert "Test before sending" not in text


def test_gm_md_death_handoff_has_no_verbatim_menu():
    text = (ROOT / ".claude" / "commands" / "gm.md").read_text(encoding="utf-8")
    start = text.index("## CHARACTER DEATH")
    end = text.index("## SAVE SESSION", start)
    death = text[start:end]
    assert "Present exactly" not in death
    assert "1. Take over a PARTY MEMBER" not in death
    assert "2. Roll a NEW character" not in death
    assert "3. Step in as a CANON" not in death


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
    text = (ROOT / ".claude" / "skills" / "gm-craft" / "SKILL.md").read_text(encoding="utf-8")
    assert "Yes, and" in text and "Persist before narrating" in text


DND_ONLY_SKILLS = ["gm-combat", "gm-levelup", "gm-spellcasting"]


def test_dnd_only_skills_carry_the_kit_guard():
    for name in DND_ONLY_SKILLS:
        text = (ROOT / ".claude" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "KIT" in text, f"{name} must defer to the scene-context KIT block"
        assert "dnd5e" in text, f"{name} must check for dnd5e"
        assert "world_kit.py info" not in text, (
            f"{name} must not instruct a world_kit.py info call"
        )


def test_no_skill_instructs_world_kit_info():
    for name in ALL_SKILLS:
        text = (ROOT / ".claude" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "world_kit.py info" not in text, (
            f"{name} must not instruct world_kit.py info for what context now carries"
        )


def test_judgment_skills_defer_five_e_tables_to_kit_block():
    for name in ("gm-skills", "gm-social", "gm-conditions"):
        text = (ROOT / ".claude" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "KIT" in text, f"{name} must defer 5e tables to the KIT block"
        assert "dnd5e" in text, f"{name} must name dnd5e as the kit that unlocks them"


def test_world_kit_exposes_kit_identity():
    import json
    import subprocess
    import sys as _sys
    r = subprocess.run([_sys.executable, str(ROOT / "lib" / "world_kit.py"), "info", "--json"],
                       capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)["data"]
    assert data["kit"] in ("dnd5e", "custom") or isinstance(data["kit"], str)
