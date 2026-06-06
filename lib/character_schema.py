#!/usr/bin/env python3
"""
Open, kit-defined character schema + migration from the legacy 5e shape.

New shape (attributes is an OPEN dict — no fixed six abilities):
{
  "identity":    {name, race, class, pronouns, background, alignment, traits, ...},
  "vitals":      {hp: {current,max}, ac},
  "attributes":  {<kit-defined stat>: value, ...},
  "progression": {level, xp, <resource>, ...},
  "inventory":   {gold, items: [...]},
  "conditions":  [...],
  "details":     {<preserved legacy extras: saves, skills, features, notes, ...>}
}

validate_character checks the shape and, when a World Kit is supplied, that the
character's attributes are within the kit's declared stat schema.
"""

from typing import Any, Dict, List, Optional, Tuple

_IDENTITY_KEYS = ('name', 'race', 'class', 'pronouns', 'background',
                  'alignment', 'traits', 'ideals', 'bonds', 'flaws')
_DETAIL_KEYS = ('saves', 'skills', 'features', 'notes', 'id', 'current_location')
_REQUIRED = ('identity', 'vitals', 'attributes', 'progression', 'inventory', 'conditions')


def is_open_schema(char: Any) -> bool:
    return isinstance(char, dict) and all(k in char for k in ('identity', 'vitals', 'attributes'))


def to_open_schema(char: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate a legacy (5e-shaped) character to the open schema. Idempotent."""
    if not isinstance(char, dict) or is_open_schema(char):
        return char

    identity = {k: char[k] for k in _IDENTITY_KEYS if k in char}
    vitals = {}
    if 'hp' in char:
        vitals['hp'] = char['hp']
    if 'ac' in char:
        vitals['ac'] = char['ac']
    progression = {'level': char.get('level', 1)}
    if 'xp' in char:
        progression['xp'] = char['xp']
    inventory = {'gold': char.get('gold', 0), 'items': list(char.get('equipment', []))}
    details = {k: char[k] for k in _DETAIL_KEYS if k in char}

    return {
        'identity': identity,
        'vitals': vitals,
        'attributes': dict(char.get('stats', {})),
        'progression': progression,
        'inventory': inventory,
        'conditions': list(char.get('conditions', [])),
        'details': details,
    }


def validate_character(char: Dict[str, Any], kit=None) -> Tuple[bool, List[str]]:
    """Validate an open-schema character. With a kit, check attributes ⊆ kit schema."""
    errors: List[str] = []
    if not isinstance(char, dict):
        return False, ['character must be an object']
    for key in _REQUIRED:
        if key not in char:
            errors.append(f'missing required key: {key}')
    if not isinstance(char.get('attributes', {}), dict):
        errors.append('attributes must be an object (open, kit-defined)')
    if kit is not None:
        allowed = set((kit.stat_schema() or {}).get('attributes', []))
        if allowed:
            extra = set(char.get('attributes', {}).keys()) - allowed
            if extra:
                errors.append(f'attributes not in active kit schema: {sorted(extra)}')
    return (len(errors) == 0), errors
