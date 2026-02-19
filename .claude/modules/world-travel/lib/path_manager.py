#!/usr/bin/env python3
"""
Path preference management for intelligent navigation
Caches DM decisions about routes between locations
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.json_ops import JsonOperations
from connection_utils import get_connection_between

MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from pathfinding import PathFinder


class PathManager:
    """Manages path preferences and intelligent navigation decisions"""

    def __init__(self, campaign_dir: str):
        self.json_ops = JsonOperations(campaign_dir)
        self.pf = PathFinder()

    def _load_path_preferences(self) -> Dict:
        """Load path preferences from campaign overview"""
        overview = self.json_ops.load_json("campaign-overview.json")
        return overview.get("path_preferences", {})

    def _save_path_preferences(self, preferences: Dict):
        """Save path preferences to campaign overview"""
        overview = self.json_ops.load_json("campaign-overview.json")
        overview["path_preferences"] = preferences
        self.json_ops.save_json("campaign-overview.json", overview)

    def _get_preference_key(self, from_loc: str, to_loc: str) -> str:
        """Generate canonical key for location pair (alphabetically sorted)"""
        locs = sorted([from_loc, to_loc])
        return f"{locs[0]} <-> {locs[1]}"

    def get_cached_decision(self, from_loc: str, to_loc: str) -> Optional[Dict]:
        """
        Check if DM has already decided on a route between these locations

        Returns:
            None if no decision cached, or dict with:
            {
                "decision": "use_route" | "direct" | "blocked",
                "route": [list of locations] if use_route,
                "decided_at": timestamp,
                "reason": optional explanation
            }
        """
        preferences = self._load_path_preferences()
        key = self._get_preference_key(from_loc, to_loc)
        return preferences.get(key)

    def cache_decision(self, from_loc: str, to_loc: str, decision: str,
                      route: Optional[List[str]] = None, reason: Optional[str] = None):
        """
        Cache DM's decision about route between locations

        Args:
            from_loc: Starting location
            to_loc: Destination location
            decision: "use_route", "direct", or "blocked"
            route: Path to use if decision is "use_route"
            reason: Optional explanation for the decision
        """
        preferences = self._load_path_preferences()
        key = self._get_preference_key(from_loc, to_loc)

        preferences[key] = {
            "decision": decision,
            "decided_at": datetime.utcnow().isoformat() + "Z",
        }

        if route is not None:
            preferences[key]["route"] = route
        if reason is not None:
            preferences[key]["reason"] = reason

        self._save_path_preferences(preferences)

    def analyze_route_options(self, from_loc: str, to_loc: str) -> Dict:
        """
        Analyze all possible routes between two locations

        Returns:
            {
                "direct_possible": bool,
                "direct_distance": int or None,
                "direct_bearing": float or None,
                "direct_blocked": bool,
                "blocked_reason": str or None,
                "existing_routes": [
                    {
                        "path": [locations],
                        "distance": total_meters,
                        "hops": number
                    }
                ]
            }
        """
        locations = self.json_ops.load_json("locations.json")

        if from_loc not in locations or to_loc not in locations:
            return {"error": "Location not found"}

        result = {
            "direct_possible": True,
            "direct_distance": None,
            "direct_bearing": None,
            "direct_blocked": False,
            "blocked_reason": None,
            "existing_routes": []
        }

        # Check direct path possibility
        from_coords = locations[from_loc].get("coordinates")
        to_coords = locations[to_loc].get("coordinates")

        if from_coords and to_coords:
            # Calculate direct distance and bearing
            result["direct_distance"] = self.pf.calculate_direct_distance(from_coords, to_coords)
            result["direct_bearing"] = self.pf.calculate_bearing(from_coords, to_coords)

            # Check if bearing is blocked
            is_blocked, reason = self.pf.is_bearing_blocked(
                locations[from_loc],
                result["direct_bearing"]
            )
            result["direct_blocked"] = is_blocked
            result["blocked_reason"] = reason

        # Find existing routes using BFS
        all_routes = self.pf.find_all_routes(from_loc, to_loc, locations, max_routes=3)
        result["existing_routes"] = all_routes

        return result

    def suggest_navigation(self, from_loc: str, to_loc: str) -> Dict:
        """
        Suggest best navigation approach considering cached decisions and route analysis

        Returns:
            {
                "method": "direct" | "route" | "blocked" | "needs_decision",
                "route": [locations] if method is "route",
                "distance": total distance,
                "message": explanation string,
                "options": dict of available choices if needs_decision
            }
        """
        # Check cached decision first
        cached = self.get_cached_decision(from_loc, to_loc)
        if cached:
            if cached["decision"] == "blocked":
                return {
                    "method": "blocked",
                    "message": f"Путь между {from_loc} и {to_loc} заблокирован: {cached.get('reason', 'неизвестная причина')}"
                }
            elif cached["decision"] == "use_route":
                route = cached.get("route", [])
                return {
                    "method": "route",
                    "route": route,
                    "message": f"Используем известный маршрут через {len(route)-2} промежуточных точек"
                }
            elif cached["decision"] == "direct":
                analysis = self.analyze_route_options(from_loc, to_loc)
                return {
                    "method": "direct",
                    "distance": analysis.get("direct_distance"),
                    "bearing": analysis.get("direct_bearing"),
                    "message": "Идём напрямую (решение сохранено)"
                }

        # No cached decision - analyze options
        analysis = self.analyze_route_options(from_loc, to_loc)

        if analysis.get("error"):
            return {
                "method": "error",
                "message": analysis["error"]
            }

        locations = self.json_ops.load_json("locations.json")
        conn = get_connection_between(from_loc, to_loc, locations)
        if conn and conn.get('distance_meters'):
            return {
                "method": "direct",
                "distance": conn['distance_meters'],
                "bearing": conn.get('bearing'),
                "terrain": conn.get('terrain', 'open'),
                "message": f"Прямой путь: {conn['distance_meters']}м"
            }

        # No direct connection — need DM decision
        options = {}

        if not analysis["direct_blocked"] and analysis["direct_distance"]:
            direct_ru, direct_en = self.pf.bearing_to_compass(analysis["direct_bearing"])
            options["direct"] = {
                "distance": analysis["direct_distance"],
                "bearing": analysis["direct_bearing"],
                "direction": f"{direct_ru} ({direct_en})",
                "description": f"Напрямую {analysis['direct_distance']}м на {direct_ru}"
            }

        if analysis["existing_routes"]:
            best_route = analysis["existing_routes"][0]
            options["use_route"] = {
                "route": best_route["path"],
                "distance": best_route["distance"],
                "hops": best_route["hops"],
                "description": f"Через {best_route['hops']} точек, {best_route['distance']}м"
            }

        if analysis["direct_blocked"]:
            options["blocked_reason"] = analysis["blocked_reason"]

        return {
            "method": "needs_decision",
            "message": f"Необходимо решение DM: как добраться из {from_loc} в {to_loc}?",
            "options": options,
            "analysis": analysis
        }


if __name__ == "__main__":
    # Test path manager
    import sys
    if len(sys.argv) < 4:
        print("Usage: python -m lib.path_manager <campaign_dir> <from> <to>")
        sys.exit(1)

    pm = PathManager(sys.argv[1])
    result = pm.suggest_navigation(sys.argv[2], sys.argv[3])
    print(json.dumps(result, indent=2, ensure_ascii=False))
