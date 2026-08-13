#!/usr/bin/env python3
"""Tier extracted entities into an ACTIVE top-N and a BACKGROUND remainder.

Imports extract every entity in a book (65 NPCs, etc.). Only a fraction of them
belong in the foreground of a scene, but the pipeline must not pre-make the
creative decision of who exists in the world — so nothing is deleted. Each type
(npcs/locations/items/plots) is ranked by IMPORTANCE, deterministically; the
top-N stay as-is and everything below is written back to the SAME file with
`"background": true` on the entity. The GM (and the entity graph) still sees
them; they simply are not the playable core.

Importance is book-agnostic (no hardcoded names):
  score = source mention-frequency (count across chunks)
        + large boost if the entity is referenced by a plot (plot.npcs / plot.locations)
        + boost for party members (is_party_member)
This guarantees the main cast is active — they are exactly the entities the main
plots reference. Plots themselves rank by their canonical type's priority
(`schemas.PLOT_TYPE_SORT`: main > threat > mystery > side > ... > optional),
then by how connected they are.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from entity_aliases import normalize_entity_name
from minor_stubs import PLOT_TYPE_SYNONYMS
from schemas import PLOT_TYPE_SORT

DEFAULT_LIMIT = 30
_PLOT_REF_BOOST = 100_000
_PARTY_BOOST = 50_000


def plot_type_weight(plot_type: str) -> int:
    """Rank weight for a plot type, derived from the canonical enum's priority.

    `PLOT_TYPE_SORT` is the one place plot priority is declared (0 = the spine).
    Inverting it here means a type added there — `threat`, `mystery` — ranks
    above `side` automatically, instead of silently falling to the unknown-type
    floor as a local hardcoded table used to make it.

    Extractor synonyms are mapped first, because `validate_plot_types` runs in
    `stub-npcs`, AFTER the cap: a plot the agent typed "main quest" reaches this
    function raw, and without the mapping the book's spine would rank below an
    `optional` errand.
    """
    n = len(PLOT_TYPE_SORT)
    t = (plot_type or "").strip().lower()
    t = PLOT_TYPE_SYNONYMS.get(t, t)
    rank = PLOT_TYPE_SORT.get(t)
    if rank is None:
        # The fallback `validate_plot_types` will apply later. Ranking an unknown
        # or blank type at the bottom here and calling it 'side' there is the same
        # disagreement, one pass apart.
        rank = PLOT_TYPE_SORT["side"]
    return n - rank


def load_corpus(chunks_dir) -> str:
    """Concatenate all chunk text (lowercased) for mention counting."""
    d = Path(chunks_dir)
    if not d.is_dir():
        return ""
    parts = []
    for f in sorted(d.glob("chunk_*.txt")):
        try:
            parts.append(f.read_text(encoding="utf-8", errors="ignore").lower())
        except OSError:
            continue
    return "\n".join(parts)


def plot_reference_names(plots: dict) -> set:
    """Normalized set of every name referenced by any plot (npcs + locations)."""
    refs = set()
    for plot in (plots or {}).values():
        if not isinstance(plot, dict):
            continue
        for key in ("npcs", "locations"):
            for ref in plot.get(key, []) or []:
                n = normalize_entity_name(ref)
                if n:
                    refs.add(n)
    return refs


def mention_count(name: str, corpus: str) -> int:
    if not name or not corpus:
        return 0
    return corpus.count(name.lower())


def importance_score(name, entity, type_name, corpus, plot_refs):
    """Higher = more important / more likely to stay active."""
    if type_name == "plots":
        weight = plot_type_weight((entity or {}).get("type", ""))
        connectedness = len((entity or {}).get("npcs", []) or []) + \
            len((entity or {}).get("locations", []) or []) + \
            len((entity or {}).get("objectives", []) or [])
        return weight * 10_000 + connectedness

    score = mention_count(name, corpus)
    if normalize_entity_name(name) in plot_refs:
        score += _PLOT_REF_BOOST
    if isinstance(entity, dict) and entity.get("is_party_member"):
        score += _PARTY_BOOST
    return score


def cap_type(entities: dict, type_name: str, corpus: str, plot_refs: set, limit: int):
    """Tier one type in place. Returns (entities, background_names).

    The dict that comes in is the dict that goes out — every entity survives.
    Entities ranked below `limit` get `"background": true`; the active top-N
    have any stale flag cleared, so re-running is idempotent. Stable: ties are
    broken by original order.
    """
    if not isinstance(entities, dict):
        return entities, []
    items = list(entities.items())
    ranked = sorted(
        enumerate(items),
        key=lambda iv: (importance_score(iv[1][0], iv[1][1], type_name, corpus, plot_refs), -iv[0]),
        reverse=True,
    )
    background = []
    for position, (i, _) in enumerate(ranked):
        name, entity = items[i]
        if not isinstance(entity, dict):
            continue
        if position < limit:
            entity.pop("background", None)
        else:
            entity["background"] = True
            background.append(name)
    return entities, background


def cap_campaign(campaign_dir, limit: int = DEFAULT_LIMIT) -> dict:
    """Tier npcs/locations/items/plots files in a campaign root in place.

    Nothing is removed from disk: each file is rewritten with the same entities,
    the ones past the top-N carrying `"background": true`.
    Returns a report: {type: {"active": n, "background": [names]}}.
    """
    cdir = Path(campaign_dir)
    corpus = load_corpus(cdir / "chunks")
    plots_path = cdir / "plots.json"
    plots = json.loads(plots_path.read_text()) if plots_path.exists() else {}
    plot_refs = plot_reference_names(plots)

    report = {}
    for type_name in ("npcs", "locations", "items", "plots"):
        path = cdir / f"{type_name}.json"
        if not path.exists():
            continue
        entities = json.loads(path.read_text())
        if not isinstance(entities, dict):
            continue
        entities, background = cap_type(entities, type_name, corpus, plot_refs, limit)
        path.write_text(json.dumps(entities, indent=2))
        # Only real entities can carry a tier — a stray scalar is neither active
        # nor background, and counting it would overstate the playable core.
        entity_count = sum(1 for v in entities.values() if isinstance(v, dict))
        report[type_name] = {"active": entity_count - len(background), "background": background}
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tier extracted entities: active top-N + background")
    parser.add_argument("campaign_dir")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()
    report = cap_campaign(args.campaign_dir, args.limit)
    for t, r in report.items():
        n_bg = len(r["background"])
        print(f"  {t}: {r['active']} active, {n_bg} background")
        if n_bg:
            print(f"    background: {', '.join(r['background'][:10])}{' ...' if n_bg > 10 else ''}")


if __name__ == "__main__":
    main()
