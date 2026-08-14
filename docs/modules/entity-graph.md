---
type: Module
title: The entity graph and name resolution
description: Why entities cross-reference by name, how the alias resolver keeps that from breaking, and the ordered repair passes an import runs before the gate.
sources:
  - { resource: /lib/entity_aliases.py }
  - { resource: /lib/entity_manager.py }
  - { resource: /lib/connection_normalize.py }
  - { resource: /lib/tag_unify.py }
  - { resource: /lib/location_reconcile.py }
  - { resource: /lib/integrity_gate.py }
  - { resource: /lib/extraction_cap.py }
  - { resource: /lib/minor_stubs.py }
  - { resource: /lib/plot_manager.py }
  - { resource: /lib/search.py }
generated: { by: cursor-grok-4.6, at: 2026-08-14T19:59:23Z }
---

# The entity graph and name resolution

Campaign state is a graph held together by **names, not IDs**: `plots.npcs`,
`plots.locations`, `npc.tags.locations`, `location.connections[].to`. That choice makes
extracted JSON readable and hand-editable, and it makes every naming wobble a broken
edge — a plot referencing "Princess Donut" when the NPC key is "Donut" resolves to
nothing at runtime.

Two mechanisms absorb the wobble: **loose resolution at runtime**, and
**canonicalization at import time**. They share one resolver, which is why they cannot
disagree.

## One resolution order, four steps of increasing looseness

`resolve_entity_name` (`lib/entity_aliases.py`): exact → case-insensitive → explicit
`aliases` on the target → normalized equality. Normalization lowercases, folds
diacritics, strips parentheticals and punctuation, and drops **leading title tokens**
from a fixed set (`lord`, `captain`, `the`, `saint`, …).

Two consequences worth knowing before you rely on it:

- **Titles are stripped only from the front.** "Donut the Princess" does not normalize
  to "Donut"; "Princess Donut" does.
- **A query that is nothing but titles normalizes to `""` and never matches.** That is a
  guard, not an accident — otherwise every empty-ish reference would match the first
  entity whose name also normalized to empty.

`EntityManager._get_entity` routes manager lookups through it, so NPC/location/plot
managers inherit alias tolerance for free. `WorldSearcher.get_npc` / `get_location`
call the same resolver — named lookups used to be exact-key only, so an alias that
`gm-npc.sh status` could see was invisible to `gm-context.sh`. One resolution path;
do not add a second.

## Import repairs run in a fixed order, and the order is the design

Each pass exists because the pass after it would otherwise fail on work it could have
fixed. Running them out of order produces a strict-mode failure on references that were
repairable.

0. **`tag_unify`** (inside normalize, since 2026-08-13) — collapse extraction-side
   `location_tags` into canonical `tags.locations`, so every pass below and the whole
   runtime read one field.
1. **cap** — rank each type and mark everything below the top-N `"background": true`.
   Nothing leaves the file, so **no edge is broken here**. See
   [importing a book](../flows/import-a-book.md).
2. **`connection_normalize`** — canonicalize resolvable `connections[].to`, and move
   rule-phrases that are not places at all ("Any line", "Transfer stations ending in 1")
   into the location's `notes` so reconcile doesn't silently delete them.
3. **`location_reconcile`** — attach a location reference to an existing node when
   the normalizer can, recording the phrasing as an `aliases` entry rather than
   stubbing a near-dupe. Otherwise **stub** it: a lightweight node wired bidirectionally
   to the most-connected hub and flagged `low_confidence: true`. Only a connection
   target that states a routing rule rather than a destination is dropped — the same
   reference arriving from a plot or a tag names a place and is always stubbed. Dropped
   names are written to `facts.json` under `dropped_references` rather than printed
   and lost.
4. **`minor_stubs`** — the same repair for `plot.npcs`: a reference that attaches to
   no NPC at all gets a minimal stub; a spelling that normalizes onto an existing
   record is aliased there and the plot ref rewritten to that key. Because the cap
   tiers rather than deletes, stubs fire only for characters the book's plots name
   and extraction never produced.
5. **`integrity_gate`** — resolve every remaining cross-reference to a canonical key,
   rewrite the reference in place, and record the variant as an `aliases` entry on the
   target. Strict mode exits non-zero on anything unresolved **or on near-duplicate
   keys** (two existing keys that normalize equal, e.g. Belit vs Bêlit).

A background entity is a **valid resolution target**: it sits in the same file under the
same key, so `plot.npcs: ["Walkon41"]` resolves whether or not Walkon41 is in the
playable core. Tiering therefore costs the gate nothing.

Step 5's alias recording is what makes the repair permanent: the drifted spelling that
was rewritten is remembered on the target, so a later reference using the old spelling
resolves at runtime through step 3 of the resolver.

The unresolved count cannot see duplicate keys. `Belit` and `Bêlit` each resolve to
themselves, so a gate that only counted dangling refs reported a clean import over two
nodes for one person. Near-duplicate keys are findings for that reason; stub and
reconcile refuse to mint the second node.

`run_gate(campaign_dir, strict=False)` (or `--no-strict`) reports without failing — the
right call when diagnosing an import, never the right call inside one.

## Background entities do not leak into scenes

For **NPCs, presence is decided by tags, not by tiering**. `npcs_present`
(`lib/entity_manager.py`) is the one who-is-here test: party member, or
case-insensitive exact equality of the current location against a `tags.locations`
entry. Session context, the place brief, and consequence tick all call it — they
used to disagree (substring search dropped untagged party members from the place
brief). A `background` flag neither widens nor narrows. A background NPC surfaces
exactly when the book put them in the room the party is standing in, which is the
correct answer, and never as an undifferentiated dump of the cast. CLI tag search
(`search_npcs_by_tag`) is discovery, not this test.

**Plots are filtered, because nothing else bounds them.** A thread has no location tag to
gate it, so `SessionManager._active_plot_threads` skips `background: true` plots and the
scene's STORY THREADS block stays the live arc rather than the book's every hook.
`PlotManager.get_active_threads` applies the same filter and `format_threads` prints
`(+N background plots …)`, so the held-back ones are disclosed rather than disappeared —
tiering that the GM cannot see reads as data loss.

## Related

- [Importing a book](../flows/import-a-book.md) — the full pipeline these passes sit in
- [NPC model](npc-model.md) — the location-tag field these passes read
- [The NPC location tag split](../gotchas/npc-location-tag-split.md)
