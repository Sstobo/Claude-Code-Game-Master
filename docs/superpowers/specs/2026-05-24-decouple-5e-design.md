# Decouple D&D 5E from System-Agnostic Core — Design

**Date:** 2026-05-24
**Branch:** `refactor/decouple-5E`
**Scope:** Mechanical decoupling of 5E from `lib/`. Thematic content out of scope per user priority.
**Status:** Revised after adversarial review (2026-05-24). Notable revisions:
- Substrate wiring split into its own Phase 0 (the middleware dispatch system is dormant today, not just "called but inert").
- Added migration story for legacy campaigns.
- Added minimal ruleset enforcement at the module-loader (last-ruleset disable + incompatible_with activation check).
- `session_manager.py` added to scope.
- Dropped the "data-only XP fallback" — full extraction.
- `status`/`list` now use pre-dispatch with module-owned routing, not post-hook append.

## Problem

`lib/` is documented in CLAUDE.md as "upstream CORE only — no custom features." Several modules in it bake in D&D 5E assumptions:

- `lib/npc_manager.py` — `PARTY_MEMBER_DEFAULTS` hardcodes STR/DEX/CON/INT/WIS/CHA, AC, HP, attack_bonus, damage. Methods `set_npc_stat`, `update_npc_hp`, `update_npc_xp`, `format_party_status` assume 5E sheet shape.
- `lib/player_manager.py` — `XP_THRESHOLDS` (lines 22-43) and level-up logic (lines 126, 130, 240-261) baked in.
- `lib/validators.py` — `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` use 5E word lists.
- `lib/schemas.py` — `validate_npc` checks `character_sheet.hp` is a `{current, max}` dict.
- `lib/extraction_schemas.py` — NPC extraction schema has explicit `hp` slot.
- `lib/session_manager.py` (lines 365-406) — `get_full_context` reads `character.level/race/class/hp/ac/xp` and `npc.character_sheet.hp/ac/level` directly to format the CHARACTER and PARTY MEMBERS sections of session context.

`features/` (character-creation, spells, rules, gear, loot, dnd-api) is already 5E-isolated — SRD-API integrations with no dispatch into core tools. Out of scope for this refactor.

### Middleware substrate status

CLAUDE.md and TODO.md describe a middleware system where CORE tools delegate to modules via `dispatch_middleware`. **Audit finding: this is aspirational, not active.** `grep -rn dispatch_middleware tools/` returns zero matches. The implementation exists in `.claude/modules/infrastructure/common-advanced.sh` (lines 27, 48, 64) but no `tools/` script sources that file or calls the dispatch functions. World-travel's middleware (`.claude/modules/world-travel/middleware/dm-session.sh`) is dead code at runtime — `tools/dm-session.sh` calls `lib/session_manager.py` directly.

This refactor therefore must wire the substrate, not extend it.

## Goal

Strip 5E specifics from `lib/`. Move them to a new `.claude/modules/dnd-5e/` ruleset module. Activate the existing middleware dispatch substrate. No new abstractions.

## Non-Goals

- Inventing a `GameSystem` ABC, `Ruleset` protocol, or rule-engine registry.
- Refactoring `features/`.
- Touching `lib/dice.py` (notation is generic).
- Touching thematic content (plot hooks, narrator styles, etc.).
- Building an alternate ruleset right now. The design must *enable* one, not ship one.
- Auditing the RAG layer for residual coupling — noted as follow-up.

## Architecture

### Two slots, both already exist

1. **`lib/` — system-agnostic core**: entities (NPCs, locations, plots, sessions, time), generic validators (name, dice notation, attitude), opaque storage for system-specific data.
2. **`.claude/modules/dnd-5e/` — ruleset module**: 5E character sheet, XP table + level-up, condition/skill/alignment vocab, party-member promotion semantics, formatting that knows about HP/AC/STR.

Tools in `tools/` route through `dispatch_middleware` first, then fall through to core lib. Modules can intercept any action and short-circuit.

### Module dispatch — convention

The dispatch contract (`common-advanced.sh:27-44`) is:

- Module middleware exit 0 → handled, short-circuit core.
- Module middleware exit 1 → declined, fall through to next module / core fallback.
- `_module_enabled` gate per-module.

**Convention codified by this design**: a module's middleware file for a tool MUST exit 1 for any action it does not explicitly handle. The `dnd-5e` middleware will own most `dm-npc.sh` actions after decoupling (~9 of 14); the few it does not own (`create`, `update`, `enhance`, `tag-*`, `list` after sheet merge) fall through. Module authors who write `exit 0` on unknown actions silently swallow core actions.

Every tool that calls `dispatch_middleware` MUST also call `dispatch_middleware_help` in its help block. No exceptions — paired rule.

### Ruleset vs. add-on module

Module-loader fields cover everything needed:

| Need | Field | Value for `dnd-5e` |
|---|---|---|
| Active by default in new campaigns | `enabled_by_default` | `true` |
| Categorization (load-bearing, see enforcement below) | `category` | `"ruleset"` |
| Exactly one ruleset active | `incompatible_with` | `[]` initially (no alt rulesets); future rulesets list `dnd-5e` here |
| Hard dependency from other modules | `dependencies` | other modules may require `dnd-5e` if they assume HP/AC |

#### Ruleset enforcement (~10 lines in `module_loader.set_campaign_module`)

Two checks, both keyed off `category == "ruleset"`:

1. **Last-ruleset disable check**: when disabling a module with `category: "ruleset"`, refuse if no other enabled module has `category: "ruleset"`. Error: `[ERROR] Cannot disable last active ruleset. Enable another ruleset first.`
2. **Symmetric activation check**: when activating a module with `category: "ruleset"`, check `incompatible_with` already enforced by the loader. The new ingredient: also refuse if another `category: "ruleset"` is already active and the new one does not list it in `incompatible_with` (defensive — two rulesets can't be silently co-active).

`category` becomes load-bearing once these checks land. Documentation must reflect this.

### Migration for existing campaigns

The substrate has never been wired, so existing campaigns have whatever `campaign-overview.json` they were created with. Three cases:

| Campaign state | `modules` key behavior | Action |
|---|---|---|
| `modules` key absent | `get_campaign_modules` writes `get_default_modules()` on first read (existing behavior, line 130-133) | Phase 1 default includes `dnd-5e: true`. No additional code needed. |
| `modules` key present and contains `dnd-5e` | Honored as-is | No action. |
| `modules` key present but missing `dnd-5e` (created during v1 module era, before this refactor) | Module remains disabled silently → 5E commands would fail | **Backfill (this design)** |

**Backfill logic** lives in `module_loader.get_campaign_modules`. On every read:

```python
mods = data.get("modules", {})
if "modules" in data and "dnd-5e" not in mods:
    # Pre-existing campaign that predates dnd-5e module.
    # Backfill iff campaign has 5E-shape data.
    if _has_5e_shape(campaign_dir):
        mods["dnd-5e"] = True
        data["modules"] = mods
        self._save_overview(path, data)
```

`_has_5e_shape(campaign_dir)` returns true if:
- `npcs.json` contains any entry with `is_party_member: true` or `character_sheet`, OR
- `character.json` exists with any of `hp`, `ac`, `level` fields populated.

Backfill is idempotent: once `dnd-5e` is written into `modules`, the check short-circuits. If the user later disables it explicitly (`dnd-5e: false`), the check also short-circuits (key present, value false ≠ absent).

### What moves where

#### NPC manager (`lib/npc_manager.py` — 948 lines)

**Stays in lib** (system-agnostic NPC management):
- `create_npc`, `update_npc`, `get_npc_status` (returns raw dict, no party-section formatting), `enhance_npc`
- Tag management: `tag_location`, `untag_location`, `tag_quest`, `untag_quest`, `get_tags`
- `set_party_member_flag(name, bool)` — new minimal method, just toggles `is_party_member`. No sheet logic.
- Opaque `character_sheet` dict storage (lib does not interpret contents)
- Equipment list as `list[str]` (no slot/weight semantics — `inventory-system` module owns those)
- Conditions list as `list[str]` (validation moves out)
- `list_npcs` returns raw dicts; module merges sheet info on output
- `create_batch`

**Moves to `.claude/modules/dnd-5e/lib/npc_5e.py`**:
- `PARTY_MEMBER_DEFAULTS`
- `promote_to_party_member` 5E sheet init (calls core `set_party_member_flag(true)` first, then writes sheet)
- `update_npc_hp` (HP-as-{current,max} semantics)
- `update_npc_xp`
- `set_npc_stat` field semantics (`ac`, `level`, `class`, `race`, `attack_bonus`, `damage`, `hp_max`)
- `update_npc_equipment`, `update_npc_condition`, `update_npc_feature` (5E vocab validation)
- 5E formatting for `format_npc_status` (party member section)
- `format_party_status`

**Tool routing**: `tools/dm-npc.sh` adds the dispatch call after `require_active_campaign`. Module ships `middleware/dm-npc.sh` that handles `promote`, `hp`, `xp`, `set`, `equip`, `unequip`, `condition`, `feature`, `party`, `status`, `list`. The middleware exits 1 for `create`, `update`, `enhance`, `tag-*` → core fallback.

For `status`: module middleware calls core `get_npc_status` (raw data), formats system-agnostic block, appends 5E sheet section if party member, prints combined, exits 0.

For `list`: module middleware calls core `list_npcs`, merges per-entry sheet info into the JSON before printing.

Pre-dispatch model is uniform — no `.post` hooks for output assembly.

#### Player manager (`lib/player_manager.py` — 766 lines)

XP coupling sized: 5 sites total (`XP_THRESHOLDS` definition at line 22-43, references at lines 126, 130, 240, 248). Tractable. Full extraction.

**Stays in lib**:
- Character file load/save (single-`character.json` mode + legacy `characters/` dir mode)
- Generic getters/setters that don't interpret 5E fields

**Moves to `.claude/modules/dnd-5e/lib/player_5e.py`**:
- `XP_THRESHOLDS` table
- Level-up logic (the `while new_level < 20 and current_xp >= XP_THRESHOLDS[new_level]` loop and surrounding)
- Any method that consults XP threshold or computes level

`tools/dm-player.sh` gets `dispatch_middleware "dm-player.sh" ...` wiring. Module ships `middleware/dm-player.sh` for XP/level actions.

#### Session manager context (`lib/session_manager.py:365-406`)

`get_full_context` interleaves a CHARACTER block and a PARTY MEMBERS block into session context output. Both read 5E sheet fields directly.

**Approach**: pre-dispatch via `tools/dm-session.sh context`. Core `get_full_context` returns only system-agnostic blocks (header, time, recent events, locations, plot threads — and emits sentinel markers like `<!--RULESET:CHARACTER-->` and `<!--RULESET:PARTY-->` at the points where the ruleset-formatted blocks belong). Module's `middleware/dm-session.sh` (extending world-travel's existing `move`-handler to also handle `context`) intercepts `context`, calls core to get the skeleton, then renders the CHARACTER and PARTY sections at the sentinels using its own 5E formatter. Exit 0.

If `dnd-5e` is disabled (alt ruleset active or none): that module's middleware fills the sentinels. If no ruleset is active (only possible if user defied the enforcement): sentinels are stripped, no character block rendered.

#### Validators (`lib/validators.py`)

**Stays in lib**:
- `validate_name`
- `validate_attitude` (friendly/neutral/hostile — universal RPG concept)
- `validate_dice` (notation parser, system-agnostic)

**Moves to `.claude/modules/dnd-5e/lib/validators_5e.py`**:
- `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type`

Verified zero callers in `lib/`, `tools/`, `features/`, `.claude/modules/`. Pure orphan extraction.

#### Schemas (`lib/schemas.py`)

`validate_npc` currently checks `character_sheet.hp` is a dict (lines ~79-95). After refactor: treat `character_sheet` as opaque dict (no type-shape check). 5E module performs HP-shape validation in `npc_5e.py` on `promote`/`set`/`hp` paths.

**Accepted looseness**: direct JSON edits, batch creates that bypass the module, or extraction outputs land in `npcs.json` without HP-shape validation. The module re-validates at first action that touches the sheet. Per YAGNI, no separate validation-hook dispatch added.

#### Extraction schemas (`lib/extraction_schemas.py`)

NPC schema's `hp` slot becomes opaque `stats: dict`. The shape is unconstrained — extractors emit whatever they find. **The 5E module's NPC initialization (`promote_to_party_member` or first-use normalization) is responsible for translating extracted `stats` dict into the 5E sheet shape.** Without that normalization step, downstream 5E code would have to parse unconstrained input — moving the responsibility into the ruleset module keeps the contract clean.

### Wiring summary

```
tools/dm-npc.sh
  ├── require_active_campaign
  ├── dispatch_middleware "dm-npc.sh" "$ACTION" "$@" && exit $?   ← Phase 0
  └── (core fallback: lib/npc_manager.py — system-agnostic actions only)

tools/common.sh
  └── source "$PROJECT_ROOT/.claude/modules/infrastructure/common-advanced.sh"   ← Phase 0

.claude/modules/dnd-5e/
  ├── module.json                       (category: ruleset, enabled_by_default: true)
  ├── middleware/
  │   ├── dm-npc.sh                     (promote/hp/xp/set/equip/condition/feature/party/status/list)
  │   ├── dm-player.sh                  (XP/level actions)
  │   └── dm-session.sh                 (context renderer — extends or coexists with world-travel's same-name file*)
  ├── lib/
  │   ├── npc_5e.py
  │   ├── player_5e.py
  │   └── validators_5e.py
  └── config/
      ├── xp_thresholds.json
      ├── skills.json
      ├── conditions.json
      ├── alignments.json
      └── damage_types.json
```

*Note on the `dm-session.sh` collision: world-travel already has `middleware/dm-session.sh` for `move`. dispatch iterates all matching middlewares; world-travel handles `move`, declines others (exit 1); dnd-5e handles `context`, declines others. Both modules co-exist on the same tool. Document this in `world-travel/middleware/dm-session.sh` once Phase 0 lands — it currently assumes it owns the file.

### Extension to alternate rulesets — what this enables

A future `modules/savage-worlds/` would:
- Declare `"category": "ruleset"`, `"incompatible_with": ["dnd-5e"]`, `"enabled_by_default": false`
- Ship its own `middleware/dm-npc.sh`, `dm-player.sh`, `dm-session.sh` for sheet/XP/context rendering
- Ship its own `validators_*.py` for its vocab
- Optionally provide a migration tool for converting 5E sheets to its format

No core changes required. That's the test of whether decoupling is real.

## Data Flow

### `dm-npc.sh promote "Carl"` after refactor

1. Bash: `require_active_campaign` (core)
2. Bash: `dispatch_middleware "dm-npc.sh" "promote" "Carl"`
3. Loader checks `dnd-5e` is enabled → invokes `modules/dnd-5e/middleware/dm-npc.sh promote Carl`
4. Module: calls `lib/npc_manager.py set-party-member Carl true` (core flag toggle), then `modules/dnd-5e/lib/npc_5e.py init-sheet Carl` (5E sheet)
5. Exit 0

### `dm-npc.sh create "Grim" "blacksmith" "friendly"` after refactor

1. `require_active_campaign`
2. `dispatch_middleware` — dnd-5e middleware doesn't handle `create` → exit 1
3. No other modules respond → return 1 to core
4. Core: `lib/npc_manager.py create` — system-agnostic NPC entry, no `character_sheet`

### `dm-npc.sh status "Carl"` after refactor

1. `dispatch_middleware` for `status` → dnd-5e middleware:
   - Calls `lib/npc_manager.py get-status-raw Carl` (returns dict)
   - Formats system-agnostic block (description, attitude, tags, recent events)
   - If `is_party_member`, calls `npc_5e.py format-sheet Carl` and appends
   - Prints combined, exit 0

### `dm-session.sh context` after refactor

1. `dispatch_middleware "dm-session.sh" context` → dnd-5e middleware:
   - Calls `lib/session_manager.py get-full-context-skeleton` (no CHARACTER/PARTY sections; sentinels in place)
   - Calls `npc_5e.format-character-block`, `npc_5e.format-party-block`
   - Substitutes sentinels, prints, exit 0
2. World-travel's middleware/dm-session.sh saw `context` first, declined (exit 1) → dispatch continued to dnd-5e.

## Error Handling

- If `dnd-5e` disabled (e.g., user explicitly disabled it post-refactor without enabling a replacement): the last-ruleset enforcement (M1) blocks the disable. So this state is unreachable through the loader. If the user hand-edits `campaign-overview.json` to bypass: 5E commands fall through to core, core has no `promote/hp/etc.` handlers → tool prints `[ERROR] No active ruleset handles this command. Enable a ruleset module.` Exit 1.
- Module middleware failures preserve exit code; user sees the module's error.
- Existing 5E NPCs in `npcs.json` with populated `character_sheet`: no migration needed (sheet stays as opaque dict in core storage; module reads/writes via same path).

## Testing

- **Existing test suite must pass with `dnd-5e` enabled** at every phase boundary. Primary correctness check.
- **Phase 0 specifically**: audit test fixtures for `world-travel: true`. Wiring the substrate activates world-travel's middleware for the first time. If any fixture relies on world-travel's middleware being inert, that fixture fails. **Mitigation**: run `dm-session.sh move <loc>` end-to-end with world-travel enabled before merging Phase 0. If world-travel's middleware is broken/stale, decide: fix it in Phase 0 or temporarily skip its middleware loading.
- **New test (Phase 1)**: disable `dnd-5e` for a test campaign by direct JSON edit (since enforcement prevents loader-based disable when last ruleset). Confirm `dm-npc.sh create/list/status/tag-*` still work; `promote/hp/set/etc.` print the no-ruleset error and exit 1. Confirm enforcement: `dm-module.sh deactivate dnd-5e` refuses with the "last ruleset" message.
- **Migration test**: create a fixture campaign with `modules: {"world-travel": true}` (5E data present, no `dnd-5e` key). Read via `get_campaign_modules`. Assert `dnd-5e: true` backfilled. Re-read. Assert no double-backfill (idempotent).
- **Lib purity check** (CI grep): `grep -rE "(\\bhp\\b|\\bAC\\b|STR|DEX|CON|INT|WIS|CHA|attack_bonus|XP_THRESHOLDS)" lib/` returns only opaque-dict storage references and string literals in deprecated/migration comments, no semantics.
- **Validator extraction check**: `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` removed from `lib/validators.py`. No import errors anywhere.

## Implementation Plan (Phased)

Each phase commits independently. Tests pass at every boundary.

### Phase 0 — substrate wiring (project-wide blast radius, isolated commit)
- `tools/common.sh` sources `.claude/modules/infrastructure/common-advanced.sh`.
- Add `dispatch_middleware "<tool>" "$ACTION" "$@" && exit $?` after `require_active_campaign` to: `dm-npc.sh`, `dm-player.sh`, `dm-session.sh`, `dm-location.sh`.
- Add `dispatch_middleware_help "<tool>"` to each of those tools' help blocks (paired rule).
- Audit world-travel: run `dm-session.sh move` end-to-end with world-travel enabled. Confirm behavior is what its docs claim. Fix any regression here, not in later phases.
- All tests pass.

**Risk-isolated commit. Bisect anchor. If anything breaks weeks later, this is where it started.**

### Phase 1 — dnd-5e skeleton + migration + enforcement
- Create `.claude/modules/dnd-5e/` with `module.json` declaring `enabled_by_default: true`, `category: ruleset`.
- No middleware files yet (or stub files that `exit 1` for all actions). Behavior unchanged.
- Add `category: "ruleset"` to existing modules' `module.json` where applicable — none currently apply, so this is a no-op for now (documentation update only in `module.json` schema notes).
- Add backfill logic to `module_loader.get_campaign_modules` (B2).
- Add last-ruleset enforcement + symmetric activation check to `module_loader.set_campaign_module` (M1).
- Tests pass. Migration test added.

### Phase 2 — validators
- Move `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` from `lib/validators.py` to `modules/dnd-5e/lib/validators_5e.py`. Backed by JSON config files in `modules/dnd-5e/config/`.
- Delete from `lib/validators.py`. No callers to update (verified zero matches repo-wide).
- Tests pass.

### Phase 3 — NPC 5E methods
- Move `PARTY_MEMBER_DEFAULTS` + 5E methods to `modules/dnd-5e/lib/npc_5e.py`.
- Strip from `lib/npc_manager.py`; leave `set_party_member_flag(name, bool)` and opaque `character_sheet` storage. Add raw-data getters (`get_status_raw`, `list_npcs_raw`) for module consumption.
- Implement `modules/dnd-5e/middleware/dm-npc.sh` (pre-dispatch for `promote/hp/xp/set/equip/condition/feature/party/status/list`; `exit 1` for unhandled actions).
- Tests pass.

### Phase 4 — player XP + session_manager context (bundled)
- Extract `XP_THRESHOLDS` + level-up logic from `lib/player_manager.py` to `modules/dnd-5e/lib/player_5e.py`. Sized at 5 sites; full extraction.
- Strip CHARACTER and PARTY MEMBERS sections from `lib/session_manager.py:get_full_context`. Emit sentinels where the ruleset-formatted blocks belong.
- Implement `modules/dnd-5e/middleware/dm-player.sh` (XP/level actions) and `modules/dnd-5e/middleware/dm-session.sh` (context renderer; declines `move` so world-travel handles it).
- Tests pass. World-travel + dnd-5e co-existence on `dm-session.sh` verified.

### Phase 5 — schemas + extraction schemas
- `lib/schemas.py:validate_npc` treats `character_sheet` as opaque dict. HP-shape check removed.
- `lib/extraction_schemas.py` NPC schema's `hp` slot → `stats: dict` (opaque).
- 5E module's `npc_5e.py` handles `stats` normalization on first-touch.
- Tests pass. Lib purity grep check added to CI.

## File Touch Inventory

Per user requirement of minimal refactor, full count:

**Modified**:
- `lib/npc_manager.py` (Phase 3 — large delta, ~half the methods move)
- `lib/player_manager.py` (Phase 4 — 5 XP sites)
- `lib/session_manager.py` (Phase 4 — `get_full_context` strip)
- `lib/validators.py` (Phase 2 — 4 functions removed)
- `lib/schemas.py` (Phase 5 — relax NPC validation)
- `lib/extraction_schemas.py` (Phase 5 — `hp` → `stats`)
- `tools/common.sh` (Phase 0 — source common-advanced.sh)
- `tools/dm-npc.sh`, `tools/dm-player.sh`, `tools/dm-session.sh`, `tools/dm-location.sh` (Phase 0 — dispatch + help wiring)
- `.claude/modules/module_loader.py` (Phase 1 — backfill + enforcement)
- `.claude/modules/world-travel/middleware/dm-session.sh` (Phase 4 — declare co-existence with dnd-5e)
- `tests/conftest.py` or per-test fixtures (test additions)
- `docs/python-modules-api.md` (update with module dispatch contract)

**New**:
- `.claude/modules/dnd-5e/module.json`
- `.claude/modules/dnd-5e/middleware/dm-npc.sh`
- `.claude/modules/dnd-5e/middleware/dm-player.sh`
- `.claude/modules/dnd-5e/middleware/dm-session.sh`
- `.claude/modules/dnd-5e/lib/npc_5e.py`
- `.claude/modules/dnd-5e/lib/player_5e.py`
- `.claude/modules/dnd-5e/lib/validators_5e.py`
- `.claude/modules/dnd-5e/config/xp_thresholds.json`
- `.claude/modules/dnd-5e/config/skills.json`
- `.claude/modules/dnd-5e/config/conditions.json`
- `.claude/modules/dnd-5e/config/alignments.json`
- `.claude/modules/dnd-5e/config/damage_types.json`

Total: ~13 modified + ~12 new = ~25 files touched across 6 phases. That's the honest size of "decouple 5E while wiring a dormant substrate" — not the ~16 the first draft implied.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Phase 0 wiring activates dormant world-travel middleware → unexpected behavior | World-travel canary test in Phase 0 acceptance criteria. Fix or skip its middleware loading in Phase 0, not later. |
| Legacy campaign loses 5E commands after upgrade | Backfill in `get_campaign_modules` (B2), idempotent. Tested. |
| User disables `dnd-5e` and breaks campaign | Last-ruleset enforcement at loader (M1). Hand-edited JSON bypass surfaces clear error message. |
| Validator removal breaks an import not caught by grep | Phase 2 is small + tested. Run full test suite. If a hidden caller exists, restore stub that imports from module. |
| `lib/schemas.py` validation loss on direct JSON edits | Accepted looseness; module re-validates on first action. No separate validation-hook dispatch added per YAGNI. |
| Player manager XP extraction larger than expected | Sized at 5 sites — verified. If discovery during Phase 4 reveals more coupling, escalate phase scope before merging. |
| World-travel and dnd-5e collide on `dm-session.sh` middleware | Dispatch iterates all matching middlewares; each declines actions it doesn't own. Both modules document co-existence. |
| RAG / context-injection paths read 5E fields directly | Out of scope this refactor. Tracked as follow-up. Grep audit (`grep -rE "(character_sheet|\bhp\b|\bac\b|\bxp\b)" lib/ tools/ --include="*.py" --include="*.sh"`) post-Phase-5 to confirm scope of follow-up. |

## YAGNI Boundary

This design adds zero new abstractions. The module-loader is the plugin registry. Middleware dispatch is the hook system. `category: "ruleset"` is a string field read by ~10 lines of enforcement code, not a new type.

A future need for richer ruleset orchestration (multi-system character conversion, system-aware UI prompts) can introduce abstractions when the need is concrete. Not now.
