---
slug: canvas-view-panel
title: Canvas view panel — persistent ASCII/ANSI second-pane game view
status: active
version: 1
supersedes: null
createdAt: 2026-06-06T16:06:57Z
updatedAt: 2026-06-06T16:06:57Z
---

## Problem Statement

The conversation scrolls; the status-bar HUD (`tools/dm-statusline.sh`) is a fixed
2-4 line strip. Neither gives a persistent, full-size surface the DM can *draw*
into — dungeon maps, combat positioning, scene art — or where party/location/combat
status stays put while play continues. Maps drawn inline vanish on the next action.

## Solution

A **canvas**: a persistent panel rendered in a SECOND terminal pane (the player runs
a VS Code split terminal → `bash tools/dm-view.sh watch`). A polling file-watcher
redraws the pane whenever campaign state changes. It shows an agent-drawn **SCENE**
region (raw ASCII passthrough, ANSI color allowed) plus **auto-derived** panels —
PARTY, HERE, and COMBAT — read live from existing state files. Auto panels need zero
agent effort (same philosophy as the HUD); the agent only ever writes the freeform scene.

## User Stories

1. As a player, I want a second pane that shows the current scene/map and party status, so the game feels like a cockpit instead of a scrolling log.
2. As the DM (agent), I want to push a drawn map/scene to the canvas with one command, so spatial state persists without me redrawing it every turn.
3. As a player in combat, I want enemy initiative + HP to appear automatically, so the tracker is always truthful (no model-memory drift).

## Implementation Decisions

- **New:** `lib/view_manager.py` (`ViewManager(EntityManager)` for the write path; module-level functions for the read/watch path) and `tools/dm-view.sh` (wrapper mirroring `dm-location.sh`; subcommands `scene` / `clear` / `watch` / `render`).
- **View state:** `world-state/campaigns/<active>/view.json` = `{title, body, updated}` — only the agent-authored scene. Panels are derived live (never stored stale). Atomic write via `lib/json_ops.py` `save_json` (temp+rename). Already gitignored.
- **Read/watch path must NOT use `EntityManager`** — its `__init__` *raises* when no campaign is active (`lib/entity_manager.py:41`). Resolve the dir directly via `CampaignManager("world-state").get_active_campaign_dir()` (returns `None` gracefully). `EntityManager` is used only for the `scene`/`clear` writes (guarded by `require_active_campaign`).
- **Scene body:** read from stdin (avoids multi-line ASCII shell-escaping). Strip C0 control chars `< 0x20` EXCEPT `\n`, `\t`, ESC `0x1b` (keep color, drop CR/BEL). Cap ~64 KB.
- **Auto panels (live-derived):**
  - PARTY — player from `character.json` + every `npcs.json` entry with `is_party_member: true` (stats at `character_sheet.{hp,ac,level,conditions}`); HP bar logic + 256-color palette ported verbatim from `tools/dm-statusline.sh` (green ≥50%, amber ≥25%, red <25%, `█`/`░`).
  - HERE — current location (`campaign-overview.json` `player_position.current_location`, fallback `character.json.current_location`) + its `locations.json` `connections` (`{to, path}`; may be `[]`). Omit the long `position` paragraph.
  - COMBAT — **enabled by the now-shipped `combat-state-persistence`**: when `combat_state.json` is active, render combatants by `initiative` with HP bars, `side`, and `round`. Hidden when no active combat. Schema: `{active, round, turn_index, combatants:[{name,hp_current,hp_max,ac,conditions,initiative,side}]}`.
- **Watcher:** 0.25s poll of an mtime signature over the relevant files + campaign name + terminal size; redraw only on change; alternate-screen buffer + cursor-home/clear-to-end (no flicker); clean SIGINT restore. Polling, not `watchdog`/inotify (zero new deps, macOS, trivially cheap; atomic writes make a single read coherent).
- **Render:** `compose_frame(state, cols, rows)` sized to `shutil.get_terminal_size` (clamp cols `[40,200]`). Helpers `visible_len` (strip `\x1b\[[0-9;]*m`) and `clip_visible` (clip on visible chars, keep escapes, append RESET). PARTY|HERE side-by-side at `cols ≥ 72`, else stacked. No-campaign → centered placeholder; loop keeps polling and lights up on activation.
- **Agent note:** one optional block in the lean CLAUDE.md (old "When to Draw Maps" anchor is gone post lean-core; place near Output Format or in the `dm-dungeon`/`dm-craft` skill). Auto panels need nothing; the agent only writes the scene.

## Testing Decisions

- **agent lane** (pytest, DCC fixture): writer round-trip (atomic, ANSI kept, ctrl stripped, body cap); `render` one-shot output asserts header/PARTY/HERE/COMBAT content + edge cases (`conditions: null`, party member w/o `character_sheet`, `hp.max==0`, empty connections, no-campaign placeholder); COMBAT panel from a seeded `combat_state.json`.
- **manual lane** (human eyeball): the watch loop — live redraw within ~250 ms on a state edit, alt-screen enter/exit, Ctrl+C restores cursor + scrollback, pane resize re-layout. These are interactive/visual and can't be asserted in code.
- Prior art: `tests/test_combat_manager.py` (reload-from-disk pattern), `tools/dm-statusline.sh` (palette/HP-bar to port).

## Out of Scope

- Real images / kitty/iTerm graphics protocol (ASCII/ANSI only).
- tmux/iTerm auto-split launchers (VS Code split terminal is the target; command is terminal-agnostic).
- A structured-JSON scene format / renderer (raw ASCII passthrough chosen).
- Wiring the canvas as a Claude Code hook or status line (user-launched process).
- Campaign-specific overlays (e.g. the DCC viewer-count/leaderboard broadcast panel) — fun, deferred.

## Further Notes

- No new Python deps (stdlib only; no `wcwidth` → `len()` on ANSI-stripped text; minor wide-glyph misalignment accepted — keep emoji minimal like the HUD).
- No `.claude/settings.json` change.
- Reuse, do not reinvent: `tools/common.sh`, `EntityManager`, `JsonOperations`, `CampaignManager`, and the HUD palette.
