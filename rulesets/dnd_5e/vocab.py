"""D&D 5E vocabulary validators.

Word lists and validation logic moved verbatim from lib/validators.py.
Lib stays system-agnostic; 5E-specific vocab lives here.
"""
from typing import Optional, Tuple

_SKILLS = [
    'acrobatics', 'animal handling', 'arcana', 'athletics',
    'deception', 'history', 'insight', 'intimidation',
    'investigation', 'medicine', 'nature', 'perception',
    'performance', 'persuasion', 'religion', 'sleight of hand',
    'stealth', 'survival',
]

_ALIGNMENTS = [
    'lawful good', 'neutral good', 'chaotic good',
    'lawful neutral', 'true neutral', 'chaotic neutral',
    'lawful evil', 'neutral evil', 'chaotic evil',
    'unaligned',
]

_CONDITIONS = [
    'blinded', 'charmed', 'deafened', 'exhaustion', 'frightened',
    'grappled', 'incapacitated', 'invisible', 'paralyzed',
    'petrified', 'poisoned', 'prone', 'restrained', 'stunned',
    'unconscious',
]

_DAMAGE_TYPES = [
    'acid', 'bludgeoning', 'cold', 'fire', 'force', 'lightning',
    'necrotic', 'piercing', 'poison', 'psychic', 'radiant',
    'slashing', 'thunder',
]


def validate_skill(skill: str) -> Tuple[bool, Optional[str]]:
    s = skill.lower().strip()
    if s not in _SKILLS:
        return False, f"Invalid skill. Valid skills: {', '.join(_SKILLS)}"
    return True, None


def validate_alignment(alignment: str) -> Tuple[bool, Optional[str]]:
    a = alignment.lower().strip()
    if a == 'neutral':
        a = 'true neutral'
    if a not in _ALIGNMENTS:
        return False, f"Invalid alignment. Valid alignments: {', '.join(_ALIGNMENTS)}"
    return True, None


def validate_condition(condition: str) -> Tuple[bool, Optional[str]]:
    c = condition.lower().strip()
    if c not in _CONDITIONS:
        return False, f"Invalid condition. Valid conditions: {', '.join(_CONDITIONS)}"
    return True, None


def validate_damage_type(damage_type: str) -> Tuple[bool, Optional[str]]:
    d = damage_type.lower().strip()
    if d not in _DAMAGE_TYPES:
        return False, f"Invalid damage type. Valid types: {', '.join(_DAMAGE_TYPES)}"
    return True, None


_ABILITIES = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
_ABILITY_ABBREVS = ['str', 'dex', 'con', 'int', 'wis', 'cha']


def validate_ability(ability: str) -> Tuple[bool, Optional[str]]:
    a = ability.lower().strip()
    if a not in _ABILITIES and a not in _ABILITY_ABBREVS:
        return False, f"Invalid ability. Valid abilities: {', '.join(_ABILITIES)}"
    return True, None
