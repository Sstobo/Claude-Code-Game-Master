#!/usr/bin/env python3
"""
Session management module for GM tools
Handles session lifecycle, party movement, and JSON-based saves
"""

import json
import os
import re
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager, npcs_present
from character_schema import to_flat
from schemas import PLOT_TYPE_SORT
from world_kit import WorldKit


class SessionManager(EntityManager):
    """Manage D&D session operations. Inherits from EntityManager for common functionality."""

    # Per-campaign play-style defaults. `action_menu` controls whether the GM ends
    # each beat with a few numbered choices (on) or an open prompt (off). Stored
    # under overview.preferences; surfaced in get_full_context so the GM honors it.
    # `player_rolls` hands dice to the player (GM pauses and prompts instead of
    # rolling); `beat_length` picks the pacing line. Same storage + surfacing.
    # `rag_inspiration` makes the GM pull source passages every beat or so for
    # grounded narration detail rather than improvising from memory.
    DEFAULT_PREFERENCES = {"action_menu": True, "player_rolls": False,
                           "beat_length": "adaptive", "rag_inspiration": True}

    SAVE_VERSION = 1
    AUTOSAVE_KEEP = 3

    # Live campaign files snapshotted when present. character.json is captured
    # via the `characters` helper (the PC sheet), not as a filename key.
    # combat_state.json is the on-disk combat file (not combats.json).
    SNAPSHOT_JSON_FILES = (
        "campaign-overview.json",
        "npcs.json",
        "locations.json",
        "facts.json",
        "plots.json",
        "items.json",
        "consequences.json",
        "ruleset.json",
        "world-bible.json",
        "threat-clocks.json",
        "campaign-memory.json",
        "chronicler.json",
        "world-tick-log.json",
        "combat_state.json",
    )
    SNAPSHOT_TEXT_FILES = (
        "rules.md",
        "session-log.md",
    )
    CONTRACT_FILES = SNAPSHOT_JSON_FILES + SNAPSHOT_TEXT_FILES + (
        "character.json",
        "fallen/*.json",
    )
    LEGACY_SNAPSHOT_KEYS = {
        "campaign_overview": "campaign-overview.json",
        "npcs": "npcs.json",
        "locations": "locations.json",
        "facts": "facts.json",
        "consequences": "consequences.json",
    }
    _AUTOSAVE_FILE = re.compile(r"^\d{8}-\d{6}-autosave(?:-\d+)?\.json$")

    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)

        # Additional paths specific to session management
        self._wsd = world_state_dir  # passed through to sibling managers (CampaignMemory)
        self.world_state_dir = self.campaign_dir  # Alias for compatibility
        self.saves_dir = self.campaign_dir / "saves"
        self.saves_dir.mkdir(parents=True, exist_ok=True)

        # Core files
        self.campaign_file = "campaign-overview.json"
        self.session_log = self.campaign_dir / "session-log.md"

        # Character file (single character per campaign)
        self.character_file = self.campaign_dir / "character.json"

    def get_timestamp(self) -> str:
        """Get formatted timestamp"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def get_iso_timestamp(self) -> str:
        """Get ISO format timestamp for filenames"""
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    # ==================== Play-Style Preferences ====================

    def get_preferences(self) -> Dict[str, Any]:
        """Return play-style preferences, defaults merged with any saved overrides."""
        campaign = self.json_ops.load_json(self.campaign_file) or {}
        prefs = dict(self.DEFAULT_PREFERENCES)
        saved = campaign.get("preferences")
        if isinstance(saved, dict):
            prefs.update(saved)
        return prefs

    def set_preference(self, key: str, value: Any) -> Dict[str, Any]:
        """Persist a single play-style preference; returns the full merged prefs."""
        campaign = self.json_ops.load_json(self.campaign_file) or {}
        prefs = campaign.get("preferences")
        if not isinstance(prefs, dict):
            prefs = {}
        prefs[key] = value
        campaign["preferences"] = prefs
        self.json_ops.save_json(self.campaign_file, campaign)
        return self.get_preferences()

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

    def end_session(self, summary: str, cliffhanger: str = None,
                    open_threads: list = None) -> bool:
        """
        End session with summary + structured footer, log to session-log.md.

        The footer (session number, ended_at, location, cliffhanger, open_threads)
        is both human-readable and machine-parseable so the next session can resume
        on the exact dramatic beat (see _latest_session_meta + get_full_context).
        """
        timestamp = self.get_timestamp()
        session_num = self._get_session_number()

        campaign = self.json_ops.load_json(self.campaign_file) or {}
        pos = campaign.get('player_position', {})
        location = pos.get('current_location', 'Unknown') if isinstance(pos, dict) else 'Unknown'
        threads_str = '; '.join(open_threads) if open_threads else ''

        with open(self.session_log, 'a') as f:
            f.write(f"### Session Ended: {timestamp}\n")
            f.write(f"{summary}\n\n")
            f.write(f"**Session:** {session_num}\n")
            f.write(f"**Location:** {location}\n")
            if cliffhanger:
                f.write(f"**Cliffhanger:** {cliffhanger}\n")
            if threads_str:
                f.write(f"**Open threads:** {threads_str}\n")
            f.write("\n---\n\n")

        print(f"[SUCCESS] Session {session_num} ended and logged")

        health = self._session_health()
        print("\n--- SESSION HEALTH (housekeeping, not canon) ---")
        if health:
            for line in health:
                print(line)
        else:
            print("All quiet — nothing stale.")
        return True

    def _session_health(self) -> list:
        """Read-only staleness scan for the session-end footer.

        Reports only what existing state already tracks: open threads (+ the
        stalest), clocks sitting at a full/due beat, and pending consequences.
        Surfaces the silent-lapse failure mode without adding any new tracking.
        ponytail: NPC canon-drift is not here yet — the re-grounding pass adds it.
        """
        plots = self.json_ops.load_json("plots.json") or {}
        clocks = self.json_ops.load_json("threat-clocks.json") or {}
        consequences = self.json_ops.load_json("consequences.json") or {}
        try:
            from npc_manager import NPCManager
            stale = NPCManager().stale_npcs()
        except Exception:
            stale = {}
        return self._health_summary(self._get_session_number(), plots, clocks,
                                    consequences, stale_npcs=stale)

    @staticmethod
    def _health_summary(session_num, plots, clocks, consequences, stale_npcs=None) -> list:
        """Pure staleness computation over already-loaded state (unit-testable)."""
        closed = {'completed', 'resolved', 'failed', 'done', 'abandoned', 'dropped'}

        open_threads = []
        if isinstance(plots, dict):
            for name, p in plots.items():
                if not isinstance(p, dict):
                    continue
                if str(p.get('status', 'active')).lower() in closed:
                    continue
                if p.get('background'):
                    continue  # import's background tier: real, but not a live thread
                events = p.get('events', [])
                last_sess = events[-1].get('session_number') if events and isinstance(events[-1], dict) else None
                stale = (session_num - last_sess) if (session_num and isinstance(last_sess, int)) else None
                open_threads.append((name, stale))

        due = []
        if isinstance(clocks, dict):
            for name, c in clocks.items():
                if not isinstance(c, dict):
                    continue
                cur, mx = c.get('current', 0), c.get('max', 0)
                if isinstance(cur, int) and isinstance(mx, int) and mx > 0 and cur >= mx:
                    due.append(name)

        pending = 0
        if isinstance(consequences, dict):
            for section in ('active', 'pending'):
                pending += sum(1 for x in consequences.get(section, []) if isinstance(x, dict))
        elif isinstance(consequences, list):
            pending += sum(1 for x in consequences if isinstance(x, dict))

        lines = []
        if open_threads:
            staley = [(n, s) for n, s in open_threads if s is not None and s > 0]
            tail = ""
            if staley:
                nm, s = max(staley, key=lambda t: t[1])
                tail = f" · stalest \"{nm}\" untouched {s} session{'s' if s != 1 else ''}"
            lines.append(f"Threads: {len(open_threads)} open{tail}")
        if due:
            lines.append(f"Clocks: {len(due)} at a due beat ({', '.join(due)}) — resolve or advance the fiction")
        if pending:
            lines.append(f"Pending consequences: {pending} waiting on a trigger")
        if stale_npcs:
            worst = max(stale_npcs.items(), key=lambda kv: kv[1])
            lines.append(f"Canon drift: {len(stale_npcs)} NPC(s) need re-grounding "
                         f"(worst \"{worst[0]}\", {worst[1]} beats) — gm-npc.sh stale")
        return lines

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

    @staticmethod
    def _normalize_connection_list(connections):
        """Coerce a connections list to {to, ...} dicts; tolerate malformed data.

        Extraction can leave bare-string connection entries. Everything here
        indexes c.get("to"), so coerce strings to {"to": name} and drop junk
        rather than crashing a move. Returns (list, changed_bool).
        """
        if not isinstance(connections, list):
            return [], True
        fixed = []
        changed = False
        for c in connections:
            if isinstance(c, dict):
                fixed.append(c)
            elif isinstance(c, str) and c.strip():
                fixed.append({"to": c.strip()})
                changed = True
            else:
                changed = True  # drop None/other junk
        return fixed, changed

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
            # Coerce malformed entries (bare-string connections from extraction)
            # so a bad data file never hard-crashes a move on c.get("to").
            old_connections, old_fixed = self._normalize_connection_list(
                locations[old_location].get("connections", []))
            new_connections, new_fixed = self._normalize_connection_list(
                locations[new_location].get("connections", []))
            if old_fixed:
                locations[old_location]["connections"] = old_connections
                changed = True
            if new_fixed:
                locations[new_location]["connections"] = new_connections
                changed = True

            # Check if connection from old -> new exists
            if not any(c.get("to") == new_location for c in old_connections):
                old_connections.append({"to": new_location, "path": "traveled"})
                locations[old_location]["connections"] = old_connections
                changed = True

            # Check if connection from new -> old exists
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

        # Update the active character's location if a sheet exists
        if self.character_file.exists():
            char_data = to_flat(self.json_ops.load_json("character.json"))
            char_data['current_location'] = location
            self.json_ops.save_json("character.json", char_data)

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
        safe_name = name.lower().replace(' ', '-')
        filename = self._unique_save_filename(safe_name)

        save_data = {
            "save_version": self.SAVE_VERSION,
            "name": name,
            "created": datetime.now(timezone.utc).isoformat(),
            "session_number": self._get_session_number(),
            "snapshot": self._build_snapshot(),
        }

        save_path = self.saves_dir / filename
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        if safe_name == "autosave":
            self._rotate_autosaves()

        print(f"[SUCCESS] Save created: {filename}")
        return filename

    def restore_save(self, name: str) -> bool:
        """
        Restore from a save point
        Name can be full filename or partial match
        """
        save_file = self._find_save(name)
        if not save_file:
            print(f"[ERROR] Save point '{name}' not found")
            return False

        try:
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Failed to load save: {e}")
            return False

        snapshot = save_data.get('snapshot', {})
        if not isinstance(snapshot, dict):
            snapshot = {}

        if save_data.get("save_version") is None:
            missing = self._uncovered_contract_files(snapshot)
            print("[WARNING] Partial restore: save has no save_version; "
                  "snapshot did not include: " + ", ".join(missing))

        for key, value in snapshot.items():
            self._restore_snapshot_entry(key, value)

        print(f"[SUCCESS] Restored from save: {save_file.name}")
        return True

    def _build_snapshot(self) -> Dict[str, Any]:
        """Snapshot every live stateful campaign file; omit missing ones."""
        snapshot = {}
        for filename in self.SNAPSHOT_JSON_FILES:
            if (self.campaign_dir / filename).is_file():
                snapshot[filename] = self.json_ops.load_json(filename)
        for filename in self.SNAPSHOT_TEXT_FILES:
            path = self.campaign_dir / filename
            if path.is_file():
                snapshot[filename] = path.read_text(encoding="utf-8")
        characters = self._load_all_characters()
        if characters:
            snapshot["characters"] = characters
        fallen_dir = self.campaign_dir / "fallen"
        if fallen_dir.is_dir():
            for fallen_file in sorted(fallen_dir.glob("*.json")):
                rel = f"fallen/{fallen_file.name}"
                snapshot[rel] = self.json_ops.load_json(rel)
        return snapshot

    def _restore_snapshot_entry(self, key: str, value: Any) -> None:
        """Restore one snapshot key. Legacy underscored names still apply."""
        if key == "characters":
            if isinstance(value, dict):
                self._restore_characters(value)
            return
        if key in self.LEGACY_SNAPSHOT_KEYS:
            self.json_ops.save_json(self.LEGACY_SNAPSHOT_KEYS[key], value)
            return
        if key in self.SNAPSHOT_TEXT_FILES:
            text = value if isinstance(value, str) else ""
            (self.campaign_dir / key).write_text(text, encoding="utf-8")
            return
        fallen = key.startswith("fallen/") and key.endswith(".json") and "/" not in key[7:]
        if key in self.SNAPSHOT_JSON_FILES or fallen:
            dest = self.campaign_dir / key
            dest.parent.mkdir(parents=True, exist_ok=True)
            self.json_ops.save_json(key, value)

    def _uncovered_contract_files(self, snapshot: Dict[str, Any]) -> List[str]:
        """Contract files this snapshot has no key for (legacy partial restores)."""
        covered = set()
        for key in snapshot:
            if key == "characters" or key == "character.json":
                covered.add("character.json")
            elif key in self.LEGACY_SNAPSHOT_KEYS:
                covered.add(self.LEGACY_SNAPSHOT_KEYS[key])
            elif key.startswith("fallen/"):
                covered.add("fallen/*.json")
            else:
                covered.add(key)
        return [name for name in self.CONTRACT_FILES if name not in covered]

    def _unique_save_filename(self, safe_name: str) -> str:
        """{timestamp}-{name}.json, uniquified if that path already exists."""
        timestamp = self.get_iso_timestamp()
        filename = f"{timestamp}-{safe_name}.json"
        if not (self.saves_dir / filename).exists():
            return filename
        n = 2
        while (self.saves_dir / f"{timestamp}-{safe_name}-{n}.json").exists():
            n += 1
        return f"{timestamp}-{safe_name}-{n}.json"

    def _autosave_seq(self, filename: str) -> int:
        """Order among same-second autosaves: bare = 1, -2 = 2, …"""
        match = re.search(r"-autosave(?:-(\d+))?\.json$", filename)
        if not match:
            return 0
        return int(match.group(1) or 1)

    def _autosave_files(self) -> List[Path]:
        """Autosave snapshots, oldest first (mtime, then same-second sequence)."""
        found = [p for p in self.saves_dir.glob("*.json")
                 if self._AUTOSAVE_FILE.match(p.name)]
        found.sort(key=lambda p: (p.stat().st_mtime, self._autosave_seq(p.name)))
        return found

    def _rotate_autosaves(self) -> None:
        """Keep at most AUTOSAVE_KEEP autosave snapshots; named saves untouched."""
        autosaves = self._autosave_files()
        while len(autosaves) > self.AUTOSAVE_KEEP:
            oldest = autosaves.pop(0)
            oldest.unlink()

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

    @staticmethod
    def _remainder(hidden: int, noun: str, hint: str) -> Optional[str]:
        """Disclosure line for a truncated list: '+N more <noun> — <hint>'."""
        if hidden <= 0:
            return None
        return f"+{hidden} more {noun} — {hint}"

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

        # --- KIT (ambient; skills defer here instead of calling world_kit.py info) ---
        kit = None
        try:
            kit = WorldKit(self._wsd)
            if kit.campaign_dir is None:
                kit = None
        except Exception:
            kit = None
        if kit is not None:
            skills = kit.skills()
            vitals = kit.vitals()
            lines.append("")
            lines.append("--- KIT ---")
            lines.append(f"kit: {kit.kit()}")
            lines.append(f"name: {kit.name()}")
            lines.append(f"resolution: {kit.resolution_model()}")
            lines.append(f"progression: {kit.progression_model()}")
            lines.append(f"vitals: {', '.join(vitals) if vitals else '(none)'}")
            lines.append(f"skills: {', '.join(skills) if skills else '(none)'}")

        # --- PRIMER (play pack: tonight's table, not the gazetteer) ---
        try:
            from play_pack import render_primer, normalize_pack, pack_is_set
            pack = normalize_pack(campaign.get("play_pack"))
            if pack_is_set(pack):
                lines.append("")
                lines.append(render_primer(pack))
        except Exception:
            pass

        # --- Play style (honor every beat; player toggles anytime) ---
        if self.get_preferences().get("beat_length", "adaptive") == "tight":
            lines.append("Pacing: TIGHT — a beat is the player's action, its immediate "
                         "consequence, and AT MOST ONE new world development. Then stop at "
                         "the first moment the player could plausibly act. Scene-state "
                         "changes (distance closing, arrivals, reveals, an NPC deciding "
                         "something new) do not happen on their own — each waits for a "
                         "player action to carry it, and each is its own beat. Before "
                         "sending, test: could the player reasonably say 'wait — I do X' "
                         "anywhere in this reply? If yes, cut there. Keep prose short: a few "
                         "sentences to a short paragraph.")
        else:
            lines.append("Pacing: no tight preference is set. Match prose to the beat, one "
                         "clear beat at a time; don't fast-forward past a choice.")

        if self.get_preferences().get("player_rolls", False):
            lines.append("Dice: PLAYER CHOOSES THE ROLL. When a check is needed, STOP at the "
                         "decision point and present it as a menu:\n"
                         "  1. Roll a <Stat> check with <+X stat / +Y other> bonuses. "
                         "Target of <Z> or higher.\n"
                         "  Or something else... (a different action — which may itself "
                         "demand its own roll, and that is fine).\n"
                         "Spell out the stat, every bonus, and the target DC. The player's "
                         "choice is to COMMIT to the roll (or pick something else) — do NOT "
                         "ask them to report a number. Once they commit: (1) narrate the "
                         "START of the attempt (a sentence or two, no outcome yet), (2) run "
                         "the dice tool `uv run python lib/dice.py \"1d20+<total bonus>\"` and "
                         "show the result line CLEARLY, (3) narrate what happens as a result — "
                         "true to the roll (nat 20 fantastic, nat 1 horrible, meet/beat the "
                         "target = success, below = failure with a real cost). GM still rolls "
                         "hidden/NPC dice the same way.")

        # Informing, not adjudicating — caps and judgment live in skills / gm-craft.
        lines.append("Failure: failure should cost something; decide the stake before the roll.")

        if self.get_preferences().get("rag_inspiration", False):
            lines.append("Inspiration: every beat (or every other beat), run "
                         "`gm-search.sh \"<what's happening now>\" --rag-only` and mine the "
                         "returned passages for a concrete image, phrase, or sensory detail "
                         "from the source. Synthesize — never paste raw passages.")
        if self.get_preferences().get("action_menu", True):
            lines.append("Play style: action menu ON — end each beat with exactly THREE "
                         "numbered options, then a final line \"Or something else...\" to "
                         "signal the player can always choose their own action.")
        else:
            lines.append("Play style: action menu OFF — end beats with an open prompt; do "
                         "NOT list numbered choices. The player drives freely. "
                         "(Toggle: /gm choices on|off)")

        # --- Scene images (gpt-image-2): only available when a key is configured ---
        if os.environ.get("OPENAI_API_KEY"):
            lines.append("Scene images: ENABLED — illustrate GENEROUSLY and with glee "
                         "(images cost ~$0.04; lean toward YES). New location, monster/boss "
                         "reveal, big loot, a styled flourish, a funny beat, a quiet vista — "
                         "any beat with a real visual or emotional charge earns one. Present "
                         "it DIEGETICALLY: frame the picture as an artifact made by an in-world "
                         "chronicler whose style fits this world's voice (e.g. \"BEHOLD, the "
                         "battle as set down by the scholar Astreus —\") and keep that same "
                         "artist + art-style across the campaign so it reads like one artbook. "
                         "Run `bash tools/gm-image.sh generate --title \"...\" --prompt \"...\"`, "
                         "then show the file:// link. (See gm-craft → Diegetic Illustration.) "
                         "Skip only truly flat beats and don't re-shoot the same static room.")
            chronicler = self.json_ops.load_json("chronicler.json") or {}
            if chronicler.get("name"):
                bits = [f"This campaign's chronicler is {chronicler['name']}"]
                if chronicler.get("persona"):
                    bits.append(f"({chronicler['persona']})")
                line = " ".join(bits) + "."
                if chronicler.get("style"):
                    line += (f" Locked art style: {chronicler['style']} "
                             "(auto-added to every prompt).")
                line += " Frame every image as their work and keep them consistent."
                lines.append("  Chronicler: " + line)
            else:
                lines.append("  Chronicler: none yet — name one the first time you "
                             "illustrate and persist it with `bash tools/gm-image.sh "
                             "chronicler --name \"...\" --style \"...\" --persona \"...\"`.")
        else:
            lines.append("Scene images: DISABLED (no OPENAI_API_KEY) — do NOT call gm-image.sh "
                         "and do NOT mention images; narrate in text only.")

        # --- Narrative Voice (write the prose in the world's authorial voice) ---
        bible = self.json_ops.load_json("world-bible.json") or {}
        voice = bible.get("voice") or {}
        style = (voice.get("style") or "").strip()
        passages = [str(p).strip() for p in (voice.get("sample_passages") or []) if str(p).strip()]
        vocab = [str(v).strip() for v in (voice.get("vocab") or []) if str(v).strip()]
        if style or passages:
            lines.append("")
            lines.append("--- NARRATIVE VOICE (narrate in this voice; a prose target, NOT lore) ---")
            if style:
                lines.append(f"Style: {style}")
            if vocab:
                shown_vocab = vocab if full else vocab[:12]
                lines.append("In-world terms to favor: " + ", ".join(shown_vocab))
                rem = None if full else self._remainder(
                    len(vocab) - len(shown_vocab), "terms", "--full")
                if rem:
                    lines.append(rem)
            shown_passages = passages if full else passages[:3]
            for p in shown_passages:
                lines.append(f"  | {p}")
            rem = None if full else self._remainder(
                len(passages) - len(shown_passages), "sample passages", "--full")
            if rem:
                lines.append(rem)

        # --- World Index (named things that exist; scan before inventing a name) ---
        index = bible.get("index") or {}
        index_labels = (
            ("npcs", "NPCs"), ("locations", "Locations"),
            ("items", "Items"), ("monsters", "Monsters"),
        )
        index_lines: List[str] = []
        for bucket, label in index_labels:
            entries = [e for e in (index.get(bucket) or []) if isinstance(e, dict) and e.get("name")]
            if not entries:
                continue
            index_lines.append(f"{label}:")
            for e in entries:
                note = str(e.get("note") or "").strip()
                index_lines.append(f"  {e['name']}" + (f" — {note}" if note else ""))
        if index_lines:
            lines.append("")
            lines.append("--- WORLD INDEX (named things that exist; scan before inventing a name) ---")
            lines.extend(index_lines)

        # --- Previously On (story spine: resume story-aware, not stat-amnesiac) ---
        # Bounded by item COUNT, never by chopping a single entry. --full shows all.
        all_summaries = self._recent_session_summaries(n=None)
        summaries = all_summaries if full else all_summaries[-3:]
        if summaries:
            lines.append("")
            lines.append("--- PREVIOUSLY ON ---")
            for s in summaries:
                lines.append(f"- {s}")
            rem = None if full else self._remainder(
                len(all_summaries) - len(summaries), "sessions",
                "--full or session-log.md")
            if rem:
                lines.append(rem)
            meta = self._latest_session_meta()
            cliff = meta.get('cliffhanger') or self._cliffhanger(summaries[-1])
            if cliff:
                lines.append(f"WHERE WE PAUSED: {cliff}")
            if meta.get('open_threads'):
                lines.append(f"OPEN THREADS: {meta['open_threads']}")

        # --- The World Remembers (memory volunteered for THIS scene, never waited for) ---
        remembered, open_debts, held_back = self._world_remembers(
            location, full=full, already_shown=summaries)
        if remembered or open_debts:
            lines.append("")
            lines.append("--- THE WORLD REMEMBERS (older history this scene touches — "
                         "use it or let it lie, but don't contradict it) ---")
            for r in remembered:
                lines.append(f"- {self._truncate(r, 240, full)}")
            for d in open_debts:
                lines.append(f"OPEN DEBT: {d}")
            if held_back:
                rem = self._remainder(
                    held_back, "remembered entries", "--full or gm-recall.sh")
                if rem:
                    lines.append(rem)

        # --- Story Threads (active plots, main first, each with its latest beat) ---
        all_threads = self._active_plot_threads(limit=None)
        threads = all_threads if full else all_threads[:6]
        if threads:
            lines.append("")
            lines.append("--- STORY THREADS ---")
            lines.extend(threads)
            rem = None if full else self._remainder(
                len(all_threads) - len(threads), "threads",
                "gm-plot.sh threads for all")
            if rem:
                lines.append(rem)

        # --- Ready Threads (dormant seeded plots that just became relevant) ---
        ready = self._ready_threads(location, full=full)
        if ready:
            lines.append("")
            lines.append("--- READY THREADS (dormant plots now relevant — wake with "
                         "gm-plot.sh update) ---")
            shown = ready if full else ready[:5]
            lines.extend(shown)
            rem = None if full else self._remainder(
                len(ready) - len(shown), "ready threads", "--full")
            if rem:
                lines.append(rem)

        # --- Key Facts (established plot facts the GM must keep continuity on) ---
        key_facts = self._key_facts(per_category=None if full else 3)
        if key_facts:
            lines.append("")
            lines.append("--- KEY FACTS ---")
            for fact_line in key_facts:
                lines.append(f"- {fact_line}")
            if not full:
                hidden_facts = len(self._key_facts(per_category=None)) - len(key_facts)
                rem = self._remainder(hidden_facts, "facts",
                                      "--full or gm-note.sh list")
                if rem:
                    lines.append(rem)

        # --- Threat Clocks (felt, mounting pressure; only when any are declared) ---
        clocks = self.json_ops.load_json("threat-clocks.json") or {}
        if clocks:
            lines.append("")
            lines.append("--- THREAT CLOCKS ---")
            for clock_name, c in clocks.items():
                cur, mx = int(c.get('current', 0)), int(c.get('max', 1))
                bar = "●" * cur + "○" * max(0, mx - cur)
                flag = "  ⚠ FULL — a beat is due" if cur >= mx else ""
                lines.append(f"{clock_name}: [{bar}] {cur}/{mx}{flag}")

        # --- Character ---
        lines.append("")
        lines.append("--- CHARACTER ---")
        char = None
        if self.character_file.exists():
            import json as _json
            try:
                with open(self.character_file, 'r', encoding='utf-8') as f:
                    char = to_flat(_json.load(f))
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

                recent = self._recent_events(npc_data, full=full)
                if recent:
                    lines.append(f"  {recent}")
                lines.append("")
            if not full and len(party_items) > max_party:
                rem = self._remainder(
                    len(party_items) - max_party, "party members", "--full")
                if rem:
                    lines.append(rem)
                lines.append("")
        else:
            lines.append("(none)")
            lines.append("")

        # --- Present NPCs (voices, inner life, and what they remember; never mutate) ---
        present_npcs = self._present_npcs(npcs, location, full=full)
        if present_npcs:
            lines.append("")
            lines.append("--- NPC VOICES (present NPCs — speak in their own words; "
                         "they remember what is listed under them) ---")
            for npc_name, vlines in present_npcs:
                inner = npcs.get(npc_name, {}) if isinstance(npcs, dict) else {}
                tags = []
                if inner.get('current_mood'):
                    tags.append(f"mood: {inner['current_mood']}")
                if inner.get('goal'):
                    tags.append(f"wants: {inner['goal']}")
                if inner.get('secret'):
                    tags.append("has a secret")  # existence only — never the secret text
                header = npc_name + (f" ({'; '.join(tags)})" if tags else "")
                lines.append(f"{header}:")
                for vl in vlines:
                    lines.append(f'  "{vl}"')
                if not full:
                    ctx_raw = inner.get('context', [])
                    raw_lines = ctx_raw if isinstance(ctx_raw, list) else (
                        [ctx_raw] if ctx_raw else [])
                    raw_n = len([x for x in raw_lines if x])
                    rem = self._remainder(
                        raw_n - len(vlines), "voice lines", "--full")
                    if rem:
                        lines.append(f"  {rem}")
                # Party members already carry their history in the block above.
                if not inner.get('is_party_member'):
                    recent = self._recent_events(inner, full=full)
                    if recent:
                        lines.append(f"  {recent}")
                    # Global facts that NAME this NPC, re-attached at read time
                    # (de-duped against PREVIOUSLY ON, world-remembers, and the
                    # NPC's own events) so per-NPC memory is not lost to the log.
                    anchored = self._npc_anchored_facts(
                        npc_name, inner,
                        already_shown=list(summaries) + list(remembered))
                    shown_anchored = anchored if full else anchored[:3]
                    for fact in shown_anchored:
                        lines.append(f"  remembers: {self._truncate(fact, 180, full)}")
                    if not full:
                        rem = self._remainder(
                            len(anchored) - len(shown_anchored),
                            "remembered facts", "--full or gm-recall.sh")
                        if rem:
                            lines.append(f"  {rem}")

        # --- Pending Consequences ---
        lines.append("")
        lines.append("--- PENDING CONSEQUENCES ---")
        consequences = self.json_ops.load_json("consequences.json") or {}
        pending = []
        if isinstance(consequences, dict):
            # Not-yet-resolved consequences live in the 'active' (and optional 'pending') lists
            for section in ('active', 'pending'):
                for cdata in consequences.get(section, []):
                    if not isinstance(cdata, dict):
                        continue
                    event = cdata.get('consequence', 'Unknown')
                    trigger = cdata.get('trigger', 'Unknown')
                    cid = str(cdata.get('id', '?'))
                    short_id = cid[:4] if len(cid) >= 4 else cid
                    pending.append(f"[{short_id}] {event} -> triggers: {trigger}")
        elif isinstance(consequences, list):
            for cdata in consequences:
                if isinstance(cdata, dict):
                    event = cdata.get('consequence', cdata.get('event', 'Unknown'))
                    trigger = cdata.get('trigger', 'Unknown')
                    cid = str(cdata.get('id', '?'))
                    short_id = cid[:4] if len(cid) >= 4 else cid
                    pending.append(f"[{short_id}] {event} -> triggers: {trigger}")

        if pending:
            max_pending = len(pending) if full else 10
            for p in pending[:max_pending]:
                lines.append(p)
            if not full and len(pending) > max_pending:
                rem = self._remainder(
                    len(pending) - max_pending, "pending consequences",
                    "--full or gm-consequence.sh check")
                if rem:
                    lines.append(rem)
        else:
            lines.append("(none)")

        # --- Your World's Rules (bespoke per-campaign systems; NEVER truncated) ---
        # Prefer kit signature_systems; campaign_rules is the legacy fallback.
        # These rules ARE the magic that makes each book feel distinct. The GM is
        # told to follow them exactly, so it must see them in full.
        systems = kit.signature_systems() if kit is not None else []
        if systems:
            lines.append("")
            lines.append("--- YOUR WORLD'S RULES (follow exactly) ---")
            for system in systems:
                name = system.get("name") or "unnamed"
                summary = system.get("summary") or ""
                extra = system.get("rules") or ""
                if summary:
                    lines.append(f"- {name}: {summary}")
                else:
                    lines.append(f"- {name}")
                if extra and extra != summary:
                    lines.append(f"    {extra}")
        else:
            rules = campaign.get('campaign_rules', {})
            if rules:
                import json
                lines.append("")
                lines.append("--- YOUR WORLD'S RULES (follow exactly) ---")
                if isinstance(rules, dict):
                    for key, val in rules.items():
                        if isinstance(val, (dict, list)):
                            lines.append(f"- {key}:")
                            for vline in json.dumps(val, indent=2, ensure_ascii=False).splitlines():
                                lines.append(f"    {vline}")
                        else:
                            lines.append(f"- {key}: {val}")
                elif isinstance(rules, list):
                    for rule in rules:
                        if isinstance(rule, (dict, list)):
                            for vline in json.dumps(rule, indent=2, ensure_ascii=False).splitlines():
                                lines.append(f"  {vline}")
                        else:
                            lines.append(f"- {rule}")

        # --- Signature Systems (executable primitives; the GM ROLLS these, not vibes) ---
        try:
            sys_list = kit.systems() if kit is not None else []
        except Exception:
            sys_list = []
        if sys_list:
            lines.append("")
            lines.append("--- YOUR WORLD'S SIGNATURE SYSTEMS (executable — ROLL these, "
                         "do not just narrate them) ---")
            lines.append("Resolve with lib/game_core primitives "
                         "(named_track / price_roll / reaction_roll / guarded_payoff).")
            for s in sys_list:
                lines.append(f"- {s['name']} ({s['primitive']}): {self._system_summary(s)}")

        context = "\n".join(lines)

        # Token observability: soft ~2k-token target is GUIDANCE only, never a hard
        # cut. Opt in with DM_DEBUG_CONTEXT=1 to watch the budget without altering output.
        if os.environ.get('DM_DEBUG_CONTEXT'):
            approx_tokens = len(context) // 4
            print(f"[context] ~{approx_tokens} tokens ({len(context)} chars)", file=sys.stderr)

        return context

    # ==================== Private Helpers ====================

    def _system_summary(self, system):
        """One-line render of an instantiated signature system for the brief."""
        prim = system.get("primitive")
        cfg = system.get("config") or {}
        if prim == "named_track":
            mx = cfg.get("max", "?")
            ths = cfg.get("thresholds") or []
            parts = "; ".join(
                f"at {t.get('at')}: {t.get('consequence', '')}".strip()
                for t in ths if isinstance(t, dict))
            return f"track 0–{mx}" + (f" — {parts}" if parts else "")
        if prim == "price_roll":
            return "taking the marked action forces a cost roll"
        if prim == "reaction_roll":
            return "NPC opening reaction, modified by this world's reputation/track"
        if prim == "guarded_payoff":
            return "roll BEFORE taking marked treasure: clean / guardian wakes / curse attaches"
        return system.get("summary") or prim or ""

    def _recent_session_summaries(self, n=3):
        """Return recent completed-session summary paragraphs (oldest -> newest).

        Parses session-log.md blocks; a completed session is one with a
        '### Session Ended:' marker. n=None returns all.
        """
        log_path = self.campaign_dir / "session-log.md"
        if not log_path.exists():
            return []
        try:
            text = log_path.read_text(encoding='utf-8')
        except (IOError, ValueError):
            return []
        summaries = []
        for block in text.split("## Session Started:"):
            if "### Session Ended:" not in block:
                continue
            after = block.split("### Session Ended:", 1)[1]
            body = []
            for ln in after.splitlines()[1:]:  # skip the 'Session Ended' timestamp line
                if ln.strip() == "---":
                    break
                if ln.strip():
                    body.append(ln.strip())
            if body:
                summaries.append(" ".join(body))
        return summaries if n is None else summaries[-n:]

    def _cliffhanger(self, summary):
        """Best-effort 'where we paused' = last 1-2 sentences of a summary.

        Superseded by structured session metadata once session-identity-metadata lands.
        """
        normalized = summary.replace('!', '.').replace('?', '.')
        parts = [s.strip() for s in normalized.split('.') if s.strip()]
        return ('. '.join(parts[-2:]) + '.') if parts else ''

    def _ready_threads(self, location, full=False):
        """Dormant seeded plots that just became relevant — a nudge for the GM to wake them.

        A dormant plot surfaces here when (a) one of its linked NPCs is present, (b) its
        linked location is the current one, or (c) a threat clock linked to it is at
        least half full. Reuses `npcs_present` (the same presence predicate the NPC
        block and consequence tick use). Read-only; returns [] on any failure. This is
        what actively tells the GM a seeded thread is relevant NOW; `gm-plot.sh update`
        wakes it (dormant -> active).
        """
        try:
            plots = self.json_ops.load_json("plots.json") or {}
        except Exception:
            return []
        dormant = [(n, p) for n, p in plots.items()
                   if isinstance(p, dict) and p.get('status') == 'dormant']
        if not dormant:
            return []

        try:
            present = set(npcs_present(
                self.json_ops.load_json("npcs.json") or {}, location).keys())
        except Exception:
            present = set()

        # plot name -> a clock linked to it that is at least half full
        mature_clock = {}
        clocks = self.json_ops.load_json("threat-clocks.json") or {}
        if isinstance(clocks, dict):
            for cname, c in clocks.items():
                if not isinstance(c, dict):
                    continue
                lp, cur, mx = c.get('linked_plot'), c.get('current', 0), (c.get('max', 0) or 0)
                if lp and mx and cur >= mx / 2:
                    mature_clock[lp] = (cname, cur, mx)

        cur_loc = (location or '').strip().lower()
        out = []
        for name, p in dormant:
            npc_hit = next((n for n in (p.get('npcs') or []) if n in present), None)
            if npc_hit:
                reason = f"{npc_hit} is here"
            elif cur_loc and any((loc or '').strip().lower() == cur_loc
                                 for loc in (p.get('locations') or [])):
                reason = f"you are at {location}"
            elif name in mature_clock:
                cname, ccur, cmx = mature_clock[name]
                reason = f'the "{cname}" clock is {ccur}/{cmx}'
            else:
                continue
            hook = self._truncate(p.get('description', ''), 120, full)
            out.append(f'💤→ "{name}" — {hook} (because {reason})')
        return out

    def _active_plot_threads(self, limit=6):
        """Active plots, main-first, each with its latest event beat. limit=None = all."""
        plots = self.json_ops.load_json("plots.json") or {}
        if not isinstance(plots, dict):
            return []
        closed = {'completed', 'resolved', 'failed', 'done', 'abandoned', 'dropped'}
        order = PLOT_TYPE_SORT
        active = []
        for name, p in plots.items():
            if not isinstance(p, dict):
                continue
            if str(p.get('status', 'active')).lower() in closed:
                continue
            if p.get('background'):
                continue  # import's background tier: real, but not a live thread
            ptype = str(p.get('type', 'side')).lower()
            # Within a type, order by spine `sequence` when present (arc order);
            # unsequenced plots sort last via a large fallback key.
            seq = p.get('sequence')
            seq = seq if isinstance(seq, int) else 9999
            latest = ''
            events = p.get('events')
            if isinstance(events, list) and events:
                ev = events[-1]
                latest = ev.get('event', ev.get('description', '')) if isinstance(ev, dict) else str(ev)
            active.append((order.get(ptype, len(order)), seq, ptype, name, latest))
        active.sort(key=lambda t: (t[0], t[1]))
        chosen = active if limit is None else active[:limit]
        return [f"[{ptype}] {name}" + (f" - latest: {latest}" if latest else "")
                for _, _seq, ptype, name, latest in chosen]

    # Categories that carry continuity the GM must not contradict. `player_choices`
    # and `npc_relations` were advertised by gm-note.sh and read by nothing, so the
    # two categories that hold what the player DID were write-only. `session_events`
    # stays out (the session log and PREVIOUSLY ON own it) and so does `rules` (the
    # world's own rules block owns that); both remain reachable through recall.
    KEY_FACT_CATEGORIES = ('plot_local', 'plot_regional', 'plot_world',
                           'player_choices', 'npc_relations', 'lore')

    def _key_facts(self, per_category=3):
        """Established facts the GM must keep continuity on. per_category=None = all."""
        facts = self.json_ops.load_json("facts.json") or {}
        if not isinstance(facts, dict):
            return []
        out = []
        for cat in self.KEY_FACT_CATEGORIES:
            items = facts.get(cat)
            if not isinstance(items, list):
                continue
            chosen = items if per_category is None else items[-per_category:]
            for it in chosen:
                txt = it.get('fact', it.get('text', it.get('event', ''))) if isinstance(it, dict) else str(it)
                if txt:
                    out.append(txt)
        return out

    def _world_remembers(self, location, full=False, already_shown=()):
        """What the campaign's long-term memory volunteers for THIS scene.

        CampaignMemory (arcs, session history, facts — embedded and searchable)
        had no automated reader: recall fired only when the GM thought to ask,
        which requires already suspecting there is something to remember. That is
        the exact failure memory exists to fix. The scene itself is the query —
        where we are, and who is standing here.

        Returns (entries, open_debts, held_back_total). Degrades to empty on any
        failure — no memory file, no embedding deps, a half-written index — so a
        broken memory costs the brief nothing mid-session.
        """
        try:
            from campaign_memory import CampaignMemory
            mem = CampaignMemory(self._wsd)
            npcs = self.json_ops.load_json("npcs.json") or {}
            present = [name for name, _ in self._present_npcs(npcs, location)]
            query = " ".join([location or ""] + present).strip()
            if not query:
                return [], [], 0
            top_k = None if full else 3
            hits = mem.recall(query, top_k=top_k)
            arcs = mem.arcs()
            debts = [str(d) for d in (arcs[-1].get("open_debts") or [])] if arcs else []
            total = len((self.json_ops.load_json(mem.memory_file) or {}).get("entries") or [])
        except Exception:
            return [], [], 0

        # Don't echo PREVIOUSLY ON. recall() falls back to re-gathering the session
        # log, so its top hits are frequently the very summaries printed above —
        # compare on collapsed whitespace, and either way round, since a gathered
        # entry may span several logged sessions.
        def _norm(s):
            return " ".join(str(s).split())

        shown = [_norm(s) for s in already_shown if _norm(s)]
        entries = []
        for h in hits:
            text = str(h.get("text", "")).strip()
            norm = _norm(text)
            if not norm or any(norm in s or s in norm for s in shown):
                continue
            shown.append(norm)
            entries.append(text)
        held_back = total - len(entries) if (entries and not full and total > len(entries)) else 0
        return entries, debts, held_back

    def _recent_events(self, entity, full=False):
        """The 'they remember you' line for an NPC, or None.

        Shared by the party block and the present-NPC block so a character's
        history renders identically wherever they appear.
        """
        if not isinstance(entity, dict):
            return None
        events = entity.get('events', [])
        if not isinstance(events, list) or not events:
            return None
        recent = events[-3:] if full else events[-2:]
        parts = []
        for ev in recent:
            text = ev.get('event', '') if isinstance(ev, dict) else str(ev)
            if text:
                parts.append(f'"{self._truncate(text, 120, full)}"')
        return f"Recent: {' -> '.join(parts)}" if parts else None

    def _npc_anchored_facts(self, npc_name, npc_data, already_shown=()):
        """Facts from facts.json whose text NAMES this NPC — surfaced under them.

        A fact logged via gm-note.sh lands only in facts.json; if it names an
        NPC ("the wench's eyes flicked to the back door — she knows more"), that
        memory never reaches her. Read-time cross-reference fixes this without
        any write-side coupling: every context build re-scans the global facts
        log and re-attaches what belongs to whoever is standing here, so there
        is no duplicate-storm in storage.

        Match is on a WORD BOUNDARY against the full NPC key and any explicit
        `aliases` entry only — so "Ana" matches "Ana" but not "Banana", and
        "Old Man Withers" matches only the whole name/alias, never a stray
        leading token like "old" in "the old rope". Short-name matching is what
        `aliases` are for (entity-dedupe records them). Excludes anything already
        in `already_shown` (the PREVIOUSLY ON / world-remembers de-dup set) and
        anything already carried in the NPC's own `events` (so it is not shown
        twice). Returns the full matched list (caller caps + discloses the
        remainder); [] when the NPC is named in no fact, or on any failure.
        """
        facts = self.json_ops.load_json("facts.json") or {}
        if not isinstance(facts, dict):
            return []
        all_facts = []
        for items in facts.values():
            if not isinstance(items, list):
                continue
            for it in items:
                txt = it.get('fact', it.get('text', it.get('event', ''))) if isinstance(it, dict) else str(it)
                if txt:
                    all_facts.append(str(txt))
        if not all_facts:
            return []

        # Needles: the full key and any explicit aliases only. No auto-derived
        # leading-token needle — a common first word ("Old", "Red", "Young")
        # would match ordinary lowercase prose and attach unrelated facts.
        needles = [npc_name]
        aliases = npc_data.get('aliases') if isinstance(npc_data, dict) else None
        if isinstance(aliases, list):
            needles.extend(str(a) for a in aliases if a)
        elif isinstance(aliases, str) and aliases:
            needles.append(aliases)
        patterns = [re.compile(r"\b" + re.escape(n) + r"\b", re.IGNORECASE)
                    for n in needles if n]

        def _norm(s):
            return " ".join(str(s).split())

        shown = {_norm(s) for s in already_shown if _norm(s)}
        events = npc_data.get('events', []) if isinstance(npc_data, dict) else []
        if isinstance(events, list):
            for ev in events:
                t = ev.get('event', '') if isinstance(ev, dict) else str(ev)
                if t:
                    shown.add(_norm(t))

        matched, seen = [], set()
        for txt in all_facts:
            norm = _norm(txt)
            if not norm or norm in shown or norm in seen:
                continue
            if any(p.search(txt) for p in patterns):
                seen.add(norm)
                matched.append(txt)
        return matched

    def _present_npcs(self, npcs, location, full=False):
        """NPCs present in the scene, with any canonical voice lines they have.

        Presence is `npcs_present` (party OR exact location tag). This method
        slices voice lines; it does not decide who is here. Returns
        [(name, [lines])]; up to 4 lines each unless full, and an empty list when
        the NPC has no extracted dialogue — presence does NOT require a voice, or
        stubbed and original-world NPCs would stand in the room invisibly.
        Read-only — never touches the stored `context` field (PROTECT
        canonical-voice extraction).
        """
        out = []
        for name, d in npcs_present(npcs, location).items():
            ctx = d.get('context', [])
            vlines = ctx if isinstance(ctx, list) else ([ctx] if ctx else [])
            vlines = [str(x) for x in vlines if x]
            out.append((name, vlines if full else vlines[:4]))
        return out

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
        """Current session number, derived from matched start/end pairs.

        Counting raw 'Session Started:' over-counts orphan/duplicate starts
        (DCC showed ~20 starts for ~13 real sessions). The current number is the
        count of completed (ended) sessions, plus 1 if a session is open now.
        """
        if not self.session_log.exists():
            return 0
        content = self.session_log.read_text()
        ended = content.count('### Session Ended:')
        started = content.count('## Session Started:')
        return ended + (1 if started > ended else 0)

    def _latest_session_meta(self) -> Dict[str, str]:
        """Parse the most recent ended session's structured footer, if present.

        Returns {'cliffhanger': ..., 'open_threads': ...} (empty strings if none).
        """
        meta = {'cliffhanger': '', 'open_threads': ''}
        if not self.session_log.exists():
            return meta
        blocks = self.session_log.read_text(encoding='utf-8').split("### Session Ended:")
        if len(blocks) < 2:
            return meta
        last = blocks[-1]
        for line in last.splitlines():
            s = line.strip()
            if s.startswith('**Cliffhanger:**'):
                meta['cliffhanger'] = s.split('**Cliffhanger:**', 1)[1].strip()
            elif s.startswith('**Open threads:**'):
                meta['open_threads'] = s.split('**Open threads:**', 1)[1].strip()
        return meta

    def _get_recent_sessions(self, count: int) -> List[str]:
        """Get recent session entries"""
        history = self.get_history()
        return history[-count:] if history else []

    def _load_all_characters(self) -> Dict[str, Any]:
        """Load the active PC for a snapshot, keyed 'character'."""
        if self.character_file.exists():
            return {"character": self.json_ops.load_json("character.json")}
        return {}

    def _restore_characters(self, characters: Dict[str, Any]) -> None:
        """Restore the active PC from a snapshot."""
        import json

        if 'character' in characters:
            with open(self.character_file, 'w', encoding='utf-8') as f:
                json.dump(characters['character'], f, indent=2)

    def _find_save(self, name: str) -> Optional[Path]:
        """Find a save file by name or partial match.

        When several files match (notably rotating autosaves), return the newest.
        """
        exact_match = self.saves_dir / name
        if exact_match.exists():
            return exact_match

        if not name.endswith('.json'):
            exact_match = self.saves_dir / f"{name}.json"
            if exact_match.exists():
                return exact_match

        needle = name.lower()
        if needle in ("autosave", "autosave.json"):
            autosaves = self._autosave_files()
            if autosaves:
                return autosaves[-1]

        matches = [p for p in self.saves_dir.glob("*.json")
                   if needle in p.name.lower()]
        if not matches:
            return None
        matches.sort(key=lambda p: (p.stat().st_mtime, p.name))
        return matches[-1]


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
    end_parser.add_argument('--cliffhanger', help='One-line cliffhanger to resume on')
    end_parser.add_argument('--open-thread', dest='open_threads', action='append',
                            default=[], help='Open thread (repeatable)')

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

    choices_parser = subparsers.add_parser('choices', help='Toggle the action-menu play style')
    choices_parser.add_argument('value', nargs='?', default='show',
                                choices=['on', 'off', 'toggle', 'show'],
                                help='on | off | toggle | show (default: show)')

    dice_parser = subparsers.add_parser('dice', help='Toggle whether the player rolls their own dice')
    dice_parser.add_argument('value', nargs='?', default='show',
                             choices=['on', 'off', 'toggle', 'show'],
                             help='on | off | toggle | show (default: show)')

    from cli_output import wants_json, strip_json_flag, emit
    json_mode = wants_json()
    args = parser.parse_args(strip_json_flag(sys.argv[1:]))

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = SessionManager()

    if json_mode and args.action == 'status':
        emit(manager.get_status(), json_mode=True)
        return
    if json_mode and args.action == 'context':
        emit({"context": manager.get_full_context(full=getattr(args, 'full', False))}, json_mode=True)
        return
    if json_mode and args.action == 'move':
        emit(manager.move_party(' '.join(args.location)), json_mode=True)
        return

    if args.action == 'start':
        summary = manager.start_session()
        print(json.dumps(summary, indent=2))

    elif args.action == 'end':
        summary_text = ' '.join(args.summary)
        if not manager.end_session(summary_text, cliffhanger=args.cliffhanger,
                                   open_threads=args.open_threads):
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

    elif args.action == 'choices':
        val = getattr(args, 'value', 'show')
        current = manager.get_preferences().get('action_menu', True)
        if val != 'show':
            new = (not current) if val == 'toggle' else (val == 'on')
            manager.set_preference('action_menu', new)
            current = new
        state = 'on' if current else 'off'
        if val == 'show':
            print(f"Action menu is {state}.")
        else:
            print(f"Action menu turned {state}. "
                  f"{'Beats will end with a few numbered choices.' if current else 'Beats will end with an open prompt.'}")

    elif args.action == 'dice':
        val = getattr(args, 'value', 'show')
        current = manager.get_preferences().get('player_rolls', False)
        if val != 'show':
            new = (not current) if val == 'toggle' else (val == 'on')
            manager.set_preference('player_rolls', new)
            current = new
        state = 'on' if current else 'off'
        if val == 'show':
            print(f"Player rolls is {state}.")
        else:
            print(f"Player rolls turned {state}. "
                  f"{'You roll your own dice; the GM only rolls hidden/NPC dice.' if current else 'The GM rolls for you again.'}")


if __name__ == "__main__":
    main()
