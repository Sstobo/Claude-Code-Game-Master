---
slug: kit-systems-authoring
title: Kit instantiates + names 1-3 systems; surfaced in context
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: world-kit-systems
blockedBy: [system-primitives-lib]
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:12:30Z
changedFiles: [lib/world_kit.py, lib/session_manager.py, lib/book_bible.py, tools/gm-extract.sh, .claude/commands/import.md, .claude/commands/new-game.md, docs/modules/game-core-and-world-kit.md, docs/modules/scene-context.md, tests/test_kit_systems.py]
resolution: kit `systems` block (WorldKit.systems + write_systems + gm-extract write-systems) instantiates the game_core primitives; scene context emits a ROLL-these SIGNATURE SYSTEMS block; import/new-game author 1-3 at creation
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:16:00Z
---

## Parent

World-Kit Systems (prds/world-kit-systems.md)

## Category

enhancement

## What to build

Let a World Kit turn the primitives into named, world-specific systems, and make
the GM see and roll them.

- `world_kit.py` / `ruleset.json` gains a `systems` block: a list of
  `{primitive, name, config}` instantiations. Legacy free-text
  `signature_systems` stays as flavor beside it.
- `/import` and `/new-game` pick 1–3 primitives fitting the world's tone/themes
  and name them (import can infer from extracted themes; new-game from tone).
- Scene context (`gm-session.sh context`) emits the active kit's `systems` —
  name, current track values, and when each fires — alongside YOUR WORLD'S RULES.
- CLAUDE.md / relevant skill guidance tells the GM to roll these systems, not
  honor them by vibes.

## Acceptance criteria

- [x] `world_kit.py` persists and round-trips a `systems` list of
      `{primitive, name, config}`. *(WorldKit.systems() + book_bible.write_systems;
      tested round-trip + drop-malformed)*
- [x] `/import` and `/new-game` produce a kit with 1–3 named systems appropriate
      to the world. *(both command prompts author 1–3 primitives + persist via
      `gm-extract.sh write-systems`)*
- [x] `gm-session.sh context` emits the instantiated systems block with names and
      the configured thresholds. *(YOUR WORLD'S SIGNATURE SYSTEMS block, tested
      emit/no-emit. NOTE: persisting a per-campaign live track VALUE is a follow-up
      — the block surfaces each system's definition/thresholds so the GM knows what
      to roll; the primitives themselves are stateless calculators.)*
- [x] Guidance instructs the GM to roll the systems (references the primitives).
      *(block header "ROLL these, do not just narrate"; import/new-game "dice, not
      vibes"; names the four primitives)*
- [x] A kit with no `systems` still loads (backward compatible). *(tested: absent/
      empty systems → no block, kit loads)*

## Out of scope

- The primitive implementations themselves (blocker ticket).
- Lethality dial and PC signature move (separate tickets).

## Verification

Lane: agent

## Blocked by

system-primitives-lib

---

## QA Reports

### 2026-08-15T16:16:00Z — verified [ss-rt14b]
- `WorldKit.systems()` reads `ruleset.json.systems` (drops malformed); `book_bible.write_systems` + `gm-extract.sh write-systems` persist authored systems onto the kit (requires an existing ruleset). `SessionManager._system_summary` + a new context block emit YOUR WORLD'S SIGNATURE SYSTEMS ("ROLL these") from `kit.systems()`, gated to non-empty, distinct from the prose YOUR WORLD'S RULES.
- 6 tests (tests/test_kit_systems.py): getter drops-malformed, block emit with named_track thresholds, no-systems→no-block, write_systems round-trip+drop. Regression: kit_block / get_full_context / game_core / character_schema green (only the pre-existing action-menu test fails, unrelated).
- import.md + new-game.md author 1–3 primitives at creation and persist. Docs: game-core-and-world-kit.md (kit-binding layer now exists) + scene-context.md (block added) ingested + restamped.
- This wires primitives → live rolls (the round-table headline). Self-reviewed + committed inline (code core adversarially tested; prompt/doc guidance) per the token-efficiency directive. NOTE: per-campaign live track STATE persistence is a deliberate follow-up.

## History

- 2026-08-15T16:16:00Z  verified (inline, self-reviewed) → done + committed  [ss-rt14b]
- 2026-08-15T16:12:30Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:12:30Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
