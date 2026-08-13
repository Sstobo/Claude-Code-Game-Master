---
type: Module
title: RAG stack
description: Two retrieval systems over the source book — 3000-char embedded chunks and a chapter-granularity index — plus the parts of each that are inert.
sources:
  - { resource: /lib/rag/__init__.py }
  - { resource: /lib/rag/rag_extractor.py }
  - { resource: /lib/rag/vector_store.py }
  - { resource: /lib/rag/embedder.py }
  - { resource: /lib/rag/coarse_index.py }
  - { resource: /lib/entity_enhancer.py }
generated: { by: claude-fable-5, at: 2026-08-13T14:27:00Z }
verified: { by: claude-fable-5, at: 2026-08-13T15:15:46Z }
---

# RAG stack

Two independent retrieval paths over the same book, built at different times for
different jobs. Both are live; they do not share an index.

| | **Chunk store** | **Coarse index** |
|---|---|---|
| Unit | 3000-char chunks (`RAGExtractor.DEFAULT_CHUNK_SIZE`) | whole chapters |
| Storage | ChromaDB, persisted per campaign under `vectors/` | rebuilt in memory per instance, never persisted |
| Embeddings | real — `all-MiniLM-L6-v2` via sentence-transformers | **none by default** (see below) |
| Returns | passage text | pointers `{index, title, score}` |
| Feeds | `/enhance`, `gm-search --rag-only`, scene passages | [the Loremaster](campaign-memory.md) |

`coarse_index.py`'s docstring frames the chunk store as "the old pipeline" it demotes.
Read that as *intent*, not status: the chunk store is what `/import` builds and what
every runtime passage lookup still goes through.

## The whole stack is optional, and its absence is silent

`lib/rag/__init__.py` probes for `sentence-transformers` and `chromadb` at import and sets
`RAG_AVAILABLE`; the class exports simply do not exist when deps are missing. Callers
degrade rather than fail — see the bare `except` in
[scene context](scene-context.md). Net effect: **a missing dependency, an unvectorized
campaign, and a genuinely irrelevant query are indistinguishable from the outside.** Check
`RAG_AVAILABLE` before concluding a campaign has no material.

## The coarse index defaults to keyword scoring, deliberately

`CoarseIndex(embedder=…)` defaults to `"keyword"` — set-intersection word counting, no
model, no vectors — so building the chapter index never requires loading a heavy model.
Passing a sentence-transformers model name gets real embedding similarity, falling back to
keyword scoring only when the RAG deps are missing.

(Until 2026-08-13 the non-keyword path was dead — it imported a class that didn't exist
with a call shape that didn't match, and a bare `except Exception` silently returned the
keyword score for every configuration. If embedder tuning appears to do nothing on an old
checkout, that is why.)

Note that no caller currently passes a non-keyword embedder — the Loremaster constructs
`CoarseIndex()` bare — so keyword scoring is still what runs in practice.

## Query templating is the anti-D&D lever

`_template()` appends `"scene character atmosphere setting"` for literary content and
`"stat block rules mechanics encounter"` for game modules. Without it, retrieval over a
novel drifts toward stat-block vocabulary. The content type is a **parameter with a
`"literary"` default** — nothing infers it from the campaign, so a module import gets
literary templating unless the caller says otherwise.

## Enhancement drops rather than pads

`_gate_passages` (`lib/entity_enhancer.py:642`) force-includes every passage that names the
entity or one of its aliases, then fills remaining slots only from passages at or under
`RELEVANCE_FLOOR`. Below-floor neighbours are **dropped, not used as padding** — a thin
entity comes back with two good passages instead of ten mediocre ones. It persists a
`context_name_match_fraction` alongside, which is the number to look at when enhancement
output reads generic: a low fraction means the entity's name barely appears in what was
retrieved.

## Related

- [Importing a book](../flows/import-a-book.md) — where vectorization happens in the pipeline
- [Scene context](scene-context.md) — how passages reach a beat
