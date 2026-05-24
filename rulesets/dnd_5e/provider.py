"""DnD5eRuleset — implements lib.ruleset.Ruleset protocol.

All 14 hooks are implemented, delegating to sibling modules:
sheet (HP/XP/stats), vocab (validators), xp (XP table), context (formatters).
"""
from typing import Any, Dict, Optional, Tuple

from . import context as _context
from . import sheet as _sheet
from . import vocab
from . import xp as _xp


class DnD5eRuleset:
    name = "dnd_5e"

    def init_sheet(self, npc_data: Dict[str, Any]) -> None:
        _sheet.init_sheet(npc_data)

    def update_hp(self, sheet: Dict[str, Any], delta: int) -> Dict[str, Any]:
        return _sheet.update_hp(sheet, delta)

    def update_xp(self, sheet: Dict[str, Any], delta: int) -> Dict[str, Any]:
        return _sheet.update_xp(sheet, delta)

    def set_field(self, sheet: Dict[str, Any], field: str, value: Any) -> bool:
        return _sheet.set_field(sheet, field, value)

    def format_npc_sheet(self, npc_data: Dict[str, Any]) -> Optional[str]:
        return _sheet.format_npc_sheet(npc_data)

    def format_party_summary(self, party: Dict[str, Dict]) -> str:
        return _sheet.format_party_summary(party)

    def format_character_block(self, character: Dict[str, Any]) -> str:
        return _context.format_character_block(character)

    def format_party_context_block(self, party: Dict[str, Dict], full: bool) -> str:
        return _context.format_party_context_block(party, full)

    def xp_threshold(self, level: int) -> Optional[int]:
        return _xp.xp_threshold(level)

    def level_for_xp(self, xp: int) -> int:
        return _xp.level_for_xp(xp)

    def validate_skill(self, skill: str) -> Tuple[bool, Optional[str]]:
        return vocab.validate_skill(skill)

    def validate_alignment(self, alignment: str) -> Tuple[bool, Optional[str]]:
        return vocab.validate_alignment(alignment)

    def validate_condition(self, condition: str) -> Tuple[bool, Optional[str]]:
        return vocab.validate_condition(condition)

    def validate_damage_type(self, damage_type: str) -> Tuple[bool, Optional[str]]:
        return vocab.validate_damage_type(damage_type)
