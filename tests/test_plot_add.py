"""QA eval for the new live plot-creation path (gm-plot.sh add / PlotManager.add_plot).

Before this there was NO way to create a plot at play time (only /import did). The
plot-weaver agent persists seeded threads through this. A seeded thread is DORMANT
(out of STORY THREADS) until the GM advances it, which WAKES it to active.
"""

import json
from pathlib import Path

from lib.plot_manager import PlotManager


def _plots(world_dir):
    active = (Path(world_dir) / "active-campaign.txt").read_text().strip()
    return Path(world_dir) / "campaigns" / active / "plots.json"


def test_add_creates_dormant_and_refuses_duplicate(dcc_world):
    pm = PlotManager(dcc_world)
    assert pm.add_plot("Wench's Bargain", plot_type="mystery", description="She knows the route.",
                       objectives=["Corner her", "Trade for the route"],
                       npcs=["Yara"], locations=["The Maul"])
    row = json.load(open(_plots(dcc_world)))["Wench's Bargain"]
    assert row["status"] == "dormant" and row["type"] == "mystery"
    assert row["npcs"] == ["Yara"] and row["locations"] == ["The Maul"]
    assert row["objectives"] == ["Corner her", "Trade for the route"]
    assert row["events"][0]["event"] == "Thread seeded"

    # a second add of the same name must NOT clobber the first
    assert pm.add_plot("Wench's Bargain", plot_type="side", description="different") is False
    assert json.load(open(_plots(dcc_world)))["Wench's Bargain"]["type"] == "mystery"


def test_unknown_type_and_status_fall_back(dcc_world):
    pm = PlotManager(dcc_world)
    assert pm.add_plot("Weird", plot_type="banana", status="sideways")
    row = json.load(open(_plots(dcc_world)))["Weird"]
    assert row["type"] == "idea", "unknown type falls back to idea"
    assert row["status"] == "dormant", "unknown status falls back to dormant"


def test_update_wakes_a_dormant_thread(dcc_world):
    pm = PlotManager(dcc_world)
    pm.add_plot("Sleeper", plot_type="threat", description="a mounting dread")
    assert json.load(open(_plots(dcc_world)))["Sleeper"]["status"] == "dormant"
    # a dormant thread is invisible to the active-threads dashboard...
    assert "Sleeper" not in pm.format_threads(pm.get_active_threads())
    # ...advancing it wakes it to active and it surfaces
    assert pm.update_plot("Sleeper", "it stirs beneath the tower")
    assert json.load(open(_plots(dcc_world)))["Sleeper"]["status"] == "active"
    assert "Sleeper" in PlotManager(dcc_world).format_threads(PlotManager(dcc_world).get_active_threads())
