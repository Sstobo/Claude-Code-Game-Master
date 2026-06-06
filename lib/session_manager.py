#!/usr/bin/env python3
"""
Session management module for DM tools
Handles session lifecycle, party movement, and JSON-based saves
"""

import sys
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

        # --- Previously On (story spine: resume story-aware, not stat-amnesiac) ---
        # Bounded by item COUNT, never by chopping a single entry. --full shows all.
        summaries = self._recent_session_summaries(n=None if full else 3)
        if summaries:
            lines.append("")
            lines.append("--- PREVIOUSLY ON ---")
            for s in summaries:
                lines.append(f"- {s}")
            meta = self._latest_session_meta()
            cliff = meta.get('cliffhanger') or self._cliffhanger(summaries[-1])
            if cliff:
                lines.append(f"WHERE WE PAUSED: {cliff}")
            if meta.get('open_threads'):
                lines.append(f"OPEN THREADS: {meta['open_threads']}")

        # --- Story Threads (active plots, main first, each with its latest beat) ---
        threads = self._active_plot_threads(limit=None if full else 6)
        if threads:
            lines.append("")
            lines.append("--- STORY THREADS ---")
            lines.extend(threads)

        # --- Key Facts (established plot facts the DM must keep continuity on) ---
        key_facts = self._key_facts(per_category=None if full else 4)
        if key_facts:
            lines.append("")
            lines.append("--- KEY FACTS ---")
            for fact_line in key_facts:
                lines.append(f"- {fact_line}")

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

        # --- NPC Voices (canonical lines for present NPCs; surface, never mutate) ---
        npc_voices = self._present_npc_voices(npcs, location, full=full)
        if npc_voices:
            lines.append("")
            lines.append("--- NPC VOICES (present NPCs, speak in their own words) ---")
            for npc_name, vlines in npc_voices:
                lines.append(f"{npc_name}:")
                for vl in vlines:
                    lines.append(f'  "{vl}"')

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
                lines.append(f"... and {len(pending) - max_pending} more pending consequences (use --full)")
        else:
            lines.append("(none)")

        # --- Your World's Rules (bespoke per-campaign systems; NEVER truncated) ---
        # These rules ARE the magic that makes each book feel distinct. The DM is
        # told to follow them exactly, so it must see them in full. Nested systems
        # (loot boxes, audience reactions, interviews) are pretty-printed whole.
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

        context = "\n".join(lines)

        # Token observability: soft ~2k-token target is GUIDANCE only, never a hard
        # cut. Opt in with DM_DEBUG_CONTEXT=1 to watch the budget without altering output.
        import os
        if os.environ.get('DM_DEBUG_CONTEXT'):
            approx_tokens = len(context) // 4
            print(f"[context] ~{approx_tokens} tokens ({len(context)} chars)", file=sys.stderr)

        return context

    # ==================== Private Helpers ====================

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

    def _active_plot_threads(self, limit=6):
        """Active plots, main-first, each with its latest event beat. limit=None = all."""
        plots = self.json_ops.load_json("plots.json") or {}
        if not isinstance(plots, dict):
            return []
        closed = {'completed', 'resolved', 'failed', 'done', 'abandoned', 'dropped'}
        order = {'main': 0, 'threat': 1, 'mystery': 2, 'side': 3}
        active = []
        for name, p in plots.items():
            if not isinstance(p, dict):
                continue
            if str(p.get('status', 'active')).lower() in closed:
                continue
            ptype = str(p.get('type', 'side')).lower()
            latest = ''
            events = p.get('events')
            if isinstance(events, list) and events:
                ev = events[-1]
                latest = ev.get('event', ev.get('description', '')) if isinstance(ev, dict) else str(ev)
            active.append((order.get(ptype, 5), ptype, name, latest))
        active.sort(key=lambda t: t[0])
        chosen = active if limit is None else active[:limit]
        return [f"[{ptype}] {name}" + (f" - latest: {latest}" if latest else "")
                for _, ptype, name, latest in chosen]

    def _key_facts(self, per_category=4):
        """Established plot facts (local/regional/world). per_category=None = all."""
        facts = self.json_ops.load_json("facts.json") or {}
        if not isinstance(facts, dict):
            return []
        out = []
        for cat in ('plot_local', 'plot_regional', 'plot_world'):
            items = facts.get(cat)
            if not isinstance(items, list):
                continue
            chosen = items if per_category is None else items[-per_category:]
            for it in chosen:
                txt = it.get('fact', it.get('text', it.get('event', ''))) if isinstance(it, dict) else str(it)
                if txt:
                    out.append(txt)
        return out

    def _present_npc_voices(self, npcs, location, full=False):
        """Canonical voice lines for NPCs present in the scene.

        Present = party members OR NPCs tagged to the current location. Returns
        [(name, [lines])]; up to 2 lines each unless full. Read-only — never
        touches the stored `context` field (PROTECT canonical-voice extraction).
        """
        if not isinstance(npcs, dict):
            return []
        loc_l = (location or '').lower()
        out = []
        for name, d in npcs.items():
            if not isinstance(d, dict):
                continue
            tags = d.get('tags', {})
            locs = [str(x).lower() for x in tags.get('locations', [])] if isinstance(tags, dict) else []
            present = bool(d.get('is_party_member')) or (bool(loc_l) and loc_l in locs)
            if not present:
                continue
            ctx = d.get('context', [])
            vlines = ctx if isinstance(ctx, list) else ([ctx] if ctx else [])
            vlines = [str(x) for x in vlines if x]
            if not vlines:
                continue
            out.append((name, vlines if full else vlines[:2]))
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


if __name__ == "__main__":
    main()
