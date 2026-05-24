"""Provider skeleton tests — Phase 1 placeholder behavior."""
import pytest

from lib import ruleset
import rulesets.dnd_5e  # noqa: F401 — registers DnD5eRuleset
from rulesets.dnd_5e.provider import DnD5eRuleset


def test_import_registers_dnd5e_provider():
    p = ruleset.get()
    assert isinstance(p, DnD5eRuleset)
    assert p.name == "dnd_5e"


@pytest.mark.parametrize(
    "method_name,args",
    [
        ("format_character_block", ({},)),
        ("format_party_context_block", ({}, False)),
        ("xp_threshold", (1,)),
        ("level_for_xp", (0,)),
    ],
)
def test_placeholder_methods_raise_not_implemented(method_name, args):
    p = DnD5eRuleset()
    with pytest.raises(NotImplementedError):
        getattr(p, method_name)(*args)


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
        assert "Invalid alignment" in err

    def test_validate_condition_valid(self):
        p = DnD5eRuleset()
        ok, _ = p.validate_condition("charmed")
        assert ok is True

    def test_validate_damage_type_valid(self):
        p = DnD5eRuleset()
        ok, _ = p.validate_damage_type("fire")
        assert ok is True


class TestSheet:
    def test_init_sheet_writes_defaults(self):
        p = DnD5eRuleset()
        npc = {'description': 'Carl', 'attitude': 'friendly'}
        p.init_sheet(npc)
        sheet = npc['character_sheet']
        assert sheet['hp'] == {'current': 10, 'max': 10}
        assert sheet['ac'] == 10
        assert sheet['level'] == 1
        assert sheet['stats'] == {'str': 10, 'dex': 10, 'con': 10,
                                  'int': 10, 'wis': 10, 'cha': 10}
        assert sheet['xp'] == 0

    def test_init_sheet_isolates_nested_dicts(self):
        """Repeated init_sheet calls must not share mutable references."""
        p = DnD5eRuleset()
        a, b = {}, {}
        p.init_sheet(a)
        p.init_sheet(b)
        a['character_sheet']['hp']['current'] = 1
        assert b['character_sheet']['hp']['current'] == 10

    def test_update_hp_clamps_to_max_and_zero(self):
        p = DnD5eRuleset()
        sheet = {'hp': {'current': 5, 'max': 10}}
        p.update_hp(sheet, 100)
        assert sheet['hp']['current'] == 10
        p.update_hp(sheet, -100)
        assert sheet['hp']['current'] == 0

    def test_update_xp_clamps_at_zero(self):
        p = DnD5eRuleset()
        sheet = {'xp': 50}
        p.update_xp(sheet, -100)
        assert sheet['xp'] == 0

    def test_set_field_numeric(self):
        p = DnD5eRuleset()
        sheet = {'hp': {'current': 10, 'max': 10}, 'ac': 10}
        assert p.set_field(sheet, 'ac', '15') is True
        assert sheet['ac'] == 15

    def test_set_field_hp_max_heals_overflow(self):
        p = DnD5eRuleset()
        sheet = {'hp': {'current': 20, 'max': 20}}
        p.set_field(sheet, 'hp_max', '10')
        assert sheet['hp']['max'] == 10
        assert sheet['hp']['current'] == 10

    def test_set_field_unknown_returns_false(self):
        p = DnD5eRuleset()
        sheet = {'hp': {'current': 10, 'max': 10}}
        assert p.set_field(sheet, 'bogus', 'x') is False

    def test_format_npc_sheet_returns_string(self):
        p = DnD5eRuleset()
        npc = {'description': 'd', 'attitude': 'a'}
        p.init_sheet(npc)
        out = p.format_npc_sheet(npc)
        assert isinstance(out, str)
        assert 'HP' in out
        assert 'AC' in out

    def test_format_party_summary_empty(self):
        p = DnD5eRuleset()
        out = p.format_party_summary({})
        assert isinstance(out, str)

    def test_set_field_hp_max_no_existing_hp(self):
        p = DnD5eRuleset()
        sheet = {}
        assert p.set_field(sheet, 'hp_max', '8') is True
        assert sheet['hp']['max'] == 8
        assert sheet['hp']['current'] == 8

    def test_set_field_xp_clamps_at_zero(self):
        p = DnD5eRuleset()
        sheet = {'xp': 100}
        p.set_field(sheet, 'xp', '-50')
        assert sheet['xp'] == 0
