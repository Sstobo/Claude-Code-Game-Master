# Decouple D&D 5E from System-Agnostic Core — Design

**Date:** 2026-05-24
**Branch:** `refactor/decouple-5E`
**Scope:** Logical decoupling of 5E mechanics from `lib/`. Thematic content out of scope per user priority.
**Status:** Rewritten after second adversarial review revealed a wrong architectural direction. Previous draft proposed reviving deleted bash middleware (commit `b0a8960` removed it deliberately). This revision uses an in-process Python registry — no bash middleware involved, no `tools/` changes, no `module_loader` changes.

## Problem

`lib/` is documented in `CLAUDE.md` as "upstream CORE only — no custom features." Several modules in it bake in D&D 5E assumptions:

- `lib/npc_manager.py` — `PARTY_MEMBER_DEFAULTS` hardcodes STR/DEX/CON/INT/WIS/CHA, AC, HP, attack_bonus, damage. Methods `set_npc_stat`, `update_npc_hp`, `update_npc_xp`, `format_party_status` assume the 5E sheet shape.
- `lib/player_manager.py` — `XP_THRESHOLDS` (lines 22-43) and level-up logic (lines 126, 130, 240-261) baked in.
- `lib/validators.py` — `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` use 5E word lists.
- `lib/schemas.py` — `validate_npc` checks `character_sheet.hp` is a `{current, max}` dict.
- `lib/extraction_schemas.py` — NPC extraction schema has explicit `hp` slot.
- `lib/session_manager.py:365-406` — `get_full_context` reads `character.level/race/class/hp/ac/xp` and `npc.character_sheet.hp/ac/level` to format CHARACTER and PARTY MEMBERS context blocks.

`features/` (character-creation, spells, rules, gear, loot, dnd-api) is already 5E-isolated — SRD-API integrations with no dispatch into core tools. Out of scope.

### Why not bash middleware

The middleware substrate (`.claude/modules/infrastructure/common-advanced.sh` — `dispatch_middleware`, `dispatch_middleware_post`, `dispatch_middleware_help`) exists but is dormant: `grep -rn dispatch_middleware tools/` returns zero matches. Commit `b0a8960` ("refactor: vanilla/advanced mode separation") deliberately stripped the middleware wiring from `tools/common.sh` to revert CORE to upstream shape. Reviving it would re-divergence CORE from upstream and undo a deliberate architectural decision by the upstream author.

The user intends to contribute this work upstream. Restoring middleware would require arguing against the upstream author's own deletion. An in-process Python registry adds a thin abstraction inside `lib/` without touching `tools/`, `module_loader.py`, or any deleted infrastructure — easier defense at upstream review.

### Why not physical isolation in lib/rulesets/

Considered: `lib/rulesets/dnd_5e/` as a sub-package of lib that lib imports by default. Rejected because the user's stated goal is *logical* decoupling. A sub-package of lib that lib imports is still a hard dependency of CORE on 5E — it just renames the file. Logical decoupling requires lib/ to depend only on an interface, with the 5E implementation reachable but not imported by lib/.

## Goal

Strip 5E specifics from `lib/`. Move them to a `rulesets/dnd_5e/` Python package that registers as the active ruleset via a registry interface in `lib/ruleset.py`. `lib/` calls the registered provider via hook methods. Alternate rulesets register the same way.

## Non-Goals

- Bash middleware revival or any change to `tools/`, `tools/common.sh`, `module_loader.py`, or `.claude/modules/infrastructure/`.
- Refactoring `features/`.
- Touching `lib/dice.py` (notation is generic).
- Touching thematic content (plot hooks, narrator styles, etc.).
- Building an alternate ruleset right now. The design must *enable* one, not ship one.
- Auditing the RAG layer for residual 5E coupling — noted as follow-up.
- Reorganizing the vanilla/advanced command split. Registry works in both unchanged.

## Architecture

### Three components

1. **`lib/ruleset.py`** — registry + `Ruleset` protocol. Pure interface, zero 5E knowledge.
2. **`rulesets/dnd_5e/`** — 5E provider. Implements the protocol. Auto-registers on import.
3. **Bootstrap** — `lib/__init__.py` imports `rulesets.dnd_5e` so the default ruleset is always available when lib is loaded. Campaign-specific override via `campaign-overview.json["ruleset"]` is a follow-up; not implemented in this refactor.

### Registry interface (`lib/ruleset.py`)

```python
# lib/ruleset.py
from typing import Protocol, Optional, Any, Dict

class Ruleset(Protocol):
    name: str
    def init_sheet(self, npc_data: Dict[str, Any]) -> None: ...
    def update_hp(self, sheet: Dict[str, Any], delta: int) -> Dict[str, Any]: ...
    def update_xp(self, sheet: Dict[str, Any], delta: int) -> Dict[str, Any]: ...
    def set_field(self, sheet: Dict[str, Any], field: str, value: Any) -> bool: ...
    def format_npc_sheet(self, npc_data: Dict[str, Any]) -> Optional[str]: ...
    def format_party_summary(self, party: Dict[str, Dict]) -> str: ...
    def format_character_block(self, character: Dict[str, Any]) -> str: ...
    def format_party_context_block(self, party: Dict[str, Dict], full: bool) -> str: ...
    def xp_threshold(self, level: int) -> Optional[int]: ...
    def level_for_xp(self, xp: int) -> int: ...
    def validate_skill(self, skill: str) -> tuple[bool, Optional[str]]: ...
    def validate_alignment(self, alignment: str) -> tuple[bool, Optional[str]]: ...
    def validate_condition(self, condition: str) -> tuple[bool, Optional[str]]: ...
    def validate_damage_type(self, damage_type: str) -> tuple[bool, Optional[str]]: ...
    def normalize_extracted_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]: ...

_provider: Optional[Ruleset] = None

def register(provider: Ruleset) -> None:
    global _provider
    _provider = provider

def get() -> Ruleset:
    if _provider is None:
        raise RuntimeError(
            "No ruleset registered. lib/__init__.py should import the default ruleset."
        )
    return _provider

def is_registered() -> bool:
    return _provider is not None
```

Single global provider per Python process. lib bootstrap registers default; alternate rulesets call `register()` to swap.

Hook surface ~15 methods. Not the full 5E API — only what lib needs to call. Methods that are purely internal to 5E (e.g., a `roll_initiative` helper) live in `rulesets/dnd_5e/` and are never called from lib.

### Provider (`rulesets/dnd_5e/`)

```
rulesets/
├── __init__.py                 (empty)
└── dnd_5e/
    ├── __init__.py             (registers provider on import)
    ├── provider.py             (DnD5eRuleset class implementing protocol)
    ├── sheet.py                (PARTY_MEMBER_DEFAULTS, init/update/set/format)
    ├── xp.py                   (XP_THRESHOLDS, level_for_xp, xp_threshold)
    ├── vocab.py                (validate_skill/alignment/condition/damage_type, word lists)
    ├── context.py              (format_character_block, format_party_context_block)
    └── tests/
        └── test_provider.py
```

`rulesets/dnd_5e/__init__.py`:

```python
from lib.ruleset import register
from .provider import DnD5eRuleset

register(DnD5eRuleset())
```

Side-effecting import — registration happens at import time. Convention noted in the file's docstring.

### Bootstrap (`lib/__init__.py`)

Currently empty (0 bytes). Becomes:

```python
# lib/__init__.py
# Bootstrap default ruleset. Side-effecting import — registers DnD5eRuleset
# with lib.ruleset. Alternate rulesets can call lib.ruleset.register() to swap.
import rulesets.dnd_5e  # noqa: F401
```

Project root must be on sys.path for `rulesets.dnd_5e` to import. The existing `sys.path.insert(0, str(Path(__file__).parent))` in each `lib/*.py` ensures lib/ is importable but not the project root. Two paths:

- Adjust the sys.path insertion in lib/* to also include `Path(__file__).parent.parent` (project root). Small one-line addition where the existing insertion lives.
- Or: when invoked via tools/, `$PYTHON_CMD` already runs from project root (since `tools/common.sh` resolves `PROJECT_ROOT`); use `uv run python lib/npc_manager.py` from project root and Python's default cwd-on-path resolves `rulesets`.

Default: `uv run python` from PROJECT_ROOT (tools already do this). Verify in Phase 1 that `import rulesets.dnd_5e` succeeds from `lib/__init__.py` under the tool invocation paths. If not, add the parent insertion.

### What moves where

#### `lib/npc_manager.py` (948 lines)

**Stays in lib** (system-agnostic):
- `create_npc`, `update_npc`, `get_npc_status`, `enhance_npc`
- Tag management: `tag_location`, `untag_location`, `tag_quest`, `untag_quest`, `get_tags`
- `is_party_member` flag toggle
- Opaque `character_sheet` dict storage (lib doesn't interpret contents)
- Equipment list, conditions list (vocab validation moves out; storage stays)
- `list_npcs`, `create_batch`

**Becomes hook calls in lib**:
- `promote_to_party_member` keeps the `is_party_member = True` toggle, calls `ruleset.init_sheet(npc_data)` for the sheet
- `update_npc_hp` → `ruleset.update_hp(sheet, amount)`
- `update_npc_xp` → `ruleset.update_xp(sheet, amount)`
- `set_npc_stat` → `ruleset.set_field(sheet, field, value)`
- `format_npc_status` party-member section → `ruleset.format_npc_sheet(npc_data)` (returns None if NPC isn't a party member or ruleset has no formatting for the state)
- `format_party_status` → `ruleset.format_party_summary(party)`

**Moves to `rulesets/dnd_5e/sheet.py`**:
- `PARTY_MEMBER_DEFAULTS`
- The actual sheet initialization, HP-as-{current,max} update logic, field-name semantics (`ac`, `level`, `class`, `race`, `attack_bonus`, `damage`, `hp_max`), 5E formatters

`update_npc_equipment`, `update_npc_condition`, `update_npc_feature`: equipment list mutations are generic (list of strings). Vocab validation (is "poisoned" a valid condition?) calls `ruleset.validate_condition(c)`. The mutation stays in lib.

#### `lib/player_manager.py` (766 lines)

XP coupling: 5 sites (`XP_THRESHOLDS` at line 22-43; references at 126, 130, 240, 248). Tractable.

**Stays in lib**:
- Character file load/save (single-`character.json` + legacy `characters/` dir)
- Generic getters/setters
- Method skeleton for XP grant + level-up; calls `ruleset.xp_threshold(level)` and `ruleset.level_for_xp(xp)` for the table consultation

**Moves to `rulesets/dnd_5e/xp.py`**:
- `XP_THRESHOLDS` array
- `xp_threshold(level) -> int`, `level_for_xp(xp) -> int`
- Any 5E-specific level-up side effects (none in current code beyond next-threshold computation)

#### `lib/session_manager.py:365-406`

`get_full_context` interleaves CHARACTER and PARTY MEMBERS blocks (5E-formatted) into session context.

**Approach**: lib emits the generic skeleton (header, time, recent events, locations, plot threads). Where the CHARACTER / PARTY blocks belong, lib calls `ruleset.format_character_block(character)` and `ruleset.format_party_context_block(party, full=...)`. Each returns a string (possibly empty if the ruleset has no opinion).

**Moves to `rulesets/dnd_5e/context.py`**:
- 5E CHARACTER block formatter (HP/AC/Level/Race/Class/XP/Gold line, Conditions line)
- 5E PARTY MEMBERS block formatter (per-NPC `Lvl Race Class HP/AC` lines + recent events)

#### `lib/validators.py`

**Stays in lib**:
- `validate_name`, `validate_attitude`, `validate_dice`

**Moves to `rulesets/dnd_5e/vocab.py`**:
- `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` with their 5E word lists

Verified zero callers in `lib/`, `tools/`, `features/`, `.claude/modules/`. If a hidden caller surfaces in a deprecated path, restore a stub that delegates: `def validate_skill(s): return get_ruleset().validate_skill(s)`. Default position: clean removal.

#### `lib/schemas.py`

`validate_npc` checks `character_sheet.hp` shape. Replace with: `character_sheet` must be a dict if present (no inner-shape check). 5E sheet shape validation runs in `rulesets/dnd_5e/sheet.py` on the action paths that touch it (init, hp update, set field).

**Accepted looseness**: direct JSON edits, batch creates that don't go through 5E sheet methods, extraction outputs can land in `npcs.json` without HP-shape validation. The ruleset re-validates at first action that touches the sheet. Per YAGNI, no separate validation-hook added.

#### `lib/extraction_schemas.py`

NPC schema's `hp` slot becomes `stats: dict` (opaque shape). Extractors emit whatever they find. `ruleset.normalize_extracted_stats(stats)` converts to provider-specific sheet shape on consumption — called by `rulesets/dnd_5e/sheet.py` when constructing a sheet from extraction output.

### Wiring summary

```
Claude
  └── bash tools/dm-npc.sh promote "Carl"          (UNCHANGED tool)
       └── uv run python lib/npc_manager.py promote Carl
            ├── import lib.ruleset                  (Python in-process)
            ├── import rulesets.dnd_5e              (via lib/__init__.py side-effect)
            │   └── lib.ruleset.register(DnD5eRuleset())
            ├── set is_party_member=True
            └── lib.ruleset.get().init_sheet(npc_data)
                 └── rulesets/dnd_5e/sheet.py writes PARTY_MEMBER_DEFAULTS
```

No bash dispatch. No `tools/` change. No `module_loader.py` change. No `common.sh` change.

### Extension to alternate rulesets

A future `rulesets/savage_worlds/` package implements `Ruleset` protocol and calls `lib.ruleset.register(SavageWorldsRuleset())`. To activate: change the import in `lib/__init__.py` (manual swap), or extend bootstrap to read `campaign-overview.json["ruleset"]` and import accordingly. The second option is the natural follow-up but is out of scope for this refactor — current scope ships with hardcoded default.

Existing `.claude/modules/` system is orthogonal to the ruleset registry. Modules (custom-stats, world-travel, inventory-system, firearms-combat) continue to participate via their existing patterns (rules.md text loading + standalone CLI). The registry handles only the lib-internal CORE-to-ruleset hook surface.

## Data Flow

### `dm-npc.sh promote "Carl"`

1. `tools/dm-npc.sh promote Carl` → `uv run python lib/npc_manager.py promote Carl`
2. Python startup: `import lib.npc_manager` → `import lib` → `lib/__init__.py` runs → `import rulesets.dnd_5e` → side-effect `register(DnD5eRuleset())`
3. `npc_manager.py promote()`:
   - `npcs[name]['is_party_member'] = True`
   - `lib.ruleset.get().init_sheet(npcs[name])` → DnD5e writes `character_sheet` from defaults
   - Save

### `dm-npc.sh create "Grim" "blacksmith" "friendly"`

1. `tools/dm-npc.sh create ...` → Python entry point
2. `npc_manager.py create()`:
   - Generic NPC entry written. No sheet. Ruleset not consulted (create is system-agnostic).

### `dm-npc.sh status "Carl"`

1. Python entry point
2. `npc_manager.py format_npc_status(name)`:
   - Generic block: description, attitude, tags, events
   - If `is_party_member`: appends `ruleset.format_npc_sheet(npc_data)` output (DnD5e returns the HP/AC/Stats/Equipment/Conditions/Features section as string; non-5E rulesets return their own or None)

### `dm-session.sh context`

1. Python entry point
2. `session_manager.get_full_context(full)`:
   - Generic header, time, recent events, locations, plot threads
   - `ruleset.format_character_block(character)` inserted where CHARACTER section belongs
   - `ruleset.format_party_context_block(party, full)` inserted where PARTY MEMBERS section belongs

## Error Handling

- If no ruleset registered (bootstrap failure): `lib.ruleset.get()` raises `RuntimeError("No ruleset registered ...")`. Surfaces immediately on any action that consults the ruleset. Better than silent fallback to nothing.
- If ruleset method returns None for a formatter call: lib treats as "no opinion, omit section." Consistent across all formatter hooks.
- Existing 5E NPCs in `npcs.json` with populated `character_sheet`: no migration needed. `character_sheet` is opaque storage in lib; DnD5e ruleset reads/writes the same shape.

## Testing

- **Existing test suite must pass at every phase boundary** with default DnD5e ruleset registered. Primary correctness check. Behavior should match pre-refactor.
- **Registry contract test**: register a mock ruleset, confirm `get()` returns it. Re-register, confirm it replaces. `is_registered()` reflects state.
- **No-ruleset test**: clear registration in a fixture, call `npc_manager.promote_to_party_member` — confirm `RuntimeError` raised (not silent failure).
- **Provider unit tests**: in `rulesets/dnd_5e/tests/`, exercise sheet init, HP update bounds, XP-to-level computation, vocab validation. Independent of lib.
- **Vocab extraction check**: `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` removed from `lib/validators.py`. No import errors.
- **Lib purity check** (CI grep, post-Phase 5): `grep -rnE "(PARTY_MEMBER_DEFAULTS|XP_THRESHOLDS|charmed|frightened|acrobatics|lawful good|bludgeoning)" lib/` returns zero matches.

## Implementation Plan (Phased)

Each phase commits independently. Tests pass at every boundary.

### Phase 1 — registry + skeleton provider + bootstrap

- Create `lib/ruleset.py` with `Ruleset` protocol, `register`, `get`, `is_registered`. Empty protocol methods documented but no implementations needed yet — protocol is a typing artifact.
- Create `rulesets/__init__.py` (empty) and `rulesets/dnd_5e/__init__.py` registering a placeholder `DnD5eRuleset` class whose methods raise `NotImplementedError`.
- Add `import rulesets.dnd_5e` to `lib/__init__.py`. Verify import path resolves from tools/ invocations (Python `cwd` is project root via `uv run python`).
- Tests pass — no code calls hook methods yet.

Sized small. Risk: import path resolution. Mitigation: bootstrap test in Phase 1 that runs `bash tools/dm-npc.sh list` (existing command) and confirms no `ImportError`.

### Phase 2 — validators extraction

- Move `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` from `lib/validators.py` to `rulesets/dnd_5e/vocab.py`.
- Implement the four `validate_*` methods on `DnD5eRuleset`, delegating to vocab module.
- Delete from `lib/validators.py`. Confirmed zero callers.
- Tests pass.

### Phase 3 — NPC sheet operations

- Move `PARTY_MEMBER_DEFAULTS` and the 5E logic of `promote_to_party_member`, `update_npc_hp`, `update_npc_xp`, `set_npc_stat`, `format_npc_status`, `format_party_status` from `lib/npc_manager.py` to `rulesets/dnd_5e/sheet.py`.
- In `lib/npc_manager.py`, replace 5E inline logic with hook calls. Keep `is_party_member` toggle and opaque `character_sheet` storage in lib.
- Implement matching methods on `DnD5eRuleset`.
- `update_npc_equipment` / `condition` / `feature`: lib does list mutation; ruleset validates vocab. Vocab calls already added in Phase 2.
- Tests pass.

### Phase 4 — player XP + session context (bundled)

- Move `XP_THRESHOLDS` and level-up logic from `lib/player_manager.py` to `rulesets/dnd_5e/xp.py`. Implement `xp_threshold`, `level_for_xp` on DnD5e provider. `player_manager` methods consult `ruleset.xp_threshold()` / `level_for_xp()` for the table.
- Strip CHARACTER and PARTY MEMBERS formatting from `lib/session_manager.py:get_full_context`. Replace with `ruleset.format_character_block(...)` / `format_party_context_block(...)` calls.
- Implement the two formatters in `rulesets/dnd_5e/context.py` and wire to provider.
- Tests pass.

Bundled because the data formats touched (character sheet + party sheet) are produced in Phase 3 and consumed here.

### Phase 5 — schemas + extraction

- `lib/schemas.py`: `validate_npc` checks `character_sheet` is a dict if present, drops inner-shape check.
- `lib/extraction_schemas.py`: NPC `hp` slot → `stats: dict` (opaque). Document that ruleset normalizes.
- DnD5e provider gains `normalize_extracted_stats` implementation: maps extracted dict to 5E sheet shape.
- Lib purity grep added to CI.
- Tests pass.

## File Touch Inventory

**Modified**:
- `lib/__init__.py` (Phase 1 — bootstrap import; currently empty)
- `lib/ruleset.py` (Phase 1 — NEW; listed here for clarity though technically new)
- `lib/validators.py` (Phase 2 — 4 functions removed)
- `lib/npc_manager.py` (Phase 3 — 5E inline logic replaced with hook calls; ~half of methods affected)
- `lib/player_manager.py` (Phase 4 — XP table + level-up consult hooks)
- `lib/session_manager.py` (Phase 4 — `get_full_context` formatter delegation)
- `lib/schemas.py` (Phase 5 — relax NPC validation)
- `lib/extraction_schemas.py` (Phase 5 — `hp` → opaque `stats`)
- `tests/conftest.py` or per-test fixtures (registry fixture additions)

**New**:
- `lib/ruleset.py`
- `rulesets/__init__.py`
- `rulesets/dnd_5e/__init__.py`
- `rulesets/dnd_5e/provider.py`
- `rulesets/dnd_5e/sheet.py`
- `rulesets/dnd_5e/xp.py`
- `rulesets/dnd_5e/vocab.py`
- `rulesets/dnd_5e/context.py`
- `rulesets/dnd_5e/tests/test_provider.py`

**Untouched**:
- `tools/*` (no change)
- `tools/common.sh` (no change)
- `.claude/modules/module_loader.py` (no change)
- `.claude/modules/infrastructure/common-advanced.sh` (still dormant, fine)
- `lib/dice.py`, `lib/colors.py`, generic entity managers' generic methods

Total: ~7 modified + ~8 new = ~15 files. Smaller than the bash-middleware design (~25) and zero divergence from upstream `tools/`.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| `import rulesets.dnd_5e` fails because project root not on sys.path | Phase 1 acceptance: bootstrap test that runs existing CLI commands and confirms no `ImportError`. If broken, add `Path(__file__).parent.parent` to sys.path inserts that already exist in `lib/*.py`. |
| Side-effecting import (`__init__.py` registers on import) is fragile to import-order changes | Tolerable — the only entry point that imports lib is the lib/ Python files invoked by tools. Documented at top of `rulesets/dnd_5e/__init__.py`. Failure mode is loud (`RuntimeError` from `get()`), not silent. |
| Tests run in different process configurations and lose registration | Each Python process boots fresh via `uv run python`; `lib/__init__.py` runs on first `import lib.*`. Registration is idempotent (last `register()` wins). Add fixture in `conftest.py` to reset between tests if cross-contamination surfaces. |
| Validator removal breaks an import not caught by grep | Phase 2 ships in isolation. If a hidden caller surfaces, restore stub: `def validate_skill(s): return get_ruleset().validate_skill(s)`. |
| Validation looseness on direct JSON edits / extraction output | Accepted per YAGNI. Ruleset re-validates on first action that touches the sheet. |
| `Ruleset` protocol surface grows during implementation | Each phase adds the methods that phase needs; protocol is documented as "what lib currently calls," not "everything a ruleset might want." Resist adding methods speculatively. |
| RAG / context-injection paths read 5E fields directly | Out of scope. Tracked as follow-up. `grep -rnE "(character_sheet|\bhp\b|\bac\b|\bxp\b)" lib/ tools/ --include="*.py" --include="*.sh"` post-Phase-5 confirms residual scope. |
| Upstream maintainer rejects the registry pattern as unwanted abstraction | The PR makes the case: alternate rulesets become possible without `lib/` changes. If still rejected, the design lives as a downstream patch — registry pattern adds one file (`lib/ruleset.py`) plus a one-line `lib/__init__.py`; minimal cherry-pick surface. |

## YAGNI Boundary

This design adds one abstraction: the `Ruleset` protocol with ~15 hook methods, scoped exactly to what `lib/` currently calls. No `Ruleset` ABC inheritance hierarchy. No system-aware UI prompts. No multi-system character conversion. No middleware revival.

`campaign-overview.json["ruleset"]` field for per-campaign ruleset selection is the natural next step but **not in this refactor**. Default DnD5e bootstrap covers all current campaigns. Adding the field is ~5 lines in `lib/__init__.py` once a second ruleset actually exists.
