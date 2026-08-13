---
type: Module
title: Scene context — the two doors
description: What the harness pushes to the model each beat, and why "context" means two different things depending on which tool you call.
sources:
  - { resource: /lib/session_manager.py }
  - { resource: /lib/scene_context.py }
  - { resource: /lib/search.py }
  - { resource: /tools/gm-context.sh }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
verified: { by: claude-fable-5, at: 2026-08-13T14:16:30Z }
---

# Scene context — the two doors

This is the mechanism the whole product rests on: instead of hoping the model remembers,
the harness *pushes* the campaign at it every beat. Two different commands both call
themselves "context" and return almost disjoint things. Calling the wrong one is the
most common way a beat comes out flat.

| Command | Code | Returns |
|---|---|---|
| `gm-session.sh context` | `SessionManager.get_full_context` (`lib/session_manager.py:405`) | The **session brief** — everything below, as formatted prose for the model |
| `gm-context.sh ["loc"]` | `SceneContext.build` (`lib/scene_context.py:37`) | The **place brief** — this location, NPCs present, named entities, plus grounded source passages |

Neither contains the other. The session brief has no source passages; the place brief has
no history, threads, clocks, voice, or rules. Narrating a scene generally wants both.

## What the session brief carries, and why each block exists

`get_full_context` assembles, in order: header (campaign, session #, location, time) ·
pacing + action-menu style · scene-image gate + chronicler · **narrative voice** ·
**previously on** + where-we-paused + open threads · story threads · key facts · threat
clocks · character · party members · **NPC voices** · pending consequences · **your
world's rules**.

Three of those blocks carry design decisions that are not obvious from reading them:

- **Narrative voice is a prose target, not lore.** The block is labelled that way in the
  output for a reason — the sample passages are style exemplars to imitate, and a model
  that treats them as world facts will narrate someone else's scene.
- **NPC secrets are surfaced by existence only.** `lib/session_manager.py:617` prints
  `"has a secret"` and never the secret text, so a secret can sit in `npcs.json` without
  leaking into narration the moment its owner walks on stage.
- **World rules are never truncated.** Every other block is bounded — by item count, not
  by chopping an entry mid-sentence — but `campaign_rules` is pretty-printed whole
  (`lib/session_manager.py:657`). The comment there is the rationale: those rules *are*
  the magic that makes each book distinct, and the GM is told to follow them exactly, so
  it must see all of them. See [game core and World Kit](game-core-and-world-kit.md).

`--full` lifts every bound. `DM_DEBUG_CONTEXT=1` prints an approximate token count to
stderr without changing the output; the ~2k-token target it reports against is guidance,
never a cut.

## RAG is optional everywhere, and fails to empty

`SceneContext.build` wraps the entire enhancer call in a bare `except Exception: pass`
(`lib/scene_context.py:56-64`). A campaign with no vector store, a missing `chromadb`, or
a runtime error inside the enhancer all produce the same thing: `passages: []` and
`rag_available: false`. Play continues on world state alone.

The cost of that choice: **a broken RAG install is indistinguishable from a campaign that
was never vectorized.** Neither logs. If passages are unexpectedly empty, check
`rag_available` in `gm-context.sh --json`, then confirm the campaign actually has vectors
rather than assuming the import worked. See [RAG stack](rag-stack.md).

## Which search tool

`gm-search.sh` is the free-text door and takes a mode flag: `--world-only`, `--rag-only`,
or neither for both. `gm-enhance.sh query` is **not** a search — it takes an entity *name*.
Reaching for it with a free-text phrase returns nothing and looks like an empty world.

`search_npcs_by_tag("locations", …)` is what decides "who is present" for both context
doors, and it reads a field whose two spellings drift apart — see
[the NPC location tag split](../gotchas/npc-location-tag-split.md).

## Related

- [Campaign memory](campaign-memory.md) — where "previously on" is built from
- [Living world](living-world.md) — clocks and consequences that appear in the brief
- [A play turn](../flows/play-turn.md) — where in the loop each door is called
