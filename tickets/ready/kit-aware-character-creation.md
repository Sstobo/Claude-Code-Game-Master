---
slug: kit-aware-character-creation
title: Character creation follows the kit; Death Protocol stops handing out 5e wizards
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: [kit-block-in-context, executable-world-kit, identity-onboarding-wiring]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T15:47:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

enhancement

## What to build

`.claude/commands/create-character.md` (and the create-character agent) is
hardcoded 5e end to end — races, classes, spell slots, "HP = Hit Die max +
CON" (:271), mandatory spell selection (:283) — and the Death Protocol
(CLAUDE.md:39-41) routes a post-death new character straight into it, so a PC
death in a bespoke world hands the player a 5e wizard builder.

1. Split create-character into a kit-generic spine (identity → stats per the
   kit's `stat_schema` → gear → visual_appearance → save via
   `gm-player.sh save-json`) plus a dnd5e branch keeping the existing
   race/class/spell flow. Branch on the KIT block / `world_kit.py info`.
2. Fix the Death Protocol hand-off: "Roll a NEW character" spawns the
   kit-appropriate path.
3. Drop the ASCII-interface mandate (:288) in favor of plain text (phone
   play); fix `tools/gm-player.sh:1`'s "D&D Player Character Manager" banner.
4. Update `docs/flows/onboarding-and-death.md` and any claiming docs in the
   same commit.

## Acceptance criteria

- [ ] On the conan fixture, the creation flow presents conan's stat schema and vitals and never mentions 5e races/classes/spell slots; the saved character validates via `schemas.validate_character` (kit-aware).
- [ ] On a dnd5e campaign, the existing 5e flow is preserved.
- [ ] The Death Protocol section routes new characters through the kit-aware path.
- [ ] No ASCII-art mandate remains in create-character.md; gm-player.sh banner is kit-neutral.
- [ ] Claiming docs restamped.

## Out of scope

The identity-onboarding three-door entry (separate ticket, a blocker); rest/
level-up mechanics; the features/character-creation API scripts beyond what
the split requires.

## Verification

Lane: agent

## Blocked by

kit-block-in-context, executable-world-kit, identity-onboarding-wiring

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]

## Triage note (2026-08-13, fable-sott1, from review-vitals-2)

- Non-5e save with no authored hp silently persists a neutral 10/10
  (features/character-creation/save_character.py:~91). Surface it: `warnings`
  entry in the return payload naming the fallback; test-pinned.
- .claude/agents/create-character.md's example JSON has no `hp` key, so the
  documented creation path never authors HP in non-5e worlds — add it.
- Live gap: conan's ruleset.json has no `kit` field → WorldKit.kit() reads
  'custom'. Coordinate with import-bible-kit-wiring on legacy kit stamping.

## Triage note 2 (2026-08-13, fable-sott1, from whole-branch review)

SEVERITY RAISED on the silent 10/10 fallback: the LIVE conan campaign's
ruleset.json has no `kit` field, so WorldKit.kit() == 'custom' — meaning the
Death Protocol's replacement character on the flagship campaign would save as
an unplayable 10/10 with no saves block and no warning. Until this ticket
lands, consider the interim mitigations: derive HP when the sheet carries
class+level, or at minimum warn in the save payload (first triage note).
Also coordinate: create-character.md:153's save-json example must author hp.
