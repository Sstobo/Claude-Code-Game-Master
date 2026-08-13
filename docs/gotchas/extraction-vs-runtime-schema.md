---
type: Gotcha
title: The extraction schema is not the runtime schema
description: Extractor output and the live campaign files share filenames and differ in fields — validating one against the other corrupts both.
sources:
  - { resource: /lib/extraction_schemas.py }
  - { resource: /lib/schemas.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
verified: { by: claude-fable-5, at: 2026-08-13T15:15:27Z }
---

# The extraction schema is not the runtime schema

`npcs.json` means two different things depending on where you are in the pipeline, and the
two schemas live in two files that never reference each other.

| | Extraction | Runtime |
|---|---|---|
| Defined in | `lib/extraction_schemas.py` | `lib/schemas.py` + whatever the managers write |
| Produced by | the `extractor-*` agents | `gm-npc.sh` and friends, during play |
| Carries | `location_tags`, `dialogue`, `source`, nullable `stats` | `created`, `tags`, `context`, `enhanced`, `is_party_member`, `status`, `aliases`, `current_mood`, `character_sheet` |

## The failure this causes

An agent asked to validate or repair extractor output naturally opens a live campaign's
`npcs.json` to see "what the schema looks like" — and copies runtime-only fields into
extraction output, or strips extraction fields that the import pipeline's later passes
depend on. Nothing rejects the result; the damage appears several passes later as
unresolved references or missing tags.

**The rule: extraction output is validated against `lib/extraction_schemas.py` and nothing
else.** Never use a campaign file as a schema reference. Campaign files under
`world-state/campaigns/` are gitignored runtime state, mid-migration by definition.

## Where the two do meet

`visual_appearance` is deliberately identical in both, and the extraction schema says so
in a comment pointing at `lib/visual_appearance.py` as the owner of the field list. That is
the exception, not the pattern — see [scene illustration](../flows/scene-illustration.md).

The bridge between the two shapes is the normalize + cap + integrity sequence in
[importing a book](../flows/import-a-book.md); that is where extraction shape becomes
runtime shape.

## Related

- [Extractor output silently vanishes on the wrong wrapper key](wrapped-vs-unwrapped-merge.md)
- [The entity graph](../modules/entity-graph.md)
