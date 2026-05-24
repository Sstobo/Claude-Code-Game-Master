# Decouple D&D 5E from System-Agnostic Core — Design

**Date:** 2026-05-24
**Branch:** `refactor/decouple-5E`
**Scope:** Mechanical decoupling of 5E from `lib/` (thematic content out of scope per user priority).

## Problem

`lib/` is documented as "upstream CORE only — no custom features," but several modules in it bake in D&D 5E assumptions:

- `lib/npc_manager.py` — `PARTY_MEMBER_DEFAULTS` hardcodes STR/DEX/CON/INT/WIS/CHA, AC, HP, attack_bonus, damage. Methods `set_npc_stat`, `update_npc_hp`, `update_npc_xp`, `format_party_status` assume the 5E sheet shape.
- `lib/player_manager.py` — 5E XP thresholds for levels 1–20 hardcoded.
- `lib/validators.py` — `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` use 5E word lists.
- `lib/schemas.py` — `character_sheet` validation expects 5E structure (`hp` as `{current, max}` dict).
- `lib/extraction_schemas.py` — NPC extraction schema has explicit `hp` slot.

`features/` (character-creation, spells, rules, gear, loot, dnd-api) is already 5E-isolated — SRD-API integrations with no dispatch into core tools. Out of scope for this refactor.

The existing module system (`.claude/modules/`) already supports rule replacement: `world-travel` declares `"replaces": ["movement"]` and overrides `dm-session.sh move` via middleware. `inventory-system` replaces `equipment[]` storage. The pattern is proven for rule replacement, not just augmentation.

## Goal

Strip 5E specifics from `lib/`. Move them to a new `.claude/modules/dnd-5e/` ruleset module. Use the existing middleware system as the plugin interface. No new abstractions.

## Non-Goals

- Inventing a `GameSystem` ABC, `StatProvider` protocol, or rule-engine registry.
- Refactoring `features/` (already isolated, user said leave alone).
- Touching `lib/dice.py` (generic dice notation; `d20` is system-agnostic).
- Touching thematic content (plot hooks, narrator styles, etc.).
- Building an alternate ruleset right now. The design must *enable* one, not ship one.

## Architecture

### Two slots, both already exist

1. **`lib/` — system-agnostic core**: entities (NPCs, locations, plots, sessions, time), generic validators (name, dice notation, attitude), opaque storage for system-specific data.
2. **`.claude/modules/dnd-5e/` — ruleset module**: 5E character sheet, XP table, condition/skill/alignment vocab, party-member promotion semantics, formatting that knows about HP/AC/STR.

Tools in `tools/` route through `dispatch_middleware` first, then fall through to core lib. Modules can intercept any action and short-circuit.

### Ruleset vs. add-on module — handled by metadata

Existing module-loader fields cover everything needed:

| Need | Field | Value for `dnd-5e` |
|---|---|---|
| Active by default in new campaigns | `enabled_by_default` | `true` |
| Exactly one ruleset active | `incompatible_with` | `[]` for now (no alt rulesets exist); future rulesets list `dnd-5e` here |
| Categorization | `category` | `"ruleset"` (new value, documentation only) |
| Hard dependency from other modules | `dependencies` | other modules may require `dnd-5e` if they assume HP/AC |

No module-loader code changes required. The `"category": "ruleset"` value is purely for human readability and `dm-module.sh list` grouping.

### What moves where

#### NPC manager (`lib/npc_manager.py` — 948 lines)

**Stays in lib** (system-agnostic NPC management):
- `create_npc`, `update_npc`, `get_npc_status`, `enhance_npc`
- Tag management: `tag_location`, `untag_location`, `tag_quest`, `untag_quest`, `get_tags`
- `is_party_member` flag toggle (just a boolean)
- Opaque `character_sheet` dict storage (lib does not interpret the contents)
- Equipment list as `list[str]` (no slot/weight semantics — that belongs to `inventory-system` module)
- Conditions list as `list[str]` (validation moves out)
- `list_npcs`, `create_batch`

**Moves to `.claude/modules/dnd-5e/lib/npc_5e.py`**:
- `PARTY_MEMBER_DEFAULTS` (the 5E sheet template)
- `promote_to_party_member` 5E sheet initialization (NPC flag stays in core; sheet template is 5E)
- `update_npc_hp` — `hp` as `{current, max}` is 5E
- `update_npc_xp` — XP as a number per character is 5E
- `set_npc_stat` field semantics (`ac`, `level`, `class`, `race`, `attack_bonus`, `damage`, `hp_max`)
- `format_npc_status` party-member section (HP/AC/Stats/Attack lines)
- `format_party_status` (HP/AC summary, CRITICAL threshold at `hp/max <= 1/4`)

**Tool routing change**: `tools/dm-npc.sh` adds `dispatch_middleware "dm-npc.sh" "$ACTION" "$@" && exit $?` after `require_active_campaign` (matches existing pattern in other tools). Module ships `middleware/dm-npc.sh` that handles `promote`, `hp`, `xp`, `set`, `equip`, `unequip`, `condition`, `feature`, `party` and short-circuits. Other actions (`create`, `update`, `status`, `enhance`, `tag-*`, `list`) fall through to core.

`status` and `list` are split-handling: core produces the system-agnostic block; module middleware on `dm-npc.sh.post` appends the 5E sheet section if the NPC is a party member. Use the existing `dispatch_middleware_post` hook (already implemented; world-travel uses it via `dm-time.sh.post`).

#### Player manager (`lib/player_manager.py` — 766 lines)

**Stays in lib**:
- Character file load/save (single-character.json mode + legacy characters-dir mode)
- Generic stat plumbing that doesn't assume specific fields

**Moves to `.claude/modules/dnd-5e/lib/player_5e.py`**:
- `XP_THRESHOLDS` table (lines 21-44 area)
- Any level-up logic that consults XP_THRESHOLDS
- 5E-specific stat semantics (HP, AC, ability scores) currently in player methods

If full method-by-method extraction is too invasive, acceptable fallback: leave the methods in `lib/player_manager.py` but replace the hardcoded XP table with a read from the active ruleset module's `config/xp_thresholds.json` (loaded via `module_loader.is_module_enabled` + path lookup). This keeps `lib/` mechanically agnostic; the 5E data lives in the module. Decide during implementation based on call-site density. **Default to the data-only extraction** (lighter diff, no method signature changes).

#### Validators (`lib/validators.py`)

**Stays in lib**:
- `validate_name` (generic identifier rules)
- `validate_attitude` (friendly/neutral/hostile — universal RPG concept)
- `validate_dice` (notation parser, system-agnostic)

**Moves to `.claude/modules/dnd-5e/lib/validators_5e.py`**:
- `validate_skill` (5E skill list)
- `validate_alignment` (9-axis grid is 5E/AD&D)
- `validate_condition` (5E condition list: charmed/frightened/etc.)
- `validate_damage_type` (acid/bludgeoning/fire/etc. — 5E damage taxonomy)

Grep confirmed these four functions have **no callers** in the current tree. Pure orphan extraction. If the 5E module needs them, it imports from its own copy. If a future caller emerges in `lib/`, that caller violates decoupling and gets re-routed through middleware.

#### Schemas (`lib/schemas.py`)

`validate_npc` is the only 5E-aware part (`character_sheet.hp` shape check, lines ~79-95). Replace with: if `character_sheet` exists, validate it's a dict (opaque). Move the HP-shape check to module-side validation called by the 5E middleware on `promote`/`set`/`hp` paths.

#### Extraction schemas (`lib/extraction_schemas.py`)

NPC schema has explicit `hp` slot. Replace with an opaque `stats` dict (extractors fill whatever they find; ruleset interprets at consumption time). Low-risk change — extraction output is descriptive, not normative.

### Wiring summary

```
tools/dm-npc.sh
  ├── require_active_campaign
  ├── dispatch_middleware "dm-npc.sh" "$ACTION" "$@" && exit $?   ← NEW
  └── (core fallback: calls lib/npc_manager.py with system-agnostic actions only)

.claude/modules/dnd-5e/
  ├── module.json                   (category: ruleset, enabled_by_default: true)
  ├── middleware/dm-npc.sh          (handles promote/hp/xp/set/equip/condition/feature/party)
  ├── middleware/dm-npc.sh.post     (appends 5E sheet to status/list output)
  ├── lib/npc_5e.py                 (5E sheet logic ex-npc_manager)
  ├── lib/player_5e.py              (XP thresholds + level logic)
  ├── lib/validators_5e.py          (skill/alignment/condition/damage_type)
  └── config/
      ├── xp_thresholds.json
      ├── skills.json
      ├── conditions.json
      ├── alignments.json
      └── damage_types.json
```

### Extension to alternate rulesets — what this enables

A future `modules/savage-worlds/` (or whatever) would:
- Declare `"category": "ruleset"`, `"incompatible_with": ["dnd-5e"]`, `"enabled_by_default": false`
- Ship its own `middleware/dm-npc.sh` handling `promote/hp/xp/set` with its own sheet shape (e.g., Trait dice instead of ability scores)
- Ship its own `validators_*.py` for its vocab

No core changes required. That's the test of whether decoupling is real.

## Data Flow

### `dm-npc.sh promote "Carl"` after refactor

1. Bash: `require_active_campaign` (core)
2. Bash: `dispatch_middleware "dm-npc.sh" "promote" "Carl"`
3. Loader checks `dnd-5e` is enabled → invokes `modules/dnd-5e/middleware/dm-npc.sh promote Carl`
4. Module middleware: calls `lib/npc_manager.py set-party-member Carl true` (new minimal core action: just sets the flag, no sheet logic), then calls `modules/dnd-5e/lib/npc_5e.py init-sheet Carl` (writes 5E sheet using `PARTY_MEMBER_DEFAULTS`)
5. Module returns 0 → bash `exit 0`

### `dm-npc.sh create "Grim" "blacksmith" "friendly"` after refactor

1. `require_active_campaign`
2. `dispatch_middleware` — module has no handler for `create` → returns non-zero → fall through
3. Core: `lib/npc_manager.py create "Grim" "blacksmith" "friendly"` — creates system-agnostic NPC entry. No `character_sheet` (none until promoted).

### `dm-npc.sh status "Carl"` after refactor

1. `dispatch_middleware` for `status` → module has no pre-handler → fall through
2. Core: prints system-agnostic block (name, description, attitude, tags, recent events)
3. `dispatch_middleware_post "dm-npc.sh" "status" "Carl"` → module appends 5E sheet section if `is_party_member`

## Error Handling

- If `dnd-5e` is disabled and user runs `dm-npc.sh promote`: middleware refuses to engage, core fallback has no `promote` handler → tool prints `[ERROR] No active ruleset for party-member operations. Enable a ruleset module.` Exit 1.
- If module middleware fails internally: existing `dispatch_middleware` contract preserves exit code; user sees the error from the module.
- Existing 5E NPCs in `npcs.json` (with `character_sheet` populated): no migration required — sheet stays as opaque dict in core storage, module reads/writes it via the same path. Backward compatible.

## Testing

- **Existing test suite must still pass with `dnd-5e` enabled.** This is the primary correctness check.
- **New test**: disable `dnd-5e` for a campaign → `dm-npc.sh create/list/status/tag-*` still work; `promote/hp/set/etc.` print the "no active ruleset" error and exit 1.
- **Lib purity check**: `grep -rE "(hp|AC|STR|DEX|CON|INT|WIS|CHA|attack_bonus|character_sheet|XP_THRESHOLDS)" lib/` returns only opaque-dict storage references, no semantics.
- **Validator extraction**: confirm `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` removed from `lib/validators.py` and no import errors anywhere.

## Implementation Plan (Phased)

Phase 1 — wiring (no behavior change yet):
- Add `dispatch_middleware "dm-npc.sh" "$ACTION" "$@" && exit $?` to `tools/dm-npc.sh`.
- Create `.claude/modules/dnd-5e/` skeleton with `module.json` declaring `enabled_by_default: true`, `category: ruleset`. Empty middleware.

Phase 2 — validators (smallest, lowest-risk extraction):
- Move 5E validators to module. Delete from `lib/validators.py`. Run full test suite.

Phase 3 — NPC party-member methods:
- Move `PARTY_MEMBER_DEFAULTS` + 5E methods to `modules/dnd-5e/lib/npc_5e.py`.
- Strip them from `lib/npc_manager.py`; leave only `set_party_member_flag(name, bool)` and opaque `character_sheet` storage.
- Implement `modules/dnd-5e/middleware/dm-npc.sh` for `promote/hp/xp/set/equip/condition/feature/party`.
- Implement `dm-npc.sh.post` middleware for `status/list` sheet append.

Phase 4 — player_manager XP table:
- Extract XP_THRESHOLDS to `modules/dnd-5e/config/xp_thresholds.json` + level-up logic to module.
- If extraction touches too many call sites, fall back to data-only extraction (lib reads JSON via module-loader path lookup).

Phase 5 — schemas + extraction schemas:
- `lib/schemas.py` `validate_npc` treats `character_sheet` as opaque dict.
- `lib/extraction_schemas.py` NPC schema's `hp` slot becomes opaque `stats` dict.

Each phase commits independently. Tests pass at every phase boundary.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| `dispatch_middleware` call in `dm-npc.sh` breaks unmodified core actions | Phase 1 wires it but ships empty module middleware — core fallback covers all actions until Phase 3 |
| 5E XP extraction is invasive (many call sites in player_manager) | Data-only fallback: leave methods, externalize the table |
| Existing tests assume 5E behavior in lib | Tests stay green because `dnd-5e` is `enabled_by_default: true` — same observable behavior, different code path |
| Module-loader semantics for "must always have one ruleset" not enforced | Acceptable for now: docs say "enable a ruleset"; tools refuse with clear error when none active. Don't add enforcement code until a second ruleset exists |
| `character_sheet` becomes opaque in lib but tools/dm-npc.sh help text still lists 5E fields | Move the help text for `promote/hp/set/etc.` into the module middleware's `--help` handler (existing `dispatch_middleware_help` pattern) |

## YAGNI Boundary

This design adds zero new abstractions. No `GameSystem` ABC. No `Ruleset` interface. No plugin registry. The module-loader already is the plugin registry; middleware dispatch already is the hook system; `"category": "ruleset"` is a string label, not a type.

A future need for richer ruleset orchestration (multi-system character conversion, system-aware UI prompts) can introduce abstractions when the need is concrete. Not now.
