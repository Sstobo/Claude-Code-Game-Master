---
slug: threat-clock-seeding
title: Seed headline threat clocks from the book at import
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: []
createdAt: 2026-06-06T16:47:47Z
updatedAt: 2026-06-06T16:47:47Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

`lib/threat_clocks.py` exists as a system (named pressure; full clock = beat due) but
import seeds ZERO clocks. The book's headline pressure (DCC: the 10-day floor
collapse) lives only as prose inside a plot description, not as an actual clock that
drives the world. Add an import step that extracts the book's primary time/pressure
threats and creates real threat-clock entries (name, size/segments, what a full clock
triggers, link to the driving plot). At minimum seed the dominant clock; capture
secondary clocks where the source is explicit.

## Acceptance criteria

- [ ] Import creates ≥1 threat-clock entry from the source's headline pressure.
- [ ] DCC import seeds the 10-day Iron Tangle collapse clock with sensible segments + a full-clock consequence.
- [ ] Each seeded clock links to its driving plot/location where applicable.
- [ ] Clocks are real `threat_clocks` entries (queryable via the existing tooling), not prose.
- [ ] Seeding is reported to the user during import.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-06-06T16:47:47Z  created → ready  [ship-it]
