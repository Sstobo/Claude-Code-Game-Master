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
        Start a new session, return world state summary and display previous session recap
        """
        import json

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

        # Display previous session recap if available
        session_history_file = self.campaign_dir / "session-history.json"
        if session_history_file.exists():
            try:
                with open(session_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                if history:
                    last_session = history[-1]
                    print("\n" + "="*60)
                    print("  PREVIOUS SESSION RECAP")
                    print("="*60)
                    print(f"  Session #{last_session.get('session_number', '?')} ended: {last_session.get('ended', 'Unknown')}")
                    print(f"  Location: {last_session.get('location', 'Unknown')}")
                    print(f"  Character: {last_session.get('character', 'Unknown')}")
                    print("")
                    print("  What happened:")
                    summary_text = last_session.get('summary', 'No summary available')
                    # Print first 300 chars of summary, wrapped
                    if len(summary_text) > 300:
                        summary_text = summary_text[:297] + "..."
                    for line in summary_text.split('\n')[:5]:  # First 5 lines
                        if line.strip():
                            print(f"    - {line.strip()[:80]}")
                    key_events = last_session.get('key_events', [])
                    if key_events:
                        print("")
                        print("  Key Events:")
                        for event in key_events[:3]:
                            print(f"    > {event[:70]}")
                    print("="*60)
            except (json.JSONDecodeError, IOError):
                pass  # Silently fail if history file is corrupted

        # Load narrative summary for DM handoff context
        narrative_file = self.campaign_dir / "narrative-summary.md"
        if narrative_file.exists():
            try:
                narrative_content = narrative_file.read_text(encoding='utf-8')
                lines = narrative_content.split('\n')
                # Only show the key sections: character, threads, and narrative direction
                # Skip the raw session log at the bottom to avoid duplication
                print("\n" + "="*60)
                print("  CAMPAIGN CONTEXT (from last save)")
                print("="*60)
                in_recent = False
                shown_lines = 0
                for line in lines:
                    if line.startswith("## Recent Activity") or line.startswith("## Narrative Direction"):
                        in_recent = True
                    if line.startswith("---") and in_recent:
                        break
                    if not in_recent and shown_lines < 60:
                        print(f"  {line}" if line.strip() else "")
                        if line.strip():
                            shown_lines += 1
                print("="*60)
                print(f"  Full summary: {narrative_file.name}")
                print("="*60 + "\n")
            except (IOError, UnicodeDecodeError):
                pass  # Silently fail if narrative file is corrupted

        print(f"\n[SUCCESS] Session started at {summary['timestamp']}")
        return summary

    def end_session(self, summary: str) -> bool:
        """
        End session with summary, log to session-log.md and save structured history
        """
        timestamp = self.get_timestamp()

        # Get session number
        session_num = self._get_session_number()

        # Log session end
        with open(self.session_log, 'a') as f:
            f.write(f"### Session Ended: {timestamp}\n")
            f.write(f"{summary}\n\n")
            f.write("---\n\n")

        # Create structured session history entry
        session_history_file = self.campaign_dir / "session-history.json"
        history_entry = {
            "session_number": session_num,
            "ended": timestamp,
            "summary": summary,
            "location": self._get_current_location(),
            "character": self._get_active_character(),
            "key_events": self._extract_key_events_from_summary(summary)
        }

        # Load existing history or create new
        import json
        history = []
        if session_history_file.exists():
            try:
                with open(session_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = []

        # Append new entry and save (keep last 20 sessions)
        history.append(history_entry)
        history = history[-20:]  # Keep only last 20 sessions

        with open(session_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        # Generate markdown version for easy reading
        self._generate_markdown_history(history)

        print(f"[SUCCESS] Session {session_num} ended and logged")
        return True

    def _generate_markdown_history(self, history: list):
        """Generate a verbose markdown version of session history with full details"""
        import json
        md_file = self.campaign_dir / "session-history.md"

        lines = []
        # Get full campaign and character data
        campaign = self.json_ops.load_json(self.campaign_file) or {}
        campaign_name = campaign.get('name', campaign.get('campaign_name', 'Unknown Campaign'))
        lines.append(f"# Session History - {campaign_name}")
        lines.append("")

        character = {}
        if self.character_file.exists():
            try:
                character = self.json_ops.load_json("character.json") or {}
            except:
                pass

        # CAMPAIGN OVERVIEW SECTION
        lines.append("## Campaign Overview")
        lines.append("")
        if character:
            name = character.get('name', 'Unknown')
            level = character.get('level', 1)
            race = character.get('race', '?')
            cls = character.get('class', '?')
            hp = character.get('hp', {})
            hp_cur = hp.get('current', 0)
            hp_max = hp.get('max', 0)
            ac = character.get('ac', 10)
            gold = character.get('gold', 0)
            xp = character.get('xp', 0)
            if isinstance(xp, dict):
                xp = xp.get('current', 0)

            lines.append(f"### Character: {name}")
            lines.append(f"**Level {level} {race} {cls}**")
            lines.append("")
            lines.append("#### Stats")
            lines.append(f"| HP | AC | Gold | XP |")
            lines.append(f"|----|----|------|----|")
            lines.append(f"| {hp_cur}/{hp_max} | {ac} | {gold} gp | {xp} |")
            lines.append("")

            # Equipment
            equipment = character.get('equipment', [])
            if equipment:
                lines.append("#### Equipment")
                for item in equipment:
                    lines.append(f"- {item}")
                lines.append("")

            # Inventory
            inventory = character.get('inventory', [])
            if inventory:
                lines.append("#### Inventory")
                for item in inventory:
                    lines.append(f"- {item}")
                lines.append("")

        # Current world state
        npcs = self.json_ops.load_json("npcs.json") or {}
        locations = self.json_ops.load_json("locations.json") or {}
        facts = self.json_ops.load_json("facts.json") or {}

        lines.append("### World State")
        lines.append(f"- **Current Location:** {self._get_current_location()}")
        lines.append(f"- **Total Sessions:** {len(history)}")
        lines.append(f"- **NPCs Discovered:** {len(npcs)}")
        lines.append(f"- **Locations Discovered:** {len(locations)}")
        lines.append(f"- **Facts Recorded:** {len(facts)}")
        lines.append("")

        # Party Members
        party = {n: d for n, d in npcs.items() if isinstance(d, dict) and d.get('is_party_member')}
        if party:
            lines.append("### Active Party")
            lines.append("")
            for name, data in party.items():
                lines.append(f"#### {name}")
                if isinstance(data, dict):
                    sheet = data.get('character_sheet', {})
                    hp = sheet.get('hp', {})
                    hp_cur = hp.get('current', '?')
                    hp_max = hp.get('max', '?')
                    ac = sheet.get('ac', '?')
                    level = sheet.get('level', '?')
                    cls = sheet.get('class', 'Unknown')
                    lines.append(f"- {cls} Level {level}")
                    lines.append(f"- HP: {hp_cur}/{hp_max}, AC: {ac}")
                    if data.get('notes'):
                        lines.append(f"- Notes: {data.get('notes')}")
                lines.append("")

        lines.append("---")
        lines.append("")

        # SESSION DETAILS SECTION
        lines.append("## Session Log")
        lines.append("")

        # Add each session (in reverse order - newest first)
        for session in reversed(history):
            session_num = session.get('session_number', '?')
            ended = session.get('ended', 'Unknown')
            summary = session.get('summary', 'No summary available')
            location = session.get('location', 'Unknown')
            character_name = session.get('character', 'Unknown')

            lines.append(f"### Session #{session_num}")
            lines.append("")
            lines.append(f"**Date:** {ended}")
            lines.append(f"**Character:** {character_name}")
            lines.append(f"**Ending Location:** {location}")
            lines.append("")

            lines.append("#### Synopsis")
            lines.append("")
            lines.append(summary)
            lines.append("")

            key_events = session.get('key_events', [])
            if key_events:
                lines.append("#### Key Events")
                lines.append("")
                for i, event in enumerate(key_events, 1):
                    lines.append(f"{i}. {event}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # LEGENDARY MOMENTS SECTION
        lines.append("## Legendary Moments")
        lines.append("")
        lines.append("*Notable achievements and viral content from this campaign*")
        lines.append("")
        lines.append("| Session | Moment | Impact |")
        lines.append("|---------|--------|--------|")
        for session in reversed(history):
            session_num = session.get('session_number', '?')
            summary = session.get('summary', '').lower()
            if 'defeated' in summary:
                lines.append(f"| #{session_num} | Boss Defeated | +Viewers |")
            if 'recruited' in summary:
                lines.append(f"| #{session_num} | New Allies | Party Grew |")
        lines.append("")

        # FOOTER
        lines.append("---")
        lines.append("")
        lines.append(f"*Generated: {self.get_timestamp()}*")
        lines.append(f"*Total Sessions: {len(history)}*")
        lines.append(f"*Campaign Directory: {self.campaign_dir.name}*")

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"[INFO] Generated session-history.md ({len(lines)} lines)")

    def _extract_key_events_from_summary(self, summary: str) -> list:
        """Extract key events from summary text"""
        events = []
        lines = summary.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 10:
                # Look for key action words
                if any(word in line.lower() for word in ['defeated', 'found', 'acquired', 'met', 'joined', 'defended', 'cleared', 'discovered', 'killed', 'recruited', 'gained', 'lost']):
                    events.append(line[:100])  # Keep first 100 chars
        return events[:5]  # Top 5 events

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
            # Check if connection from old -> new exists
            old_connections = locations[old_location].get("connections", [])
            if not any(c.get("to") == new_location for c in old_connections):
                old_connections.append({"to": new_location, "path": "traveled"})
                locations[old_location]["connections"] = old_connections
                changed = True

            # Check if connection from new -> old exists
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

        # Auto-generate narrative summary for DM handoff
        self._generate_narrative_summary(name)

        print(f"[SUCCESS] Save created: {filename}")
        return filename

    def _get_spell_flavor(self, spell_name: str) -> str:
        """Return thematic flavor annotation for known spells based on character context"""
        import json
        flavor_overrides = {}
        char = {}
        if self.character_file.exists():
            try:
                with open(self.character_file, 'r', encoding='utf-8') as f:
                    char = json.load(f)
            except (ValueError, IOError):
                pass

        # Detect fire theme from background, features, or class combo
        context_str = str({
            'class': char.get('class', ''),
            'background': char.get('background', ''),
            'features': char.get('features', []),
            'spells': char.get('spells', {}),
        }).lower()
        is_fire_themed = ('fire' in context_str or
                          ('sorcerer' in context_str and 'draconic' in context_str) or
                          'fire cult' in context_str)

        if is_fire_themed:
            flavor_overrides = {
                'Magic Missile': 'erupts as flaming bolts',
                'Fire Bolt': 'a signature blast of roaring flame',
                'Burning Hands': 'a cone of searing dragonfire',
                'Shocking Grasp': 'arcane fire arcs through the target',
                'Fog Cloud': 'rises as scorching steam',
                'Dancing Lights': 'flicker like embers caught in a updraft',
                'Minor Illusion': 'shimmers in the heat haze',
                'Prestidigitation': 'leaves the faint smell of smoke',
            }
        return flavor_overrides.get(spell_name, '')

    def _generate_narrative_summary(self, save_name: str) -> None:
        """Generate a narrative campaign summary for DM handoff after save"""
        import json
        campaign = self.json_ops.load_json(self.campaign_file) or {}
        char = {}
        if self.character_file.exists():
            try:
                with open(self.character_file, 'r', encoding='utf-8') as f:
                    char = json.load(f)
            except (ValueError, IOError):
                pass

        npcs = self.json_ops.load_json("npcs.json") or {}
        locations = self.json_ops.load_json("locations.json") or {}
        facts_data = self.json_ops.load_json("facts.json") or {}
        consequences = self.json_ops.load_json("consequences.json") or {}

        session_num = self._get_session_number()
        location = campaign.get('player_position', {}).get('current_location', 'Unknown')
        time_of_day = campaign.get('time', {}).get('time_of_day', campaign.get('time_of_day', ''))
        current_date = campaign.get('time', {}).get('current_date', campaign.get('current_date', ''))

        lines = []
        lines.append(f"# Campaign Summary — {campaign.get('campaign_name', campaign.get('name', 'Unnamed'))}")
        lines.append("")
        lines.append(f"*Auto-generated from save: {save_name}*")
        lines.append("")
        lines.append(f"**Session:** #{session_num} | **Location:** {location} | **Time:** {time_of_day} of {current_date}" if time_of_day and current_date else f"**Session:** #{session_num} | **Location:** {location}")
        lines.append("")

        # ===== CHARACTER SECTION =====
        if char:
            name = char.get('name', 'Unknown')
            race = char.get('race', '?')
            cls = char.get('class', '?')
            level = char.get('level', 1)
            hp = char.get('hp', {})
            lines.append(f"## Character: {name}")
            lines.append(f"Level {level} {race} {cls} | HP: {hp.get('current', 0)}/{hp.get('max', 0)} | AC: {char.get('ac', '?')}")
            lines.append(f"Gold: {char.get('gold', 0)} gp | XP: {char.get('xp', {}).get('current', 0)} / {char.get('xp', {}).get('next_level', '?')} to next level")

            # Spells with thematic flavor
            spells = char.get('spells', {})
            if spells:
                cantrips = spells.get('cantrips', [])
                leveled = spells.get('level_1', [])
                if cantrips:
                    flavored_cantrips = []
                    for s in cantrips:
                        flavor = self._get_spell_flavor(s)
                        flavored_cantrips.append(f"{s} ({flavor})" if flavor else s)
                    lines.append(f"Cantrips: {', '.join(flavored_cantrips)}")
                if leveled:
                    flavored_spells = []
                    for s in leveled:
                        flavor = self._get_spell_flavor(s)
                        flavored_spells.append(f"{s} ({flavor})" if flavor else s)
                    lines.append(f"Level 1 Spells: {', '.join(flavored_spells)}")
                # Sorcery Points
                features = char.get('features', [])
                for feat in features:
                    if 'Sorcery' in feat or 'Font of Magic' in feat:
                        lines.append(f"Class Features: {', '.join(f for f in features if 'Sorcery' in f or 'Font' in f or 'Metamagic' in f)}")
                        break
            lines.append("")

            # Personality - traits, ideals, bonds, flaws
            traits = char.get('traits', '')
            ideals = char.get('ideals', '')
            bonds = char.get('bonds', '')
            flaws = char.get('flaws', '')
            if any([traits, ideals, bonds, flaws]):
                lines.append("**Roleplay Anchors:**")
                if traits:
                    lines.append(f"- **Trait:** {traits}")
                if ideals:
                    lines.append(f"- **Ideal:** {ideals}")
                if bonds:
                    lines.append(f"- **Bond:** {bonds}")
                if flaws:
                    lines.append(f"- **Flaw:** {flaws}")
                lines.append("")

            # Key features
            if features:
                combat_features = [f for f in features if not any(skip in f for skip in ['Sorcery', 'Font', 'Metamagic'])]
                if combat_features:
                    lines.append(f"**Key Abilities:** {', '.join(combat_features)}")
                    lines.append("")

            # Equipment
            equipment = char.get('equipment', [])
            if equipment:
                lines.append(f"**Carried Gear:** {', '.join(equipment)}")
                lines.append("")

        # ===== KEY NPCS WITH RELATIONSHIPS =====
        if npcs and isinstance(npcs, dict):
            real_npcs = {n: d for n, d in npcs.items() if isinstance(d, dict) and not d.get('is_party_member')}
            if real_npcs:
                lines.append("## Known NPCs")
                for npc_name, npc_data in real_npcs.items():
                    desc = npc_data.get('description', npc_data.get('role', ''))
                    attitude = npc_data.get('attitude', npc_data.get('status', 'neutral'))
                    relationship = npc_data.get('relationship', '')
                    location_npc = npc_data.get('location', '')
                    parts = [f"**{npc_name}**"]
                    if desc:
                        parts.append(desc)
                    parts.append(f"({attitude})")
                    if relationship:
                        parts.append(f"— {relationship}")
                    if location_npc:
                        parts.append(f"[{location_npc}]")
                    lines.append(f"- {' '.join(parts)}")
                lines.append("")

        # ===== KNOWN LOCATIONS =====
        if locations and isinstance(locations, dict):
            lines.append("## Known Locations")
            for loc_name, loc_data in list(locations.items())[:12]:
                desc = loc_data.get('description', '') if isinstance(loc_data, dict) else ''
                marker = " **[CURRENT]**" if loc_name == location else ""
                if desc:
                    lines.append(f"- **{loc_name}**{marker} — {desc[:150]}")
                else:
                    lines.append(f"- **{loc_name}**{marker}")
            lines.append("")

        # ===== ACTIVE THREADS, LOOSE ENDS & TICKING CLOCKS =====
        lines.append("## Active Threads & Loose Ends")

        # Pull from consequences system
        pending = []
        if isinstance(consequences, dict):
            for cid, cdata in consequences.items():
                if isinstance(cdata, dict) and cdata.get('status', 'pending') == 'pending':
                    pending.append(cdata)

        if pending:
            for c in pending[:5]:
                event = c.get('event', c.get('description', '?'))
                trigger = c.get('trigger', '?')
                lines.append(f"- [ ] {event} *(trigger: {trigger})*")
        else:
            lines.append("- *(No formal consequence trackers running — see Recent Activity for narrative threads)*")

        # Extract loose ends from session log by scanning for known markers
        if self.session_log.exists():
            log_content = self.session_log.read_text()
            # Look for "Loose ends:" / "loose end" lines in the log
            for line in log_content.split('\n'):
                stripped = line.strip()
                if stripped.lower().startswith('**loose end') or stripped.lower().startswith('loose end'):
                    # Extract the loose end description after the colon/separator
                    for sep in [':', '—', '-']:
                        if sep in stripped:
                            text = stripped.split(sep, 1)[1].strip().lstrip('* ')
                            if text:
                                lines.append(f"- [ ] {text}")
                            break
                elif stripped.lower().startswith('- loose end') or stripped.lower().startswith('* loose end'):
                    text = stripped.lstrip('-* ').strip()
                    if text.lower().startswith('loose end'):
                        text = text.split(':', 1)[-1].split('—', 1)[-1].strip()
                    if text:
                        lines.append(f"- [ ] {text}")
            # Also scan for ticking clocks (phrases like "in X days" / "in X nights" near deadlines)
            clock_keywords = ['in \\d+ night', 'in \\d+ day', 'in \\d+ hour', 'countdown', 'deadline', 'within \\d+']
            import re
            for line in log_content.split('\n'):
                stripped = line.strip()
                if any(re.search(k, stripped, re.IGNORECASE) for k in clock_keywords):
                    # Don't duplicate if it's already in a loose-end line
                    is_duplicate = any(stripped in existing for existing in lines[-5:])
                    if not is_duplicate and len(stripped) > 15:
                        # Prefix with context from nearby lines
                        lines.append(f"- [ ] (ticking clock) {stripped[:200]}")
        lines.append("")

        # ===== KEY DECISIONS & NARRATIVE DIRECTION =====
        lines.append("## Narrative Direction")
        lines.append("")
        lines.append("*The following summarizes the story beats, key decisions, and the character's current trajectory to help a new DM pick up seamlessly.*")
        lines.append("")

        # Read session log for beat extraction
        story_beats = []
        if self.session_log.exists():
            log_content = self.session_log.read_text()
            lines.append(log_content.strip())
            lines.append("")

        lines.append("---")
        lines.append("*Generated: {0}*".format(self.get_timestamp()))
        lines.append("*This summary is designed for DM handoff — a new agent should read this first to understand campaign state.*")

        summary_path = self.campaign_dir / "narrative-summary.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"[INFO] Narrative summary written to {summary_path}")

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
            hp_cur = hp.get('current', 0)
            hp_max = hp.get('max', 0)
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

        # --- Narrative Summary (DM Handoff Context) ---
        narrative_file = self.campaign_dir / "narrative-summary.md"
        if narrative_file.exists():
            try:
                narrative_content = narrative_file.read_text(encoding='utf-8')
                # Extract key sections: Character, NPCs, Active Threads, Narrative Direction
                in_section = False
                sections = []
                section_lines = []
                for line in narrative_content.split('\n'):
                    if line.startswith('## ') and not line.startswith('## Recent'):
                        if section_lines:
                            sections.append('\n'.join(section_lines))
                        section_lines = [line]
                        in_section = True
                    elif line.startswith('---') or line.startswith('## Recent'):
                        if section_lines:
                            sections.append('\n'.join(section_lines))
                        section_lines = []
                        in_section = False
                    elif in_section:
                        section_lines.append(line)
                if section_lines:
                    sections.append('\n'.join(section_lines))

                if sections:
                    lines.append("")
                    lines.append("--- NARRATIVE SUMMARY (DM Handoff) ---")
                    for section in sections:
                        truncated = self._truncate(section, 600, full)
                        lines.append(truncated)
                        lines.append("")
            except (IOError, UnicodeDecodeError):
                pass

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
                json.dump(characters['character'], f, indent=2)
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
        print(json.dumps(summary, indent=2))

    elif args.action == 'end':
        summary_text = ' '.join(args.summary)
        if not manager.end_session(summary_text):
            sys.exit(1)

    elif args.action == 'status':
        status = manager.get_status()
        print(json.dumps(status, indent=2))

    elif args.action == 'move':
        location = ' '.join(args.location)
        result = manager.move_party(location)
        print(json.dumps(result, indent=2))

    elif args.action == 'save':
        name = ' '.join(args.name)
        manager.create_save(name)

    elif args.action == 'restore':
        if not manager.restore_save(args.name):
            sys.exit(1)

    elif args.action == 'list-saves':
        saves = manager.list_saves()
        if saves:
            print(json.dumps(saves, indent=2))
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
