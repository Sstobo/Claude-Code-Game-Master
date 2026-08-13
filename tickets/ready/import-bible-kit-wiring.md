---
slug: import-bible-kit-wiring
title: Author the world bible before the kit; wire book_bible derivation; delete the 5e heredoc
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: [import-extraction-repair]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T15:47:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Import Step 6.7 (`.claude/commands/import.md:424`) reads `world-bible.json`,
which no earlier step writes — FileNotFoundError on every clean import. And
Step 6.5-6.6 (import.md:336-345) hand-pastes a generic 5e ruleset heredoc,
while `draft_ruleset_from_bible` (lib/book_bible.py:65) and
`bible_to_campaign_rules` (lib/book_bible.py:55) have zero production callers.

Make the flow match the documented design ("bible → kit → overview → voice"):

1. Add an import step (before kit derivation) that authors `world-bible.json`
   from large-span source reads — expose via `gm-extract.sh draft-bible` or a
   `world_bible.py` CLI verb, whichever is smaller given the existing
   `lib/world_bible.py` surface.
2. Replace the ruleset heredoc with a call chain: bible →
   `draft_ruleset_from_bible` → `ruleset.json` (including the machine-readable
   `kit` field), then `bible_to_campaign_rules` → `campaign_rules` in the
   overview.
3. Step 6.7's bible read is now guaranteed to succeed; keep a clear error path
   if the bible draft failed.
4. Restamp `docs/flows/import-a-book.md` (and `author-a-world.md:77`'s cross
   reference) so the docs describe what ships.

## Acceptance criteria

- [ ] A fresh import (test may drive the steps programmatically) produces `world-bible.json` before any ruleset exists, and Step 6.7's read cannot hit FileNotFoundError.
- [ ] `draft_ruleset_from_bible` and `bible_to_campaign_rules` have production callers on the import path; the 5e heredoc is gone from import.md.
- [ ] The produced `ruleset.json` carries a `kit` field and does not include `spell-caster` in `active_agents` for non-dnd5e kits.
- [ ] `tests/test_book_bible_import.py` still passes; a new test covers the bible→ruleset→campaign_rules chain.
- [ ] `docs/flows/import-a-book.md` restamped and true.

## Out of scope

Rendering rules from `signature_systems()` at play time (kit-block-in-context).
Shard extraction, resumable driver (Tier 2).

## Verification

Lane: agent

## Blocked by

import-extraction-repair

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
