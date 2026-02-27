# TODO — DM System

## Module System (Community Expansion Packs)

### Done

- [x] **Module Registry** — `.claude/modules/registry.json` with metadata for all modules
- [x] **Module Loader** — `lib/module_loader.py` for module discovery and activation
- [x] **Module Structure** — each module is self-contained in `.claude/modules/<name>/`
- [x] **Middleware Architecture** — `dispatch_middleware` / `dispatch_middleware_post` / `dispatch_middleware_help`
- [x] **4 modules created**: custom-stats, world-travel, firearms-combat, inventory-system
- [x] `tools/dm-module.sh list` — show available modules
- [x] `/new-game` asks which modules to enable
- [x] `module.json` manifest with dependencies, middleware declarations, features
- [x] Module rules loaded during gameplay (`rules.md`) and campaign creation (`creation-rules.md`)

### Remaining

- [ ] `tools/dm-module.sh enable/disable` — toggle modules for active campaign
- [ ] Module dependency validation on enable (if module A requires module B)
- [ ] Community docs: module development guide

---

## custom-stats module

### Done

- [x] SurvivalEngine — per-tick stat simulation, conditional effects, threshold consequences
- [x] Sleep/rest mode with `--sleeping` flag
- [x] CLI: `dm-survival.sh tick/status/custom-stat/custom-stats-list`
- [x] Middleware: `dm-player.sh` (show stats), `dm-consequence.sh` (timed triggers)

### Remaining

- [ ] Wire `advance_time()` to `dm-time.sh.post` middleware — currently tick must be called explicitly
- [ ] Fix sleep stat drain during rest (known bug — sleep penalty applies even during sleep)

---

## world-travel module

### Done

- [x] Hierarchical locations (compound/interior with entry points)
- [x] BFS pathfinding with bidirectional connections
- [x] Coordinate system with bearing-based location creation
- [x] GUI map (tkinter) with campaign terrain colors and caching
- [x] Encounter engine with DC scaling by distance/time
- [x] Middleware: `dm-session.sh` (move intercept), `dm-location.sh`

### Remaining

- [ ] Vehicle system — code exists (`vehicle_manager.py`) but full board/exit/move cycle incomplete
- [ ] Submaps for building interiors, ship decks, dungeon floors
- [ ] Encounter generation creates type (Dangerous/Neutral/Beneficial) but DM must narrate — no auto-enemy spawn

---

## firearms-combat module

### Done

- [x] Full-auto combat resolver with RPM calculation, penetration vs protection, crits, XP
- [x] CLI: `dm-combat.sh resolve --weapon AK-74 --ammo 120 --targets "Enemy:13:30:4"`

### Remaining

- [ ] Single fire mode — currently returns "not implemented"
- [ ] Burst fire mode — currently returns "not implemented"
- [ ] Auto-update ammo in inventory after combat (currently manual)
- [ ] Enemy type support (`--enemy-type` flag parsed but not implemented)

---

## inventory-system module

### Done

- [x] Stackable + unique items with atomic transactions and rollback
- [x] Gold, HP, XP tracking
- [x] Loot shorthand: `dm-inventory.sh loot`
- [x] Migration from old `equipment[]` format
- [x] CLI: `dm-inventory.sh show/update/loot`

### Remaining

- [ ] Equipment slots (weapon, armor, accessory)
- [ ] Weight system with carry capacity (STR-based)
- [ ] Transfer items between characters
- [ ] Separate `inventory.json` file (currently stored in `character.json`)
- [ ] Filter by category: `dm-inventory.sh list --category weapon`

---

## Quest System

- [ ] `dm-plot.sh add` — create quests via CLI (currently manual JSON only)
- [ ] `dm-plot.sh objectives` — mark quest objectives as complete
- [ ] `/dm quests` — display active quests to player
