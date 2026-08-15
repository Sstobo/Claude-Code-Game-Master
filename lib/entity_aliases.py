#!/usr/bin/env python3
"""Shared entity-name normalization + alias-aware resolution.

Runtime entity lookups (npcs/locations/plots) are exact-match by key, so any
title / case / parenthetical drift in a cross-reference becomes a broken link
(e.g. a plot referencing "Princess Donut" when the NPC key is "Donut").

`normalize_entity_name()` canonicalizes a name (lowercase, fold diacritics, drop
parentheticals, drop punctuation, strip leading honorifics). `resolve_entity_name()`
matches a query against a set of entity keys in increasing looseness: exact ->
case-fold -> explicit aliases -> normalized equality. `reuse_existing_key()` is the
import-time variant: resolve, then the longest existing key whose normalized name
is a token-prefix of the query (long descriptive query -> short existing key).
`resolve_or_merge_key()` is the bidirectional sibling: it matches that same
direction AND the reverse — a short query whose normalized name is a token-prefix
of a longer existing key (materializing a proper name onto a descriptive stub) —
so the play-pack stub and its later materialize collapse to one identity. Used by
entity_manager at runtime and by the import integrity gate / connection normalizer
at extract time.
"""

import re
import unicodedata

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

    Lowercases, folds diacritics, removes parentheticals and punctuation, strips
    leading title tokens. Returns "" for empty/None or a name that is nothing but titles.
    """
    if not name:
        return ""
    s = name.lower()
    s = _PAREN_RE.sub(" ", s)
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
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


def reuse_existing_key(query, entities, aliases_key="aliases"):
    """Canonical key for an import-time reference, or None.

    resolve_entity_name first; if that fails, the longest existing key whose
    normalized name equals the query or is a token-prefix of it — so a
    descriptive phrasing attaches to the node it names rather than becoming a stub.
    """
    key = resolve_entity_name(query, entities, aliases_key)
    if key:
        return key
    q_norm = normalize_entity_name(query)
    if not q_norm:
        return None
    keys = list(entities.keys()) if isinstance(entities, dict) else list(entities)
    best, best_len = None, 0
    for k in keys:
        k_norm = normalize_entity_name(k)
        if k_norm and (q_norm == k_norm or q_norm.startswith(k_norm + " ")):
            if len(k_norm) > best_len:
                best, best_len = k, len(k_norm)
    return best


def resolve_or_merge_key(query, entities, aliases_key="aliases"):
    """Bidirectional canonical key for a materialize/import reference, or None.

    `resolve_entity_name` first (exact -> case -> aliases -> normalized equality).
    Failing that, a token-prefix match in EITHER direction:

    - **descriptive query -> short key** (the `reuse_existing_key` direction): an
      existing key whose normalized name is a token-prefix of the query. The
      longest such key wins.
    - **short query -> long descriptive key** (the play-pack materialize
      direction): the query's normalized name as a token-prefix of an existing
      key, e.g. "Aratus" attaching to an "Aratus the Kothian (...)" stub. The
      shortest such key wins.

    When both directions could match, the descriptive->short direction is
    preferred, so a pair always merges onto one deterministic key. Token
    boundaries are respected (a trailing space), so "Ara" never prefixes
    "Aratus". Returns the actual key, or None.

    CAUTION: the short->long (reverse) direction is deliberately permissive — it
    cannot tell an epithet suffix ("the Kothian") from a surname ("Baksh"), so it
    will report a longer key that merely shares a first name. Callers that MERGE on
    the result must gate the reverse case against the entity data (is the longer
    record a stub / epithet?) before collapsing two records; see
    `play_pack._merge_is_safe`. This function only proposes a candidate key.
    """
    key = resolve_entity_name(query, entities, aliases_key)
    if key:
        return key
    q_norm = normalize_entity_name(query)
    if not q_norm:
        return None
    keys = list(entities.keys()) if isinstance(entities, dict) else list(entities)

    best_desc, best_desc_len = None, 0   # existing key is a prefix of the query
    short_matches = []                   # query is a prefix of the existing key
    for k in keys:
        k_norm = normalize_entity_name(k)
        if not k_norm:
            continue
        if q_norm == k_norm or q_norm.startswith(k_norm + " "):
            if len(k_norm) > best_desc_len:
                best_desc, best_desc_len = k, len(k_norm)
        elif k_norm.startswith(q_norm + " "):
            short_matches.append((len(k_norm), k))
    if best_desc:
        return best_desc
    if short_matches:
        short_matches.sort()  # shortest normalized key, then key string — deterministic
        return short_matches[0][1]
    return None
