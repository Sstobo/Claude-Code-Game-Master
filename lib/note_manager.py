#!/usr/bin/env python3
"""Note/fact management module for DM tools."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from lib.campaign_manager import CampaignManager
from lib.json_ops import JsonOperations


class NoteManager:
    """Manage campaign facts and notes."""

    def __init__(self, world_state_dir: str = "world-state"):
        self.campaign_mgr = CampaignManager(world_state_dir)
        self.campaign_dir = self.campaign_mgr.get_active_campaign_dir()

        if self.campaign_dir is None:
            raise RuntimeError("No active campaign. Run /new-game or /import first.")

        self.json_ops = JsonOperations(str(self.campaign_dir))

        # Ensure facts file exists
        facts_path = self.campaign_dir / "facts.json"
        if not facts_path.exists():
            self.json_ops.save_json("facts.json", {})

    def add_fact(self, category: str, fact: str) -> bool:
        """Add a fact to the specified category."""
        facts = self.json_ops.load_json("facts.json")

        if category not in facts:
            facts[category] = []

        timestamp = datetime.now(timezone.utc).isoformat()
        facts[category].append({
            'fact': fact,
            'timestamp': timestamp
        })

        if not self.json_ops.save_json("facts.json", facts):
            print(f"[ERROR] Failed to save fact")
            return False

        print(f"[SUCCESS] Recorded fact in {category}: {fact}")
        return True

    def get_facts(self, category: str = None) -> dict:
        """Get facts, optionally filtered by category."""
        facts = self.json_ops.load_json("facts.json")
        if category:
            return {category: facts.get(category, [])}
        return facts

    def list_categories(self) -> list:
        """List all fact categories."""
        facts = self.get_facts()
        return list(facts.keys())


def main():
    """CLI interface for note management."""
    if len(sys.argv) < 2:
        print("Usage: python -m lib.note_manager add <category> <fact>")
        print("       python -m lib.note_manager get [category]")
        print("       python -m lib.note_manager categories")
        sys.exit(1)

    action = sys.argv[1]

    try:
        manager = NoteManager()

        if action == 'add':
            if len(sys.argv) < 4:
                print("Usage: python -m lib.note_manager add <category> <fact>")
                sys.exit(1)
            category = sys.argv[2]
            fact = sys.argv[3]
            if not manager.add_fact(category, fact):
                sys.exit(1)

        elif action == 'get':
            category = sys.argv[2] if len(sys.argv) > 2 else None
            facts = manager.get_facts(category)
            print(json.dumps(facts, indent=2, ensure_ascii=False))

        elif action == 'categories':
            categories = manager.list_categories()
            for cat in categories:
                print(f"  - {cat}")

        else:
            print(f"Unknown action: {action}")
            sys.exit(1)

    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
