#!/usr/bin/env python3
"""
NPC management module for GM tools
Handles NPC creation, updates, and tagging operations
"""

import copy
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager
import visual_appearance as va_mod


# Default character sheet for new party members
PARTY_MEMBER_DEFAULTS = {
    "race": "Unknown",
    "class": "Commoner",
    "level": 1,
    "hp": {"current": 10, "max": 10},
    "ac": 10,
    "stats": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
    "saves": {"str": 0, "dex": 0, "con": 0, "int": 0, "wis": 0, "cha": 0},
    "skills": {},
    "attack_bonus": 2,
    "damage": "1d6",
    "equipment": [],
    "features": [],
    "conditions": [],
    "xp": 0
}


def _positive_int(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _party_sheet_for_npc(npc: dict):
    """First-time party sheet + source label. Copies hp/ac from npc.stats when real."""
    sheet = copy.deepcopy(PARTY_MEMBER_DEFAULTS)
    stats = npc.get("stats") if isinstance(npc.get("stats"), dict) else {}
    hp = _positive_int(stats.get("hp"))
    ac = _positive_int(stats.get("ac"))
    if stats.get("statless") or (hp is None and ac is None):
        return sheet, "defaults (NPC has no stats)"
    if hp is not None:
        sheet["hp"] = {"current": hp, "max": hp}
    if ac is not None:
        sheet["ac"] = ac
    difficulty = stats.get("difficulty")
    if difficulty:
        source = f"from npc.stats (stat-npcs proxy, difficulty {difficulty})"
    else:
        source = "from npc.stats"
    return sheet, source


class NPCManager(EntityManager):
    """Manage NPC operations. Inherits from EntityManager for common functionality."""

    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)
        self.npcs_file = "npcs.json"

    def create_npc(self, name: str, description: str, attitude: str) -> bool:
        """
        Create a new NPC
        Returns True on success, False on failure
        """
        # Validate inputs
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return False

        # Coerce an unrecognized attitude to 'neutral' rather than aborting:
        # creation must succeed so downstream set-inner/mood calls don't fail
        # with "not found". Mirrors the batch-create path below.
        valid, error = self.validators.validate_attitude(attitude)
        if not valid:
            print(f"[WARNING] {error}")
            print(f"[WARNING] Defaulting attitude to 'neutral' for {name}")
            attitude = 'neutral'

        # Check if NPC already exists
        if self._entity_exists(self.npcs_file, name):
            print(f"[ERROR] NPC {name} already exists")
            return False

        # Create NPC data
        npc_data = {
            'description': description,
            'attitude': attitude.lower(),
            'created': self.get_timestamp(),
            'events': [],
            'visual_appearance': va_mod.empty_template(),
            'tags': {
                'locations': [],
                'quests': []
            }
        }

        # Save to file
        if self._add_entity(self.npcs_file, name, npc_data):
            print(f"[SUCCESS] Created NPC: {name} - {description} ({attitude})")
            return True
        return False

    def update_npc(self, name: str, event: str) -> bool:
        """
        Add an event to NPC's history
        """
        # Validate name
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return False

        # Check if NPC exists
        if not self._entity_exists(self.npcs_file, name):
            print(f"[ERROR] NPC {name} not found")
            return False

        # Add event
        event_data = {
            'event': event,
            'timestamp': self.get_timestamp()
        }

        if self.json_ops.append_to_list(self.npcs_file, event_data, [name, 'events']):
            print(f"[SUCCESS] Updated {name}: {event}")
            return True
        return False

    @staticmethod
    def _drift_map(npcs) -> Dict[str, int]:
        """Per-NPC count of improvised beats piled up since the last canon check.

        drift = len(events) - canon_checked_at. A materialized NPC is grounded
        at birth (0 events); every gm-npc update is an improvised beat that has
        NOT been re-verified against the source. Returns {name: drift} for
        drift > 0, worst first. Pure over a loaded dict (unit-testable).
        """
        drift = {}
        if isinstance(npcs, dict):
            for name, data in npcs.items():
                if not isinstance(data, dict):
                    continue
                events = data.get('events', [])
                n = len(events) if isinstance(events, list) else 0
                checked = data.get('canon_checked_at', 0)
                if not isinstance(checked, int):
                    checked = 0
                d = n - checked
                if d > 0:
                    drift[name] = d
        return dict(sorted(drift.items(), key=lambda kv: kv[1], reverse=True))

    def canon_drift(self) -> Dict[str, int]:
        """{name: drift} for NPCs improvised-on since their last re-grounding."""
        return self._drift_map(self.json_ops.load_json(self.npcs_file) or {})

    def stale_npcs(self, threshold: int = 3) -> Dict[str, int]:
        """The re-grounding worklist: NPCs whose canon drift >= threshold."""
        return {n: d for n, d in self.canon_drift().items() if d >= threshold}

    def mark_canon_checked(self, name: str) -> bool:
        """Stamp an NPC re-grounded: watermark = current event count, so only
        future improvisation counts as fresh drift. Call after verifying the
        NPC's journal against the source (RAG)."""
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return False
        npcs = self.json_ops.load_json(self.npcs_file) or {}
        if not isinstance(npcs.get(name), dict):
            print(f"[ERROR] NPC {name} not found")
            return False
        events = npcs[name].get('events', [])
        n = len(events) if isinstance(events, list) else 0
        npcs[name]['canon_checked_at'] = n
        self.json_ops.save_json(self.npcs_file, npcs)
        print(f"[SUCCESS] {name} re-grounded — canon check stamped at {n} beat(s)")
        return True

    def get_npc_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get NPC status and information
        """
        # Validate name
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return None

        npc = self._get_entity(self.npcs_file, name)
        if not npc:
            print(f"[ERROR] NPC {name} not found")
            return None

        return npc

    def format_npc_status(self, name: str) -> Optional[str]:
        """
        Format NPC status for display, with enhanced output for party members.
        """
        npc = self.get_npc_status(name)
        if not npc:
            return None

        lines = [f"=== {name} ===", ""]

        # Basic info
        lines.append(f"Description: {npc.get('description', 'No description')}")
        lines.append(f"Attitude: {npc.get('attitude', 'unknown')}")

        # Visual appearance (for consistent image generation)
        va_line = va_mod.format_line(name, npc.get('visual_appearance'))
        if va_line:
            lines.append(f"Appearance: {va_line}")

        # Party member status
        if npc.get('is_party_member'):
            lines.append("")
            lines.append("--- PARTY MEMBER ---")
            sheet = npc.get('character_sheet', {})

            # Core stats
            hp = sheet.get('hp', {'current': 10, 'max': 10})
            lines.append(f"HP: {hp['current']}/{hp['max']} | AC: {sheet.get('ac', 10)}")
            lines.append(f"Level {sheet.get('level', 1)} {sheet.get('race', 'Unknown')} {sheet.get('class', 'Commoner')}")
            lines.append(f"Attack: +{sheet.get('attack_bonus', 2)} | Damage: {sheet.get('damage', '1d6')}")
            lines.append(f"XP: {sheet.get('xp', 0)}")

            # Ability scores
            stats = sheet.get('stats', {})
            if stats:
                stat_line = " | ".join([f"{k.upper()}: {v}" for k, v in stats.items()])
                lines.append(f"Stats: {stat_line}")

            # Equipment
            equipment = sheet.get('equipment', [])
            if equipment:
                lines.append(f"Equipment: {', '.join(equipment)}")
            else:
                lines.append("Equipment: None")

            # Features
            features = sheet.get('features', [])
            if features:
                lines.append(f"Features: {', '.join(features)}")

            # Conditions
            conditions = sheet.get('conditions', [])
            if conditions:
                lines.append(f"Conditions: {', '.join(conditions)}")

        # Tags
        tags = npc.get('tags', {})
        if isinstance(tags, list):
            # Simple string tags from extraction
            if tags:
                lines.append("")
                lines.append("--- TAGS ---")
                lines.append(', '.join(tags))
        elif isinstance(tags, dict):
            if tags.get('locations') or tags.get('quests'):
                lines.append("")
                lines.append("--- TAGS ---")
                if tags.get('locations'):
                    lines.append(f"Locations: {', '.join(tags['locations'])}")
                if tags.get('quests'):
                    lines.append(f"Quests: {', '.join(tags['quests'])}")

        # Recent events
        events = npc.get('events', [])
        if events:
            lines.append("")
            lines.append("--- RECENT EVENTS ---")
            for event in events[-5:]:  # Show last 5 events
                if isinstance(event, dict):
                    lines.append(f"  • {event.get('event', '')}")
                else:
                    lines.append(f"  • {event}")

        return "\n".join(lines)

    def enhance_npc(self, name: str, enhanced_description: str) -> bool:
        """
        Enhance NPC description
        """
        # Validate name
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return False

        # Check if NPC exists
        if not self._entity_exists(self.npcs_file, name):
            print(f"[ERROR] NPC {name} not found")
            return False

        # Update description
        updates = {'description': enhanced_description}
        if self._update_entity(self.npcs_file, name, updates):
            print(f"[SUCCESS] Enhanced description for {name}")
            return True
        return False

    def tag_location(self, name: str, *locations: str) -> bool:
        """
        Add location tags to NPC
        """
        return self._manage_tags(name, 'locations', locations, 'add')

    def untag_location(self, name: str, *locations: str) -> bool:
        """
        Remove location tags from NPC
        """
        return self._manage_tags(name, 'locations', locations, 'remove')

    def tag_quest(self, name: str, *quests: str) -> bool:
        """
        Add quest tags to NPC
        """
        return self._manage_tags(name, 'quests', quests, 'add')

    def untag_quest(self, name: str, *quests: str) -> bool:
        """
        Remove quest tags from NPC
        """
        return self._manage_tags(name, 'quests', quests, 'remove')

    def get_tags(self, name: str) -> Optional[Dict[str, List[str]]]:
        """
        Get all tags for an NPC
        """
        npc = self.get_npc_status(name)
        if npc:
            tags = npc.get('tags', {'locations': [], 'quests': []})
            if isinstance(tags, list):
                return {'locations': [], 'quests': []}
            return tags
        return None

    def get_voice(self, name: str) -> Optional[List[str]]:
        """Return an NPC's canonical voice lines (verbatim source dialogue).

        Returns None if the NPC does not exist, [] if it has no voice yet.
        Read-only: never mutates the stored `context` field.
        """
        npc = self.get_npc_status(name)
        if npc is None:
            return None
        context = npc.get('context', [])
        if isinstance(context, list):
            return [str(line) for line in context if line]
        if isinstance(context, str) and context.strip():
            return [context.strip()]
        return []

    # NPC inner life (additive; defaults so legacy NPCs load unchanged).
    INNER_LIFE_FIELDS = ('goal', 'secret', 'current_mood', 'voice', 'bonds')

    def get_inner_life(self, name: str) -> Optional[Dict[str, Any]]:
        """Return an NPC's inner life with safe defaults, or None if not found."""
        npc = self.get_npc_status(name)
        if npc is None:
            return None
        return {
            'goal': npc.get('goal', ''),
            'secret': npc.get('secret', ''),
            'current_mood': npc.get('current_mood', 'neutral'),
            'voice': npc.get('voice', ''),
            'bonds': npc.get('bonds', {}),
        }

    def set_inner_life(self, name: str, **fields) -> bool:
        """Set any of goal/secret/current_mood/voice/bonds (additive)."""
        updates = {k: v for k, v in fields.items()
                   if k in self.INNER_LIFE_FIELDS and v is not None}
        if not updates:
            return False
        return self._update_entity(self.npcs_file, name, updates)

    def shift_mood(self, name: str, mood: str) -> bool:
        """Update an NPC's current_mood (persists across sessions)."""
        return self._update_entity(self.npcs_file, name, {'current_mood': mood})

    def get_visual_appearance(self, name: str) -> Optional[Dict[str, Any]]:
        """Return an NPC's canonical visual_appearance block, or None if not found."""
        npc = self.get_npc_status(name)
        if npc is None:
            return None
        return va_mod.normalize(npc.get('visual_appearance'))

    def set_visual_appearance(self, name: str, **fields) -> bool:
        """Merge-update an NPC's visual_appearance (only non-empty fields change)."""
        npc = self.get_npc_status(name)
        if npc is None:
            return False
        merged = va_mod.merge(npc.get('visual_appearance'), fields)
        return self._update_entity(self.npcs_file, name, {'visual_appearance': merged})

    def _manage_tags(self, name: str, tag_type: str, tags: tuple, action: str) -> bool:
        """
        Internal method to manage tags
        """
        # Validate name
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return False

        # Get current NPC data
        npcs = self._load_entities(self.npcs_file)
        if name not in npcs:
            print(f"[ERROR] NPC {name} not found")
            return False

        # Ensure tags structure exists as dict (migrate from list if needed)
        if 'tags' not in npcs[name] or isinstance(npcs[name]['tags'], list):
            npcs[name]['tags'] = {'locations': [], 'quests': []}
        if tag_type not in npcs[name]['tags']:
            npcs[name]['tags'][tag_type] = []

        current_tags = set(npcs[name]['tags'][tag_type])

        if action == 'add':
            current_tags.update(tags)
            action_word = 'Added'
        else:  # remove
            current_tags.difference_update(tags)
            action_word = 'Removed'

        npcs[name]['tags'][tag_type] = list(current_tags)

        if self._save_entities(self.npcs_file, npcs):
            print(f"[SUCCESS] {action_word} {tag_type} tags for {name}: {', '.join(tags)}")
            return True
        return False

    # ==========================================
    # Party Member Methods
    # ==========================================

    def _load_party_member(self, name: str):
        """Load and validate an NPC as a party member.
        Returns (npcs_dict, name) on success, or (None, None) on failure (with error printed).
        """
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return None, None

        npcs = self._load_entities(self.npcs_file)
        if name not in npcs:
            print(f"[ERROR] NPC {name} not found")
            return None, None

        if not npcs[name].get('is_party_member'):
            print(f"[ERROR] {name} is not a party member. Use 'gm-npc.sh promote \"{name}\"' first.")
            return None, None

        return npcs, name

    def promote_to_party_member(self, name: str) -> bool:
        """
        Promote an NPC to party member status with a character sheet.
        First-time promote copies existing npc.stats HP/AC when present;
        genuinely statless NPCs get PARTY_MEMBER_DEFAULTS (disclosed in output).
        If NPC was previously a party member (demoted), restores existing stats.
        """
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return False

        npcs = self._load_entities(self.npcs_file)
        if name not in npcs:
            print(f"[ERROR] NPC {name} not found")
            return False

        if npcs[name].get('is_party_member'):
            print(f"[INFO] {name} is already a party member")
            return True

        # Check if NPC already has a character sheet (was previously a party member)
        existing_sheet = npcs[name].get('character_sheet')

        npcs[name]['is_party_member'] = True
        # A party member is active by definition. Clearing the import's background
        # tier also puts them back in scope for `gm-enhance.sh batch`, which skips
        # background entities.
        npcs[name].pop('background', None)

        if existing_sheet:
            # Restore existing character sheet (NPC was previously demoted)
            hp = existing_sheet.get('hp', {'current': 10, 'max': 10})
            ac = existing_sheet.get('ac', 10)
            if self._save_entities(self.npcs_file, npcs):
                print(f"[SUCCESS] {name} rejoined the party (HP: {hp['current']}/{hp['max']}, AC: {ac})")
                return True
        else:
            sheet, source = _party_sheet_for_npc(npcs[name])
            npcs[name]['character_sheet'] = sheet
            if self._save_entities(self.npcs_file, npcs):
                hp = sheet['hp']
                print(
                    f"[SUCCESS] {name} is now a party member "
                    f"(HP: {hp['current']}/{hp['max']}, AC: {sheet['ac']}) — {source}"
                )
                return True

        return False

    def demote_from_party_member(self, name: str) -> bool:
        """
        Remove party member status from an NPC (keeps character_sheet for history).
        """
        valid, error = self.validators.validate_name(name)
        if not valid:
            print(f"[ERROR] {error}")
            return False

        npcs = self._load_entities(self.npcs_file)
        if name not in npcs:
            print(f"[ERROR] NPC {name} not found")
            return False

        if not npcs[name].get('is_party_member'):
            print(f"[INFO] {name} is not a party member")
            return True

        npcs[name]['is_party_member'] = False

        if self._save_entities(self.npcs_file, npcs):
            print(f"[SUCCESS] {name} is no longer a party member")
            return True
        return False

    def get_party_members(self) -> Dict[str, Dict]:
        """
        Get all NPCs who are party members.
        """
        npcs = self._load_entities(self.npcs_file)
        return {name: data for name, data in npcs.items()
                if data.get('is_party_member')}

    def update_npc_hp(self, name: str, amount: int) -> bool:
        """
        Update an NPC's HP (party members only).
        Positive amount heals, negative amount damages.
        """
        npcs, name = self._load_party_member(name)
        if npcs is None:
            return False

        sheet = npcs[name].get('character_sheet', {})
        hp = sheet.get('hp', {'current': 10, 'max': 10})

        old_hp = hp['current']
        hp['current'] = max(0, min(hp['max'], hp['current'] + amount))
        npcs[name]['character_sheet']['hp'] = hp

        if self._save_entities(self.npcs_file, npcs):
            action = "healed" if amount > 0 else "damaged"
            print(f"[SUCCESS] {name} {action}: {old_hp} → {hp['current']}/{hp['max']} HP")
            if hp['current'] == 0:
                print(f"[WARNING] {name} is at 0 HP!")
            return True
        return False

    def update_npc_xp(self, name: str, amount: int) -> bool:
        """
        Update an NPC's XP (party members only).
        """
        npcs, name = self._load_party_member(name)
        if npcs is None:
            return False

        sheet = npcs[name].get('character_sheet', {})
        old_xp = sheet.get('xp', 0)
        new_xp = max(0, old_xp + amount)
        npcs[name]['character_sheet']['xp'] = new_xp

        if self._save_entities(self.npcs_file, npcs):
            print(f"[SUCCESS] {name} XP: {old_xp} → {new_xp}")
            return True
        return False

    def set_npc_stat(self, name: str, field: str, value: Any) -> bool:
        """
        Set a character sheet field for a party member NPC.
        Supported fields: ac, level, class, race, attack_bonus, damage, hp_max
        """
        npcs, name = self._load_party_member(name)
        if npcs is None:
            return False

        sheet = npcs[name].get('character_sheet', {})

        # Handle special fields - sanitize numeric values first
        def parse_int(val, field_name):
            """Parse integer value with defensive handling."""
            try:
                # Strip whitespace and convert
                cleaned = str(val).strip()
                return int(cleaned)
            except ValueError:
                print(f"[ERROR] Invalid integer value for {field_name}: '{val}'")
                return None

        if field == 'hp_max':
            parsed = parse_int(value, 'hp_max')
            if parsed is None:
                return False
            sheet['hp']['max'] = parsed
            # Also heal to new max if current > new max
            if sheet['hp']['current'] > sheet['hp']['max']:
                sheet['hp']['current'] = sheet['hp']['max']
        elif field == 'attack':
            parsed = parse_int(value, 'attack')
            if parsed is None:
                return False
            sheet['attack_bonus'] = parsed
        elif field in ['ac', 'level', 'xp']:
            parsed = parse_int(value, field)
            if parsed is None:
                return False
            sheet[field] = parsed
        elif field in ['class', 'race', 'damage']:
            sheet[field] = str(value)
        else:
            print(f"[ERROR] Unknown field: {field}")
            print("Valid fields: ac, level, class, race, attack, damage, hp_max")
            return False

        npcs[name]['character_sheet'] = sheet

        if self._save_entities(self.npcs_file, npcs):
            print(f"[SUCCESS] {name} {field} set to {value}")
            return True
        return False

    def update_npc_equipment(self, name: str, action: str, item: str) -> bool:
        """
        Add or remove equipment from a party member NPC.
        """
        npcs, name = self._load_party_member(name)
        if npcs is None:
            return False

        sheet = npcs[name].get('character_sheet', {})
        equipment = sheet.get('equipment', [])

        if action == 'add':
            if item in equipment:
                print(f"[INFO] {name} already has {item}")
                return True
            equipment.append(item)
            action_word = "equipped"
        elif action == 'remove':
            if item not in equipment:
                print(f"[INFO] {name} doesn't have {item}")
                return True
            equipment.remove(item)
            action_word = "unequipped"
        else:
            print(f"[ERROR] Unknown action: {action}. Use 'add' or 'remove'.")
            return False

        npcs[name]['character_sheet']['equipment'] = equipment

        if self._save_entities(self.npcs_file, npcs):
            print(f"[SUCCESS] {name} {action_word}: {item}")
            return True
        return False

    def update_npc_condition(self, name: str, action: str, condition: str) -> bool:
        """
        Add or remove a condition from a party member NPC.
        """
        npcs, name = self._load_party_member(name)
        if npcs is None:
            return False

        sheet = npcs[name].get('character_sheet', {})
        conditions = sheet.get('conditions', [])

        if action == 'add':
            if condition in conditions:
                print(f"[INFO] {name} already has condition: {condition}")
                return True
            conditions.append(condition)
            action_word = "now has"
        elif action == 'remove':
            if condition not in conditions:
                print(f"[INFO] {name} doesn't have condition: {condition}")
                return True
            conditions.remove(condition)
            action_word = "no longer has"
        else:
            print(f"[ERROR] Unknown action: {action}. Use 'add' or 'remove'.")
            return False

        npcs[name]['character_sheet']['conditions'] = conditions

        if self._save_entities(self.npcs_file, npcs):
            print(f"[SUCCESS] {name} {action_word} {condition}")
            return True
        return False

    def update_npc_feature(self, name: str, action: str, feature: str) -> bool:
        """
        Add or remove a feature from a party member NPC.
        """
        npcs, name = self._load_party_member(name)
        if npcs is None:
            return False

        sheet = npcs[name].get('character_sheet', {})
        features = sheet.get('features', [])

        if action == 'add':
            if feature in features:
                print(f"[INFO] {name} already has feature: {feature}")
                return True
            features.append(feature)
            action_word = "gained"
        elif action == 'remove':
            if feature not in features:
                print(f"[INFO] {name} doesn't have feature: {feature}")
                return True
            features.remove(feature)
            action_word = "lost"
        else:
            print(f"[ERROR] Unknown action: {action}. Use 'add' or 'remove'.")
            return False

        npcs[name]['character_sheet']['features'] = features

        if self._save_entities(self.npcs_file, npcs):
            print(f"[SUCCESS] {name} {action_word} feature: {feature}")
            return True
        return False

    def format_party_status(self) -> str:
        """
        Format a summary of all party members with their combat stats.
        """
        party = self.get_party_members()
        if not party:
            return "No party members. Use 'gm-npc.sh promote \"Name\"' to add NPCs to the party."

        lines = ["=== PARTY MEMBERS ===", ""]
        for name, data in party.items():
            sheet = data.get('character_sheet', {})
            hp = sheet.get('hp', {'current': 10, 'max': 10})
            ac = sheet.get('ac', 10)
            level = sheet.get('level', 1)
            char_class = sheet.get('class', 'Commoner')
            conditions = sheet.get('conditions', [])

            # Status line
            status = f"{name} - Lvl {level} {char_class}"
            hp_str = f"HP: {hp['current']}/{hp['max']}"
            ac_str = f"AC: {ac}"

            # Warning for low HP
            if hp['current'] == 0:
                hp_str += " [DOWN!]"
            elif hp['current'] <= hp['max'] // 4:
                hp_str += " [CRITICAL]"

            # Conditions
            cond_str = ""
            if conditions:
                cond_str = f" [{', '.join(conditions)}]"

            lines.append(f"  {status}")
            lines.append(f"    {hp_str} | {ac_str}{cond_str}")
            lines.append("")

        return "\n".join(lines)

    def list_npcs(self, filter_attitude: Optional[str] = None,
                  filter_location: Optional[str] = None,
                  filter_quest: Optional[str] = None) -> Dict[str, Dict]:
        """
        List all NPCs with optional filtering
        """
        npcs = self._load_entities(self.npcs_file)
        filtered = {}

        for name, data in npcs.items():
            # Apply filters
            if filter_attitude and data.get('attitude') != filter_attitude.lower():
                continue

            tags = data.get('tags', {})
            if filter_location and filter_location not in tags.get('locations', []):
                continue
            if filter_quest and filter_quest not in tags.get('quests', []):
                continue

            filtered[name] = data

        return filtered

    def create_batch(self, npcs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple NPCs in batch

        Args:
            npcs_data: List of NPC dictionaries with name, description, attitude, etc.

        Returns:
            List of results for each NPC with success/error status
        """
        results = []
        npcs = self._load_entities(self.npcs_file)

        for npc_data in npcs_data:
            result = {'name': npc_data.get('name', 'Unknown')}

            # Validate required fields
            if not npc_data.get('name'):
                result['success'] = False
                result['error'] = 'Missing NPC name'
                results.append(result)
                continue

            name = npc_data['name']

            # Check for duplicates
            if name in npcs:
                result['success'] = False
                result['error'] = f'NPC {name} already exists'
                results.append(result)
                continue

            # Validate attitude
            attitude = npc_data.get('attitude', 'neutral')
            valid, error = self.validators.validate_attitude(attitude)
            if not valid:
                attitude = 'neutral'  # Default to neutral if invalid

            # Create NPC entry
            npc_entry = {
                'description': npc_data.get('description', 'No description provided'),
                'attitude': attitude.lower(),
                'created': self.get_timestamp(),
                'events': npc_data.get('events', []),
                'visual_appearance': va_mod.normalize(npc_data.get('visual_appearance')),
                'tags': {
                    'locations': npc_data.get('location_tags', []),
                    'quests': npc_data.get('quest_tags', [])
                }
            }

            # Add source if provided
            if npc_data.get('source'):
                npc_entry['source'] = npc_data['source']

            # Add to NPCs dictionary (pending save)
            npcs[name] = npc_entry
            result['_pending'] = True
            results.append(result)

        # Save all NPCs at once, then mark success/failure
        pending = [r for r in results if r.get('_pending')]
        if pending:
            saved = self._save_entities(self.npcs_file, npcs)
            for result in pending:
                del result['_pending']
                if saved:
                    result['success'] = True
                else:
                    result['success'] = False
                    result['error'] = 'Failed to save to file'

        return results


def main():
    """CLI interface for NPC management"""
    import argparse

    parser = argparse.ArgumentParser(description='NPC management')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Create NPC
    create_parser = subparsers.add_parser('create', help='Create new NPC')
    create_parser.add_argument('name', help='NPC name')
    create_parser.add_argument('description', help='NPC description')
    create_parser.add_argument('attitude', help='NPC attitude')

    # Update NPC
    update_parser = subparsers.add_parser('update', help='Add event to NPC')
    update_parser.add_argument('name', help='NPC name')
    update_parser.add_argument('event', help='Event description')

    # Status
    status_parser = subparsers.add_parser('status', help='Get NPC status')
    status_parser.add_argument('name', help='NPC name')

    # Enhance
    enhance_parser = subparsers.add_parser('enhance', help='Enhance NPC description')
    enhance_parser.add_argument('name', help='NPC name')
    enhance_parser.add_argument('description', help='Enhanced description')

    # Tag location
    tag_loc_parser = subparsers.add_parser('tag-location', help='Add location tags')
    tag_loc_parser.add_argument('name', help='NPC name')
    tag_loc_parser.add_argument('locations', nargs='+', help='Location tags')

    # Untag location
    untag_loc_parser = subparsers.add_parser('untag-location', help='Remove location tags')
    untag_loc_parser.add_argument('name', help='NPC name')
    untag_loc_parser.add_argument('locations', nargs='+', help='Location tags')

    # Tag quest
    tag_quest_parser = subparsers.add_parser('tag-quest', help='Add quest tags')
    tag_quest_parser.add_argument('name', help='NPC name')
    tag_quest_parser.add_argument('quests', nargs='+', help='Quest tags')

    # Untag quest
    untag_quest_parser = subparsers.add_parser('untag-quest', help='Remove quest tags')
    untag_quest_parser.add_argument('name', help='NPC name')
    untag_quest_parser.add_argument('quests', nargs='+', help='Quest tags')

    # Get tags
    tags_parser = subparsers.add_parser('tags', help='Get NPC tags')
    tags_parser.add_argument('name', help='NPC name')

    # Voice (canonical dialogue lines)
    voice_parser = subparsers.add_parser('voice', help='Get NPC canonical voice lines')
    voice_parser.add_argument('name', help='NPC name')

    # Inner life (goal/secret/mood/voice/bonds)
    inner_parser = subparsers.add_parser('inner-life', help='Get NPC inner life')
    inner_parser.add_argument('name', help='NPC name')
    setinner_parser = subparsers.add_parser('set-inner', help='Set NPC inner life fields')
    setinner_parser.add_argument('name', help='NPC name')
    setinner_parser.add_argument('--goal')
    setinner_parser.add_argument('--secret')
    setinner_parser.add_argument('--mood')
    setinner_parser.add_argument('--voice')
    mood_parser = subparsers.add_parser('mood', help='Shift NPC current mood')
    mood_parser.add_argument('name', help='NPC name')
    mood_parser.add_argument('mood', help='New mood')

    # Visual appearance (canonical look for consistent image generation)
    appearance_parser = subparsers.add_parser('appearance', help='Get NPC visual_appearance')
    appearance_parser.add_argument('name', help='NPC name')
    setappear_parser = subparsers.add_parser('set-appearance', help='Set NPC visual_appearance fields')
    setappear_parser.add_argument('name', help='NPC name')
    for _f in va_mod.VISUAL_FIELDS:
        setappear_parser.add_argument(f'--{_f}')

    # Canon re-grounding (truth-drift worklist)
    stale_parser = subparsers.add_parser('stale',
                                         help='List NPCs that have drifted from canon and need re-grounding')
    stale_parser.add_argument('--threshold', type=int, default=3,
                              help='Min improvised beats since last check (default 3)')
    checked_parser = subparsers.add_parser('checked',
                                           help='Mark an NPC re-grounded (run after verifying vs source)')
    checked_parser.add_argument('name', help='NPC name')

    # List NPCs
    list_parser = subparsers.add_parser('list', help='List NPCs')
    list_parser.add_argument('--attitude', help='Filter by attitude')
    list_parser.add_argument('--location', help='Filter by location tag')
    list_parser.add_argument('--quest', help='Filter by quest tag')

    # Party member commands
    promote_parser = subparsers.add_parser('promote', help='Promote NPC to party member')
    promote_parser.add_argument('name', help='NPC name')

    demote_parser = subparsers.add_parser('demote', help='Remove party member status')
    demote_parser.add_argument('name', help='NPC name')

    party_parser = subparsers.add_parser('party', help='List all party members')

    subparsers.add_parser('unify-tags',
                          help='Migrate legacy location_tags into tags.locations (one-time per campaign)')

    hp_parser = subparsers.add_parser('hp', help='Update party member HP')
    hp_parser.add_argument('name', help='NPC name')
    hp_parser.add_argument('amount', help='HP change (+5 or -3)')

    xp_parser = subparsers.add_parser('xp', help='Update party member XP')
    xp_parser.add_argument('name', help='NPC name')
    xp_parser.add_argument('amount', help='XP change (+100)')

    set_parser = subparsers.add_parser('set', help='Set character sheet field')
    set_parser.add_argument('name', help='NPC name')
    set_parser.add_argument('field', help='Field (ac, level, class, race, attack, damage, hp_max)')
    set_parser.add_argument('value', help='New value')

    equip_parser = subparsers.add_parser('equip', help='Add equipment')
    equip_parser.add_argument('name', help='NPC name')
    equip_parser.add_argument('item', help='Item to equip')

    unequip_parser = subparsers.add_parser('unequip', help='Remove equipment')
    unequip_parser.add_argument('name', help='NPC name')
    unequip_parser.add_argument('item', help='Item to remove')

    condition_parser = subparsers.add_parser('condition', help='Manage conditions')
    condition_parser.add_argument('name', help='NPC name')
    condition_parser.add_argument('sub_action', choices=['add', 'remove'], help='Add or remove')
    condition_parser.add_argument('condition', help='Condition name')

    feature_parser = subparsers.add_parser('feature', help='Manage features')
    feature_parser.add_argument('name', help='NPC name')
    feature_parser.add_argument('sub_action', choices=['add', 'remove'], help='Add or remove')
    feature_parser.add_argument('feature', help='Feature name')

    from cli_output import wants_json, strip_json_flag, emit, emit_error
    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = NPCManager()

    if json_mode and args.action == 'status':
        npc = manager.get_npc_status(args.name)
        if npc is not None:
            emit(npc, json_mode=True)
        else:
            sys.exit(emit_error("NPC not found", json_mode=True))
        return
    if json_mode and args.action == 'voice':
        voice = manager.get_voice(args.name)
        if voice is not None:
            emit({"voice": voice}, json_mode=True)
        else:
            sys.exit(emit_error("NPC not found", json_mode=True))
        return
    if json_mode and args.action == 'update':
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            ok = manager.update_npc(args.name, args.event)
        if ok:
            emit({"updated": args.name}, json_mode=True)
        else:
            sys.exit(emit_error("NPC update failed", json_mode=True))
        return

    if args.action == 'create':
        if not manager.create_npc(args.name, args.description, args.attitude):
            sys.exit(1)

    elif args.action == 'update':
        if not manager.update_npc(args.name, args.event):
            sys.exit(1)

    elif args.action == 'status':
        formatted = manager.format_npc_status(args.name)
        if formatted:
            print(formatted)
        else:
            sys.exit(1)

    elif args.action == 'enhance':
        if not manager.enhance_npc(args.name, args.description):
            sys.exit(1)

    elif args.action == 'tag-location':
        if not manager.tag_location(args.name, *args.locations):
            sys.exit(1)

    elif args.action == 'untag-location':
        if not manager.untag_location(args.name, *args.locations):
            sys.exit(1)

    elif args.action == 'tag-quest':
        if not manager.tag_quest(args.name, *args.quests):
            sys.exit(1)

    elif args.action == 'untag-quest':
        if not manager.untag_quest(args.name, *args.quests):
            sys.exit(1)

    elif args.action == 'unify-tags':
        from tag_unify import unify_location_tags
        npcs = manager.json_ops.load_json(manager.npcs_file) or {}
        report = unify_location_tags(npcs)
        if report['migrated']:
            manager.json_ops.save_json(manager.npcs_file, npcs)
            print(f"[SUCCESS] Unified location_tags -> tags.locations for "
                  f"{len(report['migrated'])} NPC(s), {report['tags_added']} tag(s) merged: "
                  f"{', '.join(report['migrated'])}")
        else:
            print("No legacy location_tags found — already unified.")

    elif args.action == 'tags':
        tags = manager.get_tags(args.name)
        if tags:
            import json
            print(json.dumps(tags, indent=2))
        else:
            sys.exit(1)

    elif args.action == 'voice':
        voice = manager.get_voice(args.name)
        if voice is None:
            sys.exit(1)
        import json
        print(json.dumps(voice, indent=2))

    elif args.action == 'inner-life':
        il = manager.get_inner_life(args.name)
        if il is None:
            sys.exit(1)
        import json
        print(json.dumps(il, indent=2))

    elif args.action == 'set-inner':
        if not manager.set_inner_life(args.name, goal=args.goal, secret=args.secret,
                                      current_mood=args.mood, voice=args.voice):
            sys.exit(1)

    elif args.action == 'mood':
        if not manager.shift_mood(args.name, args.mood):
            sys.exit(1)

    elif args.action == 'stale':
        worklist = manager.stale_npcs(args.threshold)
        if json_mode:
            emit({"stale": worklist}, json_mode=True)
        elif worklist:
            print(f"=== NPCs DRIFTED FROM CANON (>= {args.threshold} improvised beats) ===")
            for name, d in worklist.items():
                print(f"  {name}: {d} improvised beat(s) since last canon check")
            print("Re-ground each: pull source via RAG, reconcile, then gm-npc.sh checked \"<name>\".")
        else:
            print(f"No NPCs past the drift threshold ({args.threshold}). All grounded.")

    elif args.action == 'checked':
        if not manager.mark_canon_checked(args.name):
            sys.exit(1)

    elif args.action == 'appearance':
        va = manager.get_visual_appearance(args.name)
        if va is None:
            sys.exit(1)
        import json
        if json_mode:
            print(json.dumps(va))
        else:
            line = va_mod.format_line(args.name, va)
            print(line if line else "(no visual_appearance set yet)")

    elif args.action == 'set-appearance':
        fields = {f: getattr(args, f) for f in va_mod.VISUAL_FIELDS}
        if not manager.set_visual_appearance(args.name, **fields):
            sys.exit(1)
        print(f"[SUCCESS] Updated visual_appearance for {args.name}")

    elif args.action == 'list':
        npcs = manager.list_npcs(args.attitude, args.location, args.quest)
        import json
        print(json.dumps(npcs, indent=2))

    elif args.action == 'promote':
        if not manager.promote_to_party_member(args.name):
            sys.exit(1)

    elif args.action == 'demote':
        if not manager.demote_from_party_member(args.name):
            sys.exit(1)

    elif args.action == 'party':
        print(manager.format_party_status())

    elif args.action == 'hp':
        # Parse amount like "+5" or "-3"
        amount_str = args.amount
        if amount_str.startswith('+'):
            amount = int(amount_str[1:])
        elif amount_str.startswith('-'):
            amount = -int(amount_str[1:])
        else:
            amount = int(amount_str)
        if not manager.update_npc_hp(args.name, amount):
            sys.exit(1)

    elif args.action == 'xp':
        amount_str = args.amount
        if amount_str.startswith('+'):
            amount = int(amount_str[1:])
        else:
            amount = int(amount_str)
        if not manager.update_npc_xp(args.name, amount):
            sys.exit(1)

    elif args.action == 'set':
        if not manager.set_npc_stat(args.name, args.field, args.value):
            sys.exit(1)

    elif args.action == 'equip':
        if not manager.update_npc_equipment(args.name, 'add', args.item):
            sys.exit(1)

    elif args.action == 'unequip':
        if not manager.update_npc_equipment(args.name, 'remove', args.item):
            sys.exit(1)

    elif args.action == 'condition':
        if not manager.update_npc_condition(args.name, args.sub_action, args.condition):
            sys.exit(1)

    elif args.action == 'feature':
        if not manager.update_npc_feature(args.name, args.sub_action, args.feature):
            sys.exit(1)


if __name__ == "__main__":
    main()