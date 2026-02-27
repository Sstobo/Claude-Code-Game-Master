#!/usr/bin/env python3
"""Vehicle System — dual-map transport management."""

import sys
import json
import argparse
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
from connection_utils import add_canonical_connection, remove_canonical_connection, get_connections
from pathfinding import PathFinder

MODULE_LIB = Path(__file__).parent
if str(MODULE_LIB) not in sys.path:
    sys.path.insert(0, str(MODULE_LIB))

from hierarchy_manager import HierarchyManager


class VehicleManager:
    """Manages vehicles as dual-map entities with internal rooms and external docking."""

    def __init__(self, campaign_dir: str):
        self.campaign_dir = Path(campaign_dir)
        self.ops = JsonOperations(str(campaign_dir))
        self.hierarchy = HierarchyManager(str(campaign_dir))

    def register_vehicle(self, anchor_name: str, vehicle_id: str, vehicle_type: str,
                         dock_room: str, proximity_radius: int = 5000,
                         max_dock_connections: int = 3) -> bool:
        locations = self.ops.load_json("locations.json")
        if anchor_name not in locations:
            return False

        locations[anchor_name]["_vehicle"] = {
            "vehicle_id": vehicle_id,
            "is_vehicle_anchor": True,
            "vehicle_type": vehicle_type,
            "dock_room": dock_room,
            "proximity_radius_meters": proximity_radius,
            "max_dock_connections": max_dock_connections
        }

        locations[anchor_name]["type"] = "compound"
        locations[anchor_name].setdefault("children", [])
        locations[anchor_name].setdefault("entry_points", [])
        if dock_room and dock_room not in locations[anchor_name]["entry_points"]:
            locations[anchor_name]["entry_points"].append(dock_room)
        locations[anchor_name]["mobile"] = True

        self.ops.save_json("locations.json", locations)
        return True

    def add_room(self, vehicle_id: str, room_name: str, description: Optional[str],
                 from_room: str, bearing: float, distance: float) -> Dict[str, Any]:
        locations = self.ops.load_json("locations.json")

        if from_room not in locations:
            return {"success": False, "error": f"Room '{from_room}' not found"}

        from_coords = locations[from_room].get("coordinates", {"x": 0, "y": 0})
        coords = PathFinder.calculate_coordinates(from_coords, distance, bearing)

        locations[room_name] = {
            "description": description or f"Room aboard {vehicle_id}",
            "coordinates": coords,
            "connections": [],
            "_vehicle": {
                "vehicle_id": vehicle_id,
                "is_vehicle_anchor": False,
                "map_context": "local"
            },
            "type": "interior",
            "parent": self._get_anchor(vehicle_id, locations) or from_room
        }

        anchor_name = self._get_anchor(vehicle_id, locations)
        if anchor_name and anchor_name in locations:
            locations[anchor_name].setdefault("children", [])
            if room_name not in locations[anchor_name]["children"]:
                locations[anchor_name]["children"].append(room_name)
            if room_name in locations[anchor_name].get("entry_points", []):
                pass

        add_canonical_connection(from_room, room_name, locations,
                                distance_meters=distance, bearing=bearing, terrain="internal")
        self.ops.save_json("locations.json", locations)
        return {"success": True, "room": room_name, "coordinates": coords}

    def board_vehicle(self, vehicle_id: str, room: Optional[str] = None) -> Dict[str, Any]:
        locations = self.ops.load_json("locations.json")
        anchor_name = self._get_anchor(vehicle_id, locations)
        if not anchor_name:
            return {"success": False, "error": f"Vehicle '{vehicle_id}' not found"}

        target_room = room or locations[anchor_name]["_vehicle"].get("dock_room", anchor_name)

        rooms = self._get_rooms(vehicle_id, locations)
        if target_room not in rooms and target_room != anchor_name:
            return {"success": False, "error": f"Room '{target_room}' not part of vehicle"}

        self._update_player_position(target_room, "local", vehicle_id)
        self._sync_hierarchy_enter(anchor_name, target_room)
        return {"success": True, "room": target_room, "vehicle_id": vehicle_id}

    def exit_vehicle(self) -> Dict[str, Any]:
        status = self._get_player_vehicle_status()
        if status["map_context"] != "local":
            return {"success": False, "error": "Not inside vehicle"}

        locations = self.ops.load_json("locations.json")
        anchor_name = self._get_anchor(status["vehicle_id"], locations)
        if not anchor_name:
            return {"success": False, "error": "Vehicle anchor not found"}

        self._update_player_position(anchor_name, "global", None)
        self._sync_hierarchy_position(anchor_name, [anchor_name])
        return {"success": True, "location": anchor_name}

    def move_internal(self, room: str) -> Dict[str, Any]:
        status = self._get_player_vehicle_status()
        if status["map_context"] != "local":
            return {"success": False, "error": "Not inside vehicle"}

        locations = self.ops.load_json("locations.json")
        rooms = self._get_rooms(status["vehicle_id"], locations)
        anchor_name = self._get_anchor(status["vehicle_id"], locations)

        valid_targets = rooms + ([anchor_name] if anchor_name else [])
        if room not in valid_targets:
            return {"success": False, "error": f"Room '{room}' not part of vehicle"}

        self._update_player_position(room, "local", status["vehicle_id"])
        anchor_name = self._get_anchor(status["vehicle_id"], locations)
        self._sync_hierarchy_position(room, self.hierarchy.get_ancestors(anchor_name) + [room] if anchor_name else [room])
        return {"success": True, "room": room}

    def move_vehicle(self, vehicle_id: str, destination: Optional[str] = None,
                     x: Optional[float] = None, y: Optional[float] = None) -> Dict[str, Any]:
        locations = self.ops.load_json("locations.json")
        anchor_name = self._get_anchor(vehicle_id, locations)
        if not anchor_name:
            return {"success": False, "error": f"Vehicle '{vehicle_id}' not found"}

        if locations[anchor_name].get("_vehicle", {}).get("stationary"):
            return {"success": False, "error": f"'{anchor_name}' is stationary and cannot be moved"}

        if destination and destination in locations:
            dest_coords = locations[destination].get("coordinates", {"x": 0, "y": 0})
            old_coords = locations[anchor_name].get("coordinates", {"x": 0, "y": 0})
            dist = PathFinder.calculate_direct_distance(old_coords, dest_coords)
            dest_data = locations[destination]
            dest_radius = dest_data.get("diameter_meters", 0) / 2
            ship_radius = locations[anchor_name].get("diameter_meters", 0) / 2
            stopping_dist = max(dest_radius + ship_radius, dest_data.get("_vehicle", {}).get("proximity_radius_meters", 0))
            if not stopping_dist:
                stopping_dist = locations[anchor_name].get("_vehicle", {}).get("proximity_radius_meters", 500)
            if dist > stopping_dist:
                ratio = (dist - stopping_dist) / dist
                new_coords = {
                    "x": round(old_coords["x"] + (dest_coords["x"] - old_coords["x"]) * ratio),
                    "y": round(old_coords["y"] + (dest_coords["y"] - old_coords["y"]) * ratio)
                }
                actual_dist = stopping_dist
            else:
                new_coords = {"x": dest_coords["x"], "y": dest_coords["y"]}
                actual_dist = 0
        elif x is not None and y is not None:
            new_coords = {"x": round(x), "y": round(y)}
            destination = None
            actual_dist = None
        else:
            return {"success": False, "error": "Specify destination or --x --y"}

        old_coords = locations[anchor_name].get("coordinates", {"x": 0, "y": 0})
        dx = new_coords["x"] - old_coords["x"]
        dy = new_coords["y"] - old_coords["y"]

        locations[anchor_name]["coordinates"] = new_coords

        rooms = self._get_rooms(vehicle_id, locations)
        for room_name in rooms:
            if "coordinates" in locations[room_name]:
                rc = locations[room_name]["coordinates"]
                locations[room_name]["coordinates"] = {
                    "x": rc["x"] + dx,
                    "y": rc["y"] + dy
                }

        new_connections = self._rebuild_external_connections(anchor_name, locations)

        player_status = "outside"
        ps = self._get_player_vehicle_status()
        if ps["map_context"] == "local" and ps["vehicle_id"] == vehicle_id:
            player_status = "inside"

        self.ops.save_json("locations.json", locations)
        result = {
            "success": True,
            "vehicle_id": vehicle_id,
            "anchor": anchor_name,
            "new_coordinates": new_coords,
            "new_connections": new_connections,
            "player_status": player_status
        }
        if destination:
            result["destination"] = destination
            result["stopping_distance"] = actual_dist
        return result

    def _sync_hierarchy_enter(self, anchor_name: str, target_room: str) -> None:
        locations = self.ops.load_json("locations.json")
        anchor_data = locations.get(anchor_name, {})
        eps = anchor_data.get("entry_points", [])
        if target_room in eps:
            self.hierarchy.enter_compound(anchor_name, entry_point=target_room)
        else:
            stack = self.hierarchy.get_ancestors(anchor_name) + [target_room]
            self._sync_hierarchy_position(target_room, stack)

    def _sync_hierarchy_position(self, location: str, stack: List[str]) -> None:
        overview = self.ops.load_json("campaign-overview.json")
        pp = overview.setdefault("player_position", {})
        pp["location_stack"] = stack
        self.ops.save_json("campaign-overview.json", overview)

    def _rebuild_external_connections(self, anchor_name: str, locations: Dict) -> List[str]:
        vehicle_data = locations[anchor_name].get("_vehicle", {})
        proximity_radius = vehicle_data.get("proximity_radius_meters", 5000)
        vehicle_id = vehicle_data.get("vehicle_id")

        rooms = self._get_rooms(vehicle_id, locations)
        vehicle_locs = set(rooms + [anchor_name])

        all_conns = get_connections(anchor_name, locations)
        for conn in all_conns:
            target = conn["to"]
            if target not in vehicle_locs:
                remove_canonical_connection(anchor_name, target, locations)

        anchor_coords = locations[anchor_name].get("coordinates", {"x": 0, "y": 0})
        new_neighbors = []

        for loc_name, loc_data in locations.items():
            if loc_name in vehicle_locs:
                continue
            if self._is_internal_room(loc_name, locations) or self._is_vehicle_anchor(loc_name, locations):
                continue
            loc_coords = loc_data.get("coordinates")
            if not loc_coords:
                continue

            dist = PathFinder.calculate_direct_distance(anchor_coords, loc_coords)
            if dist <= proximity_radius:
                terrain = loc_data.get("terrain", "space")
                add_canonical_connection(anchor_name, loc_name, locations,
                                        distance_meters=dist, terrain=terrain)
                new_neighbors.append(loc_name)

        return new_neighbors

    def _get_anchor(self, vehicle_id: str, locations: Dict) -> Optional[str]:
        for name, data in locations.items():
            v = data.get("_vehicle", {})
            if v.get("vehicle_id") == vehicle_id and v.get("is_vehicle_anchor"):
                return name
        return None

    def _get_rooms(self, vehicle_id: str, locations: Dict) -> List[str]:
        result = []
        for name, data in locations.items():
            v = data.get("_vehicle", {})
            if v.get("vehicle_id") == vehicle_id and not v.get("is_vehicle_anchor"):
                result.append(name)
        return result

    def _is_internal_room(self, loc_name: str, locations: Dict) -> bool:
        v = locations.get(loc_name, {}).get("_vehicle", {})
        return bool(v) and not v.get("is_vehicle_anchor", True)

    def _is_vehicle_anchor(self, loc_name: str, locations: Dict) -> bool:
        v = locations.get(loc_name, {}).get("_vehicle", {})
        return bool(v) and v.get("is_vehicle_anchor", False)

    def _update_player_position(self, current_location: str, map_context: str,
                                vehicle_id: Optional[str]) -> None:
        overview = self.ops.load_json("campaign-overview.json")
        pp = overview.setdefault("player_position", {})
        pp["current_location"] = current_location
        pp["map_context"] = map_context
        if vehicle_id is not None:
            pp["vehicle_id"] = vehicle_id
        else:
            pp.pop("vehicle_id", None)
        self.ops.save_json("campaign-overview.json", overview)

    def _get_player_vehicle_status(self) -> Dict[str, Any]:
        overview = self.ops.load_json("campaign-overview.json")
        pp = overview.get("player_position", {})
        return {
            "current_location": pp.get("current_location"),
            "map_context": pp.get("map_context", "global"),
            "vehicle_id": pp.get("vehicle_id")
        }

    def get_status(self, vehicle_id: Optional[str] = None) -> Dict[str, Any]:
        locations = self.ops.load_json("locations.json")
        player = self._get_player_vehicle_status()

        if vehicle_id:
            anchor = self._get_anchor(vehicle_id, locations)
            rooms = self._get_rooms(vehicle_id, locations)
            return {
                "vehicle_id": vehicle_id,
                "anchor": anchor,
                "rooms": rooms,
                "vehicle_type": locations.get(anchor, {}).get("_vehicle", {}).get("vehicle_type") if anchor else None,
                "player_position": player
            }

        vehicles = []
        for name, data in locations.items():
            v = data.get("_vehicle", {})
            if v.get("is_vehicle_anchor"):
                vid = v["vehicle_id"]
                vehicles.append({
                    "vehicle_id": vid,
                    "anchor": name,
                    "rooms": self._get_rooms(vid, locations),
                    "vehicle_type": v.get("vehicle_type")
                })
        return {"vehicles": vehicles, "player_position": player}

    def list_vehicles(self) -> List[Dict[str, Any]]:
        locations = self.ops.load_json("locations.json")
        result = []
        for name, data in locations.items():
            v = data.get("_vehicle", {})
            if v.get("is_vehicle_anchor"):
                vid = v["vehicle_id"]
                result.append({
                    "vehicle_id": vid,
                    "anchor_name": name,
                    "vehicle_type": v.get("vehicle_type"),
                    "rooms_count": len(self._get_rooms(vid, locations))
                })
        return result

    def get_internal_map_data(self, vehicle_id: str) -> Dict[str, Any]:
        locations = self.ops.load_json("locations.json")
        result = {}
        for name, data in locations.items():
            v = data.get("_vehicle", {})
            if v.get("vehicle_id") == vehicle_id:
                result[name] = data
        return result


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

    vm = VehicleManager(campaign_dir)

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("register")
    p.add_argument("name")
    p.add_argument("vehicle_type")
    p.add_argument("anchor_location")
    p.add_argument("--dock-room")
    p.add_argument("--proximity-radius", type=int, default=5000)

    p = sub.add_parser("add-room")
    p.add_argument("vehicle_id")
    p.add_argument("room_name")
    p.add_argument("--from", dest="from_room", required=True)
    p.add_argument("--bearing", type=float, required=True)
    p.add_argument("--distance", type=float, required=True)

    p = sub.add_parser("move-vehicle")
    p.add_argument("vehicle_id")
    p.add_argument("destination", nargs="?")
    p.add_argument("--x", type=float)
    p.add_argument("--y", type=float)

    p = sub.add_parser("board")
    p.add_argument("vehicle_id")
    p.add_argument("--room")

    sub.add_parser("exit-vehicle")

    p = sub.add_parser("status")
    p.add_argument("vehicle_id", nargs="?")

    sub.add_parser("list-vehicles")

    p = sub.add_parser("map-internal")
    p.add_argument("vehicle_id")

    p = sub.add_parser("move-internal")
    p.add_argument("room")

    sub.add_parser("player-context")

    p = sub.add_parser("is-room")
    p.add_argument("vehicle_id")
    p.add_argument("room_name")

    args = parser.parse_args()

    if args.cmd == "register":
        dock = args.dock_room or args.name
        result = vm.register_vehicle(args.anchor_location, args.name, args.vehicle_type, dock, args.proximity_radius)
        print(json.dumps({"success": result}, ensure_ascii=False))

    elif args.cmd == "add-room":
        result = vm.add_room(args.vehicle_id, args.room_name, None, args.from_room, args.bearing, args.distance)
        print(json.dumps(result, ensure_ascii=False))

    elif args.cmd == "move-vehicle":
        if args.destination:
            result = vm.move_vehicle(args.vehicle_id, args.destination)
        elif args.x is not None and args.y is not None:
            result = vm.move_vehicle(args.vehicle_id, None, x=args.x, y=args.y)
        else:
            print("[ERROR] Specify destination or --x --y")
            sys.exit(1)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "board":
        result = vm.board_vehicle(args.vehicle_id, args.room)
        print(json.dumps(result, ensure_ascii=False))

    elif args.cmd == "exit-vehicle":
        result = vm.exit_vehicle()
        print(json.dumps(result, ensure_ascii=False))

    elif args.cmd == "status":
        result = vm.get_status(args.vehicle_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "list-vehicles":
        result = vm.list_vehicles()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "map-internal":
        result = vm.get_internal_map_data(args.vehicle_id)
        print(f"=== Internal Map: {args.vehicle_id} ===")
        for loc_name, loc_data in result.items():
            if loc_data.get("_vehicle", {}).get("is_vehicle_anchor"):
                print(f"  [+] {loc_name} [ANCHOR]")
            else:
                print(f"  [*] {loc_name}")
            for conn in loc_data.get("connections", []):
                print(f"      -> {conn['to']} ({conn.get('distance_meters', '?')}m)")

    elif args.cmd == "move-internal":
        result = vm.move_internal(args.room)
        print(json.dumps(result, ensure_ascii=False))

    elif args.cmd == "player-context":
        result = vm._get_player_vehicle_status()
        print(json.dumps(result, ensure_ascii=False))

    elif args.cmd == "is-room":
        locations = vm.ops.load_json("locations.json")
        rooms = vm._get_rooms(args.vehicle_id, locations)
        print("true" if args.room_name in rooms else "false")

    else:
        parser.print_help()
        sys.exit(1)
