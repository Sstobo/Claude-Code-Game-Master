---
type: Module
title: The entity graph and name resolution
description: Why entities cross-reference by name, how the alias resolver keeps that from breaking, and the ordered repair passes an import runs before the gate.
sources:
  - { resource: /lib/entity_aliases.py }
  - { resource: /lib/entity_manager.py }
  - { resource: /lib/connection_normalize.py }
  - { resource: /lib/location_reconcile.py }
  - { resource: /lib/integrity_gate.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# The entity graph and name resolution

Campaign state is a graph held together by **names, not IDs**: `plots.npcs`,
`plots.locations`, `npc.location_tags`, `location.connections[].to`. That choice makes
extracted JSON readable and hand-editable, and it makes every naming wobble a broken
edge — a plot referencing "Princess Donut" when the NPC key is "Donut" resolves to
nothing at runtime.

Two mechanisms absorb the wobble: **loose resolution at runtime**, and
**canonicalization at import time**. They share one resolver, which is why they cannot
disagree.

## One resolution order, four steps of increasing looseness

`resolve_entity_name` (`lib/entity_aliases.py:47`): exact → case-insensitive → explicit
`aliases` on the target → normalized equality. Normalization lowercases, strips
parentheticals and punctuation, and drops **leading title tokens** from a fixed set
(`lord`, `captain`, `the`, `saint`, …).

Two consequences worth knowing before you rely on it:

- **Titles are stripped only from the front.** "Donut the Princess" does not normalize
  to "Donut"; "Princess Donut" does.
- **A query that is nothing but titles normalizes to `""` and never matches.** That is a
  guard, not an accident — otherwise every empty-ish reference would match the first
  entity whose name also normalized to empty.

`EntityManager._get_entity` routes all runtime lookups through it, so every manager
inherits alias tolerance for free. Nothing needs to call the resolver directly.

## Import repairs run in a fixed order, and the order is the design

Each pass exists because the pass after it would otherwise fail on work it could have
fixed. Running them out of order produces a strict-mode failure on references that were
repairable.

1. **cap** — drop all but the top-N entities per type. *Creates* dangling references, by
   design. See [importing a book](../flows/import-a-book.md).
2. **`connection_normalize`** — canonicalize resolvable `connections[].to`, and move
   rule-phrases that are not places at all ("Any line", "Transfer stations ending in 1")
   into the location's `notes` so reconcile doesn't silently delete them.
3. **`location_reconcile`** — for each location reference that still doesn't resolve:
   **stub** it (a lightweight node wired bidirectionally to the most-connected hub) if the
   name looks like a place, or **drop and report** it if it's descriptive prose.
4. **`integrity_gate`** — resolve every remaining cross-reference to a canonical key,
   rewrite the reference in place, and record the variant as an `aliases` entry on the
   target. Strict mode exits non-zero on anything unresolved.

Step 4's alias recording is what makes the repair permanent: the drifted spelling that
was rewritten is remembered on the target, so a later reference using the old spelling
resolves at runtime through step 3 of the resolver.

`run_gate(campaign_dir, strict=False)` (or `--no-strict`) reports without failing — the
right call when diagnosing an import, never the right call inside one.

## Related

- [Importing a book](../flows/import-a-book.md) — the full pipeline these passes sit in
- [NPC model](npc-model.md) — the location-tag field these passes read
- [The NPC location tag split](../gotchas/npc-location-tag-split.md)
