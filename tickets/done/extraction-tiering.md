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
changedFiles: [lib/session_manager.py (one hunk), lib/plot_manager.py, lib/entity_enhancer.py, lib/npc_manager.py, tools/gm-enhance.sh, docs/import-guide.md, docs/schema-reference.md, lib/extraction_cap.py, lib/minor_stubs.py, lib/integrity_gate.py, lib/location_reconcile.py, tools/gm-extract.sh, '.claude/commands/import.md', docs/flows/import-a-book.md, docs/modules/entity-graph.md, tests/test_extraction_tiering.py, tests/test_extraction_cap.py, tests/test_location_reconcile.py]
resolution: the cap tiers into background instead of deleting; heuristic drops become marked stubs; everything discloses
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-13T22:50:39Z
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

- [x] After a capped import fixture (50+ NPCs), every extracted entity exists on disk — 30 active, the rest background-tier — and a background NPC can be promoted via existing tools (gm-npc.sh or a small promote verb).
- [x] No generic placeholder is created for an entity that extraction produced; the gate still strict-passes.
- [x] A 7-word location reference survives as a low-confidence stub with its edge intact.
- [x] Threat/mystery plots rank at least at side's weight in the cap.
- [x] Scene context / search do not surface background entities unprompted (context discipline preserved) — test asserts AVAILABLE-cast-style queries can still find them.
- [x] Full suite passes; import-a-book.md restamped.
- [x] (review) Enhancement batch skips background entities; the import.md claim is true.
- [x] (review) Synonym plot types rank at their canonical weight in the cap (main quest ranks as main).
- [x] (review) The rule-phrase drop test cannot classify a real place name containing 'via'/'upper level'/'lower level' as prose.
- [x] (review) import-guide.md + schema-reference.md document the new background/low_confidence fields.
- [x] (review) promote clears the background flag; active count excludes malformed entries.
- [x] (review) Background plots do not surface in STORY THREADS (session_manager path — pending collision decision).

## Out of scope

Shard extraction (T2.5); the validate gate (landed); entity enhancement.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-13T22:50:39Z — pass [review-tiering-2]
reviewed: perfect (round 2; all seven closed, no new defect). session_manager
staged as the single two-line hunk only — the other session's preference and
pacing hunks remain uncommitted in the worktree. Cosmetic nit (gm-enhance
usage wrap) left as-is.

### 2026-08-13T22:47:33Z — verified (fix round 2) [fable-sott1]
20/20 tiering tests; STORY THREADS skips background plots (2-line hunk,
other session's hunks untouched, verified 3 hunks total); gm-plot threads
discloses the held-back count; enhancement bounded to active tier; synonym
weights fixed; rule-phrase test confined to connections; reviewer's three
place names survive as stubs. Implementer full suite 451 passed.

### 2026-08-13T22:00:00Z — fail [review-tiering]
reviewed: needs-changes
1. import.md claim false: enhancement now covers the whole extraction (~5x cost) — background filter needed in list_unenhanced.
2. _active_plot_threads has no background filter — STORY THREADS can be all-background (session_manager.py COLLIDED, decision pending).
3. plot_type_weight runs before type normalization: 'main quest'/'conflict' fall to other=1, BELOW optional=7 — spine backgrounded.
4. _is_rule_phrase reuse deletes real places ('The Lower Level Vault', 'Kandahar via the Zhaibar Pass') and records them as rule prose.
5. import-guide.md cap row stale; schema-reference.md lacks background/low_confidence fields.
6. No scene-context test; promote leaves background:true; active count over-states on malformed entries.
Verified good: idempotent both directions, nothing deleted, gate passes, facts shape exact, canonical weights correct.

### 2026-08-13T21:52:24Z — verified [fable-sott1]
10 new tiering tests + rewritten cap/reconcile tests pass; nothing deleted
(51-NPC fixture keeps all 51, 30 active); presence verified tag-gated so
background entities cannot leak into scenes without a location tag; both
claiming docs rewritten + restamped. Scope note: two existing TEST files
edited beyond the list (they pinned retired behavior) — no production file
outside scope. Implementer full suite 409 passed.

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review; supersedes extraction-cap-importance)  [fable-sott1]
- 2026-08-13T21:38:35Z  claimed  [fable-sott1]
- 2026-08-13T21:40:06Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-13T21:52:24Z  verified → in-review  [fable-sott1]
- 2026-08-13T22:00:00Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T22:47:33Z  fix round 2 verified — followup review dispatched  [fable-sott1]
- 2026-08-13T22:50:39Z  review perfect → done, committed  [fable-sott1]
