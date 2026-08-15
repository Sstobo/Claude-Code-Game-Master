---
slug: lazy-npc-enrichment
title: Stub NPC gains an interior on first real interaction
category: enhancement
kind: hitl
priority: p2
lane: manual
parentPrd: living-world
blockedBy: []
claimedBy: ss-rt14b
claimedAt: 2026-08-15T16:20:00Z
changedFiles: [.claude/skills/gm-social/SKILL.md]
resolution: gm-social step 1b directs the GM to flesh a stub NPC (goal/secret/voice via set-inner) on first meaningful contact, never pre-built
reviewRounds: null
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:20:00Z
---

## Parent

Living World (prds/living-world.md)

## Category

enhancement

## What to build

Present NPCs correctly start as one-line stubs (don't pre-write). But the moment
the player meaningfully engages one, it should become a person — a want, a
secret, a line — and persist, so nobody the player actually talks to stays a
"neutral stub." This preserves the anti-gazetteer rule while fixing the flatness.

- Add guidance to the social flow (`gm-social` / CLAUDE.md): on first meaningful
  interaction with a stub NPC, author an interior (want / secret / voice line)
  and persist via existing `gm-npc.sh set-inner` / `update`.
- No new store; uses the fields NPCs already have.

## Acceptance criteria

- [x] Social-flow guidance instructs the GM to enrich a stub on first meaningful
      interaction and persist it. *(gm-social step 1b: `set-inner --goal --secret
      --voice` — verified those are real flags)*
- [~] Play-through: engaging a stub NPC results in a persisted interior
      (mood/goal/secret + a line) on that NPC's record. *(prompt-driven — set-inner
      is the real persistence path; end-to-end proof is a play-through)*
- [x] Uninvolved stubs are left thin (no pre-building). *("Only on real contact —
      do not pre-flesh NPCs the player never engages")*

## Out of scope

- Automatic/background enrichment of NPCs the player never engages.

## Verification

Lane: manual — verified by a human play-through confirming an engaged stub gains
and keeps an interior while untouched stubs stay thin.

## Blocked by

None.

---

## QA Reports

### 2026-08-15T16:20:00Z — verified, fast-lane [ss-rt14b]
- gm-social SKILL.md gains step 1b: on first meaningful contact, author a want/secret/voice and persist via `gm-npc.sh set-inner --goal --secret --voice` (confirmed all four are real set-inner flags — corrected an initial draft that used the read-only `voice` verb). Anti-gazetteer preserved: "only on real contact, do not pre-flesh."
- Originally kind:hitl/manual; auto-run per the user's directive. Prompt-only; fast-lane. Persisted-interior play-through marked ~.

## History

- 2026-08-15T16:20:00Z  verified (prompt-only, fast-lane; hitl auto-run per user directive) → done + committed  [ss-rt14b]
- 2026-08-15T16:20:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T16:20:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
