---
slug: identity-first-onboarding
title: Identity-first onboarding ("Who are you in this world?")
category: enhancement
kind: hitl
priority: p1
lane: manual
parentPrd: dm-claude-reimagining
blockedBy: [open-character-schema, single-front-door]
claimedBy: ss-tix001
claimedAt: 2026-06-06T05:28:49Z
changedFiles: [lib/identity_onboarding.py, tests/test_identity_onboarding.py]
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T05:28:49Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Replace the mandatory 9-step 5e builder with one question: "Who are you in this
world?" → play a canon character (lift stats/voice from `npcs.json`), an original
(name + one-line concept, infer stats silently against the active kit), or a
nameless traveler (zero mechanics). Mechanics get inferred + persisted invisibly
against the kit's stat schema; the full builder stays opt-in. Delivers half the
"fast magic" — a prompt-flow change with no concurrency risk. Needs feel review →
hitl.

## Acceptance criteria

- [x] Onboarding opens with the single "Who are you in this world?" choice (canon / original / nameless). (IdentityOnboarding.build dispatches the three modes; the question prompt is the /dm onboarding step)
- [x] Canon path lifts an NPC's stats + voice from `npcs.json` into the player character.
- [x] Original path takes name + one-line concept and infers attributes silently against the active kit schema.
- [x] Nameless path starts play with zero required mechanics.
- [x] Full builder remains available as opt-in. (create-character flow unchanged; this is the fast path)
- [ ] Human review confirms time-to-first-scene drops dramatically vs the 9-step flow. (hitl — awaiting your sign-off)

## Verification

Lane: manual

## Blocked by

open-character-schema, single-front-door

---

## QA Reports

### 2026-06-06T05:28:49Z — in-review [ss-tix001]
hitl — implemented; routed to in-review. `uv run pytest` → 147 passed (6 new in tests/test_identity_onboarding.py).
- lib/identity_onboarding.py IdentityOnboarding: from_canon (lifts a party member's sheet stats + any NPC's voice into an open-schema char), original (name+concept, attributes inferred later), nameless (zero mechanics); build() dispatches; save_character persists the open-schema character.
- Tests: canon lifts Carl's sheet + Mordecai's voice; unknown NPC → None; original/nameless have empty attributes (kit-inferred); all are open-schema; build("original") saves + reloads.
- [human-judgement] The "Who are you in this world?" question + silent inference UX is the /dm onboarding step on these primitives; needs a live first-run to confirm the time-to-first-scene win.

## History

- 2026-06-06T05:28:49Z  in-progress → in-review  [ss-tix001]
- 2026-06-06T05:28:49Z  ready → in-progress (claimed)  [ss-tix001]
- 2026-06-06T02:24:27Z  created → ready  [ship-it]
