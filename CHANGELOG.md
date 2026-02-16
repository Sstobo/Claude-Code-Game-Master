# Changelog

All notable changes to DM System will be documented in this file.

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
