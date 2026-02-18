#!/usr/bin/env python3
"""
Quest System module — plot creation (add_plot logic extracted from lib/plot_manager.py)
CORE plot_manager.py handles listing, updating, completing — this module handles creation only.
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "lib"))

from entity_manager import EntityManager


class QuestManager(EntityManager):
    def __init__(self):
        super().__init__()
        self.plots_file = "plots.json"

    def add_plot(self, name: str, description: str, plot_type: str = "side",
                 npcs: list = None, locations: list = None, objectives: list = None,
                 rewards: str = None, consequences: str = None) -> bool:
        plots = self._load_entities(self.plots_file)

        if name in plots:
            print(f"[ERROR] Plot '{name}' already exists")
            return False

        plots[name] = {
            "name": name,
            "description": description,
            "type": plot_type,
            "status": "active",
            "npcs": npcs or [],
            "locations": locations or [],
            "objectives": objectives or [],
            "rewards": rewards or "",
            "consequences": consequences or "",
            "events": [],
            "created_at": self.get_timestamp()
        }

        if self._save_entities(self.plots_file, plots):
            print(f"[SUCCESS] Created plot '{name}' (type: {plot_type})")
            if objectives:
                for obj in objectives:
                    print(f"  • {obj}")
            return True
        return False


def main():
    parser = argparse.ArgumentParser(description="Quest/Plot creation")
    subparsers = parser.add_subparsers(dest="action")

    add_parser = subparsers.add_parser("add", help="Create new plot/quest")
    add_parser.add_argument("name", help="Plot name")
    add_parser.add_argument("description", help="Plot description")
    add_parser.add_argument("--type", dest="plot_type", default="side",
                            choices=["main", "side", "mystery", "threat"],
                            help="Plot type (default: side)")
    add_parser.add_argument("--npcs", nargs="+", default=[], help="NPC names involved")
    add_parser.add_argument("--locations", nargs="+", default=[], help="Location names involved")
    add_parser.add_argument("--objectives", nargs="+", default=[], help="Objective descriptions")
    add_parser.add_argument("--rewards", default="", help="Rewards description")
    add_parser.add_argument("--consequences", default="", help="Consequences if failed/completed")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = QuestManager()

    if args.action == "add":
        success = manager.add_plot(
            name=args.name,
            description=args.description,
            plot_type=args.plot_type,
            npcs=args.npcs,
            locations=args.locations,
            objectives=args.objectives,
            rewards=args.rewards,
            consequences=args.consequences
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
