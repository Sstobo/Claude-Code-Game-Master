---
slug: kit-aware-character-creation
title: Character creation follows the kit; Death Protocol stops handing out 5e wizards
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: trust-the-agent
blockedBy: [kit-block-in-context]
claimedBy: gk-t8n2wp
claimedAt: 2026-08-14T19:30:58Z
changedFiles: [.claude/commands/create-character.md, .claude/agents/create-character.md, tools/gm-player.sh, CLAUDE.md, features/character-creation/save_character.py, docs/flows/onboarding-and-death.md, docs/modules/player-character.md, docs/log.md, tests/test_kit_aware_character_creation.py, tests/test_kit_vitals.py]
resolution: create-character branches on kit; Death Protocol no longer hands out 5e wizards; 10/10 HP warns
reviewRounds: 1
implementer: 5d1d8bb0-0f1d-4217-bc85-76c77eef07ba
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-14T19:50:00Z
---

## Parent

Trust the Agent (prds/trust-the-agent.md)

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

- [x] On the conan fixture, the creation flow presents conan's stat schema and vitals and never mentions 5e races/classes/spell slots; the saved character validates via `schemas.validate_character` (kit-aware).
- [x] On a dnd5e campaign, the existing 5e flow is preserved.
- [x] The Death Protocol section routes new characters through the kit-aware path.
- [x] No ASCII-art mandate remains in create-character.md; gm-player.sh banner is kit-neutral.
- [x] Claiming docs restamped.

## Out of scope

The identity-onboarding three-door entry (separate ticket, a blocker); rest/
level-up mechanics; the features/character-creation API scripts beyond what
the split requires.

## Verification

Lane: agent

## Blocked by

kit-block-in-context (executable-world-kit and identity-onboarding-wiring are done)

---

## QA Reports

### 2026-08-14T19:50:00Z — reviewed perfect [e0ad5764]
No correctness/regression findings. Nits (non-blocking): KIT block omits attributes so spine should prefer world_kit.py info; generic save-json example is Hyborian-shaped; agent persist uses `./tools/`; player-character.md overclaims validate_character race/class; empty race/class strings on non-dnd5e; save_character docstring still says D&D.

### 2026-08-14T19:42:00Z — verified [gk-t8n2wp]
Generic spine vs dnd5e branch in command+agent; Conan-live (no kit field) sheet without race/class validates; 10/10 fallback warns; Death Protocol SWAP is kit-aware; no ASCII mandate; gm-player banner kit-neutral. pytest kit_aware + kit_vitals + lean_core + character_schema + identity_onboarding: 73 passed.

## History

- 2026-08-14T19:50:00Z  reviewed perfect → done  [gk-t8n2wp]
- 2026-08-14T19:42:00Z  verified → in-review, review dispatched  [gk-t8n2wp]
- 2026-08-14T19:36:00Z  doc-grounding confirmed — user pre-confirmed "do ALL of this now"; implementer dispatched  [gk-t8n2wp]
- 2026-08-14T19:30:58Z  claimed; doc-grounding confirmed — user pre-confirmed "do ALL of this now"  [gk-t8n2wp]
- 2026-08-14T18:52:00Z  parent → trust-the-agent  [gk-t8n2wp]
- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-14T17:27:15Z  blockedBy trimmed — executable-world-kit + identity-onboarding-wiring are done  [gk-a8r14q]

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

## Triage note 3 (2026-08-13, fable-sott1, from review-detox round 1)

Pre-existing in both create-character files, fix while restructuring:
- "Step 1 - Introduction" jumps to "Step 3 - Background" (numbering gap) in
  both the agent (:105-110) and command (:83-88).
- The agent's save-json example (:150) omits visual_appearance even though
  :85-89 mandates authoring it.
