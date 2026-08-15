---
slug: entity-dedupe-materialize
title: Dedupe NPC identity on the materialize path (no second Aratus)
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: living-world
blockedBy: []
claimedBy: ss-rt14b
claimedAt: 2026-08-15T15:50:00Z
changedFiles: [lib/entity_aliases.py, lib/play_pack.py, tests/test_entity_dedupe_materialize.py]
resolution: bidirectional alias merge on the play-pack materialize path (stub+materialize collapse to one canonical record; fleshed distinct NPCs never over-merged)
reviewRounds: 2
implementer: null
createdAt: 2026-08-15T15:33:50Z
updatedAt: 2026-08-15T16:03:00Z
---

## Parent

Living World (prds/living-world.md)

## Category

bug

## What to build

`npcs.json` held Aratus twice — once as a long play-pack-named stub ("Aratus the
Kothian (a fat, boastful kidnapper up from Koth)") and once as the real
materialized record ("Aratus"). The `alias-dedupe-integrity` guard (done) isn't
covering the play-pack → materialize path.

- Extend the existing dedup/alias guard so that materializing an NPC that already
  exists as a present-cast stub resolves to ONE record (merge onto the canonical
  name), rather than creating a second.
- Reproduce with the conan play-pack cast first, then fix.

## Acceptance criteria

- [x] Reproduction: materializing a play-pack stub NPC currently yields two
      records; documented in the QA report.
- [x] After the fix, the stub and the fleshed record resolve to a single NPC
      entry keyed on the canonical name.
- [x] Existing `alias-dedupe-integrity` behavior for other paths is preserved
      (no regression).
- [x] The conan `npcs.json` duplicate is not reintroduced by a re-materialize.
- [x] (review) `from_book(cdir, "Aram")` when a non-stub "Aram Baksh" record already exists (real description, own tags/events) MUST create a distinct "Aram" record and leave "Aram Baksh" un-renamed, un-re-keyed, and un-demoted — no over-merge on a shared leading token when the longer record is not a descriptive stub.

## Out of scope

- Cleaning the already-dead Aratus data in conan by hand (the fix should make
  re-runs correct; a one-off data cleanup can ride with conan-backfill if needed).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-15T16:03:00Z — pass [reviewer]
reviewed: perfect (followup) — over-merge fix confirmed correct and complete: Aram/Aram-Baksh mints a distinct record and leaves the fleshed one intact; stage→materialize stub collapse still works; `reuse_existing_key` byte-for-byte unchanged; gate distinguishes surname suffix from epithet/stub. All 6 test files pass.

### 2026-08-15T16:00:00Z — fix verified, followup review dispatched [ss-rt14b]
- Over-merge gate moved to play_pack (`_merge_is_safe` / `_long_key_is_epithet`): the reverse short→long merge only fires onto a stub/epithet, never a fleshed distinct NPC. `resolve_or_merge_key` still proposes the candidate; the caller refuses for a plain-surname suffix and mints the distinct short-named record.
- New guard test `test_short_name_never_corrupts_fleshed_longer_named_npc`: `from_book("Aram")` vs a fleshed "Aram Baksh" → two distinct un-aliased records, "Aram Baksh" intact.
- Independent run: 54 passed (all six suites). `reuse_existing_key` byte-for-byte unchanged (only `resolve_or_merge_key` docstring touched). stage→materialize Aratus collapse still works.

### 2026-08-15T15:57:00Z — fail [reviewer]
reviewed: needs-changes
- entity_aliases.py:166 — reverse branch `k_norm.startswith(q_norm + " ")` merges a short query onto ANY longer key leading with those tokens: `resolve_or_merge_key("Aram", {"Aram Baksh": {}})` → "Aram Baksh" (verified). Cannot distinguish epithet suffix ("the Kothian (...)") from a surname ("Baksh") → two distinct NPCs sharing a first name over-merge.
- play_pack.py:297 / _merge_npc — worse: from_book("Aram") with a fleshed "Aram Baksh" routes into _merge_npc, `_canonical_survivor` picks shorter "Aram" as survivor → the richer "Aram Baksh" record is del'd, re-keyed to "Aram", name overwritten, "Aram Baksh" demoted to alias. Existing entity silently corrupted; the intended new distinct NPC gets no record. `_is_stub_desc` is computed but only gates description-clobbering, not the merge decision.
Fix direction: gate the reverse short→long merge on the longer record being a descriptive STUB (`_is_stub_desc` / "Present in ..." / parenthetical or leading-"the" epithet), not any bare-token prefix. Preserves the stage→materialize case (stub carries "Present in ..."), blocks the Aram/Aram Baksh corruption.

### 2026-08-15T15:55:00Z — verified [ss-rt14b]
- New `resolve_or_merge_key()` matches BOTH directions (descriptive-query→short-key and short-query→long-descriptive-key); `reuse_existing_key` left untouched so its callers (location_reconcile, minor_stubs) are unaffected.
- `apply_stage` + `from_book` route through it: stub and materialize collapse to ONE record keyed on the canonical short proper name, descriptive form → `aliases`, `tags.locations`/`events`/richer description preserved. Return shapes unchanged.
- Reproduction covered both orders; over-merge guard ("Yara" keeps its own record); reverse direction preserved.
- Independent run: 53 passed across test_entity_dedupe_materialize + test_alias_resolver + test_integrity_gate + test_play_pack + test_location_reconcile + test_minor_stubs. No regression to the existing alias/integrity machinery.
- docs: none — entity-graph.md makes no directional claim about reuse_existing_key; module docstring updated in entity_aliases.py itself.

## History

- 2026-08-15T16:03:00Z  followup review perfect → done + committed  [ss-rt14b]
- 2026-08-15T16:00:00Z  fix verified (54 tests) → followup review dispatched  [ss-rt14b]
- 2026-08-15T15:57:00Z  review needs-changes (over-merge on shared leading token) → re-delegating fix; reviewRounds 2  [ss-rt14b]
- 2026-08-15T15:55:00Z  verified → in-review  [ss-rt14b]
- 2026-08-15T15:50:00Z  doc-grounding confirmed (blanket authorization: "do all the tickets")  [ss-rt14b]
- 2026-08-15T15:50:00Z  claimed  [ss-rt14b]
- 2026-08-15T15:33:50Z  created → ready  [main]
