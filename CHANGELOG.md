# Changelog

All notable changes to DM System will be documented in this file.

## [2.1.0] - 2026-02-21

### Added
- **Hierarchical location system** — world → compound → interior with parent/children tree, entry points, and nested navigation
  - `hierarchy_manager.py` — core API: `create_compound`, `add_interior`, `enter_compound`, `exit_compound`, `move_interior` (BFS reachability), `get_tree`, `get_ancestors`, `validate_hierarchy`
  - `dm-hierarchy.sh` — CLI: `create-compound`, `add-room`, `enter`, `exit`, `move`, `tree`, `entry-config`, `validate`
  - `force_layout.py` — force-directed graph layout for interior views (spring algorithm, 100 iterations, entry point edge anchoring)
  - `migrate_to_hierarchy.py` — migration script: converts `_vehicle` fields to hierarchy format with backup
  - 60 new tests in `test_hierarchy_manager.py` (compounds, interiors, enter/exit, BFS, tree, ancestors, entry points, validation, cycles)
- **Entry point system** — `is_entry_point` + `entry_config` on interior locations: `on_enter`, `on_exit` events, `locked`, `hidden`, `leads_to` for DM guidance
- **Location stack** (`location_stack` in `player_position`) — automatic breadcrumb trail computed from parent chain on every move

### Changed
- **`map_gui.py`** — dual-mode rendering: global view (world + top-level compounds) and interior view (force-directed layout of children). Compounds render as squares. Double-click to drill down, ESC to go up. Breadcrumb bar at top with clickable navigation.
- **`location_manager.py`** — new kwargs on `add_location()`: `parent`, `location_type`, `is_entry_point`, `entry_config`, `children`. New methods: `get_parent()`, `get_children()`. `list_locations()` supports `parent` filter and `top_level` flag. All backward-compatible.
- **`session_manager.py`** — `move_party()` computes `location_stack` via parent chain. `_ensure_location_and_connection()` scope-aware: no auto-connections between interior↔world.
- **`vehicle_manager.py`** — dual-write: sets both `_vehicle` fields and hierarchy fields (`type`, `parent`, `children`, `entry_points`). Existing vehicle tests unchanged.
- **`dm-session.sh` middleware** — hierarchy-aware move: if target is compound, routes to `enter_compound` before vehicle check.

### Technical
- 265 tests, all green (was 205)
- Location types: `world` (coordinate point), `compound` (container with children), `interior` (room/zone inside compound)
- Hierarchy validation detects: parent cycles, orphan children, parent↔child desync
- Force layout: repulsion (Coulomb), attraction (spring), edge anchoring for entry points, damping 0.9

## [2.0.0] - 2026-02-21

### Added
- **Narrator style system** — 4 built-in narrative styles with voice, pacing, and forbidden patterns
  - `dm-narrator.sh` — CLI: `list`, `recommend`, `apply`, `show`, `remove`
  - `.claude/narrator-styles/` — epic-heroic, horror-atmospheric, sarcastic-puns, serious-cinematic
  - Phase 1.7 in `/new-game` — narrator style selection menu with genre-based recommendation

### Changed
- **`/dm-continue`** — rules now load via Read tool (`/tmp/dm-rules.md`) instead of inline Bash to avoid truncation
- **`dm-active-modules-rules.sh`** — rewritten for reliability

## [1.9.0] - 2026-02-19

### Added
- **Vehicle system in `world-travel`** — dual-map transport: global anchor location + internal rooms on local map. Works for ships, cities, trains, dungeons — anything with an "inside".
  - `dm-vehicle.sh` — CLI: `create`, `add-room`, `board`, `exit`, `move`, `status`, `map`, `list`
  - `lib/vehicle_manager.py` — `VehicleManager` class with full API
  - `stationary` flag on vehicle — prevents accidental `move` (use for cities, buildings)
  - Internal movement via `dm-session.sh move` — middleware intercepts when `map_context=local`, no encounter/time tick
  - Vehicle movement rebuilds external connections by proximity radius (terrain="docking")
  - Player inside vehicle travels with it; player outside gets `player_status: "outside"` warning
  - Boarding another vehicle (ship-to-ship transfer) supported via `exit` → `move` to anchor → `board`
- **`_find_project_root()`** in `vehicle_manager.py` and tests — walks up to `pyproject.toml` instead of fragile `parent.parent.parent...` chains

### Changed
- **`world-travel` middleware `dm-session.sh`** — vehicle check injected before navigation: if player is in `local` map context and destination is a vehicle room, routes to `move-internal` instead of navigation
- **`world-travel/rules.md`** — Part 3 added: full vehicle system docs in English (create, board, exit, move, city/stationary, ship switching, data schema)

## [1.8.0] - 2026-02-19

### Fixed
- **`world-travel`: connections not created on `dm-location.sh add`** — `add_canonical_connection()` silently returned if the new location wasn't yet in `locations_data`. Fixed by inserting the location stub into the dict before calling `add_canonical_connection`, so both endpoints exist at the time of connection creation.

### Added
- **`dm-module.sh list-verbose`** — detailed module listing with status, description, genre tags, and top-3 use cases. Used by `/new-game` module selection menu.
- **Module selection phase in `/new-game`** (Phase 1.5) — after campaign creation, DM presents a numbered toggle menu of all available modules; activates/deactivates per player choice; loads rules into context before world-building continues.
- **Slot-based rules system** (`tools/dm-active-modules-rules.sh` rewrite) — game rules are now loaded from `.claude/dm/slots/*.md` in alphabetical order. Modules declare `"replaces": ["slot-name"]` in `module.json` to override a core slot with their own rules; addon modules (no `replaces`) are appended after all slots. Conflict detection included.
- **`replaces` field** in all `module.json` manifests — `world-travel` replaces `movement` slot; others have empty `replaces: []`.
- **`post_middleware` field** in `registry.json`** for `custom-stats` — documents that `dm-time.sh.post` fires after CORE time advance (already wired, now formally in registry).

### Changed
- **`/dm` command** — stripped down to campaign selection menu only; no longer loads rules or narrates. Rules load happens in `/dm-continue` after campaign switch.
- **`dm-campaign.sh switch`** — now calls `dm-active-modules-rules.sh` automatically after switching, so module rules are always fresh in context.
- **`module.json` formatting** — all modules: arrays expanded to multiline JSON for readability; trailing newline added.
- **`ensure_ascii=False`** added to all remaining `json.dump()` calls in `lib/campaign_manager.py`, `lib/session_manager.py`, `features/character-creation/save_character.py` — Cyrillic names no longer get `\uXXXX`-escaped in saved files.
- **`registry.json`** — `custom-stats` middleware list updated: `dm-time.sh` removed (was pre-hook), `dm-time.sh.post` added to `post_middleware`.

## [1.7.0] - 2026-02-19

### Added
- **`world-travel` module** — merge of `coordinate-navigation` + `encounter-system` into one module. `dm-session.sh` middleware intercepts `move`, calculates distance, and auto-runs encounter check. Single module to install for spatial world simulation.
- **`custom-stats` module** (renamed from `survival-stats`) — hardcoded hunger/thirst removed. Now supports any stat: mana, sanity, oxygen, reputation, etc. Zero hardcoded field names.
- **Module `activate` / `deactivate` commands** (`tools/dm-module.sh`) — enable or disable modules per campaign with dependency checking (can't activate if dependency is off; can't deactivate if dependents exist).
- **`_module_enabled()` helper** in `tools/common.sh` — reads `campaign-overview.json["modules"]` as single source of truth.
- **`dispatch_middleware_post()` helper** in `tools/common.sh` — post-hook pattern: called after CORE completes, not instead of it.
- **`--elapsed <hours>` flag** for `lib/time_manager.py` — stores `total_hours_elapsed` in campaign-overview. Advance time auto-ticks timed consequences.
- **Timed consequences** in `lib/consequence_manager.py` — `add --hours <N>` numeric trigger, `tick <hours>` counts down and fires at ≤ 0. `check` now shows `(in 3.0h)` for timed events.
- **`dm-time.sh --elapsed` flag** and post-hook wiring.
- **`dm-consequence.sh tick` command** and `--hours` flag.
- **`add_plot()` in CORE** (`lib/plot_manager.py`) — moved from quest-system module. `dm-plot.sh add` is now vanilla CORE, no module required.
- **`README.md` in each module** (`custom-stats`, `firearms-combat`, `inventory-system`, `world-travel`) — human-readable docs with CORE vs module tables, command examples, configuration reference.

### Changed
- **`lib/module_loader.py` rewritten** — single source of truth: `campaign-overview.json["modules"]`. `activate`/`deactivate` with full dependency graph validation.
- **`lib/campaign_manager.py`** — campaign creation initializes `modules` dict from module defaults.
- **`module.json` standardized** across all modules — removed junk fields, added `genre_tags`, `middleware`, `features`, `adds_to_core`, `use_cases`, `architecture`, `post_middleware`.
- **`custom-stats` middleware** switched to post-hook pattern (`dm-time.sh.post`) — called after CORE, reads `--elapsed` from args, ticks custom stats. No duplication, no direct CORE calls from middleware.
- **`features/character-creation/save_character.py`** — stat normalization: `constitution→con`, `strength→str`, etc.
- **`tools/dm-player.sh`** — `save-json` now reads from stdin instead of argument (fixes quoting edge cases).
- **`tests/test_time_effects.py`** — updated for new `update_time()` return type (`dict` instead of `bool`).
- **`tests/test_survival_engine.py`** — fixed import path (`survival-stats` → `custom-stats`).

### Removed
- **`quest-system` module** — `add_plot()` promoted to CORE `lib/plot_manager.py`. Quest/plot creation no longer requires a module.
- **`coordinate-navigation` and `encounter-system` modules** — merged into `world-travel`.
- **`survival-stats` module** — replaced by `custom-stats` (same engine, no hardcoded stat names).

### Technical
- 166 tests, all green.
- `world-travel` middleware uses `dispatch_middleware_post` pattern — CORE move runs first, then encounter check on distance.
- Module dependency graph: `world-travel` has no deps; `custom-stats` requires nothing; `firearms-combat` and `inventory-system` are standalone.

## [1.6.0] - 2026-02-18

### Added
- **Module mod selection at campaign creation** — DM scans available modules via `dm-module.sh list` and presents a numbered menu to the player; reads `adds_to_core.data_fields` from each `module.json` and patches `campaign-overview.json` / `character.json` automatically
- **Module rules auto-injection** — `/dm` now injects all module `rules.md` files into context at startup via `!cat` in `dm.md`; DM knows all module mechanics from turn one
- **Separate dev/game context** — `CLAUDE.md` contains dev rules only; game rules live in `.claude/rules/dm-rules.md` and are loaded exclusively via `/dm` skill
- **Middleware help text** — all module middlewares support `--help` flag and expose their actions dynamically; CORE tool `--help` outputs are now module-aware

### Changed
- `CLAUDE_game.md` moved to `.claude/rules/dm-rules.md`; `CLAUDE.md` reset to minimal dev rules
- `dm.md` skill injects `dm-rules.md` + all module `rules.md` via `!cat` at startup
- Module creation checklist in `dm-rules.md` now instructs DM to scan modules dynamically instead of hardcoding a fixed list

### Removed
- Hardcoded module list from `dm-rules.md` (replaced with dynamic scan instruction)

## [1.5.0] - 2026-02-17

### Added
- **Module System** — optional campaign features extracted into self-contained modules in `.claude/modules/`
  - `coordinate-navigation` — PathManager, PathFinder, path intersections, map rendering (ASCII & GUI)
  - `encounter-system` — travel encounter checks with distance-based DC scaling
  - `firearms-combat` — automated firearms resolver with fire modes, PEN/PROT, RPM
  - `survival-stats` — time effects engine, per-tick simulation, conditional effects, sleep restoration
- **Module Loader** (`lib/module_loader.py`) — discovers and validates installed modules
- **Module CLI** (`tools/dm-module.sh`) — list, info, and status for installed modules
- **Module Registry** (`.claude/modules/registry.json`) — central manifest of available modules
- **Navigation Module CLI** (`dm-navigation.sh add`) — coordinate-based location creation with auto-connection and path splitting

### Changed
- **CORE decoupled from modules** — `lib/` has zero imports of module code (no PathManager, PathFinder, encounter_manager, combat_resolver)
- `session_manager.py` — `move_party()` simplified to direct-connection lookup via `connection_utils`; removed PathManager routing, blocked/needs_decision handling
- `location_manager.py` — `add_location()` simplified to CRUD; coordinate params (`--from/--bearing/--distance`) delegate to navigation module via `dm-location.sh`
- `time_manager.py` — survival stats logic (`_apply_time_effects`, `_check_stat_consequences`, `sleeping` flag) moved to survival-stats module engine
- `dm-location.sh` — `add --from` auto-delegates to navigation module; decide/routes/block/unblock delegate to `dm-navigation.sh`
- `dm-combat.sh`, `dm-encounter.sh`, `dm-map.sh`, `dm-time.sh` — delegate to respective module wrappers

### Removed
- `lib/combat_resolver.py` — moved to `.claude/modules/firearms-combat/`
- `lib/encounter_manager.py` — moved to `.claude/modules/encounter-system/`
- `lib/path_manager.py` — moved to `.claude/modules/coordinate-navigation/`
- `lib/pathfinding.py` — moved to `.claude/modules/coordinate-navigation/`
- `lib/path_intersect.py` — moved to `.claude/modules/coordinate-navigation/`
- `lib/path_split.py` — moved to `.claude/modules/coordinate-navigation/`
- `lib/map_renderer.py` — moved to `.claude/modules/coordinate-navigation/`
- `lib/map_gui.py` — moved to `.claude/modules/coordinate-navigation/`
- `lib/location_manager.py.backup` — cleanup

### Technical
- CORE `lib/` reduced from 11 files to 3 changed files + 8 deleted (moved to modules)
- Each module is self-contained: own `lib/`, `tools/`, `tests/`, `module.json`, `rules.md`
- Modules import CORE utilities (`json_ops`, `connection_utils`); CORE never imports modules
- 73 module tests passing across all 4 modules

## [1.4.0] - 2026-02-17

### Added
- **Unified Inventory Manager** (`dm-inventory.sh`) — atomic transaction system for character state changes
  - Multi-flag operations: `--gold`, `--hp`, `--xp`, `--add`, `--remove`, `--add-unique`, `--remove-unique`, `--set`, `--custom-stat`
  - All changes apply together or fail together (rollback on error)
  - `--test` flag for validation without applying changes
  - Stackable items system (consumables with quantities: Medkit x3, Ammo 9mm x60)
  - Unique items system (weapons, armor, quest items — one entry per item)
  - Auto-migration from old `equipment` array format to new `stackable`/`unique` structure
  - Creates timestamped backup on first migration
  - Validates gold/HP bounds, item quantities, custom stat min/max
- **Combat Resolver** (`dm-combat.sh`) — automated firearms combat system for modern/STALKER campaigns
  - Calculates rounds per D&D turn (6 sec) based on weapon RPM
  - Fire modes: `single`, `burst`, `full_auto` with progressive attack penalties
  - Accounts for Стрелок subclass bonuses (reduced penalties)
  - Detailed shot-by-shot output: d20 roll, modifier, hit/miss, damage dice, raw damage, PEN vs PROT scaling, final damage
  - Auto-persists ammo consumption and XP awards
  - `--test` flag to preview combat without updating character state
  - Supports manual target specification or enemy type lookup from `campaign_rules`
- **Modern Firearms Campaign Template** (`.claude/modules/firearms-combat/templates/modern-firearms-campaign.json`)
  - Pre-configured weapons (АКМ, АК-74, M4A1, SVD, PMm, etc.) with RPM, damage, PEN values
  - Fire mode definitions with attack penalties
  - Armor types with PROT ratings
  - Custom survival stats (hunger, thirst, radiation, sleep)
  - Time effects with hourly stat changes
  - Encounter system configuration
  - Sample enemies (snorks, bandits, mercenaries) with AC/HP/PROT
- **Plot Manager Enhancements**
  - `dm-plot.sh add` command for creating new plots/quests
  - Support for plot types (main, side, personal, faction)
  - Structured fields: description, NPCs, locations, objectives, rewards, consequences
- **Consequence Manager Improvements**
  - Time-remaining display for timed consequences
  - Shows "IMMINENT!" when trigger time has passed
  - Human-readable time format (minutes, hours, days)

### Changed
- **CLAUDE.md** — comprehensive documentation updates
  - Added "Firearms Combat" section with combat resolver usage
  - Added "Unified Inventory Manager" section with multi-flag examples
  - Added "Inventory Manager Flags Reference" with complete flag documentation
  - Prioritized unified manager over legacy commands in State Persistence section
  - Added inventory auto-migration notes to Technical Notes
  - Updated Combat Resolution workflow to show `--test` flag usage
- **Dungeon Location Creation** — changed from automatic to manual
  - `dm-session.sh move` no longer auto-creates dungeon locations
  - DM must manually create dungeon rooms with `dm-location.sh add` before moving
  - Prevents accidental location bloat in structured dungeons

### Fixed
- Type hints consistency across managers (`Optional[str] = None` instead of `str = None`)
- Consequence list display showing trigger conditions properly

### Technical
- New modules: `lib/combat_resolver.py` (18KB), `lib/inventory_manager.py` (24KB)
- Bash wrappers: `tools/dm-combat.sh`, `tools/dm-inventory.sh`
- Combat resolver uses character subclass detection for attack penalty modifiers
- Inventory manager uses deepcopy snapshots for rollback capability
- PEN vs PROT damage scaling: `FULL (100%)` → `HIGH (75%)` → `REDUCED (50%)` → `MINIMAL (25%)`

## [1.3.0] - 2026-02-16

### Added
- `--sleeping` flag for `dm-time.sh` — inverts sleep stat drain to restoration during rest (configurable `sleep_restore_per_hour`, default 12.5/hr)
- Conditional time effects — rules in `time_effects.rules[]` now support a `condition` field (e.g. `"hp < max"`, `"stat:hunger > 0"`) that gates whether the effect applies
- Condition parser supports: `hp`, `stat:<name>`, operators `< <= > >= == !=`, values or `max` keyword
- Auto-split paths — adding a location with coordinates now automatically splits existing paths that geometrically pass through the new point
- `TODO.md` — development roadmap with planned inventory weight/slots system

### Changed
- **Time effects use per-hour tick simulation** — instead of batch-multiplying `per_hour × elapsed`, the engine now simulates hour-by-hour, re-evaluating conditions each tick. This means conditional effects (like artifact healing) correctly stop mid-period when their condition becomes false
- `_apply_time_effects()` refactored: snapshot → simulate on deepcopy → apply deltas to real character in one batch
- `CLAUDE.md` — added process rules section (changelog/commit hygiene)

### Fixed
- Sleep stat draining during rest instead of restoring
- Conditional effects evaluated once for entire period instead of per-tick (artifact would radiate for full 8 hours even after HP reached max on hour 4)
- Effects within same tick no longer affect each other's conditions (snapshot-per-tick isolation)

## [1.2.0] - 2026-02-16

### Added
- `lib/connection_utils.py` — canonical connection management module (single source of truth for all location edges)
- `tools/migrate-connections.py` — migration script for deduplicating bidirectional connections (`--dry-run` / `--apply`)
- `dm-location.sh connect` now accepts `--terrain` and `--distance` flags

### Changed
- **Connections are now stored once** — in the alphabetically-first location of the pair. All modules read edges through `connection_utils` helpers, which reconstruct reverse direction (bearing +180°) on the fly
- `dm-session.sh move` **no longer auto-creates connections**. If no path exists between two known locations, it rejects the move and suggests `dm-location.sh connect`
- Map renderers (`map_renderer.py`, `map_gui.py`) use `get_unique_edges()` — each line drawn exactly once
- Pathfinding (`pathfinding.py`, `path_manager.py`) uses canonical connection API
- `path_split.py` delegates to `add/remove_canonical_connection()`
- `encounter_manager.py` waypoints use `add_canonical_connection()`
- `world_stats.py` and `search.py` use `get_connections()` for accurate counts

### Fixed
- Double line rendering on maps (edges were drawn from both sides)
- Connection data desync (one side had terrain/distance, reverse had bare `"traveled"`)
- `ensure_ascii=False` added to all `json.dumps()` calls across 15+ files — Russian text no longer escaped as `\uXXXX`
- Duplicate custom stats output in `time_manager._print_time_report()`

### Technical
- `canonical_pair(a, b)` — alphabetical ordering determines storage location
- `get_connections(loc, data)` — returns forward + reverse edges with auto-flipped bearing
- `get_connection_between(a, b, data)` — O(n) lookup for specific edge
- `get_unique_edges(data)` — deduplicated edge list for renderers
- `add/remove_canonical_connection()` — single-point mutation API

## [1.1.0] - 2026-02-15

### Added
- `map.sh` — quick launcher for GUI map from project root
- Refresh button on GUI map (bottom-right corner, also R key)
- Terrain colors now loaded from campaign (`terrain_colors` in `campaign-overview.json`)
- Custom terrain types per campaign (e.g. `industrial` for STALKER)
- Terrain generation timer in logs and on-screen (`Terrain: X.Xs`)
- Test fantasy campaign "Forgotten Realms — Sword Coast" with 20 locations

### Changed
- Terrain surface auto-scales to max 2000px — large maps no longer take 30+ seconds
- Zoom-in rendering uses `subsurface` crop — no more lag when zoomed in close
- Min zoom reduced to 0.01x — can see entire map at once
- Terrain colors fallback to defaults if campaign doesn't define them

### Fixed
- Viewport-based terrain rendering eliminates frame drops at high zoom levels
- Large maps (30km+) no longer create 25M+ pixel surfaces

### Technical
- `MAX_TERRAIN_PIXELS = 2000` caps terrain surface dimensions
- `meters_per_pixel` auto-calculated from world bounds
- `sample` rate auto-scaled to world size
- `draw_terrain_background()` crops to visible screen area before scaling

## [1.0.0] - 2026-02-12

### Initial Release
- AI Dungeon Master for D&D 5e campaigns
- Campaign management (create, switch, list)
- PDF/document import with RAG search
- Interactive Pygame GUI map with terrain visualization
- Custom stats & time effects system
- Coordinate navigation with bearing/distance
- Encounter system v6.0 for travel
- NPC management with tags and party system
- Consequence tracking with timed triggers
- Session save/restore system
- Specialist agent integration (monster-manual, spell-caster, etc.)
