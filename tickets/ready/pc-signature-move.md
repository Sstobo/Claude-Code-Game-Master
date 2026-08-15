---
slug: pc-signature-move
title: Non-5e PCs get a signature move (end features:[])
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: world-kit-systems
blockedBy: [system-primitives-lib]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:33:50Z
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

- [ ] A character created under a custom/non-5e kit has ≥1 entry in `features`.
- [ ] When the kit has instantiated `systems`, at least one granted move
      references or interacts with one of them.
- [ ] The dnd5e branch (race/class/features) is unchanged.
- [ ] Persisted via the existing `gm-player.sh save-json` path.

## Out of scope

- A full per-genre move library — one grounded signature move is the bar.

## Verification

Lane: agent

## Blocked by

system-primitives-lib

---

## QA Reports

## History

- 2026-08-15T15:33:50Z  created → ready  [main]
