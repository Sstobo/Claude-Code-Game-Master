#!/usr/bin/env python3
"""
Player character management module for DM tools
Handles PC operations: XP, HP, level progression, and character data
"""

import sys
import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager


class PlayerManager(EntityManager):
    """Manage player character operations. Inherits from EntityManager for common functionality."""

    # D&D 5e XP thresholds for levels 1-20
    XP_THRESHOLDS = [
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

    def __init__(self, world_state_dir: Optional[str] = None, require_active_campaign: bool = True):
        super().__init__(world_state_dir, require_active_campaign)

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

    def _load_character(self, name: Optional[str] = None) -> Optional[Dict]:
        """
        Load character data from file
        In single-character mode, name is optional/ignored
        """
        # New format: single character.json
        if self._is_using_single_character():
            try:
                with open(self.character_file, 'r', encoding='utf-8') as f:
                    char = json.load(f)
                return self._normalize_hp(char)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[ERROR] Failed to load character: {e}")
                return None

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
                char = json.load(f)
            return self._normalize_hp(char)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Failed to load character: {e}")
            return None

    def _save_character(self, name: str, data: Dict) -> bool:
        """Save character data to file using atomic writes via json_ops"""
        # New format: single character.json
        if self._is_using_single_character():
            return self.json_ops.save_json("character.json", data)

        # Legacy format: characters/<name>.json
        char_path = self._get_character_path(name)
        char_path.parent.mkdir(parents=True, exist_ok=True)
        return self.json_ops.save_json(str(char_path), data)

    def _normalize_hp(self, char: Dict) -> Dict:
        """Normalize HP to object format {current, max}"""
        hp = char.get('hp', 0)
        if isinstance(hp, int):
            max_hp = char.get('max_hp', hp)
            char['hp'] = {'current': hp, 'max': max_hp}
        elif not isinstance(hp, dict):
            char['hp'] = {'current': 0, 'max': 0}
        return char

    def _normalize_xp(self, char: Dict) -> Dict:
        """Normalize XP to object format {current, next_level}"""
        xp = char.get('xp', 0)
        level = char.get('level', 1)

        if isinstance(xp, int):
            # Old format: plain integer
            next_threshold = self.XP_THRESHOLDS[level] if level < 20 else xp
            char['xp'] = {'current': xp, 'next_level': next_threshold}
        elif not isinstance(xp, dict):
            # Invalid format, reset
            char['xp'] = {'current': 0, 'next_level': self.XP_THRESHOLDS[1]}

        return char

    def _get_active_character_name(self) -> Optional[str]:
        """Get active character name from campaign overview"""
        campaign = self.json_ops.load_json(self.campaign_file)
        return campaign.get('current_character')

    def get_player(self, name: Optional[str] = None) -> Optional[Dict]:
        """
        Get full player character data
        If name is None, uses active character from campaign
        """
        if name is None:
            name = self._get_active_character_name()
            if not name:
                print(f"[ERROR] No active character in campaign")
                return None

        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return None
        return char

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

        # Check for level up
        new_level = current_level
        while new_level < 20 and current_xp >= self.XP_THRESHOLDS[new_level]:
            new_level += 1

        leveled_up = new_level > current_level
        if leveled_up:
            char['level'] = new_level

        # Update next level threshold
        next_threshold = self.XP_THRESHOLDS[new_level] if new_level < 20 else current_xp
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

    def modify_hp(self, name: Optional[str] = None, amount: int = 0) -> Dict[str, Any]:
        """
        Modify character HP (positive = heal, negative = damage)
        If name is None, uses active character
        Returns dict with HP status info
        """
        if name is None:
            name = self._get_active_character_name()
            if not name:
                print(f"[ERROR] No active character in campaign")
                return {'success': False}

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
            'bloodied': 0 < new_hp <= max_hp // 4
        }

    def modify_gold(self, name: Optional[str] = None, amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Modify character gold or show current gold if no amount given
        If name is None, uses active character
        Returns dict with gold status info
        """
        if name is None:
            name = self._get_active_character_name()
            if not name:
                print(f"[ERROR] No active character in campaign")
                return {'success': False}

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

    # Check level status
    level_parser = subparsers.add_parser('level-check', help='Check XP and level status')
    level_parser.add_argument('name', help='Character name')

    # Modify HP
    hp_parser = subparsers.add_parser('hp', help='Modify character HP')
    hp_parser.add_argument('name', nargs='?', default=None, help='Character name (optional, uses active)')
    hp_parser.add_argument('amount', help='HP change (+5 to heal, -3 for damage)')

    # Get full character JSON
    get_parser = subparsers.add_parser('get', help='Get full character JSON')
    get_parser.add_argument('name', help='Character name')

    # Modify gold
    gold_parser = subparsers.add_parser('gold', help='Modify or show character gold')
    gold_parser.add_argument('name', help='Character name')
    gold_parser.add_argument('amount', nargs='?', help='Gold change (+50 to gain, -10 to spend). Omit to show current.')

    # Manage inventory
    inv_parser = subparsers.add_parser('inventory', help='Manage character inventory')
    inv_parser.add_argument('name', help='Character name')
    inv_parser.add_argument('inv_action', choices=['add', 'remove', 'list'], help='Action to perform')
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

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = PlayerManager()

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

    elif args.action == 'level-check':
        if not manager.get_xp_status(args.name):
            sys.exit(1)

    elif args.action == 'hp':
        # Auto-detect: if name looks like an amount, shift args
        name = args.name
        amount_str = args.amount
        if name is not None and re.match(r'^[+-]\d+$', name):
            amount_str = name
            name = None

        try:
            if amount_str.startswith('+'):
                amount = int(amount_str[1:])
            else:
                amount = int(amount_str)
        except ValueError:
            print(f"[ERROR] Invalid HP amount: {amount_str}")
            sys.exit(1)

        result = manager.modify_hp(name, amount)
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'get':
        char = manager.get_player(args.name)
        if char:
            print(json.dumps(char, indent=2, ensure_ascii=False))
        else:
            sys.exit(1)

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
        result = manager.modify_inventory(args.name, args.inv_action, args.item)
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
