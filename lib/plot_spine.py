#!/usr/bin/env python3
"""Derive a plot spine (arc ordering + dependencies + through-line) from extracted plots.

plots.json is a flat bag of independent hooks with no ordering, so the story-spine
context can only sort by type. This orders the MAIN plots into the book's arc by
earliest source appearance, chains them with `depends_on`, records a `sequence`, and
writes a campaign-level `story_spine` (ordered arc + through-line) the context loader
can surface. Deterministic: ordering comes from chunk position, not model judgment.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extraction_cap import load_corpus

_WORD_RE = re.compile(r"[a-z0-9]+")


def _snippet(text: str, words: int = 6) -> str:
    toks = _WORD_RE.findall((text or "").lower())
    return " ".join(toks[:words])


def _earliest_index(plot: dict, corpus: str) -> int:
    """Earliest position in the corpus where this plot's description/name appears."""
    candidates = [_snippet(plot.get("description", "")), _snippet(plot.get("name", ""))]
    best = len(corpus) + 1
    for snip in candidates:
        if not snip:
            continue
        idx = corpus.find(snip)
        if idx != -1:
            best = min(best, idx)
    return best


def derive_spine(plots: dict, corpus: str) -> dict:
    """Assign sequence + depends_on to MAIN plots; return the campaign story_spine.

    Mutates main plots in place. Returns {"through_line": str, "arc": [names...]}.
    """
    mains = [(name, p) for name, p in (plots or {}).items()
             if isinstance(p, dict) and str(p.get("type", "")).lower() == "main"]
    # Order by earliest source appearance; stable on ties by original order.
    ordered = sorted(enumerate(mains), key=lambda ip: (_earliest_index(ip[1][1], corpus), ip[0]))
    arc = []
    prev = None
    for seq, (_, (name, plot)) in enumerate(ordered, start=1):
        plot["sequence"] = seq
        plot["depends_on"] = [prev] if prev else []
        arc.append(name)
        prev = name

    through_line = " → ".join(arc) if arc else ""
    return {"through_line": through_line, "arc": arc}


def apply_spine(campaign_dir) -> dict:
    """Derive + persist the spine onto plots.json and campaign-overview.json."""
    cdir = Path(campaign_dir)
    corpus = load_corpus(cdir / "chunks")
    plots_path = cdir / "plots.json"
    plots = json.loads(plots_path.read_text()) if plots_path.exists() else {}
    spine = derive_spine(plots, corpus)
    plots_path.write_text(json.dumps(plots, indent=2))

    ov_path = cdir / "campaign-overview.json"
    if ov_path.exists():
        overview = json.loads(ov_path.read_text())
        overview["story_spine"] = spine
        ov_path.write_text(json.dumps(overview, indent=2))
    return spine


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Derive a plot spine")
    parser.add_argument("campaign_dir")
    args = parser.parse_args()
    spine = apply_spine(args.campaign_dir)
    print(f"  arc ({len(spine['arc'])} main beats):")
    for i, name in enumerate(spine["arc"], 1):
        print(f"    {i}. {name}")


if __name__ == "__main__":
    main()
