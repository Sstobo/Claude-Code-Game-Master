#!/usr/bin/env python3
"""Tests for HierarchyManager — compound locations with interiors and nested navigation."""

import pytest
import sys
import json
from pathlib import Path


def _find_project_root() -> Path:
    for p in Path(__file__).parents:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("pyproject.toml not found")


PROJECT_ROOT = _find_project_root()
sys.path.insert(0, str(PROJECT_ROOT / "lib"))
sys.path.insert(0, str(PROJECT_ROOT / ".claude/modules/world-travel/lib"))

from hierarchy_manager import HierarchyManager


@pytest.fixture
def campaign_dir(tmp_path):
    d = tmp_path / "campaigns" / "test"
    d.mkdir(parents=True)

    locations = {
        "City Center": {
            "description": "Main city area",
            "connections": []
        },
        "Outskirts": {
            "description": "Edge of town",
            "connections": []
        }
    }

    overview = {
        "player_position": {
            "current_location": "City Center"
        }
    }

    (d / "locations.json").write_text(json.dumps(locations), encoding="utf-8")
    (d / "campaign-overview.json").write_text(json.dumps(overview), encoding="utf-8")
    return d


def _load_locations(campaign_dir):
    return json.loads((campaign_dir / "locations.json").read_text(encoding="utf-8"))


def _load_overview(campaign_dir):
    return json.loads((campaign_dir / "campaign-overview.json").read_text(encoding="utf-8"))


def _setup_tavern(campaign_dir):
    hm = HierarchyManager(str(campaign_dir))
    hm.create_compound("Tavern", parent="City Center", description="A cozy tavern")
    hm.add_interior("Main Hall", parent="Tavern", is_entry_point=True,
                     connections=[{"to": "Kitchen"}, {"to": "Upstairs"}],
                     description="The main hall")
    hm.add_interior("Kitchen", parent="Tavern",
                     connections=[{"to": "Main Hall"}],
                     description="The kitchen")
    hm.add_interior("Upstairs", parent="Tavern",
                     connections=[{"to": "Main Hall"}],
                     description="Second floor")
    return hm


class TestCreateCompound:
    def test_create_basic(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.create_compound("Tavern", description="A tavern")
        assert result["success"] is True
        assert result["name"] == "Tavern"
        assert result["type"] == "compound"

        locs = _load_locations(campaign_dir)
        assert "Tavern" in locs
        assert locs["Tavern"]["type"] == "compound"
        assert locs["Tavern"]["children"] == []

    def test_create_with_parent(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.create_compound("Tavern", parent="City Center")
        assert result["success"] is True

        locs = _load_locations(campaign_dir)
        assert locs["Tavern"]["parent"] == "City Center"
        assert "Tavern" in locs["City Center"]["children"]

    def test_create_with_entry_points(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.create_compound("Tavern", entry_points=["Front Door"])
        assert result["success"] is True

        locs = _load_locations(campaign_dir)
        assert locs["Tavern"]["entry_points"] == ["Front Door"]

    def test_create_mobile(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.create_compound("Ship", mobile=True)
        assert result["success"] is True

        locs = _load_locations(campaign_dir)
        assert locs["Ship"]["mobile"] is True

    def test_create_duplicate_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        result = hm.create_compound("Tavern")
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_create_existing_location_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.create_compound("City Center")
        assert result["success"] is False

    def test_create_with_nonexistent_parent_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.create_compound("Tavern", parent="Nowhere")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_create_no_mobile_flag_omits_key(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        locs = _load_locations(campaign_dir)
        assert "mobile" not in locs["Tavern"]


class TestAddInterior:
    def test_add_basic_interior(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        result = hm.add_interior("Main Hall", parent="Tavern", description="Hall")
        assert result["success"] is True
        assert result["name"] == "Main Hall"
        assert result["parent"] == "Tavern"
        assert result["is_entry_point"] is False

        locs = _load_locations(campaign_dir)
        assert locs["Main Hall"]["type"] == "interior"
        assert locs["Main Hall"]["parent"] == "Tavern"
        assert "Main Hall" in locs["Tavern"]["children"]

    def test_add_as_entry_point(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        result = hm.add_interior("Front Door", parent="Tavern", is_entry_point=True)
        assert result["is_entry_point"] is True

        locs = _load_locations(campaign_dir)
        assert "Front Door" in locs["Tavern"]["entry_points"]

    def test_add_with_entry_config(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        config = {"requires_key": True, "dc": 15}
        result = hm.add_interior("Back Door", parent="Tavern",
                                  is_entry_point=True, entry_config=config)
        assert result["success"] is True

        locs = _load_locations(campaign_dir)
        assert locs["Back Door"]["entry_config"] == config

    def test_add_with_connections(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        hm.add_interior("Main Hall", parent="Tavern")
        result = hm.add_interior("Kitchen", parent="Tavern",
                                  connections=[{"to": "Main Hall"}])
        assert result["success"] is True

        locs = _load_locations(campaign_dir)
        assert locs["Kitchen"]["connections"] == [{"to": "Main Hall"}]

    def test_add_duplicate_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        hm.add_interior("Main Hall", parent="Tavern")
        result = hm.add_interior("Main Hall", parent="Tavern")
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_add_to_nonexistent_parent_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.add_interior("Room", parent="Nowhere")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_entry_config_not_set_without_entry_point_flag(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        hm.add_interior("Room", parent="Tavern",
                         is_entry_point=False, entry_config={"dc": 10})
        locs = _load_locations(campaign_dir)
        assert "entry_config" not in locs["Room"]


class TestEnterCompound:
    def test_enter_default_entry_point(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        result = hm.enter_compound("Tavern")
        assert result["success"] is True
        assert result["location"] == "Main Hall"
        assert "location_stack" in result

    def test_enter_specific_entry_point(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        hm.add_interior("Front Door", parent="Tavern", is_entry_point=True)
        hm.add_interior("Back Door", parent="Tavern", is_entry_point=True)
        result = hm.enter_compound("Tavern", entry_point="Back Door")
        assert result["success"] is True
        assert result["location"] == "Back Door"

    def test_enter_updates_player_position(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        overview = _load_overview(campaign_dir)
        pp = overview["player_position"]
        assert pp["current_location"] == "Main Hall"
        assert "location_stack" in pp

    def test_enter_nonexistent_compound_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.enter_compound("Ghost Building")
        assert result["success"] is False

    def test_enter_non_compound_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.enter_compound("City Center")
        assert result["success"] is False
        assert "not a compound" in result["error"]

    def test_enter_compound_no_entry_points_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Empty Building")
        result = hm.enter_compound("Empty Building")
        assert result["success"] is False
        assert "no entry points" in result["error"]

    def test_enter_invalid_entry_point_fails(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        result = hm.enter_compound("Tavern", entry_point="Secret Door")
        assert result["success"] is False
        assert "not an entry point" in result["error"]


class TestExitCompound:
    def test_exit_returns_to_parent(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        result = hm.exit_compound()
        assert result["success"] is True
        assert result["location"] == "Tavern"

    def test_exit_updates_player_position(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        hm.exit_compound()
        overview = _load_overview(campaign_dir)
        assert overview["player_position"]["current_location"] == "Tavern"

    def test_exit_at_top_level_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.exit_compound()
        assert result["success"] is False
        assert "top level" in result["error"]

    def test_exit_no_current_location_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        overview = _load_overview(campaign_dir)
        del overview["player_position"]["current_location"]
        (campaign_dir / "campaign-overview.json").write_text(
            json.dumps(overview), encoding="utf-8"
        )
        result = hm.exit_compound()
        assert result["success"] is False


class TestMoveInterior:
    def test_move_to_connected_room(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        result = hm.move_interior("Kitchen")
        assert result["success"] is True
        assert result["location"] == "Kitchen"

    def test_move_updates_player_position(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        hm.move_interior("Kitchen")
        overview = _load_overview(campaign_dir)
        assert overview["player_position"]["current_location"] == "Kitchen"

    def test_move_to_unreachable_room_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Tavern")
        hm.add_interior("Room A", parent="Tavern", is_entry_point=True, connections=[])
        hm.add_interior("Room B", parent="Tavern", connections=[])
        hm.enter_compound("Tavern")
        result = hm.move_interior("Room B")
        assert result["success"] is False
        assert "not reachable" in result["error"]

    def test_move_to_different_compound_fails(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.create_compound("Shop")
        hm.add_interior("Counter", parent="Shop", is_entry_point=True)
        hm.enter_compound("Tavern")
        result = hm.move_interior("Counter")
        assert result["success"] is False
        assert "not in the same compound" in result["error"]

    def test_move_to_nonexistent_fails(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        result = hm.move_interior("Dungeon")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_move_no_current_location_fails(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        overview = _load_overview(campaign_dir)
        del overview["player_position"]["current_location"]
        (campaign_dir / "campaign-overview.json").write_text(
            json.dumps(overview), encoding="utf-8"
        )
        result = hm.move_interior("Kitchen")
        assert result["success"] is False

    def test_move_to_self_succeeds(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        result = hm.move_interior("Main Hall")
        assert result["success"] is True

    def test_move_chain_through_rooms(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        hm.move_interior("Kitchen")
        result = hm.move_interior("Main Hall")
        assert result["success"] is True
        assert result["location"] == "Main Hall"


class TestGetTree:
    def test_tree_full(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        tree = hm.get_tree()
        assert isinstance(tree, list)
        names = [n["name"] for n in tree]
        assert "City Center" in names or "Tavern" in names

    def test_tree_specific_root(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        tree = hm.get_tree("Tavern")
        assert tree["name"] == "Tavern"
        child_names = [c["name"] for c in tree.get("children", [])]
        assert "Main Hall" in child_names
        assert "Kitchen" in child_names
        assert "Upstairs" in child_names

    def test_tree_nonexistent_root(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        result = hm.get_tree("Nowhere")
        assert "error" in result

    def test_tree_leaf_node(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        tree = hm.get_tree("Kitchen")
        assert tree["name"] == "Kitchen"
        assert "children" not in tree


class TestGetAncestors:
    def test_ancestors_of_interior(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        ancestors = hm.get_ancestors("Kitchen")
        assert ancestors == ["City Center", "Tavern", "Kitchen"]

    def test_ancestors_of_top_level(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        ancestors = hm.get_ancestors("City Center")
        assert ancestors == ["City Center"]

    def test_ancestors_of_compound(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        ancestors = hm.get_ancestors("Tavern")
        assert ancestors == ["City Center", "Tavern"]


class TestGetChildren:
    def test_children_of_compound(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        children = hm.get_children("Tavern")
        assert "Main Hall" in children
        assert "Kitchen" in children
        assert "Upstairs" in children

    def test_children_of_leaf(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        children = hm.get_children("Kitchen")
        assert children == []

    def test_children_of_nonexistent(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        children = hm.get_children("Nowhere")
        assert children == []


class TestGetEntryPoints:
    def test_entry_points_list(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        eps = hm.get_entry_points("Tavern")
        assert len(eps) == 1
        assert eps[0]["name"] == "Main Hall"
        assert eps[0]["description"] == "The main hall"

    def test_entry_points_with_config(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Vault")
        config = {"requires_key": True}
        hm.add_interior("Vault Door", parent="Vault",
                         is_entry_point=True, entry_config=config)
        eps = hm.get_entry_points("Vault")
        assert eps[0]["entry_config"] == config

    def test_entry_points_empty(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Empty")
        eps = hm.get_entry_points("Empty")
        assert eps == []

    def test_entry_points_nonexistent_compound(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        eps = hm.get_entry_points("Nowhere")
        assert eps == []


class TestValidateHierarchy:
    def test_valid_hierarchy(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        result = hm.validate_hierarchy()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_missing_parent_detected(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        locs = _load_locations(campaign_dir)
        locs["Orphan"] = {"type": "interior", "parent": "Deleted Building"}
        (campaign_dir / "locations.json").write_text(
            json.dumps(locs), encoding="utf-8"
        )
        result = hm.validate_hierarchy()
        assert result["valid"] is False
        assert any("missing parent" in e for e in result["errors"])

    def test_missing_child_detected(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        locs = _load_locations(campaign_dir)
        locs["Tavern"]["children"].append("Ghost Room")
        (campaign_dir / "locations.json").write_text(
            json.dumps(locs), encoding="utf-8"
        )
        result = hm.validate_hierarchy()
        assert result["valid"] is False
        assert any("missing child" in e for e in result["errors"])

    def test_parent_child_mismatch_detected(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        locs = _load_locations(campaign_dir)
        locs["Kitchen"]["parent"] = "City Center"
        (campaign_dir / "locations.json").write_text(
            json.dumps(locs), encoding="utf-8"
        )
        result = hm.validate_hierarchy()
        assert result["valid"] is False

    def test_cycle_detected(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        locs = _load_locations(campaign_dir)
        locs["A"] = {"type": "compound", "parent": "B", "children": ["B"]}
        locs["B"] = {"type": "compound", "parent": "A", "children": ["A"]}
        (campaign_dir / "locations.json").write_text(
            json.dumps(locs), encoding="utf-8"
        )
        result = hm.validate_hierarchy()
        assert result["valid"] is False
        assert any("Cycle" in e or "cycle" in e.lower() for e in result["errors"])


class TestNestedCompounds:
    def test_nested_compound_creation(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        result = hm.create_compound("Wine Cellar", parent="Tavern")
        assert result["success"] is True

        locs = _load_locations(campaign_dir)
        assert "Wine Cellar" in locs["Tavern"]["children"]
        assert locs["Wine Cellar"]["parent"] == "Tavern"

    def test_deep_ancestors(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.create_compound("Wine Cellar", parent="Tavern")
        hm.add_interior("Barrel Room", parent="Wine Cellar", is_entry_point=True)
        ancestors = hm.get_ancestors("Barrel Room")
        assert ancestors == ["City Center", "Tavern", "Wine Cellar", "Barrel Room"]


class TestEdgeCases:
    def test_empty_locations_file(self, campaign_dir):
        (campaign_dir / "locations.json").write_text("{}", encoding="utf-8")
        hm = HierarchyManager(str(campaign_dir))
        result = hm.create_compound("First")
        assert result["success"] is True

    def test_move_interior_updates_stack_correctly(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        result = hm.move_interior("Kitchen")
        assert result["location_stack"][-1] == "Kitchen"

    def test_multiple_entry_points(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Castle")
        hm.add_interior("Main Gate", parent="Castle", is_entry_point=True)
        hm.add_interior("Side Gate", parent="Castle", is_entry_point=True)
        hm.add_interior("Secret Passage", parent="Castle", is_entry_point=True)

        eps = hm.get_entry_points("Castle")
        assert len(eps) == 3
        ep_names = [e["name"] for e in eps]
        assert "Main Gate" in ep_names
        assert "Side Gate" in ep_names
        assert "Secret Passage" in ep_names

    def test_bfs_reachability_through_chain(self, campaign_dir):
        hm = HierarchyManager(str(campaign_dir))
        hm.create_compound("Dungeon")
        hm.add_interior("Room1", parent="Dungeon", is_entry_point=True,
                         connections=[{"to": "Room2"}])
        hm.add_interior("Room2", parent="Dungeon",
                         connections=[{"to": "Room1"}, {"to": "Room3"}])
        hm.add_interior("Room3", parent="Dungeon",
                         connections=[{"to": "Room2"}])

        hm.enter_compound("Dungeon")
        result = hm.move_interior("Room3")
        assert result["success"] is True

    def test_enter_exit_roundtrip(self, campaign_dir):
        hm = _setup_tavern(campaign_dir)
        hm.enter_compound("Tavern")
        hm.move_interior("Kitchen")
        hm.exit_compound()
        overview = _load_overview(campaign_dir)
        assert overview["player_position"]["current_location"] == "Tavern"
