#!/usr/bin/env python3
"""
Player character management module for GM tools
Handles PC operations: XP, HP, level progression, and character data
"""

import sys
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager
from character_schema import to_flat, is_open_schema


class PlayerManager(EntityManager):
    """Manage player character operations. Inherits from EntityManager for common functionality."""

    # Default XP thresholds (used only when the active World Kit does not declare
    # its own xp-levels progression). NOT a hardcoded leveling path — see
    # _xp_thresholds(), which delegates to the kit.
    DEFAULT_XP_THRESHOLDS = [
        0,       # Level 1
        300,     # Level 2
        900,     # Level 3
        2700,    # Level 4
        6500,    # Level 5
        14000,   # Level 6
        23000,   # Level 7
        34000,   # Level 8
        48000,   # Level 9
        64000,   # Level 10
        85000,   # Level 11
        100000,  # Level 12
        120000,  # Level 13
        140000,  # Level 14
        165000,  # Level 15
        195000,  # Level 16
        225000,  # Level 17
        265000,  # Level 18
        305000,  # Level 19
        355000,  # Level 20
    ]

    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)

        # Additional paths specific to player management
        self.world_state_dir = self.campaign_dir  # Alias for compatibility
        self.campaign_file = "campaign-overview.json"

        # New: single character file per campaign
        self.character_file = self.campaign_dir / "character.json"

        # Legacy: characters directory (for backwards compatibility)
        self.characters_dir = self.campaign_dir / "characters"

    def _name_to_id(self, name: str) -> str:
        """Convert character name to file ID"""
        return name.lower().replace(' ', '-')

    def _is_using_single_character(self) -> bool:
        """Check if we're using the new single character.json format"""
        return self.character_file.exists()

    def _get_character_path(self, name: str) -> Path:
        """Get path to character JSON file"""
        # New format: single character.json
        if self._is_using_single_character():
            return self.character_file

        # Legacy format: characters/<name>.json
        char_id = self._name_to_id(name)
        return self.characters_dir / f"{char_id}.json"

    def _load_character(self, name: str = None) -> Optional[Dict]:
        """
        Load character data from file
        In single-character mode, name is optional/ignored
        """
        # New format: single character.json
        if self._is_using_single_character():
            try:
                with open(self.character_file, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[ERROR] Failed to load character: {e}")
                return None
            return self._normalize_loaded(raw, "character.json")

        # Legacy format: need name to find file
        if not name:
            # Try to get from campaign overview
            campaign = self.json_ops.load_json(self.campaign_file)
            name = campaign.get('current_character')
            if not name:
                return None

        char_path = self._get_character_path(name)
        if not char_path.exists():
            return None
        try:
            with open(char_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Failed to load character: {e}")
            return None
        return self._normalize_loaded(raw, str(char_path))

    def _normalize_loaded(self, raw: Dict, save_path: str) -> Dict:
        """Return the character in canonical FLAT shape, migrating any legacy
        open-schema file on disk to flat the first time it is read."""
        if is_open_schema(raw):
            flat = to_flat(raw)
            self.json_ops.save_json(save_path, flat)
            return flat
        return raw

    def _save_character(self, name: str, data: Dict) -> bool:
        """Save character data to file using atomic writes via json_ops"""
        # Persist in canonical flat shape (no-op if already flat).
        data = to_flat(data)
        # New format: single character.json
        if self._is_using_single_character():
            return self.json_ops.save_json("character.json", data)

        # Legacy format: characters/<name>.json
        char_path = self._get_character_path(name)
        char_path.parent.mkdir(parents=True, exist_ok=True)
        return self.json_ops.save_json(str(char_path), data)

    def _xp_thresholds(self):
        """Level thresholds from the active World Kit (xp-levels model), else the
        default table. Index L = XP required to reach level L+1; index 0 == 0.

        This is how leveling delegates to the kit instead of a hardcoded 5e path.
        """
        ruleset = self.json_ops.load_json("ruleset.json") or {}
        prog = ruleset.get("progression", {}) or {}
        if prog.get("model") == "xp-levels" and prog.get("thresholds"):
            return [0] + list(prog["thresholds"])
        return self.DEFAULT_XP_THRESHOLDS

    def _normalize_xp(self, char: Dict) -> Dict:
        """Normalize XP to object format {current, next_level}"""
        xp = char.get('xp', 0)
        level = char.get('level', 1)
        thresholds = self._xp_thresholds()

        if isinstance(xp, int):
            # Old format: plain integer
            next_threshold = thresholds[level] if level < len(thresholds) else xp
            char['xp'] = {'current': xp, 'next_level': next_threshold}
        elif not isinstance(xp, dict):
            # Invalid format, reset
            char['xp'] = {'current': 0, 'next_level': thresholds[1] if len(thresholds) > 1 else 0}

        return char

    def get_player(self, name: str) -> Optional[Dict]:
        """Get full player character data"""
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return None
        return char

    def get_visual_appearance(self, name: str = None) -> Optional[Dict[str, Any]]:
        """Return the PC's canonical visual_appearance block, or None if no PC."""
        char = self._load_character(name)
        if not char:
            return None
        import visual_appearance as va_mod
        return va_mod.normalize(char.get('visual_appearance'))

    def set_visual_appearance(self, name: str = None, **fields) -> bool:
        """Merge-update the PC's visual_appearance (only non-empty fields change)."""
        char = self._load_character(name)
        if not char:
            return False
        import visual_appearance as va_mod
        char['visual_appearance'] = va_mod.merge(char.get('visual_appearance'), fields)
        return self._save_character(char.get('name', name), char)

    def list_players(self) -> List[str]:
        """List all player character IDs"""
        players = []

        # New format: single character.json
        if self._is_using_single_character():
            char = self._load_character()
            if char:
                # Use the character name or 'character' as ID
                players.append(char.get('name', 'character').lower().replace(' ', '-'))
            return players

        # Legacy format: scan characters/ directory
        if self.characters_dir.exists():
            for f in self.characters_dir.glob("*.json"):
                players.append(f.stem)
        return sorted(players)

    def show_player(self, name: str) -> Optional[str]:
        """Get formatted player summary"""
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return None

        hp = char.get('hp', {})
        gold = char.get('gold', 0)
        summary = f"{char.get('name', name)} - {char.get('race', '?')} {char.get('class', '?')} Level {char.get('level', 1)} (HP: {hp.get('current', 0)}/{hp.get('max', 0)}, Gold: {gold})"
        status = char.get('status')
        if status in ('dying', 'dead'):
            summary += f" | {status.upper()}"
        conditions = char.get('conditions', [])
        if conditions:
            summary += f" | Conditions: {', '.join(conditions)}"
        return summary

    def show_all_players(self) -> List[str]:
        """Get summaries for all players"""
        summaries = []

        # New format: single character.json
        if self._is_using_single_character():
            char = self._load_character()
            if char:
                hp = char.get('hp', {})
                gold = char.get('gold', 0)
                summaries.append(
                    f"{char.get('name', 'Unknown')} - {char.get('race', '?')} {char.get('class', '?')} Level {char.get('level', 1)} (HP: {hp.get('current', 0)}/{hp.get('max', 0)}, Gold: {gold})"
                )
            return summaries

        # Legacy format: scan characters/ directory
        if self.characters_dir.exists():
            for char_file in self.characters_dir.glob("*.json"):
                try:
                    with open(char_file, 'r', encoding='utf-8') as f:
                        char = json.load(f)
                    hp = char.get('hp', {})
                    gold = char.get('gold', 0)
                    summaries.append(
                        f"{char.get('name', char_file.stem)} - {char.get('race', '?')} {char.get('class', '?')} Level {char.get('level', 1)} (HP: {hp.get('current', 0)}/{hp.get('max', 0)}, Gold: {gold})"
                    )
                except (json.JSONDecodeError, IOError):
                    continue
        return summaries

    def set_current_player(self, name: str) -> bool:
        """Set character as current active PC in campaign"""
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return False

        # Get actual name from character file
        actual_name = char.get('name', name)

        if self.json_ops.update_json(self.campaign_file, {'current_character': actual_name}):
            print(f"[SUCCESS] Set current character to: {actual_name}")
            return True
        return False

    def award_xp(self, name: str, amount: int) -> Dict[str, Any]:
        """
        Award XP to character and check for level up
        Returns dict with xp_gained, new_total, level_up, new_level
        """
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False}

        # Normalize XP structure
        char = self._normalize_xp(char)

        # Add XP
        char['xp']['current'] += amount
        current_xp = char['xp']['current']
        current_level = char.get('level', 1)

        # Check for level up — bound by the active kit's thresholds, not a hardcoded 20.
        thresholds = self._xp_thresholds()
        new_level = current_level
        while new_level < len(thresholds) and current_xp >= thresholds[new_level]:
            new_level += 1

        leveled_up = new_level > current_level
        if leveled_up:
            char['level'] = new_level

        # Update next level threshold (kit-driven)
        thresholds = self._xp_thresholds()
        next_threshold = thresholds[new_level] if new_level < len(thresholds) else current_xp
        char['xp']['next_level'] = next_threshold

        # Save character
        if not self._save_character(name, char):
            return {'success': False}

        result = {
            'success': True,
            'name': char.get('name', name),
            'xp_gained': amount,
            'current_xp': current_xp,
            'next_level_xp': next_threshold if new_level < 20 else 'MAX',
            'level_up': leveled_up,
            'old_level': current_level,
            'new_level': new_level
        }

        # Print result
        if leveled_up:
            print(f"LEVEL_UP {char.get('name', name)} gained {amount} XP and leveled up to Level {new_level}!")
            print(f"XP: {current_xp}/{next_threshold if new_level < 20 else 'MAX'}")
        else:
            print(f"XP_GAIN {char.get('name', name)} gained {amount} XP!")
            print(f"XP: {current_xp}/{next_threshold if new_level < 20 else 'MAX'}")

        return result

    def _spectacle_config(self) -> Dict[str, Any]:
        """Spectacle tier table + optional follower currency from the active kit.
        Tiers default to game_core.DEFAULT_SPECTACLE_TIERS; a kit overrides them
        (and declares a follower currency) via ruleset.json -> progression.spectacle."""
        import game_core
        ruleset = self.json_ops.load_json("ruleset.json") or {}
        prog = ruleset.get("progression", {}) or {}
        spec = prog.get("spectacle", {}) or {}
        return {
            'model': prog.get("model", "milestone"),
            'tiers': spec.get("tiers") or game_core.DEFAULT_SPECTACLE_TIERS,
            'follower_field': spec.get("follower_field"),   # e.g. "followers"
            'follower_label': spec.get("follower_label", "followers"),
        }

    def award_spectacle(self, name: str, tier: str, reason: str = None) -> Dict[str, Any]:
        """
        Award discretionary "spectacle" progress for a clever/effective/unique/
        punishing beat of ANY kind (skill check, social win, exploration, escape,
        surviving punishing odds) — not just kills. Kit-agnostic: the reward shape
        is computed by game_core.spectacle_award against the active progression
        model (XP for level kits, milestone for milestone kits) and any kit-defined
        follower currency. Reuses award_xp so LEVEL_UP detection still fires.
        """
        import game_core
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False, 'error': f"Character '{name}' not found"}

        cfg = self._spectacle_config()
        actual_name = char.get('name', name)

        # XP gap to next level (drives XP scaling; 0 for non-XP kits).
        char = self._normalize_xp(char)
        xp_to_next = max(0, char['xp']['next_level'] - char['xp']['current'])

        award = game_core.spectacle_award(
            tier,
            progression_model=cfg['model'],
            xp_to_next=xp_to_next,
            tiers=cfg['tiers'],
            has_follower_currency=bool(cfg.get('follower_field')),
        )
        if not award.get('ok'):
            valid = ', '.join(award.get('valid', []))
            print(f"[ERROR] Unknown tier '{tier}'. Valid: {valid}")
            return {'success': False, 'error': award.get('error', 'unknown tier')}

        result = {'success': True, 'name': actual_name, 'tier': award['tier'], 'reason': reason}

        # XP-based kits: route through award_xp (handles level-up + LEVEL_UP).
        if award['xp'] > 0:
            xp_result = self.award_xp(actual_name, award['xp'])
            if not xp_result.get('success'):
                return xp_result
            result.update({k: v for k, v in xp_result.items() if k != 'reason'})

        # Milestone kits: tick the milestone counter.
        if award['milestone'] > 0:
            char = self._load_character(actual_name) or char
            new_ms = int(char.get('milestone', 0) or 0) + award['milestone']
            char['milestone'] = new_ms
            self._save_character(actual_name, char)
            result['milestone_gained'] = award['milestone']
            result['milestone_total'] = new_ms
            print(f"MILESTONE +{award['milestone']} -> {new_ms}")

        # Kit follower currency (DCC viewers), co-awarded in the same call.
        follower_field = cfg.get('follower_field')
        if follower_field and award['followers'] > 0:
            char = self._load_character(actual_name) or char
            new_followers = int(char.get(follower_field, 0) or 0) + award['followers']
            char[follower_field] = new_followers
            self._save_character(actual_name, char)
            result['followers_gained'] = award['followers']
            result['followers_total'] = new_followers
            print(f"{cfg['follower_label'].upper()} +{award['followers']} -> {new_followers}")

        if reason:
            print(f"SPECTACLE [{award['tier']}] {actual_name}: {reason}")
        return result

    def get_xp_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get XP and level status for character"""
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return None

        # Normalize XP structure
        char = self._normalize_xp(char)
        self._save_character(name, char)

        current_xp = char['xp']['current']
        current_level = char.get('level', 1)
        next_level_xp = char['xp']['next_level']

        # Check if ready to level up
        ready_to_level = current_xp >= next_level_xp and current_level < 20
        remaining = next_level_xp - current_xp if not ready_to_level else 0

        char_name = char.get('name', name)
        print(f"{char_name} - Level {current_level}")
        print(f"XP: {current_xp}/{next_level_xp}")

        if ready_to_level:
            print("READY_TO_LEVEL_UP")
        else:
            print(f"Next level in: {remaining} XP")

        return {
            'name': char_name,
            'level': current_level,
            'current_xp': current_xp,
            'next_level_xp': next_level_xp,
            'ready_to_level': ready_to_level,
            'xp_remaining': remaining
        }

    def modify_hp(self, name: str, amount: int) -> Dict[str, Any]:
        """
        Modify character HP (positive = heal, negative = damage)
        Returns dict with HP status info
        """
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False}

        hp = char.get('hp', {})
        current_hp = hp.get('current', 0)
        max_hp = hp.get('max', 0)

        # Apply change and clamp between 0 and max
        new_hp = max(0, min(current_hp + amount, max_hp))
        char['hp']['current'] = new_hp

        # Track the dying gate. 0 HP -> dying (unless already dead). Healing off
        # 0 -> alive. A 'dead' status is sticky (only kill_character sets it; only
        # an explicit revive would clear it), so it is never silently overwritten.
        if char.get('status') != 'dead':
            if new_hp == 0:
                char['status'] = 'dying'
            elif new_hp > 0 and char.get('status') == 'dying':
                char['status'] = 'alive'

        # Save character
        if not self._save_character(name, char):
            return {'success': False}

        char_name = char.get('name', name)

        # Determine status
        if amount < 0:
            print(f"DAMAGE {char_name} took {abs(amount)} damage!")
        else:
            print(f"HEAL {char_name} healed {amount} HP!")

        print(f"HP: {new_hp}/{max_hp}")

        if new_hp == 0:
            print("STATUS: UNCONSCIOUS")
        elif new_hp <= max_hp // 4:
            print("STATUS: BLOODIED")

        return {
            'success': True,
            'name': char_name,
            'hp_change': amount,
            'current_hp': new_hp,
            'max_hp': max_hp,
            'unconscious': new_hp == 0,
            'bloodied': 0 < new_hp <= max_hp // 4,
            'status': char.get('status', 'alive'),
        }

    def kill_character(self, name: str, cause: Optional[str] = None) -> Dict[str, Any]:
        """Mark a character as dead: HP 0, status 'dead', stamp died_at + cause.

        Persists the death state. The Death Protocol (CLAUDE.md) handles the
        hand-off; this just records the fact on the sheet.
        """
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False}

        char_name = char.get('name', name)
        hp = char.get('hp', {})
        max_hp = hp.get('max', 0)
        char.setdefault('hp', {})
        char['hp']['current'] = 0
        char['status'] = 'dead'
        char['died_at'] = self.get_timestamp()
        if cause:
            char['cause'] = cause

        if not self._save_character(name, char):
            return {'success': False}

        print(f"DEATH {char_name} has died.")
        if cause:
            print(f"Cause: {cause}")
        print(f"HP: 0/{max_hp}")
        print("STATUS: DEAD")

        return {
            'success': True,
            'name': char_name,
            'status': 'dead',
            'died_at': char['died_at'],
            'cause': cause,
        }

    def become(self, npc_name: str) -> Dict[str, Any]:
        """Hand off the active PC to a party member (Death Protocol SWAP).

        Reads the named party member's character_sheet from npcs.json, flattens it
        into the canonical character.json runtime shape, archives the current
        character.json to fallen/<deadname>-<id>.json, writes the new sheet,
        updates current_character on the campaign overview, and removes the
        promoted NPC from the party list so they aren't double-tracked.
        """
        # Locate the party member sheet in npcs.json.
        npcs = self.json_ops.load_json("npcs.json") or {}
        npc = npcs.get(npc_name)
        if npc is None:
            # Alias-aware fallback (case/title drift).
            from entity_aliases import resolve_entity_name
            key = resolve_entity_name(npc_name, npcs)
            if key:
                npc_name = key
                npc = npcs[key]
        if npc is None:
            print(f"[ERROR] NPC '{npc_name}' not found")
            return {'success': False}
        if not npc.get('is_party_member'):
            print(f"[ERROR] '{npc_name}' is not a party member. Promote them first "
                  f"(gm-npc.sh promote \"{npc_name}\").")
            return {'success': False}

        sheet = npc.get('character_sheet')
        if not sheet:
            print(f"[ERROR] '{npc_name}' has no character sheet to take over.")
            return {'success': False}

        # Build the new flat PC sheet from the party member's sheet.
        new_char = to_flat(dict(sheet))
        new_char['name'] = npc_name
        new_char.setdefault('status', 'alive')
        # A new PC is taking the helm; clear any stale death stamps.
        new_char.pop('died_at', None)
        new_char.pop('cause', None)

        # Archive the fallen PC (if a character.json exists) before overwriting.
        archived_path = None
        if self.character_file.exists():
            old = self._load_character()
            fallen_dir = self.campaign_dir / "fallen"
            fallen_dir.mkdir(parents=True, exist_ok=True)
            dead_name = (old.get('name') if old else None) or 'fallen-hero'
            dead_id = (old.get('id') if old else None) or self._name_to_id(dead_name)
            archived_path = fallen_dir / f"{self._name_to_id(dead_name)}-{dead_id}.json"
            with open(archived_path, 'w', encoding='utf-8') as f:
                json.dump(old or {}, f, indent=2)

        # Write the new character.json.
        if not self.json_ops.save_json("character.json", new_char):
            return {'success': False}

        # Update current_character on the campaign overview.
        self.json_ops.update_json(self.campaign_file, {'current_character': npc_name})

        # Remove the promoted NPC from the party so they aren't double-tracked.
        npcs = self.json_ops.load_json("npcs.json") or {}
        if npc_name in npcs:
            npcs[npc_name]['is_party_member'] = False
            npcs[npc_name]['became_pc'] = True
            self.json_ops.save_json("npcs.json", npcs)

        print(f"BECOME You now play as {npc_name}.")
        if archived_path is not None:
            print(f"Archived the fallen hero to: {archived_path}")
        hp = new_char.get('hp', {})
        print(f"HP: {hp.get('current', 0)}/{hp.get('max', 0)} | "
              f"Level {new_char.get('level', 1)} {new_char.get('race', '?')} "
              f"{new_char.get('class', '?')}")

        return {
            'success': True,
            'name': npc_name,
            'archived': str(archived_path) if archived_path else None,
        }

    def modify_gold(self, name: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Modify character gold or show current gold if no amount given
        Returns dict with gold status info
        """
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False}

        char_name = char.get('name', name)

        # Get current gold, handling migration from equipment string
        current_gold = char.get('gold', 0)
        if not isinstance(current_gold, (int, float)):
            current_gold = 0

        # If no amount specified, just show current gold
        if amount is None:
            print(f"{char_name}: {current_gold} gold")
            return {
                'success': True,
                'name': char_name,
                'gold': current_gold
            }

        # Apply change
        new_gold = current_gold + amount
        if new_gold < 0:
            print(f"[WARNING] {char_name} only has {current_gold} gold (tried to spend {abs(amount)}). Set to 0.")
            new_gold = 0
        char['gold'] = new_gold

        # Save character
        if not self._save_character(name, char):
            return {'success': False}

        # Report change
        if amount > 0:
            print(f"GOLD_GAINED {char_name} gained {amount} gold!")
        elif amount < 0:
            print(f"GOLD_SPENT {char_name} spent {abs(amount)} gold!")
        else:
            print(f"{char_name} gold unchanged.")

        print(f"Gold: {new_gold}")

        return {
            'success': True,
            'name': char_name,
            'gold_change': amount,
            'current_gold': new_gold
        }

    def modify_inventory(self, name: str, action: str, item: Optional[str] = None) -> Dict[str, Any]:
        """
        Add, remove, or list inventory items
        action: 'add', 'remove', or 'list'
        Returns dict with inventory status
        """
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False}

        char_name = char.get('name', name)
        equipment = char.get('equipment', [])

        if action == 'list':
            print(f"{char_name}'s Inventory:")
            if equipment:
                for i, eq in enumerate(equipment, 1):
                    print(f"  {i}. {eq}")
            else:
                print("  (empty)")
            return {
                'success': True,
                'name': char_name,
                'equipment': equipment
            }

        if not item:
            print(f"[ERROR] Item name required for {action}")
            return {'success': False}

        if action == 'add':
            equipment.append(item)
            char['equipment'] = equipment
            if not self._save_character(name, char):
                return {'success': False}
            print(f"ITEM_ADDED {char_name} gained: {item}")
            return {
                'success': True,
                'name': char_name,
                'action': 'add',
                'item': item,
                'equipment': equipment
            }

        elif action == 'remove':
            # Find item (case-insensitive partial match)
            found_idx = None
            for idx, eq in enumerate(equipment):
                if item.lower() in eq.lower():
                    found_idx = idx
                    break

            if found_idx is None:
                print(f"[ERROR] Item '{item}' not found in inventory")
                return {'success': False, 'error': 'item_not_found'}

            removed_item = equipment.pop(found_idx)
            char['equipment'] = equipment
            if not self._save_character(name, char):
                return {'success': False}
            print(f"ITEM_REMOVED {char_name} lost: {removed_item}")
            return {
                'success': True,
                'name': char_name,
                'action': 'remove',
                'item': removed_item,
                'equipment': equipment
            }

        else:
            print(f"[ERROR] Unknown inventory action: {action}")
            return {'success': False}

    def apply_loot(self, name: str, items: List[str], gold: int = 0) -> Dict[str, Any]:
        """
        Apply multiple loot items and gold in a single operation.
        Loads character once, adds all items + gold, saves once.
        Returns dict with loot summary.
        """
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False}

        char_name = char.get('name', name)
        equipment = char.get('equipment', [])
        current_gold = char.get('gold', 0)
        if not isinstance(current_gold, (int, float)):
            current_gold = 0

        # Add items
        for item in items:
            equipment.append(item)
        char['equipment'] = equipment

        # Add gold
        if gold:
            char['gold'] = current_gold + gold

        # Save once
        if not self._save_character(name, char):
            return {'success': False}

        # Print loot summary
        print(f"LOOT {char_name} received:")
        if gold > 0:
            print(f"  + {gold} gold")
        for item in items:
            print(f"  + {item}")
        print(f"Gold: {current_gold} -> {char.get('gold', current_gold)}")

        return {
            'success': True,
            'name': char_name,
            'items_added': items,
            'gold_added': gold,
            'total_gold': char.get('gold', current_gold),
            'equipment': char['equipment']
        }

    def modify_condition(self, name: str, action: str, condition: Optional[str] = None) -> Dict[str, Any]:
        """
        Add, remove, or list conditions on a character
        action: 'add', 'remove', or 'list'
        """
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False}

        char_name = char.get('name', name)

        # Auto-init conditions list if missing
        if 'conditions' not in char:
            char['conditions'] = []

        conditions = char['conditions']

        if action == 'list':
            print(f"{char_name}'s Conditions:")
            if conditions:
                for c in conditions:
                    print(f"  - {c}")
            else:
                print("  (none)")
            return {'success': True, 'name': char_name, 'conditions': conditions}

        if not condition:
            print(f"[ERROR] Condition name required for {action}")
            return {'success': False}

        if action == 'add':
            # Case-insensitive dedup
            if condition.lower() not in [c.lower() for c in conditions]:
                conditions.append(condition)
                char['conditions'] = conditions
                if not self._save_character(name, char):
                    return {'success': False}
                print(f"CONDITION_ADDED {char_name}: {condition}")
            else:
                print(f"{char_name} already has condition: {condition}")
            return {'success': True, 'name': char_name, 'conditions': conditions}

        elif action == 'remove':
            # Case-insensitive match
            found_idx = None
            for idx, c in enumerate(conditions):
                if c.lower() == condition.lower():
                    found_idx = idx
                    break
            if found_idx is None:
                print(f"[ERROR] Condition '{condition}' not found on {char_name}")
                return {'success': False}
            removed = conditions.pop(found_idx)
            char['conditions'] = conditions
            if not self._save_character(name, char):
                return {'success': False}
            print(f"CONDITION_REMOVED {char_name}: {removed}")
            return {'success': True, 'name': char_name, 'conditions': conditions}

        else:
            print(f"[ERROR] Unknown condition action: {action}")
            return {'success': False}


def main():
    """CLI interface for player management"""
    import argparse

    parser = argparse.ArgumentParser(description='Player character management')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Show player(s)
    show_parser = subparsers.add_parser('show', help='Show player(s)')
    show_parser.add_argument('name', nargs='?', help='Character name (optional, shows all if omitted)')

    # List players
    subparsers.add_parser('list', help='List all player IDs')

    # Set current player
    set_parser = subparsers.add_parser('set', help='Set current active character')
    set_parser.add_argument('name', help='Character name')

    # Award XP
    xp_parser = subparsers.add_parser('xp', help='Award XP to character')
    xp_parser.add_argument('name', help='Character name')
    xp_parser.add_argument('amount', help='XP amount (can include + prefix)')

    # Discretionary "spectacle" XP (kit-aware, level-scaled; co-awards followers)
    award_parser = subparsers.add_parser('award', help='Award level-scaled spectacle XP for a clever/effective/unique/punishing beat')
    award_parser.add_argument('name', nargs='?', help='Character name (optional; defaults to active PC)')
    award_parser.add_argument('--tier', required=True, choices=['minor', 'major', 'legendary'], help='Reward tier')
    award_parser.add_argument('--reason', help='Why the beat earned it (logged)')

    # Check level status
    level_parser = subparsers.add_parser('level-check', help='Check XP and level status')
    level_parser.add_argument('name', help='Character name')

    # Modify HP
    hp_parser = subparsers.add_parser('hp', help='Modify character HP')
    hp_parser.add_argument('name', help='Character name')
    hp_parser.add_argument('amount', help='HP change (+5 to heal, -3 for damage)')

    # Kill character (death state)
    kill_parser = subparsers.add_parser('kill', help='Mark character dead (status + HP 0 + cause)')
    kill_parser.add_argument('name', help='Character name')
    kill_parser.add_argument('--cause', help='How they died')

    # Become a party member (Death Protocol hand-off)
    become_parser = subparsers.add_parser('become', help='Take over a party member as the active PC')
    become_parser.add_argument('name', help='Party member NPC name')

    # Get full character JSON
    get_parser = subparsers.add_parser('get', help='Get full character JSON')
    get_parser.add_argument('name', help='Character name')

    # Visual appearance (canonical look for consistent image generation)
    import visual_appearance as va_mod
    appearance_parser = subparsers.add_parser('appearance', help='Get the PC visual_appearance')
    appearance_parser.add_argument('name', nargs='?', help='Character name (optional)')
    setappear_parser = subparsers.add_parser('set-appearance', help='Set PC visual_appearance fields')
    setappear_parser.add_argument('name', nargs='?', help='Character name (optional)')
    for _f in va_mod.VISUAL_FIELDS:
        setappear_parser.add_argument(f'--{_f}')

    # Modify gold
    gold_parser = subparsers.add_parser('gold', help='Modify or show character gold')
    gold_parser.add_argument('name', help='Character name')
    gold_parser.add_argument('amount', nargs='?', help='Gold change (+50 to gain, -10 to spend). Omit to show current.')

    # Manage inventory
    inv_parser = subparsers.add_parser('inventory', help='Manage character inventory')
    inv_parser.add_argument('name', nargs='?', help='Character name (optional; defaults to active PC)')
    inv_parser.add_argument('inv_action', nargs='?', help='Action: add/remove/list (default: list)')
    inv_parser.add_argument('item', nargs='?', help='Item name (required for add/remove)')

    # Batch loot
    loot_parser = subparsers.add_parser('loot', help='Apply multiple items + gold at once')
    loot_parser.add_argument('name', help='Character name')
    loot_parser.add_argument('--gold', type=int, default=0, help='Gold to add')
    loot_parser.add_argument('--items', nargs='+', default=[], help='Items to add')

    # Manage conditions
    cond_parser = subparsers.add_parser('condition', help='Manage character conditions')
    cond_parser.add_argument('name', help='Character name')
    cond_parser.add_argument('cond_action', choices=['add', 'remove', 'list'], help='Action to perform')
    cond_parser.add_argument('condition', nargs='?', help='Condition name (required for add/remove)')

    from cli_output import wants_json, strip_json_flag, emit, emit_error
    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = PlayerManager()

    if json_mode and args.action in ('get', 'show'):
        # `show --json` emits the full active (or named) character record.
        char = manager.get_player(args.name) if args.action == 'get' else manager._load_character(args.name)
        if char:
            emit(char, json_mode=True)
        else:
            sys.exit(emit_error("player not found", json_mode=True))
        return
    if json_mode and args.action == 'hp':
        import contextlib
        import io
        try:
            amount = int(args.amount.lstrip('+'))
        except ValueError:
            sys.exit(emit_error(f"invalid HP amount: {args.amount}", json_mode=True))
        with contextlib.redirect_stdout(io.StringIO()):
            result = manager.modify_hp(args.name, amount)
        if result.get('success'):
            emit(result, json_mode=True)
        else:
            sys.exit(emit_error(result.get('error', 'hp update failed'), json_mode=True))
        return
    if json_mode and args.action in ('kill', 'become'):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            if args.action == 'kill':
                result = manager.kill_character(args.name, getattr(args, 'cause', None))
            else:
                result = manager.become(args.name)
        if result.get('success'):
            emit(result, json_mode=True)
        else:
            sys.exit(emit_error(result.get('error', f'{args.action} failed'), json_mode=True))
        return

    if json_mode and args.action == 'award':
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            result = manager.award_spectacle(args.name, args.tier, getattr(args, 'reason', None))
        if result.get('success'):
            emit(result, json_mode=True)
        else:
            sys.exit(emit_error(result.get('error', 'award failed'), json_mode=True))
        return

    if args.action == 'show':
        if args.name:
            result = manager.show_player(args.name)
            if result:
                print(result)
            else:
                sys.exit(1)
        else:
            summaries = manager.show_all_players()
            for s in summaries:
                print(s)

    elif args.action == 'list':
        players = manager.list_players()
        for p in players:
            print(p)

    elif args.action == 'set':
        if not manager.set_current_player(args.name):
            sys.exit(1)

    elif args.action == 'xp':
        # Parse amount (handle +150 format)
        amount_str = args.amount.replace('+', '')
        try:
            amount = int(amount_str)
        except ValueError:
            print(f"[ERROR] Invalid XP amount: {args.amount}")
            sys.exit(1)

        result = manager.award_xp(args.name, amount)
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'award':
        result = manager.award_spectacle(args.name, args.tier, getattr(args, 'reason', None))
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'level-check':
        if not manager.get_xp_status(args.name):
            sys.exit(1)

    elif args.action == 'hp':
        # Parse amount (handle +5 or -3 format)
        amount_str = args.amount
        try:
            if amount_str.startswith('+'):
                amount = int(amount_str[1:])
            else:
                amount = int(amount_str)
        except ValueError:
            print(f"[ERROR] Invalid HP amount: {args.amount}")
            sys.exit(1)

        result = manager.modify_hp(args.name, amount)
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'kill':
        result = manager.kill_character(args.name, getattr(args, 'cause', None))
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'become':
        result = manager.become(args.name)
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'get':
        char = manager.get_player(args.name)
        if char:
            print(json.dumps(char, indent=2))
        else:
            sys.exit(1)

    elif args.action == 'appearance':
        va = manager.get_visual_appearance(args.name)
        if va is None:
            sys.exit(emit_error("no active character", json_mode=json_mode) if json_mode else 1)
        if json_mode:
            emit(va, json_mode=True)
        else:
            char = manager._load_character(args.name)
            line = va_mod.format_line((char or {}).get('name', 'The hero'), va)
            print(line if line else "(no visual_appearance set yet)")

    elif args.action == 'set-appearance':
        fields = {f: getattr(args, f) for f in va_mod.VISUAL_FIELDS}
        if not manager.set_visual_appearance(args.name, **fields):
            sys.exit(1)
        print("[SUCCESS] Updated visual_appearance for the active character")

    elif args.action == 'gold':
        # Parse amount if provided
        amount = None
        if args.amount:
            amount_str = args.amount
            try:
                if amount_str.startswith('+'):
                    amount = int(amount_str[1:])
                else:
                    amount = int(amount_str)
            except ValueError:
                print(f"[ERROR] Invalid gold amount: {args.amount}")
                sys.exit(1)

        result = manager.modify_gold(args.name, amount)
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'inventory':
        # Allow `inventory [name] [action] [item]` with name optional. When the
        # first positional is an action keyword, it lands in `name`; shift it so
        # it's treated as the action against the active PC.
        actions = ('add', 'remove', 'list')
        name, inv_action, item = args.name, args.inv_action, args.item
        if name in actions:
            name, inv_action, item = None, name, inv_action
        if inv_action is None:
            inv_action = 'list'
        if inv_action not in actions:
            print(f"[ERROR] Unknown inventory action: {inv_action} (choose from add, remove, list)")
            sys.exit(1)
        result = manager.modify_inventory(name, inv_action, item)
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'loot':
        if not args.items and args.gold == 0:
            print("[ERROR] Provide --items and/or --gold")
            sys.exit(1)
        result = manager.apply_loot(args.name, args.items, args.gold)
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'condition':
        result = manager.modify_condition(args.name, args.cond_action, args.condition)
        if not result.get('success'):
            sys.exit(1)


if __name__ == "__main__":
    main()
