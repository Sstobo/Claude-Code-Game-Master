# Decouple D&D 5E from System-Agnostic Core — Design

**Date:** 2026-05-24
**Branch:** `refactor/decouple-5E`
**Scope:** Logical decoupling of 5E mechanics from `lib/`. Thematic content out of scope per user priority.
**Status:** Third revision. Initial draft proposed reviving deleted bash middleware; second revision moved to Python registry; this revision tightens the registry design after a second adversarial review pass (BLOCKER-1 import path, BLOCKER-2 validators CLI, BLOCKER-3 YAGNI hook removal, plus seven major/minor refinements).

## Problem

`lib/` is documented in `CLAUDE.md` as "upstream CORE only — no custom features." Several modules in it bake in D&D 5E assumptions:

- `lib/npc_manager.py` — `PARTY_MEMBER_DEFAULTS` hardcodes STR/DEX/CON/INT/WIS/CHA, AC, HP, attack_bonus, damage. Methods `set_npc_stat`, `update_npc_hp`, `update_npc_xp`, `format_party_status`, party-member block of `format_npc_status` assume the 5E sheet shape.
- `lib/player_manager.py` — `XP_THRESHOLDS` (lines 22-43) and 5 reference sites: `_normalize_xp` (lines 126, 130), `award_xp` (lines 240, 248). `_normalize_xp` is itself called from `award_xp` (231) and `get_xp_status` (284). Three methods total touch the 5E table.
- `lib/validators.py` — `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` use 5E word lists. Also exposed via the file's `__main__` argparse CLI (lines 261-300) with these four type choices.
- `lib/schemas.py` — `validate_npc` checks `character_sheet.hp` is a `{current, max}` dict (lines ~79-95). `validate_character` (lines 243-292) enforces `hp` as dict, hardcodes `level/ac/proficiency_bonus/speed` numerics, hardcodes `str/dex/con/int/wis/cha` ability keys.
- `lib/extraction_schemas.py` — NPC extraction schema has explicit `hp` slot.
- `lib/session_manager.py:354-427` — `get_full_context` reads `character.level/race/class/hp/ac/xp` and `npc.character_sheet.hp/ac/level` to format CHARACTER and PARTY MEMBERS context blocks.

`features/` (character-creation, spells, rules, gear, loot, dnd-api) is already 5E-isolated — SRD-API integrations with no dispatch into core tools. Out of scope.

### Why not bash middleware

The middleware substrate (`.claude/modules/infrastructure/common-advanced.sh` — `dispatch_middleware`, `dispatch_middleware_post`, `dispatch_middleware_help`) exists but is dormant: `grep -rn dispatch_middleware tools/` returns zero matches. Commit `b0a8960` ("refactor: vanilla/advanced mode separation") deliberately stripped the wiring to revert CORE to upstream shape. The user intends to contribute this work upstream. Restoring middleware would require arguing against the upstream author's own deletion. An in-process Python registry adds a thin abstraction inside `lib/` without touching `tools/`, `module_loader.py`, or any deleted infrastructure — easier defense at upstream review.

### Why not physical isolation in lib/rulesets/

A sub-package of lib that lib imports is still a hard dependency of CORE on 5E — it just renames the file. Logical decoupling requires lib to depend only on an interface; the 5E implementation must be reachable but not imported by lib.

## Goal

Strip 5E specifics from `lib/`. Move them to a `rulesets/dnd_5e/` Python package that registers as the active ruleset via a registry interface in `lib/ruleset.py`. `lib/` calls the registered provider via hook methods. Alternate rulesets register the same way.

## Non-Goals

- Bash middleware revival or any change to `tools/`, `tools/common.sh`, `module_loader.py`, or `.claude/modules/infrastructure/`.
- Refactoring `features/`.
- Touching `lib/dice.py`, `lib/colors.py`, or other system-agnostic modules.
- Touching thematic content.
- Building an alternate ruleset right now. The design must *lower the cost* of adding one; current scope ships with a hardcoded DnD5e default.
- Auditing the RAG layer for residual 5E coupling — noted as follow-up.
- Reorganizing the vanilla/advanced command split. Registry works in both unchanged.
- Introducing new behavior (e.g., vocab validation at mutation sites that don't validate today). YAGNI per the user's directive.

## Architecture

### Three components

1. **`lib/ruleset.py`** — registry + `Ruleset` protocol. Pure interface, zero 5E knowledge.
2. **`rulesets/dnd_5e/`** — 5E provider. Implements the protocol. Auto-registers on import.
3. **Bootstrap** — `lib/__init__.py` imports `rulesets.dnd_5e` so the default ruleset is always available when lib is loaded.

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

14 hook methods, each tied to a concrete current call site (mapped below). The protocol is a typing artifact — `typing.Protocol` is not enforced at runtime even with `@runtime_checkable`. The contract is enforced by tests calling each hook with realistic inputs.

**Hook-to-call-site mapping** (the protocol is exactly what lib currently calls; nothing speculative):

| Hook | Call site |
|---|---|
| `init_sheet` | `npc_manager.promote_to_party_member` (sheet seed) |
| `update_hp` | `npc_manager.update_npc_hp` |
| `update_xp` | `npc_manager.update_npc_xp` |
| `set_field` | `npc_manager.set_npc_stat` |
| `format_npc_sheet` | `npc_manager.format_npc_status` (party-member block, lines 140-173) |
| `format_party_summary` | `npc_manager.format_party_status` (lines 605-642) |
| `format_character_block` | `session_manager.get_full_context` (character section, lines 354-383) |
| `format_party_context_block` | `session_manager.get_full_context` (party section, lines 387-427) |
| `xp_threshold` | `player_manager._normalize_xp` (line 126, 130) |
| `level_for_xp` | `player_manager.award_xp` level-up loop (line 240) |
| `validate_skill` etc. | `lib/validators.py` CLI dispatch (today) — no in-process callers |

### Provider (`rulesets/dnd_5e/`)

```
rulesets/
├── __init__.py                 (empty)
└── dnd_5e/
    ├── __init__.py             (registers provider on import — side-effecting)
    ├── provider.py             (DnD5eRuleset class implementing protocol)
    ├── sheet.py                (PARTY_MEMBER_DEFAULTS, init/update/set/format)
    ├── xp.py                   (XP_THRESHOLDS, level_for_xp, xp_threshold)
    ├── vocab.py                (validate_skill/alignment/condition/damage_type, word lists)
    ├── context.py              (format_character_block, format_party_context_block)
    └── tests/
        ├── conftest.py         (provider-snapshot fixture for this subtree)
        └── test_provider.py
```

`rulesets/dnd_5e/__init__.py`:

```python
"""Side-effecting import: registers DnD5eRuleset with lib.ruleset on import."""
from lib.ruleset import register
from .provider import DnD5eRuleset

register(DnD5eRuleset())
```

### Bootstrap (`lib/__init__.py`)

Currently empty. Becomes:

```python
# lib/__init__.py
# Bootstrap default ruleset. Side-effecting import.
# Order matters: lib.ruleset is imported first so `register` is defined
# before rulesets.dnd_5e tries to call it (avoids partial-module circular
# import where `from lib.ruleset import register` could resolve to an
# incomplete lib module).
import sys
from pathlib import Path

# Defensive: ensure project root is on sys.path so `rulesets` resolves
# even under non-uv Python invocations (python3 lib/foo.py). Idempotent.
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from lib import ruleset  # noqa: F401  — register must be defined first
import rulesets.dnd_5e   # noqa: F401  — side-effects: registers DnD5eRuleset
```

### Package declaration (`pyproject.toml`)

Add `rulesets` and `rulesets.dnd_5e` to the `packages` list:

```toml
[tool.setuptools]
packages = ["lib", "features", "rulesets", "rulesets.dnd_5e"]
```

This handles editable install (`uv pip install -e .`), wheel builds, and any non-uv `pip install` path.

### Belt-and-suspenders rationale (orthogonal coverage)

- `pyproject.toml` declaration — covers `uv` editable install / wheel build path.
- `sys.path.insert` in `lib/__init__.py` — covers `python3 lib/foo.py` and cwd-relative invocations where the editable-install `.pth` isn't loaded.
- Dual-invocation Phase 1 acceptance test (`uv run` AND `python3` fallback) — proves both layers work.

Each layer covers a distinct failure mode. Dropping any one leaves a silent breakage path.

### Data-shape contract (lib ↔ ruleset)

Lib never reads inside `character_sheet`. The ruleset interprets it. Shapes:

**`npcs.json[name]`** (lib-owned):
```
{
  "description": str,
  "attitude": str,
  "is_party_member": bool,         (lib reads + writes)
  "character_sheet": dict,         (opaque to lib; ruleset reads + writes)
  "equipment": list[str],          (lib mutates the list; ruleset interprets meaning if any)
  "tags": {...},
  "events": [...],
  ...
}
```

**`character.json`** (lib-owned, PC sheet):
```
{
  "name": str,
  ...                              (ruleset-specific flat fields: hp, ac, xp, level, race, class, etc.)
}
```

Note the asymmetry: `npcs.json[name].character_sheet` is **wrapped** under a sub-key. `character.json` is **flat**. The two formatter hooks reflect this:
- `format_character_block(character)` receives the flat PC dict.
- `format_party_context_block(party, full)` receives the wrapped NPCs dict where each value has a `character_sheet` sub-key.

`init_sheet(npc_data)` operates on an NPC entry (writes the `character_sheet` sub-key). It does NOT operate on a PC. The PC's flat schema is set by character creation flows (in `features/character-creation/`), which is out of scope for this refactor.

The field name `character_sheet` is itself 5E-flavored vocabulary leaking into the lib schema. Renaming to `sheet` or `system_data` is a future cleanup, explicitly out of scope here.

### What moves where

#### `lib/npc_manager.py` (948 lines)

**Stays in lib** (system-agnostic):
- `create_npc`, `update_npc`, `get_npc_status`, `enhance_npc`
- Tag management
- `is_party_member` flag toggle
- Opaque `character_sheet` dict storage
- Equipment, conditions, features lists (mutation only; vocab validation NOT introduced)
- `list_npcs`, `create_batch`
- The "now has X" / "no longer has Y" print strings in `update_npc_condition` and similar — accepted carryover. They're display text in lib that happens to read 5E-ish; they don't interpret 5E semantics. No hook for now. Cleanup deferred.

**Becomes hook calls in lib**:
- `promote_to_party_member` → toggle flag, then `ruleset.init_sheet(npc_data)` for sheet seed. **Idempotency guard**: only call `init_sheet` if `character_sheet` is absent from `npc_data`; existing demoted-then-repromoted NPCs preserve their sheet.
- `update_npc_hp` → `ruleset.update_hp(sheet, amount)`
- `update_npc_xp` → `ruleset.update_xp(sheet, amount)`
- `set_npc_stat` → `ruleset.set_field(sheet, field, value)`
- `format_npc_status` party-member section → `ruleset.format_npc_sheet(npc_data)`
- `format_party_status` → `ruleset.format_party_summary(party)`

**Moves to `rulesets/dnd_5e/sheet.py`**:
- `PARTY_MEMBER_DEFAULTS`
- 5E logic of sheet init, HP-as-{current,max} update, field-name semantics, formatters

#### `lib/player_manager.py` (766 lines)

XP coupling **audit-confirmed**: 5 reference sites across 3 methods.
- `_normalize_xp` (lines 126, 130) — called from `award_xp` (231) and `get_xp_status` (284)
- `award_xp` level-up loop (lines 240, 248)

All three methods consult the table via `ruleset.xp_threshold(level)` / `ruleset.level_for_xp(xp)`.

**Stays in lib**:
- Character file load/save
- Generic getters/setters
- Method skeletons of `_normalize_xp`, `award_xp`, `get_xp_status`; XP-table access becomes a ruleset call

**Moves to `rulesets/dnd_5e/xp.py`**:
- `XP_THRESHOLDS` array
- `xp_threshold(level) -> int`, `level_for_xp(xp) -> int`

The `xp.next_level` field written by `_normalize_xp` is 5E-shaped (assumes a "next level" exists). It stays for the current ruleset's behavior; a generic alternative is out of scope.

#### `lib/session_manager.py:354-427`

`get_full_context` interleaves CHARACTER and PARTY MEMBERS blocks (5E-formatted). Audit confirms surrounding control flow is **not tangled** — the 5E sections are contiguous and cleanly liftable.

**Lib's revised flow**:
- Emit generic skeleton
- At CHARACTER slot: call `ruleset.format_character_block(character_dict)` — flat shape per data contract above
- At PARTY MEMBERS slot: call `ruleset.format_party_context_block(party, full)` — wrapped shape

**Moves to `rulesets/dnd_5e/context.py`**:
- The two formatters

#### `lib/validators.py`

**Stays in lib**:
- `validate_name`, `validate_attitude`, `validate_dice`, `validate_ability`, `validate_quest_priority`, `validate_time_of_day`, `validate_plot_type`, `validate_plot_status` (other generic validators present in the file)

**Moves to `rulesets/dnd_5e/vocab.py`**:
- `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` with 5E word lists
- Implementations exposed via `DnD5eRuleset` provider methods

**CLI cleanup** (`lib/validators.py` `__main__` block, lines 261-300): clean removal. Drop these from the argparse `choices=` list and from the dispatch dict:

```python
# before
choices=['name', 'attitude', 'dice', 'damage_type', 'skill',
         'alignment', 'condition', 'ability', 'priority', 'time',
         'plot_type', 'plot_status']
# after
choices=['name', 'attitude', 'dice', 'ability', 'priority', 'time',
         'plot_type', 'plot_status']
```

Drop the corresponding 4 entries from `validators_map`. CLI shrinks; remaining 8 choices work. Zero in-process callers of the 4 removed methods (verified across `lib/`, `tools/`, `features/`, `.claude/modules/`).

`agent_extractor.py:45` and `entity_manager.py:43,58` instantiate `Validators()` but call only generic surviving methods — verified clean for this scope.

#### `lib/schemas.py`

**Phase 5 relaxes both validators**:
- `validate_npc`: `character_sheet` must be a dict if present (no inner-shape check)
- `validate_character`: drop hp-as-dict requirement; drop hardcoded `level/ac/proficiency_bonus/speed` numeric checks; drop ability-key hardcoding (`str/dex/con/int/wis/cha`). Treat sheet fields as opaque post-refactor.

Ruleset re-validates on action paths (init_sheet / update_hp / set_field). Accepted looseness: direct JSON edits or extraction outputs can land in storage without inner-shape validation. Per YAGNI, no separate validation-hook added.

#### `lib/extraction_schemas.py`

NPC schema's `hp` slot becomes `stats: dict` (opaque shape). Extractors emit whatever they find.

**Dropped**: `normalize_extracted_stats` hook from the protocol. Originally proposed for the consumption side of extraction; verified zero current consumers construct sheets from extraction output. YAGNI — add the hook when an actual consumer materializes.

## Data Flow

### `dm-npc.sh promote "Carl"`

1. `tools/dm-npc.sh promote Carl` → `uv run python lib/npc_manager.py promote Carl`
2. Python startup: `import lib.npc_manager` → triggers `import lib` → `lib/__init__.py` runs:
   - sys.path defensively includes project root
   - `import lib.ruleset` (defines `register`)
   - `import rulesets.dnd_5e` → side-effect `register(DnD5eRuleset())`
3. `npc_manager.promote_to_party_member(name)`:
   - `npcs[name]['is_party_member'] = True`
   - If `character_sheet` absent: `lib.ruleset.get().init_sheet(npcs[name])`
   - Save

### `dm-npc.sh status "Carl"`

1. Python entry point (bootstrap runs)
2. `npc_manager.format_npc_status(name)`:
   - Generic block: description, attitude, tags, events
   - If `is_party_member`: append `ruleset.format_npc_sheet(npc_data)` output

### `dm-session.sh context`

1. Python entry point
2. `session_manager.get_full_context(full)`:
   - Generic header, time, recent events, locations, plot threads
   - `ruleset.format_character_block(character)` inserted at CHARACTER slot
   - `ruleset.format_party_context_block(party, full)` inserted at PARTY MEMBERS slot

## Error Handling

- `lib.ruleset.get()` with no registration raises `RuntimeError`. Surfaces immediately on first ruleset-touching action. Better than silent fallback.
- If bootstrap import of `rulesets.dnd_5e` fails (e.g., a syntax error during development), all `import lib.*` fail. Intentional: fail loud rather than run with broken provider.
- Formatter hooks returning `None` / empty string are treated as "no opinion, omit section." Consistent across hooks.
- Existing 5E NPCs in `npcs.json` with populated `character_sheet`: no migration needed. Lib's storage stays opaque; DnD5e ruleset interprets the same shape.

## Testing

- **Existing tests must pass at every phase boundary** with default DnD5e registered. Tests are implicitly 5E-coupled (e.g., `tests/test_player_manager.py:200-219` asserts `level_up=True` after awarding 300 XP — passes because 300 is DnD5e's level-2 threshold). Parameterizing tests over arbitrary rulesets is out of scope.
- **Phase 1 dual-invocation bootstrap test**: run `bash tools/dm-npc.sh list` under (a) `uv run` and (b) `python3` fallback path (after temporarily renaming uv binary or via `PYTHON_CMD=python3 bash tools/dm-npc.sh list`). Both must succeed. Catches BLOCKER-1 regressions.
- **`tests/conftest.py` autouse provider-snapshot fixture** (Phase 1): snapshots `lib.ruleset._provider` before each test, restores after. Required because pytest runs the whole suite in one process and side-effecting imports leave global state. Place at `tests/conftest.py`; pytest scoping means tests outside this subtree (e.g., `rulesets/dnd_5e/tests/`) need their own conftest with the same fixture. `rulesets/dnd_5e/tests/conftest.py` is created in Phase 3.
- **Registry contract tests**: `register()` sets provider; `get()` returns it; re-`register()` replaces; `is_registered()` reflects state.
- **No-ruleset test**: fixture clears `_provider`, calls a ruleset-touching method, expects `RuntimeError`. Provider-snapshot fixture restores afterward.
- **Provider unit tests** in `rulesets/dnd_5e/tests/`: sheet init, HP update bounds, XP-to-level computation, vocab validation. Independent of lib.
- **Lib purity check** (CI grep, post-Phase 5): `grep -rnE --include="*.py" "(PARTY_MEMBER_DEFAULTS|XP_THRESHOLDS|charmed|frightened|acrobatics|lawful good|bludgeoning)" lib/ | grep -v "^[^:]*:[[:space:]]*#"` — case-sensitive, .py-only, comment-line stripping. Some false positives in docstrings expected; curate the output, treat as audit not strict gate. May tighten later with word boundaries.

## Implementation Plan (Phased)

Each phase commits independently. Tests pass at every boundary.

### Phase 1 — registry + skeleton provider + bootstrap + conftest

- Create `lib/ruleset.py` with `Ruleset` protocol, `register`, `get`, `is_registered`.
- Create `rulesets/__init__.py` and `rulesets/dnd_5e/__init__.py` registering a placeholder `DnD5eRuleset` class with `NotImplementedError` methods.
- Add `rulesets`, `rulesets.dnd_5e` to `pyproject.toml` `packages` list.
- Add bootstrap to `lib/__init__.py`: defensive sys.path insert, then ordered imports (lib.ruleset, then rulesets.dnd_5e).
- Add `tests/conftest.py` autouse provider-snapshot fixture.
- **Dual-invocation acceptance test**: `bash tools/dm-npc.sh list` succeeds under both `uv run` and `python3` fallback.
- Tests pass.

### Phase 2 — validators extraction + CLI cleanup

- Move `validate_skill`, `validate_alignment`, `validate_condition`, `validate_damage_type` from `lib/validators.py` to `rulesets/dnd_5e/vocab.py`.
- Implement matching methods on `DnD5eRuleset`, delegating to vocab module.
- Clean removal from `lib/validators.py`: drop the 4 method definitions AND drop them from the `__main__` argparse `choices=` + `validators_map` dict. CLI shrinks from 12 to 8 choices.
- No new validation calls introduced at lib mutation sites. Behavior unchanged.
- Tests pass.

### Phase 3 — NPC sheet operations + idempotency guard

- Move `PARTY_MEMBER_DEFAULTS` and 5E logic of party-member methods from `lib/npc_manager.py` to `rulesets/dnd_5e/sheet.py`.
- In `lib/npc_manager.py`, replace 5E inline logic with hook calls. Keep flag toggle, opaque storage, list mutations, carryover print strings.
- `promote_to_party_member`: idempotency guard — only call `init_sheet` if `character_sheet` absent.
- Implement matching methods on `DnD5eRuleset`.
- Add `rulesets/dnd_5e/tests/conftest.py` with provider-snapshot fixture (subtree scope).
- Tests pass.

### Phase 4 — player XP + session context (bundled)

- Move `XP_THRESHOLDS` from `lib/player_manager.py` to `rulesets/dnd_5e/xp.py`.
- `_normalize_xp` (lines 126, 130), `award_xp` level-up loop (lines 240, 248): all consult `ruleset.xp_threshold()` / `level_for_xp()`. Three methods affected: `_normalize_xp`, `award_xp`, `get_xp_status` (indirectly via `_normalize_xp`).
- Note `xp.next_level` field shape is 5E carryover (assumes "next level" exists). Documented; cleanup deferred.
- Strip CHARACTER and PARTY MEMBERS formatting from `lib/session_manager.py:get_full_context`. Replace with `ruleset.format_character_block` / `format_party_context_block` calls.
- Implement formatters in `rulesets/dnd_5e/context.py`.
- Tests pass.

### Phase 5 — schemas + extraction

- `lib/schemas.py:validate_npc`: `character_sheet` opaque-dict check.
- `lib/schemas.py:validate_character`: drop hp-as-dict, drop hardcoded level/ac/proficiency/speed/ability-key checks. Treat as opaque.
- `lib/extraction_schemas.py`: NPC `hp` slot → `stats: dict` (opaque).
- Lib purity grep added to CI as an audit (not strict gate, given comment/docstring noise).
- Tests pass.

## File Touch Inventory

**Modified**:
- `lib/__init__.py` (Phase 1 — bootstrap; currently empty)
- `lib/validators.py` (Phase 2 — 4 methods removed; CLI argparse + dispatch dict trimmed)
- `lib/npc_manager.py` (Phase 3 — 5E inline replaced with hook calls + idempotency guard)
- `lib/player_manager.py` (Phase 4 — 3 methods consult ruleset hooks for XP table)
- `lib/session_manager.py` (Phase 4 — `get_full_context` delegates 2 sections to formatters)
- `lib/schemas.py` (Phase 5 — both `validate_npc` and `validate_character` relaxed)
- `lib/extraction_schemas.py` (Phase 5 — `hp` → opaque `stats`)
- `pyproject.toml` (Phase 1 — packages list)
- `tests/conftest.py` (Phase 1 — provider-snapshot fixture added; existing fixtures unchanged)

**New**:
- `lib/ruleset.py`
- `rulesets/__init__.py`
- `rulesets/dnd_5e/__init__.py`
- `rulesets/dnd_5e/provider.py`
- `rulesets/dnd_5e/sheet.py`
- `rulesets/dnd_5e/xp.py`
- `rulesets/dnd_5e/vocab.py`
- `rulesets/dnd_5e/context.py`
- `rulesets/dnd_5e/tests/conftest.py`
- `rulesets/dnd_5e/tests/test_provider.py`

**Untouched**:
- `tools/*` (no change)
- `tools/common.sh` (no change)
- `.claude/modules/module_loader.py` (no change)
- `.claude/modules/infrastructure/common-advanced.sh` (still dormant, fine)
- `lib/dice.py`, `lib/colors.py`, `lib/agent_extractor.py`, `lib/entity_enhancer.py`, `lib/entity_manager.py` (verified — no removed-validator callers)

Total: ~9 modified + ~10 new = ~19 files across 5 phases. Slightly larger than the previous draft's claim (~15) because pyproject.toml, conftest.py, and rulesets/dnd_5e/tests/conftest.py are now explicit.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| `import rulesets.dnd_5e` fails under non-uv invocation | Belt-and-suspenders: pyproject packages declaration + defensive sys.path insert in `lib/__init__.py` + dual-invocation Phase 1 acceptance test. |
| Circular import: `rulesets/dnd_5e/__init__.py` does `from lib.ruleset import register` during `lib/__init__.py` bootstrap | `lib/__init__.py` imports `lib.ruleset` FIRST, then `rulesets.dnd_5e`. Order documented in the file. |
| pytest global state contamination across tests | Phase 1 ships autouse provider-snapshot fixture in `tests/conftest.py`. Subtree tests (`rulesets/dnd_5e/tests/`) get same fixture in subtree conftest. |
| Validator removal breaks an unknown caller | Phase 2 isolated. Audit clean (zero in-process callers, only the file's own CLI which is updated in the same phase). If a hidden caller emerges, restore stub: `def validate_skill(s): return lib.ruleset.get().validate_skill(s)`. |
| `promote_to_party_member` re-call stomps existing sheet | Idempotency guard: only call `init_sheet` if `character_sheet` absent. |
| Validation looseness on direct JSON edits | Accepted per YAGNI. Ruleset re-validates on first action that touches the sheet. |
| `Ruleset` protocol surface grows during implementation | Each phase adds the methods that phase needs; protocol is documented as "what lib currently calls," not "everything a ruleset might want." Adding methods speculatively is rejected (see `normalize_extracted_stats` removal). |
| Tests bake in DnD 5E numbers (XP 300 → level 2, etc.) | Accepted. Tests pass because DnD5e is default. Ruleset parameterization is out of scope. |
| RAG / context-injection paths read 5E fields directly | Out of scope. Follow-up grep audit: `grep -rnE "(character_sheet|\bhp\b|\bac\b|\bxp\b)" lib/ tools/ --include="*.py" --include="*.sh"` post-Phase 5. |
| Upstream PR rejected as unwanted abstraction | Cherry-pick surface is minimal — `lib/ruleset.py` (NEW), 1-line bootstrap, ~9 modified files. If rejected upstream, lives as downstream patch with low merge friction. |

## YAGNI Boundary

This design adds one abstraction: the `Ruleset` protocol with 14 hook methods, each tied to a current lib call site. Speculative hooks (`normalize_extracted_stats`) removed during review. No `Ruleset` ABC inheritance. No new validation behavior introduced. No middleware revival. No tools/ touched.

Future natural follow-ups, explicitly **not in scope**:
- `campaign-overview.json["ruleset"]` field for per-campaign ruleset selection. Default DnD5e bootstrap covers all current campaigns. Adding the field is ~5 lines in `lib/__init__.py` once a second ruleset exists.
- Rename `character_sheet` field to `sheet` or `system_data`. Vocabulary cleanup, not a coupling fix.
- Generalize `xp_threshold`/`level_for_xp` for systems without levels (FATE, PbtA). Reshape the protocol when a non-d20 ruleset is actually being added.
- New vocab validation calls at condition/equipment/feature mutation sites. New behavior, not in this refactor.

## Upstream PR Framing

The pitch: **registry pattern lowers the coupling required to add an alternate ruleset.** Not "alternate rulesets become possible" — for non-d20 systems the protocol still needs reshaping. Concrete improvements for the upstream PR description:
- Lib no longer imports 5E tables / vocabulary
- New file `lib/ruleset.py` defines the hook surface
- Default DnD5e provider preserves all current behavior
- Single bootstrap line; cherry-pick surface minimal
- No `tools/` changes; no module-loader changes
- 5 phases, each independently mergeable
