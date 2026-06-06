---
slug: import-integrity-gate
title: Post-extraction reconciliation + fail-on-unresolved gate
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: import-pipeline-hardening
blockedBy: [alias-runtime-resolver]
createdAt: 2026-06-06T16:37:48Z
updatedAt: 2026-06-06T16:37:48Z
---

## Parent

prds/import-pipeline-hardening.md

## Category

enhancement

## What to build

Add a post-extraction integrity pass (new `dm-extract.sh` subcommand or step in the
normalize flow) that, after cap + before play: collects every cross-reference
(plot.npcs, plot.locations, npc.location_tags, location.connections.to) and
canonicalizes each to a real entity key using the shared alias normalizer. If a ref
matches an entity via alias, rewrite it to the canonical key OR record the variant
in that entity's `aliases`. Specifically set Donut's canonical key + alias so all
21 "Princess Donut" plot refs resolve. The gate FAILS the import (non-zero exit +
clear report) if any ref is still unresolved after alias matching and after the
missing-location reconcile.

## Acceptance criteria

- [ ] New integrity step runs in the import flow after cap-extraction-30.
- [ ] Every plot/npc/location cross-reference resolves to a canonical key or is recorded as an alias.
- [ ] Donut entity carries canonical key + "Princess Donut" alias; all plot refs to her resolve.
- [ ] Unresolved refs cause the gate to fail with a report listing each (file, entity, ref).
- [ ] Reuses the shared normalizer from alias-runtime-resolver (no duplicate logic).
- [ ] import.md documents the gate as a required step.

## Verification

Lane: agent

## Blocked by

alias-runtime-resolver

---

## QA Reports

## History

- 2026-06-06T16:37:48Z  created → ready  [ship-it]
