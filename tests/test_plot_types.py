"""Tests for plot-type-enum-unify: one canonical plot taxonomy, imported everywhere."""

import json
import subprocess
from pathlib import Path

from lib.schemas import PLOT_TYPES, PLOT_TYPE_SORT

REPO = Path(__file__).resolve().parent.parent


def test_sort_order_covers_every_canonical_type():
    assert set(PLOT_TYPE_SORT) == PLOT_TYPES
    # every type gets a distinct rank, so ordering is total
    assert len(set(PLOT_TYPE_SORT.values())) == len(PLOT_TYPES)
    assert PLOT_TYPE_SORT['main'] < PLOT_TYPE_SORT['threat'] < PLOT_TYPE_SORT['mystery'] \
        < PLOT_TYPE_SORT['side']


def test_only_schemas_defines_the_enum():
    """No module may re-declare the plot-type set (grep-verifiable)."""
    hits = subprocess.run(
        ["grep", "-rln", "PLOT_TYPE_SORT = {", str(REPO / "lib")],
        capture_output=True, text=True,
    ).stdout.split()
    assert hits == [str(REPO / "lib" / "schemas.py")]


def test_every_former_site_imports_the_canonical_enum():
    for module in ("validators.py", "minor_stubs.py", "plot_manager.py", "session_manager.py",
                   "world_stats.py"):
        src = (REPO / "lib" / module).read_text()
        assert "from schemas import PLOT_TYPE" in src, module


def test_gm_plot_usage_prints_the_canonical_types():
    """The CLI help derives its type list from the enum rather than restating it."""
    out = subprocess.run(["bash", str(REPO / "tools" / "gm-plot.sh")],
                         capture_output=True, text=True, cwd=REPO).stdout
    expected = ', '.join(sorted(PLOT_TYPES, key=PLOT_TYPE_SORT.get))
    assert f"Types: {expected}" in out


def test_story_threads_sort_covers_all_canonical_types(dcc_world):
    from lib.session_manager import SessionManager
    camp = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl"
    plots = {f"Plot {t}": {"type": t, "status": "active"} for t in PLOT_TYPES}
    (camp / "plots.json").write_text(json.dumps(plots))

    threads = SessionManager(dcc_world)._active_plot_threads(limit=None)

    assert len(threads) == len(PLOT_TYPES)
    ranks = [PLOT_TYPE_SORT[line.split(']')[0].lstrip('[')] for line in threads]
    assert ranks == sorted(ranks)


def test_world_stats_counts_every_canonical_type(dcc_world, capsys):
    from lib.world_stats import WorldStats
    camp = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl"
    plots = {f"Plot {t}": {"type": t, "status": "active"} for t in PLOT_TYPES}
    (camp / "plots.json").write_text(json.dumps(plots))

    stats = WorldStats(dcc_world)
    counts = stats.get_counts()
    for t in PLOT_TYPES:
        assert counts[f"plots_{t}"] == 1, t

    # the breakdown line lists every type that actually has plots
    stats.print_overview()
    types_line = [l for l in capsys.readouterr().out.splitlines() if l.strip().startswith("Types:")][0]
    for t in PLOT_TYPES:
        assert f"1 {t}" in types_line, t


def test_world_stats_breakdown_hides_empty_types(dcc_world, capsys):
    from lib.world_stats import WorldStats
    camp = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl"
    (camp / "plots.json").write_text(json.dumps({"Only One": {"type": "threat", "status": "active"}}))

    WorldStats(dcc_world).print_overview()
    types_line = [l for l in capsys.readouterr().out.splitlines() if l.strip().startswith("Types:")][0]
    assert types_line.strip() == "Types: 1 threat"


def test_plot_manager_threads_bucket_every_canonical_type(dcc_world):
    from lib.plot_manager import PlotManager
    camp = Path(dcc_world) / "campaigns" / "dungeon-crawler-carl"
    plots = {f"Plot {t}": {"type": t, "status": "active"} for t in PLOT_TYPES}
    (camp / "plots.json").write_text(json.dumps(plots))

    pm = PlotManager(dcc_world)
    threads = pm.get_active_threads()
    assert set(threads) == PLOT_TYPES
    assert all(threads[t] for t in PLOT_TYPES)   # nothing dumped into 'other'
    pm.format_threads(threads)                   # renders every bucket without KeyError
