#!/usr/bin/env python3
"""Hierarchy manager — compound locations with interiors, entry points, and nested navigation."""

import sys
import json
import argparse
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Any


def _find_project_root() -> Path:
    for p in Path(__file__).parents:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("pyproject.toml not found")


PROJECT_ROOT = _find_project_root()
sys.path.insert(0, str(PROJECT_ROOT / "lib"))

from json_ops import JsonOperations

MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from connection_utils import get_connections


class HierarchyManager:

    def __init__(self, campaign_dir: str):
        self.campaign_dir = Path(campaign_dir)
        self.ops = JsonOperations(str(campaign_dir))

    def create_compound(self, name: str, parent: Optional[str] = None,
                        entry_points: Optional[List[str]] = None,
                        mobile: bool = False, description: str = "") -> Dict[str, Any]:
        locations = self.ops.load_json("locations.json")

        if name in locations:
            return {"success": False, "error": f"Location '{name}' already exists"}

        if parent and parent not in locations:
            return {"success": False, "error": f"Parent '{parent}' not found"}

        loc_data: Dict[str, Any] = {
            "description": description,
            "type": "compound",
            "children": [],
            "entry_points": entry_points or [],
            "connections": []
        }

        if parent:
            loc_data["parent"] = parent
            locations.setdefault(parent, {}).setdefault("children", [])
            if name not in locations[parent]["children"]:
                locations[parent]["children"].append(name)

        if mobile:
            loc_data["mobile"] = True

        locations[name] = loc_data
        self.ops.save_json("locations.json", locations)
        return {"success": True, "name": name, "type": "compound"}

    def add_interior(self, name: str, parent: str,
                     connections: Optional[List[Dict[str, str]]] = None,
                     is_entry_point: bool = False,
                     entry_config: Optional[Dict[str, Any]] = None,
                     description: str = "") -> Dict[str, Any]:
        locations = self.ops.load_json("locations.json")

        if name in locations:
            return {"success": False, "error": f"Location '{name}' already exists"}

        if parent not in locations:
            return {"success": False, "error": f"Parent '{parent}' not found"}

        loc_data: Dict[str, Any] = {
            "description": description,
            "type": "interior",
            "parent": parent,
            "connections": connections or []
        }

        if is_entry_point:
            if entry_config:
                loc_data["entry_config"] = entry_config
            locations[parent].setdefault("entry_points", [])
            if name not in locations[parent]["entry_points"]:
                locations[parent]["entry_points"].append(name)

        locations[parent].setdefault("children", [])
        if name not in locations[parent]["children"]:
            locations[parent]["children"].append(name)

        locations[name] = loc_data
        self.ops.save_json("locations.json", locations)
        return {"success": True, "name": name, "parent": parent, "is_entry_point": is_entry_point}

    def enter_compound(self, compound_name: str,
                       entry_point: Optional[str] = None) -> Dict[str, Any]:
        locations = self.ops.load_json("locations.json")

        if compound_name not in locations:
            return {"success": False, "error": f"Compound '{compound_name}' not found"}

        compound = locations[compound_name]
        if compound.get("type") != "compound":
            return {"success": False, "error": f"'{compound_name}' is not a compound"}

        eps = compound.get("entry_points", [])
        if not eps:
            return {"success": False, "error": f"Compound '{compound_name}' has no entry points"}

        target = entry_point or eps[0]
        if target not in eps:
            return {"success": False, "error": f"'{target}' is not an entry point of '{compound_name}'"}

        if target not in locations:
            return {"success": False, "error": f"Entry point location '{target}' not found"}

        stack = self.get_ancestors(compound_name)
        stack.append(target)

        self._update_player_position(target, stack)
        return {"success": True, "location": target, "location_stack": stack}

    def exit_compound(self) -> Dict[str, Any]:
        overview = self.ops.load_json("campaign-overview.json")
        pp = overview.get("player_position", {})
        stack = pp.get("location_stack", [])
        current = pp.get("current_location")

        if not current:
            return {"success": False, "error": "No current location"}

        locations = self.ops.load_json("locations.json")
        current_data = locations.get(current, {})
        parent_name = current_data.get("parent")

        if not parent_name:
            return {"success": False, "error": "Already at top level"}

        parent_data = locations.get(parent_name, {})
        grandparent = parent_data.get("parent")

        if grandparent:
            new_stack = self.get_ancestors(parent_name)
            target = parent_name
        else:
            new_stack = [parent_name]
            target = parent_name

        self._update_player_position(target, new_stack)
        return {"success": True, "location": target, "location_stack": new_stack}

    def move_interior(self, target: str) -> Dict[str, Any]:
        overview = self.ops.load_json("campaign-overview.json")
        pp = overview.get("player_position", {})
        current = pp.get("current_location")
        stack = pp.get("location_stack", [])

        if not current:
            return {"success": False, "error": "No current location"}

        locations = self.ops.load_json("locations.json")

        if target not in locations:
            return {"success": False, "error": f"Location '{target}' not found"}

        current_data = locations.get(current, {})
        target_data = locations.get(target, {})
        current_parent = current_data.get("parent")
        target_parent = target_data.get("parent")

        if current_parent != target_parent:
            return {"success": False, "error": f"'{target}' is not in the same compound as '{current}'"}

        if not self._bfs_reachable(current, target, locations):
            return {"success": False, "error": f"'{target}' is not reachable from '{current}'"}

        new_stack = stack[:]
        if new_stack and new_stack[-1] == current:
            new_stack[-1] = target
        elif new_stack:
            new_stack.append(target)
        else:
            new_stack = self.get_ancestors(target)

        self._update_player_position(target, new_stack)
        return {"success": True, "location": target, "location_stack": new_stack}

    def get_tree(self, root: Optional[str] = None) -> Any:
        locations = self.ops.load_json("locations.json")

        if root:
            if root not in locations:
                return {"error": f"Location '{root}' not found"}
            return self._build_tree_node(root, locations)

        top_level = []
        for name, data in locations.items():
            if not data.get("parent") and data.get("type") in ("compound", None):
                top_level.append(self._build_tree_node(name, locations))
        return top_level

    def get_ancestors(self, name: str) -> List[str]:
        locations = self.ops.load_json("locations.json")
        chain = []
        current = name
        visited = set()

        while current:
            if current in visited:
                break
            visited.add(current)
            chain.append(current)
            current = locations.get(current, {}).get("parent")

        chain.reverse()
        return chain

    def get_children(self, name: str) -> List[str]:
        locations = self.ops.load_json("locations.json")
        return locations.get(name, {}).get("children", [])

    def get_entry_points(self, compound: str) -> List[Dict[str, Any]]:
        locations = self.ops.load_json("locations.json")
        compound_data = locations.get(compound, {})
        ep_names = compound_data.get("entry_points", [])

        result = []
        for ep in ep_names:
            ep_data = locations.get(ep, {})
            result.append({
                "name": ep,
                "entry_config": ep_data.get("entry_config", {}),
                "description": ep_data.get("description", "")
            })
        return result

    def get_location_type(self, name: str) -> str:
        locations = self.ops.load_json("locations.json")
        return locations.get(name, {}).get("type", "")

    def validate_hierarchy(self) -> Dict[str, Any]:
        locations = self.ops.load_json("locations.json")
        errors = []

        for name, data in locations.items():
            parent = data.get("parent")
            if parent:
                if parent not in locations:
                    errors.append(f"'{name}' references missing parent '{parent}'")
                elif name not in locations[parent].get("children", []):
                    errors.append(f"'{name}' has parent '{parent}' but is not in parent's children list")

            for child in data.get("children", []):
                if child not in locations:
                    errors.append(f"'{name}' references missing child '{child}'")
                elif locations[child].get("parent") != name:
                    errors.append(f"Child '{child}' of '{name}' has different parent: '{locations[child].get('parent')}'")

        for name in locations:
            visited = set()
            current = name
            while current:
                if current in visited:
                    errors.append(f"Cycle detected at '{name}' involving '{current}'")
                    break
                visited.add(current)
                current = locations.get(current, {}).get("parent")

        return {"valid": len(errors) == 0, "errors": errors}

    def resolve_player_position(self) -> Dict[str, Any]:
        overview = self.ops.load_json("campaign-overview.json")
        pp = overview.get("player_position", {})
        current = pp.get("current_location")
        if not current:
            return {"success": False, "error": "No current location"}

        locations = self.ops.load_json("locations.json")
        loc_data = locations.get(current, {})

        if loc_data.get("type") != "compound":
            return {"success": True, "location": current, "resolved": False}

        eps = loc_data.get("entry_points", [])
        if not eps:
            children = loc_data.get("children", [])
            if children:
                target = children[0]
            else:
                return {"success": True, "location": current, "resolved": False}
        else:
            target = eps[0]

        stack = self.get_ancestors(target)
        self._update_player_position(target, stack)
        return {"success": True, "location": target, "resolved": True,
                "previous": current, "location_stack": stack}

    def _build_tree_node(self, name: str, locations: Dict) -> Dict[str, Any]:
        data = locations.get(name, {})
        node: Dict[str, Any] = {
            "name": name,
            "type": data.get("type", "location"),
        }
        children = data.get("children", [])
        if children:
            node["children"] = [self._build_tree_node(c, locations) for c in children if c in locations]
        return node

    def _bfs_reachable(self, start: str, target: str, locations: Dict) -> bool:
        if start == target:
            return True

        visited = {start}
        queue = deque([start])

        while queue:
            current = queue.popleft()
            for conn in get_connections(current, locations):
                neighbor = conn.get("to") if isinstance(conn, dict) else conn
                if neighbor == target:
                    return True
                if neighbor not in visited and neighbor in locations:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    def _update_player_position(self, current_location: str,
                                location_stack: List[str]) -> None:
        overview = self.ops.load_json("campaign-overview.json")
        pp = overview.setdefault("player_position", {})
        pp["current_location"] = current_location
        pp["location_stack"] = location_stack
        self.ops.save_json("campaign-overview.json", overview)


if __name__ == "__main__":
    def get_campaign_dir():
        project_root = _find_project_root()
        active_file = project_root / "world-state" / "active-campaign.txt"
        if active_file.exists():
            name = active_file.read_text().strip()
            d = project_root / "world-state" / "campaigns" / name
            if d.exists():
                return str(d)
        return None

    campaign_dir = get_campaign_dir()
    if not campaign_dir:
        print("[ERROR] No active campaign")
        sys.exit(1)

    hm = HierarchyManager(campaign_dir)

    parser = argparse.ArgumentParser(description="Hierarchy Manager")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("create-compound")
    p.add_argument("name")
    p.add_argument("--parent")
    p.add_argument("--entry-points", nargs="*", default=[])
    p.add_argument("--mobile", action="store_true")
    p.add_argument("--description", default="")

    p = sub.add_parser("add-room")
    p.add_argument("name")
    p.add_argument("--parent", required=True)
    p.add_argument("--connections", type=json.loads, default=None)
    p.add_argument("--entry-point", action="store_true")
    p.add_argument("--entry-config", type=json.loads, default=None)
    p.add_argument("--description", default="")

    p = sub.add_parser("enter")
    p.add_argument("compound")
    p.add_argument("--entry-point")

    sub.add_parser("exit")

    p = sub.add_parser("move")
    p.add_argument("target")

    p = sub.add_parser("tree")
    p.add_argument("root", nargs="?")

    p = sub.add_parser("children")
    p.add_argument("name")

    p = sub.add_parser("ancestors")
    p.add_argument("name")

    p = sub.add_parser("entry-config")
    p.add_argument("compound")

    p = sub.add_parser("get-type")
    p.add_argument("name")

    sub.add_parser("validate")
    sub.add_parser("resolve")

    args = parser.parse_args()

    if args.cmd == "create-compound":
        result = hm.create_compound(args.name, parent=args.parent,
                                    entry_points=args.entry_points,
                                    mobile=args.mobile, description=args.description)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "add-room":
        result = hm.add_interior(args.name, parent=args.parent,
                                 connections=args.connections,
                                 is_entry_point=args.entry_point,
                                 entry_config=args.entry_config,
                                 description=args.description)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "enter":
        result = hm.enter_compound(args.compound, entry_point=args.entry_point)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "exit":
        result = hm.exit_compound()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "move":
        result = hm.move_interior(args.target)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "tree":
        result = hm.get_tree(args.root)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "children":
        result = hm.get_children(args.name)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "ancestors":
        result = hm.get_ancestors(args.name)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "entry-config":
        result = hm.get_entry_points(args.compound)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "get-type":
        result = hm.get_location_type(args.name)
        print(result)

    elif args.cmd == "validate":
        result = hm.validate_hierarchy()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "resolve":
        result = hm.resolve_player_position()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        parser.print_help()
        sys.exit(1)
