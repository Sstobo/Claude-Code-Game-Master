#!/usr/bin/env python3
"""
Consequence management module for DM tools
Handles tracking future events and consequences
"""

import sys
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager


class ConsequenceManager(EntityManager):
    """Manage consequence/event tracking. Inherits from EntityManager for common functionality."""

    def __init__(self, world_state_dir: Optional[str] = None):
        super().__init__(world_state_dir)
        self.consequences_file = "consequences.json"
        self._ensure_file()

    def _ensure_file(self):
        """Ensure consequences file has proper structure"""
        data = self.json_ops.load_json(self.consequences_file)
        if not isinstance(data, dict) or 'active' not in data:
            data = {'active': [], 'resolved': []}
            self.json_ops.save_json(self.consequences_file, data)

    def add_consequence(self, description: str, trigger: str,
                        hours: Optional[float] = None) -> str:
        """Add a new consequence. If hours given, stores hours_remaining for auto-tick."""
        data = self.json_ops.load_json(self.consequences_file)

        consequence_id = str(uuid.uuid4())[:8]
        consequence = {
            'id': consequence_id,
            'consequence': description,
            'trigger': trigger,
            'created': self.json_ops.get_timestamp()
        }
        if hours is not None:
            consequence['hours_remaining'] = float(hours)

        if 'active' not in data:
            data['active'] = []
        data['active'].append(consequence)

        if self.json_ops.save_json(self.consequences_file, data):
            if hours is not None:
                print(f"[SUCCESS] Added consequence [{consequence_id}]: {description} (triggers in {hours}h)")
            else:
                print(f"[SUCCESS] Added consequence [{consequence_id}]: {description} (triggers: {trigger})")
            return consequence_id
        return ""

    def tick(self, elapsed_hours: float) -> List[Dict[str, Any]]:
        """Subtract elapsed_hours from all timed consequences. Returns list of triggered ones."""
        data = self.json_ops.load_json(self.consequences_file)
        triggered = []
        remaining = []

        for c in data.get('active', []):
            if 'hours_remaining' not in c:
                remaining.append(c)
                continue

            c['hours_remaining'] = round(c['hours_remaining'] - elapsed_hours, 2)
            if c['hours_remaining'] <= 0:
                triggered.append(c)
                c['triggered_at'] = self.json_ops.get_timestamp()
                if 'resolved' not in data:
                    data['resolved'] = []
                data['resolved'].append(c)
            else:
                remaining.append(c)

        if triggered:
            data['active'] = remaining
            self.json_ops.save_json(self.consequences_file, data)
            print(f"[TIME TICK] {elapsed_hours}h elapsed — {len(triggered)} consequence(s) triggered:")
            for c in triggered:
                print(f"  ⚡ [{c['id']}] {c['consequence']}")
        else:
            data['active'] = remaining
            self.json_ops.save_json(self.consequences_file, data)

        return triggered

    def check_pending(self) -> List[Dict[str, Any]]:
        """
        Get all pending consequences
        """
        data = self.json_ops.load_json(self.consequences_file)
        return data.get('active', [])

    def resolve(self, consequence_id: str) -> bool:
        """
        Resolve a consequence by ID
        """
        data = self.json_ops.load_json(self.consequences_file)

        resolved = None
        remaining = []

        for c in data.get('active', []):
            if c['id'] == consequence_id:
                resolved = c
                resolved['resolved'] = self.json_ops.get_timestamp()
                if 'resolved' not in data:
                    data['resolved'] = []
                data['resolved'].append(resolved)
            else:
                remaining.append(c)

        if resolved:
            data['active'] = remaining
            if self.json_ops.save_json(self.consequences_file, data):
                print(f"[SUCCESS] Resolved: {resolved['consequence']}")
                return True
        else:
            print(f"[ERROR] Consequence '{consequence_id}' not found")

        return False

    def list_resolved(self) -> List[Dict[str, Any]]:
        """
        Get all resolved consequences
        """
        data = self.json_ops.load_json(self.consequences_file)
        return data.get('resolved', [])


def main():
    """CLI interface for consequence management"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Consequence management')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Add consequence
    add_parser = subparsers.add_parser('add', help='Add new consequence')
    add_parser.add_argument('description', help='Consequence description')
    add_parser.add_argument('trigger', help='Trigger condition (text) or use --hours')
    add_parser.add_argument('--hours', type=float, default=None,
                            help='Hours until trigger (enables auto-tick)')

    # Tick time
    tick_parser = subparsers.add_parser('tick', help='Advance time, trigger timed consequences')
    tick_parser.add_argument('hours', type=float, help='Hours elapsed')

    # Check pending
    subparsers.add_parser('check', help='Check pending consequences')

    # Resolve
    resolve_parser = subparsers.add_parser('resolve', help='Resolve a consequence')
    resolve_parser.add_argument('id', help='Consequence ID')

    # List resolved
    subparsers.add_parser('list-resolved', help='List resolved consequences')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = ConsequenceManager()

    if args.action == 'add':
        if not manager.add_consequence(args.description, args.trigger, args.hours):
            sys.exit(1)

    elif args.action == 'tick':
        manager.tick(args.hours)

    elif args.action == 'check':
        pending = manager.check_pending()
        if not pending:
            print("No pending consequences")
        else:
            print(f"{len(pending)} pending consequences:")
            for c in pending:
                if 'hours_remaining' in c:
                    print(f"  [{c['id']}] {c['consequence']} (in {c['hours_remaining']}h)")
                else:
                    print(f"  [{c['id']}] {c['consequence']} (triggers: {c['trigger']})")

    elif args.action == 'resolve':
        if not manager.resolve(args.id):
            sys.exit(1)

    elif args.action == 'list-resolved':
        resolved = manager.list_resolved()
        if resolved:
            print(json.dumps(resolved, indent=2, ensure_ascii=False))
        else:
            print("No resolved consequences")


if __name__ == "__main__":
    main()
