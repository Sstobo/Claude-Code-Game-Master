---
slug: pc-signature-move
title: Non-5e PCs get a signature move (end features:[])
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: world-kit-systems
blockedBy: [system-primitives-lib]
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:07:00Z
changedFiles: [.claude/agents/create-character.md]
resolution: create-character generic spine now grants a signature move into features (kit-systems-tied), ending empty features on non-5e PCs
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:12:00Z
---

## Parent

World-Kit Systems (prds/world-kit-systems.md)

## Category

enhancement

## What to build

Non-5e-kit characters come out of creation as bare stat blocks with
`features: []` (Conan has no mechanical fingerprint). Kit-aware character creation
should grant every PC at least one signature move, drawn from the kit's systems
where they exist.

- The generic (non-dnd5e) branch of `create-character` authors ≥1 signature
  move/feature tied to the kit (and to the kit's instantiated systems when
  present).
- Persisted onto `character.json` `features`.

## Acceptance criteria

- [x] A character created under a custom/non-5e kit has ≥1 entry in `features`.
      *(generic spine now has a Signature move step: "never an empty `features`")*
- [x] When the kit has instantiated `systems`, at least one granted move
      references or interacts with one of them. *(step: "Draw it from the kit's
      declared `systems`/`signature_systems` when it has them")*
- [x] The dnd5e branch (race/class/features) is unchanged. *(only the generic
      spine section was edited)*
- [x] Persisted via the existing `gm-player.sh save-json` path. *(save_character.py:147
      `"features": character_data.get('features', [])` — verified persisted; save-json example updated to include features)*

## Out of scope

- A full per-genre move library — one grounded signature move is the bar.

## Verification

Lane: agent

## Blocked by

system-primitives-lib

---

## QA Reports

### 2026-08-15T16:12:00Z — verified, fast-lane [ss-rt14b]
- Generic (non-dnd5e) spine gains a "Signature move" step (walk item 5 + Step 5 detail): grant ≥1 signature ability tied to the kit's `systems`/`signature_systems` (or concept), persist in `features`, never empty, never 5e class features on a non-dnd5e kit. save-json example updated to carry `features`.
- dnd5e branch untouched. Persistence confirmed: `features/character-creation/save_character.py:147` keeps `features` from the input JSON.
- Prompt-only change (agent guidance); fast-lane (no code logic to adversarially test — the assertable half, features persistence, is verified). True end-to-end proof is a create-character play-through.

## History

- 2026-08-15T16:12:00Z  verified (prompt-only, fast-lane) → done + committed  [ss-rt14b]
- 2026-08-15T16:07:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:07:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
