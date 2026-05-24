"""DnD5eRuleset — implements lib.ruleset.Ruleset protocol.

Phase 1: all hooks raise NotImplementedError. Subsequent phases fill in hooks
by delegating to sibling modules (sheet, xp, vocab, context).
"""
from typing import Any, Dict, Optional, Tuple

from . import vocab


class DnD5eRuleset:
    name = "dnd_5e"

    def init_sheet(self, npc_data: Dict[str, Any]) -> None:
        raise NotImplementedError

    def update_hp(self, sheet: Dict[str, Any], delta: int) -> Dict[str, Any]:
        raise NotImplementedError

    def update_xp(self, sheet: Dict[str, Any], delta: int) -> Dict[str, Any]:
        raise NotImplementedError

    def set_field(self, sheet: Dict[str, Any], field: str, value: Any) -> bool:
        raise NotImplementedError

    def format_npc_sheet(self, npc_data: Dict[str, Any]) -> Optional[str]:
        raise NotImplementedError

    def format_party_summary(self, party: Dict[str, Dict]) -> str:
        raise NotImplementedError

    def format_character_block(self, character: Dict[str, Any]) -> str:
        raise NotImplementedError

    def format_party_context_block(self, party: Dict[str, Dict], full: bool) -> str:
        raise NotImplementedError

    def xp_threshold(self, level: int) -> Optional[int]:
        raise NotImplementedError

    def level_for_xp(self, xp: int) -> int:
        raise NotImplementedError

    def validate_skill(self, skill: str) -> Tuple[bool, Optional[str]]:
        return vocab.validate_skill(skill)

    def validate_alignment(self, alignment: str) -> Tuple[bool, Optional[str]]:
        return vocab.validate_alignment(alignment)

    def validate_condition(self, condition: str) -> Tuple[bool, Optional[str]]:
        return vocab.validate_condition(condition)

    def validate_damage_type(self, damage_type: str) -> Tuple[bool, Optional[str]]:
        return vocab.validate_damage_type(damage_type)
