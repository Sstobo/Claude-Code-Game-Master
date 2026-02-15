# Changelog

All notable changes to DM System will be documented in this file.

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
