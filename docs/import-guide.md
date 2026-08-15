---
type: Playbook
title: Import operations guide
description: Operator's side of import — the live path is index then stage; this page also covers repairing a leftover census run.
sources:
  - { resource: /tools/gm-extract.sh }
  - { resource: /tools/gm-search.sh }
  - { resource: /lib/minor_stubs.py }
  - { resource: /lib/extraction_cap.py }
  - { resource: /lib/entity_enhancer.py }
  - { resource: /.claude/commands/import.md }
generated: { by: cursor-grok-4.6, at: 2026-08-14T23:39:02Z }
verified: { by: claude-fable-5, at: 2026-08-13T15:15:27Z }
---

# Import operations guide

```
/import <file-path> [campaign-name]
```

Drop a PDF, DOCX, TXT, or MD into `source-material/` and run it. The campaign name defaults
to the filename. **The live path is index → identity → one stage** — see
[importing a book](flows/import-a-book.md) and [the dream](conventions/the-dream.md).
This page is the operator's side: running steps by hand, and repairing a **legacy
census** import that already scraped the book into a gazetteer.

`/import` does **not** run the four extractors, `cap`, `reconcile`, `stub-npcs`, or
`integrity`. Those verbs still exist for old campaigns. Do not use them to "finish"
a new import.

`bash tools/gm-extract.sh` with no arguments prints the authoritative command list. Prefer
that over any list written here.

## Running a step by hand

Every pass takes an optional campaign name, defaulting to the active campaign:

```bash
bash tools/gm-extract.sh prepare "source-material/book.pdf" "campaign-name"
bash tools/gm-extract.sh cap "campaign-name" 30
bash tools/gm-extract.sh integrity "campaign-name" --no-strict   # report, don't fail
```

Re-running a pass is safe — they are written to be idempotent — but **re-running one out of
order is not**, because several passes depend on repairs made by earlier ones.

## `validate` is a gate, not a report

```bash
bash tools/gm-extract.sh validate "campaign-name"
```

It exits **non-zero**, naming the type and the reason, when any of the four
`extracted/*.json` files is missing, is unparseable, holds a malformed entity (a non-object
entry, a non-string `name`), or when `npcs`/`locations` came back with zero entities. Empty
`items` or `plots` only warn. This gate belongs to the **legacy census** path
(`normalize` and the repair chain). A stage-first import never writes `extracted/` and
never needs this gate.

Two entities with the same `name` collapse onto one key, so a count reads
`43 entries, 41 unique names` when they differ. That is the runtime shape being honest —
the campaign root can only hold one entity per key.

Counting goes through the same shape rule `normalize` uses
(`minor_stubs.normalize_entity_shape`), because extractor agents emit **lists** in
practice — even though `EXTRACTION_RESULT_SCHEMA` declares keyed dicts — while the
runtime managers want a keyed `{name: {...}}` dict. A count that understood only
one of those shapes is how 43 correctly extracted items once read as `EMPTY (0 entities)`
while the run reported success.

## `merge` / `save` / `review` are the legacy path

`gm-extract.sh` still offers `merge`, `save [rename|skip|overwrite]`, and `review`. The
`/import` command does **not** call them. Reach for `merge`/`save` only when
deliberately folding a second extraction into a **legacy** campaign.

## Checking a finished import

```bash
bash tools/gm-search.sh "a phrase from the book" --rag-only -n 20   # vectors alive?
bash tools/gm-search.sh "character name" --world-only               # entities landed?
uv run python lib/schemas.py                                        # validate world state
uv run python lib/world_bible.py validate                           # bible complete?
```

An empty `--rag-only` result is ambiguous by design: no vectors, missing RAG dependencies,
and a genuinely absent phrase all look identical. Check
`bash tools/gm-context.sh --json` for `rag_available` before concluding the book is thin.
See [the RAG stack](modules/rag-stack.md).

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| No text extracted at all | the PDF is image-only. **There is no OCR path** — convert the file before importing |
| `integrity` fails strict with unresolved refs | a repair pass was skipped or run out of order — re-run `normalize-connections` → `reconcile` → `stub-npcs`, then `integrity` |
| One entity type came back empty | the merge dropped it on a wrapper-key mismatch — see [wrapped vs unwrapped](gotchas/wrapped-vs-unwrapped-merge.md) |
| An entity literally named `npcs` | same bug, other direction |
| Entities present but bland | enhancement didn't ground — check `context_name_match_fraction`, then re-run `gm-enhance.sh batch` |
| No source passages during play | RAG deps missing, or the campaign was never vectorized |
| Main cast missing after `cap` | `cap` deletes nothing — they are still in `npcs.json`, tiered `background: true` because no plot referenced them. Promote the ones you want active (`gm-npc.sh promote` clears the flag for party members) or re-run `cap` with a higher limit; never hand-edit the file to add them back |
| A background entity reads bland in play | `gm-enhance.sh batch` skips background entities on purpose (a RAG round-trip each). Ground it when you promote it: `gm-enhance.sh query "<name>"` then `apply "<name>"` |
| Agents produced nothing | `validate` fails and names each bad type — re-run those agents alone |

## Notes that are easy to get wrong

- **Vectorizing is expensive once, free afterward.** The store is persistent; a 500+ page
  book takes minutes the first time and nothing on restart.
- **Chunks are ~3000 characters** and are a different index from the chapter-granularity
  one the Loremaster uses. Both exist; see [the RAG stack](modules/rag-stack.md).
- **Use every passage the harness surfaces during play.** Loosely related prose still
  carries the author's atmosphere, which is the point of grounding.
- **`source-material/` and extracted book text are gitignored** — a cloned repo has no
  books and no vectors.

## Related

- [Importing a book](flows/import-a-book.md) — the pipeline and its ordering
- [World state schema reference](schema-reference.md) — what the files end up looking like
