---
type: Gotcha
title: Extractor output silently vanishes on the wrong wrapper key
description: The merge branches on filename and key name; a mismatch drops the entities with no error, and the whole loop swallows exceptions.
sources:
  - { resource: /lib/agent_extractor.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# Extractor output silently vanishes on the wrong wrapper key

Extraction agents write JSON files that `AgentExtractor` merges. The merge decides how to
read a file **by its filename** (`lib/agent_extractor.py:292-337`), and every way of
getting that wrong loses data without raising.

## Two shapes, chosen by filename

| File | Expected shape |
|---|---|
| `npcs.json`, `locations.json`, `items.json`, `plots.json` | **unwrapped** — the whole file is the entity map: `{"Donut": {...}}` |
| anything else (`agent-*.json`) | **wrapped** — `{"npcs": {...}, "locations": {...}}` |

Write a wrapped `{"npcs": {...}}` into `npcs.json` and the merge takes the file as the
entity map: you get one entity named `"npcs"` whose body is the real cast. Write an
unwrapped map into `agent-npcs.json` and none of the recognized keys are present, so
nothing merges at all.

`to_dict` accepts a list as well as a dict and keys it by each item's `name`, so a
top-level array survives either way.

## The wrapped path has no `plots` key

It reads `plot_hooks` (`lib/agent_extractor.py:328`) — **not** `plots`, even though the
unwrapped file is called `plots.json` and the runtime file is `plots.json`. An agent that
emits `{"plots": {...}}` in a wrapped file loses every plot, silently. The rename happens
on the unwrapped path too: `plots.json` merges into `merged['plot_hooks']`.

## Nothing fails loudly

The per-file body is wrapped in `except Exception as e` that prints one line and continues
(`lib/agent_extractor.py:339`). A malformed file, a permissions error, or an unexpected
type produces a single line in a long import log, and the run reports success with a
smaller `extraction_summary`.

**How to catch it:** compare `extraction_summary` counts against what the preview step
promised. A count of zero for one type, or an entity literally named `npcs`, is this bug.
`lib/agent_extractor.py` is the authority — re-derive from the merge block rather than from
any schema doc, including this one.

## Related

- [Extraction schema is not the runtime schema](extraction-vs-runtime-schema.md)
- [Importing a book](../flows/import-a-book.md)
