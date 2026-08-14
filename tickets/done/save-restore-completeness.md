---
slug: save-restore-completeness
title: Whole-campaign saves, versioned, with rotating autosaves
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: trust-the-agent
blockedBy: [kit-block-in-context]
claimedBy: gk-t8n2wp
claimedAt: 2026-08-14T19:30:58Z
changedFiles: [lib/session_manager.py, docs/schema-reference.md, docs/log.md, tests/test_save_restore.py]
resolution: whole-campaign saves, save_version 1; legacy warns partial; autosaves rotate to 3
reviewRounds: 1
implementer: a0980324-f80f-43fe-a8e0-b7de2b5a68c2
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-14T19:53:00Z
---

## Parent

Trust the Agent (prds/trust-the-agent.md)

## Category

bug

## What to build

`create_save` (lib/session_manager.py:279-286) snapshots 6 of ~13 stateful
files — omitting `plots.json`, `items.json`, `threat-clocks.json`,
`campaign-memory.json`, `world-bible.json`, `ruleset.json`, `combats.json` —
so `restore_save` (:326-341) reverts part of the world and leaves quests and
clocks at present time: a world that never existed. Meanwhile
`.claude/hooks/session-autosave.sh` writes a full new snapshot every turn,
forever.

1. Snapshot and restore every stateful campaign file (enumerate from the
   campaign dir contract in docs/schema-reference.md; skip chunks/vectors/
   images and derived caches).
2. Stamp `save_version` in the snapshot; on restore, treat pre-version saves
   as partial and say so in the output rather than silently mixing state.
3. Autosaves rotate: the Stop-hook path writes `autosave` keeping at most N
   (default 3) autosave snapshots; named manual saves are untouched.
4. Update `docs/schema-reference.md:434-452` (save shape) in the same commit.

## Acceptance criteria

- [x] Round-trip test: snapshot → mutate plots, clocks, items, NPCs, character → restore → every stateful file deep-equals the snapshot state.
- [x] Restoring a legacy (pre-version) save prints a partial-restore warning listing what was not covered.
- [x] After 10 autosave cycles, at most N autosave snapshots exist; named saves persist.
- [x] `docs/schema-reference.md` save section restamped and true.

## Out of scope

Moving the memory refresh off the Stop-hook critical path (Tier 2/ideas);
save-file compression.

## Verification

Lane: agent

## Blocked by

kit-block-in-context (session_manager.py one-writer chain)

---

## QA Reports

### 2026-08-14T19:53:00Z — reviewed perfect [c5209227]
No correctness, regression, or criteria-gap findings.

### 2026-08-14T19:42:00Z — verified [gk-t8n2wp]
Round-trip restores plots/clocks/items/NPCs/character/combat_state/fallen; legacy restore warns plots.json+items.json+threat-clocks.json and leaves mixed plots; 10 autosaves rotate to 3 and named saves persist. `uv run pytest tests/test_save_restore.py` 4 passed.

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-14T19:53:00Z  reviewed perfect → done  [gk-t8n2wp]
- 2026-08-14T19:42:00Z  verified → in-review, review dispatched  [gk-t8n2wp]
- 2026-08-14T19:36:00Z  doc-grounding confirmed — user pre-confirmed "do ALL of this now"; implementer dispatched  [gk-t8n2wp]
- 2026-08-14T19:30:58Z  claimed; doc-grounding confirmed — user pre-confirmed "do ALL of this now"  [gk-t8n2wp]
- 2026-08-14T18:52:00Z  blocked → ready; parent trust-the-agent; blockedBy kit-block-in-context  [gk-t8n2wp]
- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
