"""Tests for extraction-output-verification: the import stops on bad agent output.

`gm-extract.sh validate` sits between the parallel extractor agents and the repair
chain. Two things have to hold or the chain writes a half-empty campaign that looks
imported: the count must be true for EVERY shape an agent emits (a list-shaped
items.json of 43 items used to report "EMPTY (0 entities)"), and a real failure must
exit non-zero naming the type, not print "All files valid".

These run the real wrapper, but never against the live world-state: every test
pins GM_WORLD_STATE_BASE to a tree under tmp_path, so the fixture campaigns are
built and read there and the player's active-campaign.txt is never touched.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from lib.minor_stubs import entry_count, normalize_entity_shape

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_ACTIVE_FILE = REPO_ROOT / "world-state" / "active-campaign.txt"

EXTRACTION_TYPES = ["npcs", "locations", "items", "plots"]


@pytest.fixture(autouse=True)
def pinned_world_state(isolated_world_state):
    """Every test in this module resolves world-state to tmp_path. Autouse because
    an ambient GM_WORLD_STATE_BASE outranks the script's own location, so the
    throwaway PROJECT_ROOT below is not isolation on its own."""
    return isolated_world_state


def isolated_tools(tmp_path: Path) -> Path:
    """A throwaway PROJECT_ROOT — common.sh derives every non-redirected path from
    the script's own location, so copying tools/ and symlinking lib/ keeps even a
    tool that ignores the env seam away from the live world-state."""
    (tmp_path / "tools").mkdir()
    for script in ("common.sh", "gm-extract.sh"):
        shutil.copy(REPO_ROOT / "tools" / script, tmp_path / "tools" / script)
    (tmp_path / "lib").symlink_to(REPO_ROOT / "lib")
    return tmp_path / "tools" / "gm-extract.sh"


def write_extraction(tmp_path: Path, slug: str, files: dict) -> Path:
    """Lay down extracted/<type>.json for a fixture campaign. `files` maps a type to
    its JSON payload; a type mapped to None is left missing on disk."""
    extracted = tmp_path / "world-state" / "campaigns" / slug / "extracted"
    extracted.mkdir(parents=True)
    for type_name, payload in files.items():
        if payload is None:
            continue
        (extracted / f"{type_name}.json").write_text(json.dumps(payload))
    return extracted


def run(script: Path, *args) -> subprocess.CompletedProcess:
    # cwd stays the repo so `uv run python` resolves this project's environment.
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


def item_list(n: int) -> list:
    """Extractor output in the shape ITEM_SCHEMA actually declares: a list."""
    return [{"name": f"Item {i}", "type": "wondrous", "description": "x"} for i in range(n)]


def full_extraction(**overrides) -> dict:
    files = {
        "npcs": {"Strahd": {"name": "Strahd", "description": "vampire"}},
        "locations": {"Barovia": {"name": "Barovia", "description": "village"}},
        "items": item_list(43),
        "plots": {"Escape": {"name": "Escape", "type": "main"}},
    }
    files.update(overrides)
    return files


# --- counting -------------------------------------------------------------


def test_list_shaped_items_are_counted_not_reported_empty(tmp_path):
    """The bug: 43 correctly list-shaped items reported as EMPTY (0 entities)."""
    script = isolated_tools(tmp_path)
    write_extraction(tmp_path, "fixture", full_extraction())

    result = run(script, "validate", "fixture")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "items: 43 entities" in result.stdout
    assert "EMPTY" not in result.stdout


# --- the gate -------------------------------------------------------------


def test_missing_file_fails_and_names_the_type(tmp_path):
    script = isolated_tools(tmp_path)
    write_extraction(tmp_path, "fixture", full_extraction(locations=None))

    result = run(script, "validate", "fixture")
    assert result.returncode != 0
    assert "locations: MISSING" in result.stdout
    assert "locations: file missing" in result.stdout


def test_empty_npcs_fails_and_names_the_type(tmp_path):
    script = isolated_tools(tmp_path)
    write_extraction(tmp_path, "fixture", full_extraction(npcs={}))

    result = run(script, "validate", "fixture")
    assert result.returncode != 0
    assert "npcs: EMPTY (0 entities)" in result.stdout
    assert "EXTRACTION FAILED" in result.stdout
    assert "npcs: 0 entities" in result.stdout


def test_invalid_json_fails_and_names_the_type(tmp_path):
    script = isolated_tools(tmp_path)
    extracted = write_extraction(tmp_path, "fixture", full_extraction())
    (extracted / "plots.json").write_text("{not json")

    result = run(script, "validate", "fixture")
    assert result.returncode != 0
    assert "plots: INVALID JSON" in result.stdout


@pytest.mark.parametrize("optional_type", ["items", "plots"])
def test_empty_optional_types_warn_but_pass(tmp_path, optional_type):
    """A book with no treasure or no explicit quest hooks is unusual, not broken."""
    script = isolated_tools(tmp_path)
    write_extraction(tmp_path, "fixture", full_extraction(**{optional_type: []}))

    result = run(script, "validate", "fixture")
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{optional_type}: WARNING - 0 entities" in result.stdout


# --- shape normalization --------------------------------------------------


@pytest.mark.parametrize("type_name", EXTRACTION_TYPES)
@pytest.mark.parametrize("shape", ["list", "dict", "wrapped_list", "wrapped_dict"])
def test_every_extractor_shape_lands_flat_and_keyed(type_name, shape):
    """Agents emit lists in practice (EXTRACTION_RESULT_SCHEMA declares keyed
    dicts); the runtime managers want {name: {...}}. Both, wrapped or bare,
    must arrive at the same flat shape."""
    entities = [{"name": "Alpha", "description": "a"}, {"name": "Beta", "description": "b"}]
    keyed = {e["name"]: e for e in entities}
    wrapper = "plot_hooks" if type_name == "plots" else type_name
    data = {
        "list": entities,
        "dict": keyed,
        "wrapped_list": {"document": "book.pdf", wrapper: entities},
        "wrapped_dict": {"document": "book.pdf", wrapper: keyed},
    }[shape]

    assert normalize_entity_shape(data, type_name) == keyed


def test_normalize_command_flattens_a_list_into_the_campaign_root(tmp_path, pinned_world_state):
    """The shell pass, not just the helper: a list-shaped items.json must land as
    keyed items.json at the campaign root, which is all the runtime can read."""
    script = isolated_tools(tmp_path)
    write_extraction(tmp_path, "fixture", full_extraction())

    result = run(script, "normalize", "fixture")
    assert result.returncode == 0, result.stdout + result.stderr

    written = json.loads((pinned_world_state / "campaigns" / "fixture" / "items.json").read_text())
    assert len(written) == 43
    assert written["Item 0"]["type"] == "wondrous"


def test_unnamed_list_entries_still_get_a_key():
    """A nameless entry must not collapse the whole set onto one key."""
    flat = normalize_entity_shape([{"description": "a"}, {"description": "b"}], "npcs")
    assert len(flat) == 2


@pytest.mark.parametrize("type_name", EXTRACTION_TYPES)
def test_an_entity_named_like_the_wrapper_key_survives(type_name):
    """A keyed dict whose values are all entities is already flat — unwrapping one
    that happens to hold an entity named "items" would swallow the whole file."""
    wrapper = "plot_hooks" if type_name == "plots" else type_name
    keyed = {
        "Alpha": {"name": "Alpha", "description": "a"},
        wrapper: {"name": wrapper, "description": "an entity that shares the wrapper's name"},
    }
    assert normalize_entity_shape(keyed, type_name) == keyed


@pytest.mark.parametrize("siblings", [
    {},                                        # the common agent shape, bare
    {"document": "book.pdf"},                  # scalar scrap
    {"metadata": {"chunks_processed": 12}},    # a dict scrap is still not an entity
])
def test_a_wrapper_beside_non_entity_keys_is_still_unwrapped(siblings):
    inner = {"Alpha": {"name": "Alpha"}}
    assert normalize_entity_shape({"npcs": inner, **siblings}, "npcs") == inner


# --- malformed entities ---------------------------------------------------


@pytest.mark.parametrize("bad_name", [["Alpha", "Beta"], {"first": "Alpha"}, 7])
def test_a_non_string_name_is_a_named_failure_not_a_traceback(tmp_path, bad_name):
    script = isolated_tools(tmp_path)
    write_extraction(tmp_path, "fixture", full_extraction(items=[{"name": bad_name}]))

    result = run(script, "validate", "fixture")
    assert result.returncode != 0
    assert "INVALID ENTITY" in result.stdout
    assert "items: name is not a string" in result.stdout
    assert "Traceback" not in result.stderr


def test_a_non_object_entry_is_a_named_failure(tmp_path):
    script = isolated_tools(tmp_path)
    write_extraction(tmp_path, "fixture", full_extraction(items=["just a string"]))

    result = run(script, "validate", "fixture")
    assert result.returncode != 0
    assert "items: entry 0 is str" in result.stdout
    assert "Traceback" not in result.stderr


def test_a_non_container_file_is_a_named_failure(tmp_path):
    script = isolated_tools(tmp_path)
    write_extraction(tmp_path, "fixture", full_extraction(npcs="no entities found"))

    result = run(script, "validate", "fixture")
    assert result.returncode != 0
    assert "npcs: file holds str" in result.stdout


def test_normalize_writes_nothing_when_one_type_is_malformed(tmp_path):
    """A partial normalize leaves the campaign root part old, part new."""
    script = isolated_tools(tmp_path)
    campaign = tmp_path / "world-state" / "campaigns" / "fixture"
    write_extraction(tmp_path, "fixture", full_extraction(plots=[{"name": ["bad"]}]))

    result = run(script, "normalize", "fixture")
    assert result.returncode != 0
    assert "NORMALIZE FAILED" in result.stdout
    # npcs/locations/items normalized cleanly and must STILL not have been written.
    written = sorted(p.name for p in campaign.iterdir())
    assert written == ["extracted"], f"partial write: {written}"


# --- duplicate names ------------------------------------------------------


def test_duplicate_names_are_reported_not_silently_collapsed(tmp_path):
    script = isolated_tools(tmp_path)
    dupes = [{"name": "Rope"}, {"name": "Rope"}, {"name": "Torch"}]
    write_extraction(tmp_path, "fixture", full_extraction(items=dupes))

    assert entry_count(dupes, "items") == 3
    assert len(normalize_entity_shape(dupes, "items")) == 2

    result = run(script, "validate", "fixture")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "items: 3 entries, 2 unique names" in result.stdout


# --- isolation ------------------------------------------------------------


def test_the_live_world_state_is_never_touched(tmp_path, pinned_world_state):
    """Isolation itself: a validate + normalize cycle leaves the player's pointer
    unmodified, and writes its campaign only under the pinned tmp base."""
    before = LIVE_ACTIVE_FILE.read_bytes() if LIVE_ACTIVE_FILE.exists() else None
    before_mtime = LIVE_ACTIVE_FILE.stat().st_mtime_ns if LIVE_ACTIVE_FILE.exists() else None

    script = isolated_tools(tmp_path)
    write_extraction(tmp_path, "fixture", full_extraction())
    assert run(script, "validate", "fixture").returncode == 0
    assert run(script, "normalize", "fixture").returncode == 0

    after = LIVE_ACTIVE_FILE.read_bytes() if LIVE_ACTIVE_FILE.exists() else None
    assert after == before
    if before_mtime is not None:
        assert LIVE_ACTIVE_FILE.stat().st_mtime_ns == before_mtime
    assert not (REPO_ROOT / "world-state" / "campaigns" / "fixture").exists()
    assert (pinned_world_state / "campaigns" / "fixture" / "items.json").exists()
