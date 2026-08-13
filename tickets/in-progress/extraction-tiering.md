---
slug: extraction-tiering
title: The cap ranks into a background tier instead of deleting the book's cast
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T21:38:35Z
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-13T21:38:35Z
---

## Parent

State of the Table (prds/state-of-the-table.md) · Trust the Agent review (artifact 1a6acb14)

## Category

enhancement

## What to build

Supersedes extraction-cap-importance (moved to wontfix; its triage notes fold
in here). The import pipeline pre-makes the most creative decision of an
import — who exists — and papers over the damage:

1. **lib/extraction_cap.py:24,117** — DEFAULT_LIMIT=30 per type;
   `cap_campaign` OVERWRITES the entity files with survivors only. A 65-NPC
   book permanently loses 35 characters; mention-frequency scoring kills
   vivid one-scene characters. Change: rank as today, but write the tail to a
   background tier (e.g. `background: true` flag on the entity, or a
   `background/` sibling file — pick whichever the runtime managers and
   scene-context queries handle most cheaply) that the GM can promote
   mid-play. Active-tier default can stay 30 for context discipline; nothing
   is deleted. Also import PLOT_TYPES from schemas for `_PLOT_TYPE_WEIGHT`
   and stop ranking threat/mystery at the unknown floor (from the superseded
   ticket).
2. **lib/minor_stubs.py stub factory + lib/integrity_gate.py:110-116** — with
   nothing deleted, references resolve to real (background) entities; retire
   the generic-placeholder invention (keep stub creation only for entities
   the BOOK references but extraction never produced).
3. **lib/location_reconcile.py:24-35** — the six-word/slash/"unknown"
   heuristic silently drops place references and their edges. Stub-and-mark
   (low_confidence: true) instead of dropping; persist dropped names into the
   campaign rather than stdout only.
4. gm-extract.sh cap/reconcile output explains the tiering; import.md + 
   docs/flows/import-a-book.md updated + restamped (the "cap deliberately
   breaks the graph" claim changes).

## Acceptance criteria

- [ ] After a capped import fixture (50+ NPCs), every extracted entity exists on disk — 30 active, the rest background-tier — and a background NPC can be promoted via existing tools (gm-npc.sh or a small promote verb).
- [ ] No generic placeholder is created for an entity that extraction produced; the gate still strict-passes.
- [ ] A 7-word location reference survives as a low-confidence stub with its edge intact.
- [ ] Threat/mystery plots rank at least at side's weight in the cap.
- [ ] Scene context / search do not surface background entities unprompted (context discipline preserved) — test asserts AVAILABLE-cast-style queries can still find them.
- [ ] Full suite passes; import-a-book.md restamped.

## Out of scope

Shard extraction (T2.5); the validate gate (landed); entity enhancement.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review; supersedes extraction-cap-importance)  [fable-sott1]
- 2026-08-13T21:38:35Z  claimed  [fable-sott1]
- 2026-08-13T21:40:06Z  doc-grounding confirmed  [fable-sott1]
