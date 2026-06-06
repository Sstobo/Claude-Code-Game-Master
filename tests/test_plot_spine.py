"""Tests for plot-spine-extraction: arc ordering, depends_on, through-line, sort."""

import json
from lib.plot_spine import derive_spine, apply_spine


def test_main_plots_ordered_by_source_appearance():
    plots = {
        "Finale": {"type": "main", "description": "overload the soul crystals at the end"},
        "Opening": {"type": "main", "description": "escape the moving train at the start"},
        "Middle": {"type": "main", "description": "decode the stairwell map midway"},
        "ASide": {"type": "side", "description": "a small errand"},
    }
    # corpus orders them: start ... midway ... end
    corpus = "escape the moving train at the start ... decode the stairwell map midway ... overload the soul crystals at the end"
    spine = derive_spine(plots, corpus)
    assert spine["arc"] == ["Opening", "Middle", "Finale"]
    assert plots["Opening"]["sequence"] == 1
    assert plots["Finale"]["sequence"] == 3
    assert "→" in spine["through_line"]


def test_depends_on_chains_the_arc():
    plots = {
        "A": {"type": "main", "description": "alpha first"},
        "B": {"type": "main", "description": "beta second"},
    }
    corpus = "alpha first then beta second"
    derive_spine(plots, corpus)
    assert plots["A"]["depends_on"] == []
    assert plots["B"]["depends_on"] == ["A"]


def test_side_plots_not_sequenced():
    plots = {"S": {"type": "side", "description": "x"}}
    derive_spine(plots, "x")
    assert "sequence" not in plots["S"]


def test_apply_spine_persists_to_overview(tmp_path):
    (tmp_path / "chunks").mkdir()
    (tmp_path / "chunks" / "chunk_000.txt").write_text("escape first then decode second")
    (tmp_path / "plots.json").write_text(json.dumps({
        "Decode": {"type": "main", "description": "decode second"},
        "Escape": {"type": "main", "description": "escape first"},
    }))
    (tmp_path / "campaign-overview.json").write_text(json.dumps({"campaign_name": "T"}))
    spine = apply_spine(str(tmp_path))
    assert spine["arc"] == ["Escape", "Decode"]
    ov = json.loads((tmp_path / "campaign-overview.json").read_text())
    assert ov["story_spine"]["arc"] == ["Escape", "Decode"]


def test_source_chunk_drives_order_when_descriptions_are_paraphrases():
    """Regression: extractor descriptions are paraphrases absent from the corpus,
    so corpus.find() returns -1 for all but one plot whose snippet coincidentally
    matches. The old logic pinned the unmatched plots to the end and let the lone
    coincidental match leapfrog to seq 1 — rooting the arc on the story's ENDING.
    With source-chunk citations the arc must follow the cited chunk order."""
    plots = {
        # Listed end-first to prove dict/extraction order doesn't save us, and the
        # ending's description is the ONLY one that appears verbatim in the corpus.
        "Ending": {"type": "main", "description": "he sets her aflame and sails on",
                   "source": "Part 5 (chunk 277)"},
        "Opening": {"type": "main", "description": "flees the city after a killing",
                    "source": "Part 1 (chunks 251-253)"},
        "Middle": {"type": "main", "description": "lured up the poison river",
                   "source": "Part 2 (chunk 260)"},
    }
    corpus = "he sets her aflame and sails on"  # only the Ending paraphrase matches
    spine = derive_spine(plots, corpus)
    assert spine["arc"] == ["Opening", "Middle", "Ending"]
    assert plots["Opening"]["sequence"] == 1
    assert plots["Ending"]["sequence"] == 3
    assert plots["Ending"]["depends_on"] == ["Middle"]


def test_source_chunk_range_uses_lowest_number():
    """A cited range like 'chunks 255-257' orders by its start (255)."""
    plots = {
        "Later": {"type": "main", "description": "zzz", "source": "chunks 255-257"},
        "Earlier": {"type": "main", "description": "yyy", "source": "chunk 251"},
    }
    spine = derive_spine(plots, "no paraphrase matches here")
    assert spine["arc"] == ["Earlier", "Later"]


def test_falls_back_to_corpus_when_no_source_chunk():
    """Plots without a cited chunk still order by corpus appearance (legacy path)."""
    plots = {
        "Finale": {"type": "main", "description": "overload at the end"},
        "Opening": {"type": "main", "description": "escape at the start"},
    }
    corpus = "escape at the start ... overload at the end"
    spine = derive_spine(plots, corpus)
    assert spine["arc"] == ["Opening", "Finale"]


def test_story_threads_honor_sequence(dcc_world):
    import json as _json
    from pathlib import Path
    from lib.session_manager import SessionManager
    camp = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl"
    plots_path = camp / "plots.json"
    # Two main plots out of natural order; sequence should drive ordering.
    plots_path.write_text(_json.dumps({
        "Second Beat": {"type": "main", "status": "active", "sequence": 2},
        "First Beat": {"type": "main", "status": "active", "sequence": 1},
    }))
    sm = SessionManager(dcc_world)
    threads = sm._active_plot_threads(limit=None)
    # First Beat (sequence 1) must come before Second Beat (sequence 2)
    assert threads.index("[main] First Beat") < threads.index("[main] Second Beat")
