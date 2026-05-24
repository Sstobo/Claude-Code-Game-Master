"""Provider skeleton tests — Phase 1 placeholder behavior."""
import pytest

from lib import ruleset
import rulesets.dnd_5e  # noqa: F401 — registers DnD5eRuleset
from rulesets.dnd_5e.provider import DnD5eRuleset


def test_import_registers_dnd5e_provider():
    p = ruleset.get()
    assert isinstance(p, DnD5eRuleset)
    assert p.name == "dnd_5e"


def test_placeholder_methods_raise_not_implemented():
    p = DnD5eRuleset()
    with pytest.raises(NotImplementedError):
        p.init_sheet({})


class TestVocab:
    def test_validate_skill_valid(self):
        p = DnD5eRuleset()
        ok, err = p.validate_skill("acrobatics")
        assert ok is True
        assert err is None

    def test_validate_skill_invalid(self):
        p = DnD5eRuleset()
        ok, err = p.validate_skill("juggling")
        assert ok is False
        assert "Invalid skill" in err

    def test_validate_skill_case_insensitive(self):
        p = DnD5eRuleset()
        ok, _ = p.validate_skill("ACROBATICS")
        assert ok is True

    def test_validate_alignment_neutral_alias(self):
        p = DnD5eRuleset()
        ok, _ = p.validate_alignment("neutral")
        assert ok is True

    def test_validate_alignment_invalid(self):
        p = DnD5eRuleset()
        ok, err = p.validate_alignment("very confused")
        assert ok is False

    def test_validate_condition_valid(self):
        p = DnD5eRuleset()
        ok, _ = p.validate_condition("charmed")
        assert ok is True

    def test_validate_damage_type_valid(self):
        p = DnD5eRuleset()
        ok, _ = p.validate_damage_type("fire")
        assert ok is True
