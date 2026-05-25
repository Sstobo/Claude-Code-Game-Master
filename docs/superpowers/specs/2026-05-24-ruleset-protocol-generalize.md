# Ruleset Protocol Generalization

**Date:** 2026-05-24
**Branch:** refactor/decouple-5E
**Status:** Approved, pending implementation

## Problem

The previous refactor (`b8de876`…`3c26d7e`) moved 5E tables and vocabulary out of `lib/` into
`rulesets/dnd_5e/`, but several 5E-specific field names and concepts remain embedded in lib/:

1. **`lib/ruleset.py` protocol** — `update_xp`, `xp_threshold`, `level_for_xp` encode the
   5E XP/level advancement model. Many game systems have no XP or levels.

2. **`lib/npc_manager.py:304-310`** — success print reads `sheet['hp']` and `sheet['ac']`
   directly after `init_sheet`, bypassing the ruleset for display.

3. **`lib/npc_manager.py:347-380`** — `update_npc_hp` and `update_npc_xp` read `sheet['hp']`
   and `sheet['xp']` field names after calling ruleset hooks.

4. **`lib/player_manager.py`** — `_normalize_xp`, `award_xp`, `get_xp_status` orchestrate XP
   and level logic inline; `modify_hp` clamps and status-checks HP without the ruleset;
   `show_player`/`show_all_players` read `char['hp']` and `char['level']` for display.

5. **`lib/validators.py`** — `validate_ability` hardcodes STR/DEX/CON/INT/WIS/CHA — a
   D&D-specific vocabulary that should live in the ruleset alongside the other four vocab
   validators removed in the previous refactor.

## Approach

Approach A: named semantic hooks. Extend the `Ruleset` protocol with purpose-specific hooks
that own each concern. lib/ calls hooks; the ruleset implementation owns all field names and
thresholds. No 5E concepts leak into lib/ call sites.

## Protocol Changes (`lib/ruleset.py`)

### Remove

| Method | Reason |
|---|---|
| `update_xp(sheet, delta)` | XP is 5E-specific |
| `xp_threshold(level)` | 5E table lookup |
| `level_for_xp(xp)` | 5E table lookup |

### Change return type

`update_hp(sheet, delta) -> Dict[str, Any]`

- Sheet is still mutated in place (existing behaviour preserved).
- Return value changes from the mutated sheet to a result dict, so lib/ never needs to
  read field names to build log messages:

```python
{'old': int, 'new': int, 'max': int, 'status': Optional[str]}
```

`status` is a ruleset-supplied string (e.g. `'UNCONSCIOUS'`, `'BLOODIED'`, `None`).
lib/ prints it without knowing what thresholds produced it.

### Add

| Method | Signature | Purpose |
|---|---|---|
| `normalize_advancement` | `(char) -> None` | Migrate legacy advancement data format in-place. No-op for rulesets without progression. |
| `advance` | `(char, amount: int) -> Dict[str, Any]` | Award advancement. Mutates char. Returns `{amount, level_changed, old_level, new_level, summary}`. |
| `advancement_status` | `(char) -> str` | Read-only display of current advancement state. |
| `format_character_summary` | `(char) -> str` | One-liner for CLI display (used in turn-render path). |
| `validate_ability` | `(ability: str) -> Tuple[bool, Optional[str]]` | Moved from `lib/validators.py`. |

`update_hp` and `advance` both accept either a full PC `char` dict or an NPC
`character_sheet` sub-dict — both have the same top-level structure.

## 5E Provider Changes (`rulesets/dnd_5e/`)

### `sheet.py`

- Update `update_hp` to return result dict instead of mutated sheet.
- 5E status rules: `'UNCONSCIOUS'` if new == 0; `'BLOODIED'` if `0 < new <= max // 4`; else `None`.

### `xp.py`

- Keep `xp_threshold` and `level_for_xp` as module-level helpers (internal only).
- Add `normalize_advancement(char)` — converts `char['xp']` int → `{'current', 'next_level'}` dict; no-op if already that shape.
- Add `advance(char, amount)` — current `award_xp` logic extracted from `lib/player_manager`; mutates `char['xp']` and `char['level']`; returns `{amount, level_changed, old_level, new_level, summary}`.
- Add `advancement_status(char)` — calls `normalize_advancement` then returns display string (e.g. `"Level 5 | XP: 1500/2700"` or `"Level 20 | XP: MAX"`).

### `vocab.py`

- Add `validate_ability(ability)` — existing implementation from `lib/validators.py`, unchanged.

### `context.py`

- Add `format_character_summary(char)` — one-liner format matching current `show_player` output:
  `"{name} - {race} {class} Level {level} (HP: {cur}/{max}, Gold: {gold})"`.
  May append conditions if present.

### `provider.py`

- Remove delegations: `update_xp`, `xp_threshold`, `level_for_xp`.
- Update `update_hp` delegation (return type change handled in sheet.py).
- Add delegations: `normalize_advancement`, `advance`, `advancement_status` → `_xp`; `format_character_summary` → `_context`; `validate_ability` → `vocab`.

## lib/ Caller Changes

### `lib/npc_manager.py`

| Location | Change |
|---|---|
| `promote_to_party_member:304-310` | Replace `sheet['hp']`/`sheet['ac']` reads with `ruleset.get().format_npc_sheet(npcs[name])` in success print |
| `update_npc_hp:347-364` | Use `result = ruleset.get().update_hp(sheet, amount)`; log from `result` keys |
| `update_npc_xp:366-380` | Replace `update_xp` call + `sheet['xp']` read with `result = ruleset.get().advance(sheet, amount)`; log from result |

### `lib/player_manager.py`

| Location | Change |
|---|---|
| `_normalize_xp:96-110` | Delegate to `ruleset.get().normalize_advancement(char)`; method becomes two lines |
| `award_xp:198-253` | Call `normalize_advancement`, then `result = ruleset.get().advance(char, amount)`; save char; print/return from result dict |
| `get_xp_status:255-290` | Call `normalize_advancement`, save, print `ruleset.get().advancement_status(char)`; return `{'success': True, 'name': char_name}` (rich XP/level keys removed — callers use printed output) |
| `modify_hp:292-337` | Delegate to `result = ruleset.get().update_hp(char, amount)`; build output from result; remove inline clamp and BLOODIED threshold |
| `show_player:138-151` | Delegate to `ruleset.get().format_character_summary(char)` |
| `show_all_players:153-181` | Same |

### `lib/validators.py`

- Remove `validate_ability` method.
- Remove from CLI argparse choices and validators map.

## Test Changes

### `tests/test_ruleset_registry.py`

- `_StubProvider`: remove `update_xp`, `xp_threshold`, `level_for_xp` stubs; add stubs for `normalize_advancement`, `advance`, `advancement_status`, `format_character_summary`, `validate_ability`.

### `tests/test_validators_cleanup.py`

- Move `validate_ability` from "must remain" list to "must be removed" list.

### `rulesets/dnd_5e/tests/test_provider.py`

- Update `update_hp` tests: assert result dict shape and 5E status thresholds.
- Remove `update_xp`, `xp_threshold`, `level_for_xp` tests (logic moves to `advance`).
- Add tests for `normalize_advancement` (int→dict, already-normalized no-op).
- Add tests for `advance` (accumulation, level-up, cap).
- Add tests for `advancement_status` (display string, MAX at cap).
- Add tests for `format_character_summary` (one-liner shape).
- Add tests for `validate_ability` (full names, abbreviations, invalid).

## Scope

~12 files, ~300–400 lines changed. No new files required.
