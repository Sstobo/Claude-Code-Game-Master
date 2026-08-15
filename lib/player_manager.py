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

        # Base dir the kit is loaded from (self.world_state_dir below is a legacy
        # alias for the CAMPAIGN dir, so the real base has to be kept separately).
        self._kit_base = world_state_dir
        self._kit = None

        # Additional paths specific to player management
        self.world_state_dir = self.campaign_dir  # Alias for compatibility
        self.campaign_file = "campaign-overview.json"

        # Single character file per campaign
        self.character_file = self.campaign_dir / "character.json"

    def _name_to_id(self, name: str) -> str:
        """Convert character name to file ID"""
        return name.lower().replace(' ', '-')

    def _load_character(self, name: str = None) -> Optional[Dict]:
        """Load the active PC from character.json (name is ignored)."""
        if not self.character_file.exists():
            return None
        try:
            with open(self.character_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Failed to load character: {e}")
            return None
        return self._normalize_loaded(raw, "character.json")

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
        return self.json_ops.save_json("character.json", data)

    def world_kit(self):
        """The active campaign's World Kit (cached). The single source of truth for
        vitals and the progression model, so a ruleset-less campaign gets the kit's
        own defaults instead of a second, disagreeing fallback here."""
        if self._kit is None:
            from world_kit import WorldKit
            self._kit = WorldKit(self._kit_base)
        return self._kit

    def _xp_thresholds(self):
        """Level thresholds from the active World Kit (xp-levels model), else the
        default table. Index L = XP required to reach level L+1; index 0 == 0.

        This is how leveling delegates to the kit instead of a hardcoded 5e path.
        Asked of the kit's built progression object rather than re-parsed from
        ruleset.json, so every ruleset syntax the kit accepts (including the bare
        string form and the 'level' alias) is understood here too.
        """
        progression = self.world_kit().progression
        thresholds = getattr(progression, 'thresholds', None)
        if progression.name == "xp-levels" and thresholds:
            return [0] + list(thresholds)
        return self.DEFAULT_XP_THRESHOLDS

    def _max_level(self) -> int:
        """Top level this kit's threshold table describes (5e's 20 is just the
        default table's length, not a law of the engine)."""
        return len(self._xp_thresholds())

    def _xp_view(self, char: Dict) -> Dict[str, int]:
        """{current, next_level} READ off the sheet without writing anything.

        Both stored shapes are honored (legacy plain int, canonical object). Nothing
        is created: a milestone or resource-axis sheet that has never tracked XP
        must not grow a phantom xp object just because something read it.
        """
        thresholds = self._xp_thresholds()
        level = char.get('level', 1)
        raw = char.get('xp', 0)

        if isinstance(raw, dict):
            current = int(raw.get('current', 0) or 0)
            next_level = raw.get('next_level')
        elif isinstance(raw, (int, float)):
            current, next_level = int(raw), None
        else:
            current, next_level = 0, None

        if next_level is None:
            next_level = thresholds[level] if level < len(thresholds) else current
        return {'current': current, 'next_level': int(next_level)}

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
        """List the active PC's ID (single-character campaigns)."""
        char = self._load_character()
        if not char:
            return []
        return [char.get('name', 'character').lower().replace(' ', '-')]

    def show_player(self, name: str) -> Optional[str]:
        """Get formatted player summary"""
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return None

        hp = char.get('hp', {})
        gold = char.get('gold', 0)
        summary = f"{char.get('name', name)} - {char.get('race', '?')} {char.get('class', '?')} Level {char.get('level', 1)} (HP: {hp.get('current', 0)}/{hp.get('max', 0)}, Gold: {gold})"
        summary += self._vitals_summary(char)
        status = char.get('status')
        if status in ('dying', 'dead'):
            summary += f" | {status.upper()}"
        conditions = char.get('conditions', [])
        if conditions:
            summary += f" | Conditions: {', '.join(conditions)}"
        return summary

    def show_all_players(self) -> List[str]:
        """Summary line for the active PC (single-character campaigns)."""
        char = self._load_character()
        if not char:
            return []
        hp = char.get('hp', {})
        gold = char.get('gold', 0)
        return [
            f"{char.get('name', 'Unknown')} - {char.get('race', '?')} {char.get('class', '?')} Level {char.get('level', 1)} (HP: {hp.get('current', 0)}/{hp.get('max', 0)}, Gold: {gold})"
            + self._vitals_summary(char)
        ]

    def set_current_player(self, name: str) -> bool:
        """Set character as current active PC in campaign.

        Re-seed the opening when it has never been matched to a PC
        (``opening_matched_to_pc`` absent/false). Provisional ``seed_opening``
        does not set that flag; ``reseed_opening`` does. Covers the
        ``save-json`` path, where ``current_character`` may already be filled.
        Later ``set`` / ``become`` calls leave a PC-matched opening alone.
        ``onboard`` always re-seeds on its own (the real first-PC path).
        """
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return False

        # Get actual name from character file
        actual_name = char.get('name', name)

        campaign = self.json_ops.load_json(self.campaign_file) or {}
        unmatched = not campaign.get('opening_matched_to_pc')

        if self.json_ops.update_json(self.campaign_file, {'current_character': actual_name}):
            print(f"[SUCCESS] Set current character to: {actual_name}")
            if unmatched:
                from opening_seed import reseed_opening
                reseed_opening(str(self.campaign_dir), char)
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

        current_xp = self._xp_view(char)['current'] + amount
        current_level = char.get('level', 1)

        # Check for level up — bound by the active kit's thresholds, not a hardcoded 20.
        thresholds = self._xp_thresholds()
        max_level = self._max_level()
        new_level = current_level
        while new_level < len(thresholds) and current_xp >= thresholds[new_level]:
            new_level += 1

        leveled_up = new_level > current_level
        if leveled_up:
            char['level'] = new_level

        # Write the canonical XP object (kit-driven next threshold). An explicit XP
        # award is the ONLY thing that puts one on a sheet.
        next_threshold = thresholds[new_level] if new_level < len(thresholds) else current_xp
        char['xp'] = {'current': current_xp, 'next_level': next_threshold}

        # Save character
        if not self._save_character(name, char):
            return {'success': False}

        result = {
            'success': True,
            'name': char.get('name', name),
            'xp_gained': amount,
            'current_xp': current_xp,
            'next_level_xp': next_threshold if new_level < max_level else 'MAX',
            'level_up': leveled_up,
            'old_level': current_level,
            'new_level': new_level
        }

        # Print result
        if leveled_up:
            print(f"LEVEL_UP {char.get('name', name)} gained {amount} XP and leveled up to Level {new_level}!")
            print(f"XP: {current_xp}/{next_threshold if new_level < max_level else 'MAX'}")
        else:
            print(f"XP_GAIN {char.get('name', name)} gained {amount} XP!")
            print(f"XP: {current_xp}/{next_threshold if new_level < max_level else 'MAX'}")

        return result

    def _spectacle_config(self) -> Dict[str, Any]:
        """Spectacle tier table + optional follower currency from the active kit.
        Tiers default to game_core.DEFAULT_SPECTACLE_TIERS; a kit overrides them
        (and declares a follower currency) via ruleset.json -> progression.spectacle."""
        import game_core
        ruleset = self.json_ops.load_json("ruleset.json") or {}
        prog = ruleset.get("progression", {}) or {}
        spec = (prog.get("spectacle") or {}) if isinstance(prog, dict) else {}
        return {
            # The EFFECTIVE model (what make_progression built), so a typo'd model
            # name degrades to milestone here exactly as it does in the core.
            'model': self.world_kit().progression.name,
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

        # XP gap to next level (drives XP scaling; read-only — a milestone or
        # resource-axis sheet must not gain an xp object from a spectacle beat).
        xp = self._xp_view(char)
        xp_to_next = max(0, xp['next_level'] - xp['current'])

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

        # Read-only view of XP — a status check never writes, and never invents an
        # xp object on a sheet that does not track one.
        xp = self._xp_view(char)
        current_xp = xp['current']
        current_level = char.get('level', 1)
        next_level_xp = xp['next_level']

        # Check if ready to level up (top level comes from the kit's table)
        ready_to_level = current_xp >= next_level_xp and current_level < self._max_level()
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

        # A corpse does not take damage and does not heal. kill_character sets HP
        # itself and never routes through here, so the guard cannot block a death.
        if char.get('status') == 'dead':
            char_name = char.get('name', name)
            print(f"[ERROR] {char_name} is dead — HP is frozen at "
                  f"{current_hp}/{max_hp}. Run the Death Protocol (become a "
                  f"party member / new character) to continue play, or "
                  f"`gm-player.sh revive` if the story brings them back.")
            return {
                'success': False,
                'name': char_name,
                'hp_change': 0,
                'current_hp': current_hp,
                'max_hp': max_hp,
                'status': 'dead',
                'error': 'character is dead',
            }

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

    def _kit_vitals(self) -> List[str]:
        """Vital tracks the active World Kit declares — 'hp' plus whatever else the
        world runs on (vigor, corruption, water, heat).

        Asked of the kit rather than re-read off ruleset.json here, so a campaign
        with no ruleset gets the kit's own default (['hp']) instead of an empty list
        that would refuse a plain HP change.
        """
        return self.world_kit().vitals()

    @staticmethod
    def _read_vital(char: Dict, vital: str):
        """(current, max) for a vital. max is None for plain-number tracks, and an
        undeclared-but-untracked vital reads as 0 rather than erroring."""
        raw = char.get(vital)
        if isinstance(raw, dict):
            return raw.get('current', 0), raw.get('max')
        if isinstance(raw, (int, float)):
            return raw, None
        return 0, None

    def _vitals_summary(self, char: Dict) -> str:
        """' | Vigor: 3/5 | Corruption: 2' for the kit vitals present on the sheet."""
        parts = []
        for vital in self._kit_vitals():
            if vital == 'hp' or vital not in char:
                continue
            current, maximum = self._read_vital(char, vital)
            value = f"{current}/{maximum}" if maximum is not None else f"{current}"
            parts.append(f"{vital.capitalize()}: {value}")
        return f" | {' | '.join(parts)}" if parts else ""

    def modify_vital(self, name: str, vital: str, amount: Optional[int] = None,
                     set_value: Optional[int] = None) -> Dict[str, Any]:
        """Read or change any vital the active World Kit declares.

        `hp` keeps its dedicated path (dying gate, max clamp) — a vital call for it
        delegates to modify_hp. Other tracks keep whatever shape the sheet stores:
        a {current, max} dict stays a dict (and clamps to max), a plain number
        stays a plain number. A vital the kit never declared is refused.
        """
        declared = self._kit_vitals()
        if vital not in declared:
            print(f"[ERROR] '{vital}' is not a vital in this world. "
                  f"Declared: {', '.join(declared) if declared else '(none)'}")
            return {'success': False, 'error': f"unknown vital: {vital}"}

        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False}

        char_name = char.get('name', name)
        current, maximum = self._read_vital(char, vital)

        if amount is None and set_value is None:
            value = f"{current}/{maximum}" if maximum is not None else f"{current}"
            print(f"{char_name} - {vital}: {value}")
            return {'success': True, 'name': char_name, 'vital': vital,
                    'current': current, 'max': maximum}

        if vital == 'hp':
            delta = (set_value - current) if set_value is not None else amount
            result = self.modify_hp(char_name, delta)
            if result.get('success'):
                # One verb, one response shape: every vital result carries
                # vital/current/max, hp's own keys included.
                result.update({'vital': 'hp', 'previous': current,
                               'current': result['current_hp'], 'max': result['max_hp']})
            return result

        new_value = set_value if set_value is not None else current + amount
        new_value = max(0, new_value)
        if maximum is not None:
            new_value = min(new_value, maximum)

        if isinstance(char.get(vital), dict):
            char[vital]['current'] = new_value
        else:
            char[vital] = new_value

        if not self._save_character(char_name, char):
            return {'success': False}

        shown = f"{new_value}/{maximum}" if maximum is not None else f"{new_value}"
        print(f"VITAL {char_name} {vital}: {current} -> {new_value}")
        print(f"{vital.capitalize()}: {shown}")

        return {
            'success': True,
            'name': char_name,
            'vital': vital,
            'previous': current,
            'current': new_value,
            'max': maximum,
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
        # A death and a revival are mutually exclusive states, so the last one
        # wins: dying again clears the stamps a previous revive left behind.
        char.pop('revived_at', None)
        char.pop('revived_reason', None)

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

    def revive(self, name: Optional[str] = None, hp: Optional[int] = None,
               reason: Optional[str] = None) -> Dict[str, Any]:
        """Bring a dead character back: status 'alive', HP restored, death stamps cleared.

        The escape hatch for the stories that end a death differently — a
        resurrection, a healer's miracle, a death the fiction walks back. The
        corpse guard in modify_hp is what makes this an explicit verb rather than
        a heal: only this clears a 'dead' status.

        ``hp`` defaults to 1 (back on their feet, barely) and clamps to 1..max —
        a revive never lands a character alive at 0. ``reason`` is recorded on the
        sheet where the death's cause was, so the world remembers how they came
        back.
        """
        char = self._load_character(name)
        if not char:
            print(f"[ERROR] Character '{name}' not found")
            return {'success': False}

        char_name = char.get('name', name)
        # In single-character mode _load_character ignores the name and hands back
        # the sitting PC, so a revive aimed at a hero already archived to fallen/
        # would silently hit whoever holds character.json. Refuse instead.
        if name and str(char_name).strip().lower() != str(name).strip().lower():
            print(f"[ERROR] The active character is {char_name}, not '{name}'. "
                  f"Only the sitting PC can be revived — a hero archived to "
                  f"fallen/ has to be brought back with `gm-player.sh become` or "
                  f"a fresh sheet.")
            return {
                'success': False,
                'name': char_name,
                'error': f"active character is {char_name}, not '{name}'",
            }

        if char.get('status') != 'dead':
            print(f"[ERROR] {char_name} is not dead (status: "
                  f"{char.get('status', 'alive')}) — nothing to revive. Use "
                  f"`gm-player.sh hp` to heal them.")
            return {
                'success': False,
                'name': char_name,
                'status': char.get('status', 'alive'),
                'error': 'character is not dead',
            }

        max_hp = char.get('hp', {}).get('max', 0)
        new_hp = max(1, 1 if hp is None else hp)   # never alive at 0
        if max_hp:
            new_hp = min(new_hp, max_hp)
        char.setdefault('hp', {})
        char['hp']['current'] = new_hp
        char['status'] = 'alive'
        char.pop('died_at', None)
        char.pop('cause', None)
        char['revived_at'] = self.get_timestamp()
        if reason:
            char['revived_reason'] = reason

        if not self._save_character(name, char):
            return {'success': False}

        print(f"REVIVED {char_name} lives again.")
        if reason:
            print(f"How: {reason}")
        print(f"HP: {new_hp}/{max_hp}")
        print("STATUS: ALIVE")

        return {
            'success': True,
            'name': char_name,
            'status': 'alive',
            'current_hp': new_hp,
            'max_hp': max_hp,
            'revived_at': char['revived_at'],
            'reason': reason,
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


def _parse_vital_change(args):
    """(amount, set_value) for `vital <name> [<+/-N> | set N]`. Both None = read only.
    Raises ValueError on a malformed amount."""
    if args.amount is None:
        return None, None
    if args.amount.lower() == 'set':
        if args.value is None:
            raise ValueError("set requires a value")
        return None, int(args.value)
    return int(args.amount.lstrip('+')), None


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

    # Modify any vital the active World Kit declares (vigor, corruption, ...)
    vital_parser = subparsers.add_parser('vital', help="Read or change a kit vital on the active PC")
    vital_parser.add_argument('vital', help='Vital name as declared in ruleset.json stat_schema.vitals')
    vital_parser.add_argument('amount', nargs='?', help='+N / -N to adjust, or the literal "set"')
    vital_parser.add_argument('value', nargs='?', help='New value (only with "set")')

    # Kill character (death state)
    kill_parser = subparsers.add_parser('kill', help='Mark character dead (status + HP 0 + cause)')
    kill_parser.add_argument('name', help='Character name')
    kill_parser.add_argument('--cause', help='How they died')

    # Revive a dead character (the story brought them back)
    revive_parser = subparsers.add_parser('revive', help='Bring a dead character back (status alive + HP)')
    revive_parser.add_argument('name', help='Character name')
    revive_parser.add_argument('--hp', type=int, help='HP to restore to (default 1, clamped to max)')
    revive_parser.add_argument('--reason', help='How they came back (recorded on the sheet)')

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
    if json_mode and args.action == 'vital':
        import contextlib
        import io
        try:
            amount, set_value = _parse_vital_change(args)
        except ValueError:
            sys.exit(emit_error(f"invalid vital amount: {args.amount} {args.value or ''}".strip(),
                                json_mode=True))
        with contextlib.redirect_stdout(io.StringIO()):
            result = manager.modify_vital(None, args.vital, amount, set_value)
        if result.get('success'):
            emit(result, json_mode=True)
        else:
            sys.exit(emit_error(result.get('error', 'vital update failed'), json_mode=True))
        return
    if json_mode and args.action in ('kill', 'become', 'revive'):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            if args.action == 'kill':
                result = manager.kill_character(args.name, getattr(args, 'cause', None))
            elif args.action == 'revive':
                result = manager.revive(args.name, getattr(args, 'hp', None),
                                        getattr(args, 'reason', None))
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

    elif args.action == 'vital':
        try:
            amount, set_value = _parse_vital_change(args)
        except ValueError:
            print(f"[ERROR] Invalid vital amount: {args.amount} {args.value or ''}".rstrip())
            sys.exit(1)
        result = manager.modify_vital(None, args.vital, amount, set_value)
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'kill':
        result = manager.kill_character(args.name, getattr(args, 'cause', None))
        if not result.get('success'):
            sys.exit(1)

    elif args.action == 'revive':
        result = manager.revive(args.name, getattr(args, 'hp', None),
                                getattr(args, 'reason', None))
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
