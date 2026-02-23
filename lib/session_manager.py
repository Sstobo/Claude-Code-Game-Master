#!/usr/bin/env python3
"""
Session management module for DM tools
Handles session lifecycle, party movement, and JSON-based saves
"""

import sys
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager


class SessionManager(EntityManager):
    """Manage D&D session operations. Inherits from EntityManager for common functionality."""

    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)

        # Additional paths specific to session management
        self.world_state_dir = self.campaign_dir  # Alias for compatibility
        self.saves_dir = self.campaign_dir / "saves"
        self.saves_dir.mkdir(parents=True, exist_ok=True)

        # Core files
        self.campaign_file = "campaign-overview.json"
        self.session_log = self.campaign_dir / "session-log.md"

        # Character file (single character per campaign)
        self.character_file = self.campaign_dir / "character.json"

        # Legacy characters dir (for backwards compatibility)
        self.characters_dir = self.campaign_dir / "characters"

    def get_timestamp(self) -> str:
        """Get formatted timestamp"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def get_iso_timestamp(self) -> str:
        """Get ISO format timestamp for filenames"""
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    # ==================== Session Lifecycle ====================

    def start_session(self) -> Dict[str, Any]:
        """
        Start a new session, return world state summary
        """
        # Ensure session log exists
        if not self.session_log.exists():
            self.session_log.write_text("# Campaign Session Log\n\n")

        # Gather world state summary
        summary = {
            "facts_count": self._count_items("facts.json"),
            "npcs_count": self._count_items("npcs.json"),
            "locations_count": self._count_items("locations.json"),
            "current_location": self._get_current_location(),
            "active_character": self._get_active_character(),
            "timestamp": self.get_timestamp()
        }

        # Log session start
        with open(self.session_log, 'a') as f:
            f.write(f"## Session Started: {summary['timestamp']}\n\n")

        print(f"[SUCCESS] Session started at {summary['timestamp']}")
        return summary

    def end_session(self, summary: str) -> bool:
        """
        End session with summary, log to session-log.md
        """
        timestamp = self.get_timestamp()

        # Get session number
        session_num = self._get_session_number()

        # Log session end
        with open(self.session_log, 'a') as f:
            f.write(f"### Session Ended: {timestamp}\n")
            f.write(f"{summary}\n\n")
            f.write("---\n\n")

        print(f"[SUCCESS] Session {session_num} ended and logged")
        return True

    def get_status(self) -> Dict[str, Any]:
        """
        Get current campaign status
        """
        return {
            "facts_count": self._count_items("facts.json"),
            "npcs_count": self._count_items("npcs.json"),
            "locations_count": self._count_items("locations.json"),
            "current_location": self._get_current_location(),
            "active_character": self._get_active_character(),
            "session_number": self._get_session_number(),
            "recent_sessions": self._get_recent_sessions(5)
        }

    # ==================== Party Movement ====================

    def _build_location_stack(self, location_name: str) -> List[str]:
        locations = self.json_ops.load_json("locations.json") or {}
        stack = []
        visited = set()
        current = location_name
        while current and current not in visited:
            visited.add(current)
            stack.append(current)
            loc_data = locations.get(current, {})
            current = loc_data.get("parent") if isinstance(loc_data, dict) else None
        stack.reverse()
        return stack

    def _ensure_location_and_connection(self, old_location: str, new_location: str) -> None:
        """
        Auto-create destination location if missing and add bidirectional
        connection between old and new location if one doesn't exist.
        """
        locations = self.json_ops.load_json("locations.json") or {}
        changed = False

        # Create destination if it doesn't exist
        if new_location not in locations:
            locations[new_location] = {
                "position": "unknown",
                "connections": [],
                "description": "",
                "discovered": self.get_timestamp()
            }
            changed = True

        # Add bidirectional connection if old location is valid and known
        if old_location and old_location != "Unknown" and old_location in locations:
            old_data = locations[old_location]
            new_data = locations[new_location]
            old_type = old_data.get("type") if isinstance(old_data, dict) else None
            new_type = new_data.get("type") if isinstance(new_data, dict) else None
            old_parent = old_data.get("parent") if isinstance(old_data, dict) else None
            new_parent = new_data.get("parent") if isinstance(new_data, dict) else None

            def _get_ancestors(loc: str) -> set:
                visited = set()
                current = loc
                while current and current not in visited:
                    visited.add(current)
                    d = locations.get(current, {})
                    current = d.get("parent") if isinstance(d, dict) else None
                return visited

            should_connect = True
            if old_type == "interior" or new_type == "interior":
                if old_parent != new_parent:
                    old_ancestors = _get_ancestors(old_location)
                    new_ancestors = _get_ancestors(new_location)
                    if new_location not in old_ancestors and old_location not in new_ancestors:
                        should_connect = False

            if should_connect:
                old_connections = locations[old_location].get("connections", [])
                if not any(c.get("to") == new_location for c in old_connections):
                    old_connections.append({"to": new_location, "path": "traveled"})
                    locations[old_location]["connections"] = old_connections
                    changed = True

                new_connections = locations[new_location].get("connections", [])
                if not any(c.get("to") == old_location for c in new_connections):
                    new_connections.append({"to": old_location, "path": "traveled"})
                    locations[new_location]["connections"] = new_connections
                    changed = True

        if changed:
            self.json_ops.save_json("locations.json", locations)

    def move_party(self, location: str) -> Dict[str, str]:
        """
        Move party to new location
        Returns dict with previous and current location
        """
        campaign = self.json_ops.load_json(self.campaign_file)

        if 'player_position' not in campaign:
            campaign['player_position'] = {}

        old_location = campaign['player_position'].get('current_location', 'Unknown')

        # Auto-create location and connections
        self._ensure_location_and_connection(old_location, location)

        campaign['player_position']['previous_location'] = old_location
        campaign['player_position']['current_location'] = location
        campaign['player_position']['arrival_time'] = self.get_timestamp()
        campaign['player_position']['location_stack'] = self._build_location_stack(location)

        self.json_ops.save_json(self.campaign_file, campaign)

        # Update character's location if exists
        # Try new single character.json first, fall back to legacy characters/ dir
        if self.character_file.exists():
            char_data = self.json_ops.load_json("character.json")
            char_data['current_location'] = location
            self.json_ops.save_json("character.json", char_data)
        else:
            # Legacy: check characters/ directory
            active_char = campaign.get('current_character', '')
            if active_char:
                char_id = active_char.lower().replace(' ', '-')
                char_file = self.characters_dir / f"{char_id}.json"
                if char_file.exists():
                    char_data = self.json_ops.load_json(str(char_file))
                    char_data['current_location'] = location
                    self.json_ops.save_json(str(char_file), char_data)

        result = {
            "previous_location": old_location,
            "current_location": location
        }

        print(f"[SUCCESS] Party moved from {old_location} to {location}")
        return result

    # ==================== Save System ====================

    def create_save(self, name: str) -> str:
        """
        Create a named save point (JSON snapshot)
        Returns the save filename
        """
        # Normalize name
        safe_name = name.lower().replace(' ', '-')
        timestamp = self.get_iso_timestamp()
        filename = f"{timestamp}-{safe_name}.json"

        # Gather all world state
        snapshot = {
            "campaign_overview": self.json_ops.load_json(self.campaign_file),
            "npcs": self.json_ops.load_json("npcs.json"),
            "locations": self.json_ops.load_json("locations.json"),
            "facts": self.json_ops.load_json("facts.json"),
            "consequences": self.json_ops.load_json("consequences.json"),
            "characters": self._load_all_characters()
        }

        save_data = {
            "name": name,
            "created": datetime.now(timezone.utc).isoformat(),
            "session_number": self._get_session_number(),
            "snapshot": snapshot
        }

        # Save to file (use absolute path directly, bypassing json_ops path resolution)
        save_path = self.saves_dir / filename
        import json
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"[SUCCESS] Save created: {filename}")
        return filename

    def restore_save(self, name: str) -> bool:
        """
        Restore from a save point
        Name can be full filename or partial match
        """
        import json

        # Find the save file
        save_file = self._find_save(name)
        if not save_file:
            print(f"[ERROR] Save point '{name}' not found")
            return False

        # Load save data directly from absolute path
        try:
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Failed to load save: {e}")
            return False

        snapshot = save_data.get('snapshot', {})

        # Restore each file
        if 'campaign_overview' in snapshot:
            self.json_ops.save_json(self.campaign_file, snapshot['campaign_overview'])
        if 'npcs' in snapshot:
            self.json_ops.save_json("npcs.json", snapshot['npcs'])
        if 'locations' in snapshot:
            self.json_ops.save_json("locations.json", snapshot['locations'])
        if 'facts' in snapshot:
            self.json_ops.save_json("facts.json", snapshot['facts'])
        if 'consequences' in snapshot:
            self.json_ops.save_json("consequences.json", snapshot['consequences'])

        # Restore characters
        if 'characters' in snapshot:
            self._restore_characters(snapshot['characters'])

        print(f"[SUCCESS] Restored from save: {save_file.name}")
        return True

    def list_saves(self) -> List[Dict[str, Any]]:
        """
        List all save points
        """
        import json
        saves = []
        for save_file in sorted(self.saves_dir.glob("*.json"), reverse=True):
            try:
                with open(save_file, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
                saves.append({
                    "filename": save_file.name,
                    "name": save_data.get("name", "Unknown"),
                    "created": save_data.get("created", "Unknown"),
                    "session_number": save_data.get("session_number", "?")
                })
            except (json.JSONDecodeError, IOError):
                continue
        return saves

    def delete_save(self, name: str) -> bool:
        """
        Delete a save point
        """
        save_file = self._find_save(name)
        if not save_file:
            print(f"[ERROR] Save point '{name}' not found")
            return False

        save_file.unlink()
        print(f"[SUCCESS] Deleted save: {save_file.name}")
        return True

    def get_history(self) -> List[str]:
        """
        Get session history from session log
        """
        if not self.session_log.exists():
            return []

        content = self.session_log.read_text()
        lines = content.split('\n')

        # Extract session entries
        sessions = []
        for line in lines:
            if 'Session Started:' in line or 'Session Ended:' in line:
                sessions.append(line.strip())

        return sessions[-10:]  # Return last 10 entries

    # ==================== Full Session Context ====================

    def _truncate(self, text: str, limit: int, full: bool) -> str:
        """Trim long text in compact context mode."""
        if full or not text or len(text) <= limit:
            return text
        return text[:limit - 3].rstrip() + "..."

    def get_full_context(self, full: bool = False) -> str:
        """
        Aggregate all session state into a single readable output.
        Replaces the 5-step startup checklist with one command.
        """
        lines = []

        # --- Campaign header ---
        campaign = self.json_ops.load_json(self.campaign_file) or {}
        campaign_name = campaign.get('name', campaign.get('campaign_name', 'Unknown Campaign'))
        session_num = self._get_session_number()
        location = campaign.get('player_position', {}).get('current_location', 'Unknown')
        time_of_day = campaign.get('time', {}).get('time_of_day', campaign.get('time_of_day', ''))
        current_date = campaign.get('time', {}).get('current_date', campaign.get('current_date', ''))
        time_str = f"{time_of_day}, {current_date}" if time_of_day and current_date else time_of_day or current_date or 'Unknown'

        lines.append("=== SESSION CONTEXT ===")
        lines.append(f"Campaign: {campaign_name} | Session #{session_num}")
        lines.append(f"Location: {location} | Time: {time_str}")

        # --- Character ---
        lines.append("")
        lines.append("--- CHARACTER ---")
        char = None
        if self.character_file.exists():
            import json as _json
            try:
                with open(self.character_file, 'r', encoding='utf-8') as f:
                    char = _json.load(f)
            except (ValueError, IOError):
                pass

        if char:
            name = char.get('name', 'Unknown')
            level = char.get('level', 1)
            race = char.get('race', '?')
            cls = char.get('class', '?')
            hp = char.get('hp', {})
            if isinstance(hp, dict):
                hp_cur = hp.get('current', 0)
                hp_max = hp.get('max', 0)
            else:
                hp_cur = hp
                hp_max = char.get('max_hp', hp)
            ac = char.get('ac', '?')
            xp = char.get('xp', {})
            if isinstance(xp, dict):
                xp_val = xp.get('current', 0)
            else:
                xp_val = xp
            gold = char.get('gold', 0)
            conditions = char.get('conditions', [])
            cond_str = ', '.join(conditions) if conditions else '(none)'
            lines.append(f"{name} - Level {level} {race} {cls} | HP: {hp_cur}/{hp_max} | AC: {ac} | XP: {xp_val} | Gold: {gold}")
            lines.append(f"Conditions: {cond_str}")
        else:
            lines.append("No character found.")

        # --- Party Members ---
        lines.append("")
        lines.append("--- PARTY MEMBERS ---")
        npcs = self.json_ops.load_json("npcs.json") or {}
        party = {n: d for n, d in npcs.items() if isinstance(d, dict) and d.get('is_party_member')}

        if party:
            party_items = list(party.items())
            max_party = len(party_items) if full else 8
            shown_party = party_items[:max_party]
            for npc_name, npc_data in shown_party:
                sheet = npc_data.get('character_sheet', {})
                hp = sheet.get('hp', {'current': 10, 'max': 10})
                ac = sheet.get('ac', 10)
                level = sheet.get('level', 1)
                race = sheet.get('race', 'Unknown')
                cls = sheet.get('class', 'Commoner')
                conditions = sheet.get('conditions', [])
                cond_str = f" [{', '.join(conditions)}]" if conditions else ""
                desc = self._truncate(npc_data.get('description', ''), 180, full)

                lines.append(f"{npc_name} (Lvl {level} {race} {cls}) HP: {hp['current']}/{hp['max']} AC: {ac}{cond_str}")
                if desc:
                    lines.append(f"  {desc}")

                # Recent events
                events = npc_data.get('events', [])
                if events:
                    recent = events[-3:] if full else events[-2:]
                    event_strs = []
                    for ev in recent:
                        if isinstance(ev, dict):
                            event_strs.append(f"\"{self._truncate(ev.get('event', ''), 120, full)}\"")
                        else:
                            event_strs.append(f"\"{self._truncate(str(ev), 120, full)}\"")
                    lines.append(f"  Recent: {' -> '.join(event_strs)}")
                lines.append("")
            if not full and len(party_items) > max_party:
                lines.append(f"... and {len(party_items) - max_party} more party members (use --full)")
                lines.append("")
        else:
            lines.append("(none)")
            lines.append("")

        # --- Pending Consequences ---
        lines.append("--- PENDING CONSEQUENCES ---")
        consequences = self.json_ops.load_json("consequences.json") or {}
        pending = []
        if isinstance(consequences, dict):
            for cid, cdata in consequences.items():
                if isinstance(cdata, dict) and cdata.get('status', 'pending') == 'pending':
                    event = cdata.get('event', cdata.get('description', 'Unknown'))
                    trigger = cdata.get('trigger', 'Unknown')
                    short_id = cid[:4] if len(cid) >= 4 else cid
                    pending.append(f"[{short_id}] {event} -> triggers: {trigger}")
        elif isinstance(consequences, list):
            for cdata in consequences:
                if isinstance(cdata, dict) and cdata.get('status', 'pending') == 'pending':
                    event = cdata.get('event', cdata.get('description', 'Unknown'))
                    trigger = cdata.get('trigger', 'Unknown')
                    cid = str(cdata.get('id', '?'))
                    short_id = cid[:4] if len(cid) >= 4 else cid
                    pending.append(f"[{short_id}] {event} -> triggers: {trigger}")

        if pending:
            max_pending = len(pending) if full else 10
            for p in pending[:max_pending]:
                lines.append(p)
            if not full and len(pending) > max_pending:
                lines.append(f"... and {len(pending) - max_pending} more pending consequences (use --full)")
        else:
            lines.append("(none)")

        # --- Campaign Rules ---
        rules = campaign.get('campaign_rules', {})
        if rules:
            lines.append("")
            lines.append("--- CAMPAIGN RULES ---")
            if isinstance(rules, dict):
                for key, val in rules.items():
                    value_text = self._truncate(str(val), 220, full)
                    lines.append(f"- {key}: {value_text}")
            elif isinstance(rules, list):
                max_rules = len(rules) if full else 12
                for rule in rules[:max_rules]:
                    lines.append(f"- {self._truncate(str(rule), 220, full)}")
                if not full and len(rules) > max_rules:
                    lines.append(f"- ... and {len(rules) - max_rules} more rules (use --full)")

        return "\n".join(lines)

    # ==================== Private Helpers ====================

    def _count_items(self, filename: str) -> int:
        """Count items in a JSON file"""
        data = self.json_ops.load_json(filename)
        if isinstance(data, dict):
            # For facts.json, sum all category counts
            if filename == "facts.json":
                return sum(len(v) for v in data.values() if isinstance(v, list))
            return len(data)
        elif isinstance(data, list):
            return len(data)
        return 0

    def _get_current_location(self) -> Optional[str]:
        """Get current party location"""
        campaign = self.json_ops.load_json(self.campaign_file)
        return campaign.get('player_position', {}).get('current_location')

    def _get_active_character(self) -> Optional[str]:
        """Get active character name"""
        campaign = self.json_ops.load_json(self.campaign_file)
        return campaign.get('current_character')

    def _get_session_number(self) -> int:
        """Get current session number from log"""
        if not self.session_log.exists():
            return 0
        content = self.session_log.read_text()
        return content.count('Session Started:')

    def _get_recent_sessions(self, count: int) -> List[str]:
        """Get recent session entries"""
        history = self.get_history()
        return history[-count:] if history else []

    def _load_all_characters(self) -> Dict[str, Any]:
        """Load character data for snapshot"""
        characters = {}

        # Try new single character.json first
        if self.character_file.exists():
            char_data = self.json_ops.load_json("character.json")
            # Use 'character' as the key for the single character
            characters['character'] = char_data
        elif self.characters_dir.exists():
            # Legacy: load from characters/ directory
            for char_file in self.characters_dir.glob("*.json"):
                # Use relative path from campaign dir
                char_data = self.json_ops.load_json(f"characters/{char_file.name}")
                characters[char_file.stem] = char_data

        return characters

    def _restore_characters(self, characters: Dict[str, Any]) -> None:
        """Restore character data from snapshot"""
        import json

        # Check if this is new format (single 'character' key) or legacy
        if 'character' in characters and len(characters) == 1:
            # New format: restore to character.json
            with open(self.character_file, 'w', encoding='utf-8') as f:
                json.dump(characters['character'], f, indent=2, ensure_ascii=False)
        else:
            # Legacy format: restore to characters/ directory
            self.characters_dir.mkdir(parents=True, exist_ok=True)
            for name, data in characters.items():
                char_file = self.characters_dir / f"{name}.json"
                self.json_ops.save_json(str(char_file), data)

    def _find_save(self, name: str) -> Optional[Path]:
        """Find a save file by name or partial match"""
        # Try exact filename first
        exact_match = self.saves_dir / name
        if exact_match.exists():
            return exact_match

        # Try with .json extension
        if not name.endswith('.json'):
            exact_match = self.saves_dir / f"{name}.json"
            if exact_match.exists():
                return exact_match

        # Try partial match
        for save_file in self.saves_dir.glob("*.json"):
            if name.lower() in save_file.name.lower():
                return save_file

        return None


def main():
    """CLI interface for session management"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Session management')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Start session
    subparsers.add_parser('start', help='Start new session')

    # End session
    end_parser = subparsers.add_parser('end', help='End session')
    end_parser.add_argument('summary', nargs='+', help='Session summary')

    # Status
    subparsers.add_parser('status', help='Get campaign status')

    # Move party
    move_parser = subparsers.add_parser('move', help='Move party to location')
    move_parser.add_argument('location', nargs='+', help='Location name')

    # Save
    save_parser = subparsers.add_parser('save', help='Create save point')
    save_parser.add_argument('name', nargs='+', help='Save name')

    # Restore
    restore_parser = subparsers.add_parser('restore', help='Restore from save')
    restore_parser.add_argument('name', help='Save name or filename')

    # List saves
    subparsers.add_parser('list-saves', help='List all save points')

    # Delete save
    delete_parser = subparsers.add_parser('delete-save', help='Delete a save point')
    delete_parser.add_argument('name', help='Save name or filename')

    # History
    subparsers.add_parser('history', help='Show session history')

    # Full session context
    context_parser = subparsers.add_parser('context', help='Get full session context (one-command startup)')
    context_parser.add_argument('--full', action='store_true', help='Show full context with less truncation')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = SessionManager()

    if args.action == 'start':
        summary = manager.start_session()
        print(json.dumps(summary, indent=2, ensure_ascii=False))

    elif args.action == 'end':
        summary_text = ' '.join(args.summary)
        if not manager.end_session(summary_text):
            sys.exit(1)

    elif args.action == 'status':
        status = manager.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.action == 'move':
        location = ' '.join(args.location)
        result = manager.move_party(location)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == 'save':
        name = ' '.join(args.name)
        manager.create_save(name)

    elif args.action == 'restore':
        if not manager.restore_save(args.name):
            sys.exit(1)

    elif args.action == 'list-saves':
        saves = manager.list_saves()
        if saves:
            print(json.dumps(saves, indent=2, ensure_ascii=False))
        else:
            print("No saves found")

    elif args.action == 'delete-save':
        if not manager.delete_save(args.name):
            sys.exit(1)

    elif args.action == 'history':
        history = manager.get_history()
        for entry in history:
            print(entry)

    elif args.action == 'context':
        print(manager.get_full_context(full=getattr(args, 'full', False)))


if __name__ == "__main__":
    main()
