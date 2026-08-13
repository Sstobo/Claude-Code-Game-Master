#!/usr/bin/env python3
"""
Character schema helpers + conversion between the flat and open shapes.

CANONICAL SHAPE = FLAT. The whole runtime (player_manager, session context,
campaign list, schema validation, and the bash/jq statusline) reads flat
top-level keys (name, race, class, level, hp, ac, stats, gold, equipment,
conditions, ...). `stats` is itself an OPEN, kit-defined dict, so flat is fully
kit-agnostic (no fixed six abilities) despite the legacy field names. Use
`to_flat()` to normalize any loaded character; it is the inverse of
`to_open_schema()` and migrates legacy open-schema files to canonical flat.

The OPEN shape below is retained only as a legacy input that `to_flat()` accepts
and converts; producers should write flat (see to_flat / to_open_schema):
{
  "identity":    {name, race, class, pronouns, background, alignment, traits, ...},
  "vitals":      {hp: {current,max}, ac},
  "attributes":  {<kit-defined stat>: value, ...},
  "progression": {level, xp, <resource>, ...},
  "inventory":   {gold, items: [...]},
  "conditions":  [...],
  "details":     {<preserved legacy extras: saves, skills, features, notes, ...>}
}

Validation lives in schemas.validate_character (shape-agnostic, kit-aware).
"""

from typing import Any, Dict

_IDENTITY_KEYS = ('name', 'race', 'class', 'pronouns', 'background',
                  'alignment', 'traits', 'ideals', 'bonds', 'flaws')
_DETAIL_KEYS = ('saves', 'skills', 'features', 'notes', 'id', 'current_location')


def is_open_schema(char: Any) -> bool:
    return isinstance(char, dict) and all(k in char for k in ('identity', 'vitals', 'attributes'))


def to_open_schema(char: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate a flat (legacy) character to the structured open shape. Idempotent.

    Lossless inverse of to_flat: every flat key is routed to a known section, and
    any unrecognized top-level keys (kit vitals like water/heat/corruption, plus
    anything else) are swept into `details` so to_flat can restore them. Flat is
    the canonical persisted shape, so this is rarely needed at runtime — it exists
    so the flat<->open conversion pair is complete and lossless."""
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

    # Everything not consumed above is preserved in details (lossless). This keeps
    # kit vitals (water/heat/corruption) and any extras from being dropped.
    consumed = set(_IDENTITY_KEYS) | {
        'hp', 'ac', 'level', 'xp', 'gold', 'equipment', 'conditions', 'stats'}
    details = {k: v for k, v in char.items() if k not in consumed}

    return {
        'identity': identity,
        'vitals': vitals,
        'attributes': dict(char.get('stats', {})),
        'progression': progression,
        'inventory': inventory,
        'conditions': list(char.get('conditions', [])),
        'details': details,
    }


# Structured sections of the open schema (everything else at the top level of an
# open character is an extra to be preserved verbatim, e.g. voice/origin/concept).
_OPEN_SECTIONS = ('identity', 'vitals', 'attributes', 'progression',
                  'inventory', 'conditions', 'details')


def to_flat(char: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten an open-schema character into the FLAT canonical runtime shape.

    Flat is the single canonical shape the whole runtime speaks — player_manager,
    session context, campaign list, schema validation, and the bash/jq statusline
    all read top-level keys (name, hp, stats, level, gold, ...). This is the
    inverse of to_open_schema and the normalizer applied on load so legacy
    open-schema characters (e.g. from identity_onboarding) read correctly and are
    migrated to flat on first touch.

    Idempotent: a character already in flat shape is returned unchanged.
    Lossless: every open section is spread to the top level, kit vitals
    (water/heat/corruption/...) included, and any unrecognized open keys are kept.
    """
    if not isinstance(char, dict) or not is_open_schema(char):
        return char

    flat: Dict[str, Any] = {}
    # Preserve unknown/extra top-level open keys first (voice, origin, concept...)
    for k, v in char.items():
        if k not in _OPEN_SECTIONS:
            flat[k] = v
    # details lifted to top level (saves, skills, features, notes, id, location...)
    details = char.get('details') or {}
    if isinstance(details, dict):
        flat.update(details)
    # identity -> top level (name, race, class, background, bonds, ...)
    identity = char.get('identity') or {}
    if isinstance(identity, dict):
        flat.update(identity)
    # vitals -> top level (hp, ac, + any kit vitals like water/heat/corruption)
    vitals = char.get('vitals') or {}
    if isinstance(vitals, dict):
        flat.update(vitals)
    # attributes -> stats (open, kit-defined dict)
    flat['stats'] = dict(char.get('attributes') or {})
    # progression -> level/xp + any extras (model, milestones, ...)
    prog = char.get('progression') or {}
    if isinstance(prog, dict):
        flat['level'] = prog.get('level', 1)
        for k, v in prog.items():
            if k != 'level':
                flat[k] = v
    # inventory -> gold/equipment
    inv = char.get('inventory') or {}
    if isinstance(inv, dict):
        flat['gold'] = inv.get('gold', 0)
        flat['equipment'] = list(inv.get('items', []))
    # conditions
    flat['conditions'] = list(char.get('conditions') or [])
    return flat


# The character validator lives in schemas.validate_character (shape-agnostic,
# kit-aware). The open-shape-only validator that used to live here reported a
# loaded flat sheet as entirely missing — deleted 2026-08-13.
