#!/usr/bin/env python3
"""
World statistics module for DM tools
Provides counts and summaries of world state
"""

import sys
import json
from typing import Dict, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from json_ops import JsonOperations
from campaign_manager import CampaignManager


class WorldStats:
    """Generate world state statistics and summaries"""

    def __init__(self, world_state_dir: str = None):
        # Use campaign manager to resolve the correct directory
        base_dir = world_state_dir or "world-state"
        self.campaign_mgr = CampaignManager(base_dir)

        # Get the active campaign directory (falls back to legacy root)
        self.world_state_dir = self.campaign_mgr.get_active_campaign_dir()
        self.json_ops = JsonOperations(str(self.world_state_dir))

        # Character file (new format: single character.json)
        self.character_file = self.world_state_dir / "character.json"

        # Legacy characters dir (for backwards compatibility)
        self.characters_dir = self.world_state_dir / "characters"

    def get_counts(self) -> Dict[str, int]:
        """Get counts of all world entities"""
        counts = {
            "npcs": 0,
            "locations": 0,
            "facts": 0,
            "consequences_active": 0,
            "consequences_resolved": 0,
            "characters": 0,
            "sessions": 0,
            "plots_total": 0,
            "plots_active": 0,
            "plots_completed": 0,
            "plots_main": 0,
            "plots_side": 0,
            "plots_mystery": 0,
            "plots_threat": 0
        }

        # NPCs
        npcs = self.json_ops.load_json("npcs.json")
        counts["npcs"] = len(npcs) if isinstance(npcs, dict) else 0

        # Locations
        locations = self.json_ops.load_json("locations.json")
        counts["locations"] = len(locations) if isinstance(locations, dict) else 0

        # Facts
        facts = self.json_ops.load_json("facts.json")
        if isinstance(facts, dict):
            counts["facts"] = sum(len(v) for v in facts.values() if isinstance(v, list))

        # Consequences
        consequences = self.json_ops.load_json("consequences.json")
        if isinstance(consequences, dict):
            counts["consequences_active"] = len(consequences.get("active", []))
            counts["consequences_resolved"] = len(consequences.get("resolved", []))

        # Plots
        plots = self.json_ops.load_json("plots.json")
        if isinstance(plots, dict):
            counts["plots_total"] = len(plots)
            for name, data in plots.items():
                if isinstance(data, dict):
                    # Count by status (default to 'active')
                    status = data.get('status', 'active').lower()
                    if status == 'active':
                        counts["plots_active"] += 1
                    elif status == 'completed':
                        counts["plots_completed"] += 1
                    # Count by type
                    plot_type = data.get('type', '').lower()
                    if plot_type == 'main':
                        counts["plots_main"] += 1
                    elif plot_type == 'side':
                        counts["plots_side"] += 1
                    elif plot_type == 'mystery':
                        counts["plots_mystery"] += 1
                    elif plot_type == 'threat':
                        counts["plots_threat"] += 1

        # Characters (new format: single character.json)
        if self.character_file.exists():
            counts["characters"] = 1
        elif self.characters_dir.exists():
            counts["characters"] = len(list(self.characters_dir.glob("*.json")))

        # Sessions
        session_log = self.world_state_dir / "session-log.md"
        if session_log.exists():
            content = session_log.read_text()
            counts["sessions"] = content.count("Session Started:")

        return counts

    def get_current_status(self) -> Dict[str, Any]:
        """Get current campaign status"""
        overview = self.json_ops.load_json("campaign-overview.json")
        return {
            "campaign_name": overview.get("campaign_name", "Unknown"),
            "current_location": overview.get("player_position", {}).get("current_location"),
            "time_of_day": overview.get("time_of_day", "Unknown"),
            "current_date": overview.get("current_date", "Unknown"),
            "active_character": overview.get("current_character")
        }

    def get_overview(self, detailed: bool = False) -> Dict[str, Any]:
        """Get full world overview"""
        result = {
            "status": self.get_current_status(),
            "counts": self.get_counts()
        }

        if detailed:
            result["details"] = self._get_details()

        return result

    def _get_details(self) -> Dict[str, Any]:
        """Get detailed entity lists"""
        details = {}

        # NPCs (first 10)
        npcs = self.json_ops.load_json("npcs.json")
        if npcs:
            details["npcs"] = [
                {"name": name, "attitude": data.get("attitude", "unknown")}
                for name, data in sorted(npcs.items())[:10]
            ]
            details["npcs_total"] = len(npcs)

        # Locations (first 10)
        locations = self.json_ops.load_json("locations.json")
        if locations:
            details["locations"] = [
                {"name": name, "connections": len(data.get("connections", []))}
                for name, data in sorted(locations.items())[:10]
            ]
            details["locations_total"] = len(locations)

        # Facts by category
        facts = self.json_ops.load_json("facts.json")
        if facts:
            details["fact_categories"] = {
                cat: len(items) for cat, items in sorted(facts.items())[:5]
            }

        # Active consequences (first 3)
        consequences = self.json_ops.load_json("consequences.json")
        if consequences.get("active"):
            details["active_consequences"] = [
                {"trigger": c.get("trigger"), "description": c.get("consequence", "")[:50]}
                for c in consequences["active"][:3]
            ]

        # Active plots (first 5)
        plots = self.json_ops.load_json("plots.json")
        if plots:
            active_plots = []
            for name, data in sorted(plots.items()):
                if isinstance(data, dict) and data.get('status', 'active').lower() == 'active':
                    active_plots.append({
                        "name": name,
                        "type": data.get("type", "unknown"),
                        "npcs": len(data.get("npcs", [])),
                        "locations": len(data.get("locations", []))
                    })
                    if len(active_plots) >= 5:
                        break
            details["active_plots"] = active_plots
            details["plots_total"] = len(plots)

        # Characters (new format: single character.json)
        if self.character_file.exists():
            char_data = self.json_ops.load_json("character.json")
            details["characters"] = [{
                "name": char_data.get("name", "Unknown"),
                "level": char_data.get("level", 1),
                "race": char_data.get("race", "Unknown"),
                "class": char_data.get("class", "Unknown")
            }]
        elif self.characters_dir.exists():
            chars = []
            for char_file in list(self.characters_dir.glob("*.json"))[:5]:
                # Use relative path from campaign dir
                char_data = self.json_ops.load_json(f"characters/{char_file.name}")
                chars.append({
                    "name": char_data.get("name", char_file.stem),
                    "level": char_data.get("level", 1),
                    "race": char_data.get("race", "Unknown"),
                    "class": char_data.get("class", "Unknown")
                })
            details["characters"] = chars

        return details

    def print_overview(self, detailed: bool = False):
        """Print formatted overview to stdout"""
        overview = self.get_overview(detailed)
        status = overview["status"]
        counts = overview["counts"]

        print("\nCURRENT STATUS")
        print(f"  Location: {status['current_location'] or 'Unknown'}")
        print(f"  Time: {status['time_of_day']} on {status['current_date']}")
        print(f"  Active Character: {status['active_character'] or 'None'}")

        print(f"\nNPCs: {counts['npcs']}")
        if detailed and "details" in overview and "npcs" in overview["details"]:
            for npc in overview["details"]["npcs"]:
                print(f"  - {npc['name']} ({npc['attitude']})")
            if overview["details"]["npcs_total"] > 10:
                print(f"  ... and {overview['details']['npcs_total'] - 10} more")

        print(f"\nLocations: {counts['locations']}")
        if detailed and "details" in overview and "locations" in overview["details"]:
            for loc in overview["details"]["locations"]:
                print(f"  - {loc['name']} ({loc['connections']} connections)")
            if overview["details"]["locations_total"] > 10:
                print(f"  ... and {overview['details']['locations_total'] - 10} more")

        print(f"\nFacts: {counts['facts']}")
        if detailed and "details" in overview and "fact_categories" in overview["details"]:
            for cat, count in overview["details"]["fact_categories"].items():
                print(f"  - {cat}: {count} facts")

        print(f"\nConsequences: {counts['consequences_active']} active, {counts['consequences_resolved']} resolved")
        if detailed and "details" in overview and "active_consequences" in overview["details"]:
            for c in overview["details"]["active_consequences"]:
                print(f"  - {c['trigger']}: {c['description']}...")

        print(f"\nPlots: {counts['plots_total']} total ({counts['plots_active']} active)")
        if counts['plots_total'] > 0:
            print(f"  Types: {counts['plots_main']} main, {counts['plots_side']} side, {counts['plots_mystery']} mystery, {counts['plots_threat']} threat")
        if detailed and "details" in overview and "active_plots" in overview["details"]:
            print("  Active plots:")
            for p in overview["details"]["active_plots"]:
                print(f"    - {p['name']} ({p['type'].upper()}) - {p['npcs']} NPCs, {p['locations']} locations")
            if overview["details"]["plots_total"] > 5:
                print(f"    ... and {overview['details']['plots_total'] - 5} more")

        print(f"\nCharacters: {counts['characters']}")
        if detailed and "details" in overview and "characters" in overview["details"]:
            for char in overview["details"]["characters"]:
                print(f"  - {char['name']} - Level {char['level']} {char['race']} {char['class']}")

        print(f"\nSessions: {counts['sessions']}")

    def print_counts(self):
        """Print simple counts for preview"""
        counts = self.get_counts()
        print(f"  - {counts['npcs']} NPCs")
        print(f"  - {counts['locations']} Locations")
        print(f"  - {counts['facts']} Facts")
        print(f"  - {counts['consequences_active'] + counts['consequences_resolved']} Consequences")
        print(f"  - {counts['characters']} Characters")
        print(f"  - {counts['sessions']} Sessions logged")


def main():
    """CLI interface for world statistics"""
    import argparse

    parser = argparse.ArgumentParser(description='World state statistics')
    parser.add_argument('action', nargs='?', default='overview',
                        choices=['overview', 'counts', 'json'],
                        help='Action to perform')
    parser.add_argument('--detailed', '-d', action='store_true',
                        help='Show detailed information')

    args = parser.parse_args()

    stats = WorldStats()

    if args.action == 'overview':
        stats.print_overview(args.detailed)
    elif args.action == 'counts':
        stats.print_counts()
    elif args.action == 'json':
        overview = stats.get_overview(args.detailed)
        print(json.dumps(overview, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
