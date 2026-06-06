#!/usr/bin/env python3
"""Shared entity-name normalization + alias-aware resolution.

Runtime entity lookups (npcs/locations/plots) are exact-match by key, so any
title / case / parenthetical drift in a cross-reference becomes a broken link
(e.g. a plot referencing "Princess Donut" when the NPC key is "Donut").

`normalize_entity_name()` canonicalizes a name (lowercase, drop parentheticals,
drop punctuation, strip leading honorifics). `resolve_entity_name()` matches a
query against a set of entity keys in increasing looseness: exact -> case-fold ->
explicit aliases -> normalized equality. Used by entity_manager at runtime and by
the import integrity gate / connection normalizer at extract time.
"""

import re

# Leading honorifics/titles stripped during normalization.
_TITLES = {
    "princess", "prince", "king", "queen", "mistress", "master",
    "lord", "lady", "sir", "dame", "mr", "mrs", "ms", "dr", "doctor",
    "captain", "lieutenant", "sergeant", "general", "admiral",
    "the", "saint", "st",
}

_PAREN_RE = re.compile(r"\([^)]*\)")
_NONWORD_RE = re.compile(r"[^\w\s]")


def normalize_entity_name(name: str) -> str:
    """Canonicalize an entity name for loose matching.

    Lowercases, removes parentheticals and punctuation, strips leading title
    tokens. Returns "" for empty/None or a name that is nothing but titles.
    """
    if not name:
        return ""
    s = name.lower()
    s = _PAREN_RE.sub(" ", s)
    s = _NONWORD_RE.sub(" ", s)
    tokens = s.split()
    while tokens and tokens[0] in _TITLES:
        tokens.pop(0)
    return " ".join(tokens)


def resolve_entity_name(query, entities, aliases_key="aliases"):
    """Resolve a query string to an actual key in `entities`.

    Args:
        query: the name to resolve (may carry titles/parens/wrong case).
        entities: dict of {key: data} (data may carry an `aliases` list) OR an
            iterable of key strings.
        aliases_key: entity field holding alternate names.

    Resolution order: exact -> case-insensitive -> explicit aliases ->
    normalized equality. Returns the actual key, or None if unresolved.
    A query that normalizes to "" (pure titles) never matches via normalization.
    """
    if query is None:
        return None

    if isinstance(entities, dict):
        keys = list(entities.keys())
        data_map = entities
    else:
        keys = list(entities)
        data_map = {}

    # 1. exact
    if query in keys:
        return query

    # 2. case-insensitive exact
    q_lower = query.lower()
    for k in keys:
        if k.lower() == q_lower:
            return k

    q_norm = normalize_entity_name(query)

    # 3. explicit aliases on the entity
    for k in keys:
        data = data_map.get(k)
        if isinstance(data, dict):
            for a in data.get(aliases_key, []) or []:
                if a.lower() == q_lower or (q_norm and normalize_entity_name(a) == q_norm):
                    return k

    # 4. normalized equality (skip when query is pure titles -> "")
    if q_norm:
        for k in keys:
            if normalize_entity_name(k) == q_norm:
                return k

    return None
