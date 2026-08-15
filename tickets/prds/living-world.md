---
slug: living-world
title: Living World — remember people, seed pressure and connections
status: active
version: 1
supersedes: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T15:33:50Z
---

## Problem Statement

The engine remembers *facts* but forgets *people*, and it seeds a *stage* but no
*pressure*. Two round-table wounds:

- **Memory lands in the wrong place.** The most alive thread of the Conan
  session — the Brythunian wench whose eyes flicked to the back door, "she knows
  more than the rest" — was logged to `facts.json` (plot) and never attached to
  *her* NPC record. Next time she's on stage, the world can't recall it about
  her. `npc-memory-in-scene` (done) surfaces per-NPC `events`, but a fact that
  names an NPC doesn't reach that NPC. And the play-pack/materialize path spawns
  duplicate identities (Aratus existed twice) despite `alias-dedupe-integrity`
  (done) — the dedup guard isn't covering that path.
- **No spine.** `/new-game` and `/import` correctly stop at one stage (the
  anti-gazetteer rule is right and stays). But a stage without a countdown is
  inert: the source villain (Yara) shipped with no clock and no plan, and the
  world-bible's faction/geography graphs shipped with `edges: []` — a cast list,
  not a world with tensions.

This is the difference between "don't pre-build a gazetteer" (correct) and
"don't give the story an engine of pressure or a single wired relationship"
(a real gap).

## Solution

Close the two gaps without violating the anti-gazetteer philosophy:

1. **Anchor memory to people.** When a logged fact/event names a known NPC, it
   attaches to that NPC (their `events`) so it resurfaces under them in scene
   context — not just in the global facts log. Extend the existing dedup guard to
   the materialize path so one entity is one record.
2. **Seed pressure at creation.** Every new campaign ships with at least one
   antagonist/threat clock whose aim completes off-screen, and a few wired graph
   edges (2–4 real tensions), so the world has a countdown and a first
   relationship the moment play begins. Still one stage — but a *live* one.
3. **Enrich lazily.** A present NPC that starts as a one-line stub gains an
   interior (a want, a secret, a line) on first meaningful interaction — never
   pre-written, never a permanent "neutral stub."

## User Stories

1. As a player, when I come back to an NPC, I want the world to remember what I
   learned or did about *them*, so people feel persistent, not disposable.
2. As a player, I want the world to keep moving against me on a clock, so it
   feels alive whether or not I'm watching.
3. As the GM, I want the factions and places to already tension against each
   other, so I can pull on a real relationship instead of inventing one.
4. As a player, I want an NPC I actually talk to to become a person, so no one I
   engage stays a flavorless stub.

## Implementation Decisions

- **Entity-anchored memory.** A fact/note that references a known NPC name also
  appends to that NPC's `events` (or scene-context cross-references facts by
  entity), so per-NPC recall isn't lost to the general log. Prefer extending the
  existing `gm-note.sh` / `gm-npc.sh update` / scene-context path over a new
  store.
- **Dedup on materialize.** Extend the `alias-dedupe-integrity` guard to the
  play-pack → materialize → `npcs.json` path so a stub and its fleshed record
  resolve to one identity (no second Aratus).
- **Antagonist clock at creation.** `/import` and `/new-game` seed ≥1
  `threat-clocks.json` clock representing the antagonist's off-screen aim.
  Import can ground it in extracted plots; new-game authors from tone/themes.
- **Bible edges at creation.** The world-bible builder writes 2–4 `edges` into
  the faction and/or geography graphs instead of `edges: []`.
- **Lazy NPC enrichment.** On first meaningful interaction, a stub NPC is given
  an interior (want/secret/line) and persisted, via existing `gm-npc.sh`
  set-inner / update tooling plus GM guidance in the social flow.

## Testing Decisions

- A fact naming a present NPC landing on that NPC's `events` → agent.
- Materializing an NPC that already exists as a stub yielding one record, not two
  → agent.
- Creation writing ≥1 threat clock and ≥2 bible edges → agent.
- The GM enriching a stub on first interaction is prose/judgment → manual.

## Out of Scope

- Pre-building a gazetteer, a full cast, or keyed locations ahead of play — the
  anti-gazetteer doctrine is deliberately preserved.
- The World Index roster of what *could* be materialized (separate PRD
  `world-index`) — this PRD is about what happens once something is *in* play.
- Reworking the RAG/recall vector pipeline.

## Further Notes

- Resurrects the intent of the retired `make-the-world-remember` PRD, scoped to
  the specific gaps the round table found in live play.
- Anti-gazetteer guardrail (Sly Flourish's dissent, which the table accepted):
  thin locations, unbuilt dungeons, and one-line stubs are correct; only the
  broken persistence and the missing spine are defects.
