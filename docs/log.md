# Bundle log

## The settled command

```bash
node ~/.claude/skills/okf/scripts/okf.mjs check --root . docs
```

`--root .` so `sources` resolve as repo-relative paths; the scan set is `docs` only.
No `--exclude` — verbatim material (`source-material/`, `world-state/campaigns/`,
`tests/fixtures/`) is already outside the scan set. No `--index` — the repo has no
hand-written docs router; `docs/index.md` is generated.

Swap `check` for `drift` / `noise` / `index` as needed; the flags never change.

---

## 2026-08-15 — play pack (kit + primer + one room)

- `docs/conventions/the-dream.md`, `docs/schema-reference.md`, `docs/modules/scene-context.md` — `play_pack` on the overview; PRIMER in context; `gm-playpack.sh` set / stage / from-book.
- `docs/flows/import-a-book.md`, `author-a-world.md`, `play-turn.md` — import and new-game write a pack, not a census; fan-out is opt-in later.

## 2026-08-14 — the dream (holodeck, not gazetteer)

- `docs/conventions/the-dream.md` — campaign JSON is a journal; the book is the world; session 0 is one stage.
- `docs/flows/import-a-book.md`, `import-guide.md`, `play-turn.md`, `author-a-world.md`, `onboarding-and-death.md` — `/import` indexes and opens a door; census extractors/cap/stub/integrity are leftover machinery, not the path.

## 2026-08-14 — fence-disclosures ingest

- `docs/modules/living-world.md` — tick fires 2 and discloses the rest (already-fired annotates, does not suppress); world-tick applies every proposal and warns on cap overflow (`fence-disclosures`).
- `docs/modules/scene-context.md` — truncated context sections print `+N more`; NPC voice lines 4, vocab 12 (`fence-disclosures`).

## 2026-08-14 — presence-resolver-unification ingest

- `docs/modules/scene-context.md`, `entity-graph.md`, `living-world.md`, `gotchas/npc-location-tag-split.md` — presence is one helper (party OR exact location tag); CLI tag search stays substring (`presence-resolver-unification`).

## 2026-08-14 — save-restore-completeness ingest

- `docs/schema-reference.md` — whole-campaign saves, `save_version: 1`; legacy restores warn partial; autosaves rotate to 3 (`save-restore-completeness`).

## 2026-08-14 — kit-aware-character-creation ingest

- `docs/flows/onboarding-and-death.md`, `docs/modules/player-character.md` — Death hand-off new-character route is kit-aware create-character; silent 10/10 HP fallback now warns in the save payload (`kit-aware-character-creation`).

## 2026-08-14 — kit-block-in-context ingest

- `docs/modules/scene-context.md`, `game-core-and-world-kit.md`, `lean-core-and-skill-routing.md` — KIT block in session context; signature_systems render in YOUR WORLD'S RULES (campaign_rules is the legacy fallback); STEP-0 defers to that block (`kit-block-in-context`).

## 2026-08-14 — recall top-k ingest

- `docs/modules/campaign-memory.md` — recall default top-k is 5; `gm-recall.sh recall` takes `--top-k` (`recall-top-k`).

## 2026-08-14 — opening seed does not fabricate a session

- `docs/flows/import-a-book.md`, `author-a-world.md`, `onboarding-and-death.md` — seed-opening is provisional location + `opening_hook` data; no fake session-log, plots not stamped active (`opening-seed-no-fake-session`).

## 2026-08-14 — clock-tick-magnitude ingest

- `docs/modules/living-world.md` — time-clock ticks scale with `--ticks`/`--duration`; default remains 1 (`clock-tick-magnitude`).

## 2026-08-14 — core-prompt-detox ingest

- `docs/modules/scene-context.md` — play-style flags stay; failure is one informing sentence; caps/judgment live in skills/gm-craft (`core-prompt-detox`).

## 2026-08-14 — alias / enhance / promote ingest

- `docs/modules/entity-graph.md` — normalization folds diacritics; integrity reports near-duplicate keys (`alias-dedupe-integrity`).
- `docs/modules/rag-stack.md` — 0-name-bearing enhancement attaches nothing; batch warns/exits at 25% (`enhancement-relevance-honesty`).
- `docs/modules/npc-model.md` — promote copies existing stats; defaults only for statless, disclosed (`party-promote-real-stats`).
- `docs/flows/import-a-book.md`, `author-a-world.md`, `onboarding-and-death.md` — opening is provisional then re-seeded on first PC (`opening-beat-after-character`).

## 2026-08-13 — bundle created

First OKF pass on the repo. Prior state: four unversioned docs, last touched
2026-06-06, covering the import pipeline and two `lib/` modules out of ~55.

**Written:** 5 Flows, 9 Modules, 3 Conventions, 3 Gotchas, 2 Playbooks, plus the two
kept docs re-verified and annotated.

**Deleted:**

- `python-modules-api.md` — restated function signatures for `json_ops.py` and
  `validators.py`. The code is the better document.
- `import-system-deep-dive.md` — cited `lib/smart_chunker.py`, which does not exist;
  the RAG stack moved to `lib/rag/` and `coarse_index.py` inverted the architecture the
  doc described (embeddings demoted to a chapter finder). Live knowledge lifted into
  `flows/import-a-book.md` and `modules/rag-stack.md`.

**Not touched:** the working tree carried 101 uncommitted deletions (`AGENTS.md`,
`tickets/`, `_backups/`) belonging to another session. Left alone; the OKF write-back
section went into `CLAUDE.md` instead of the usual `AGENTS.md`.

**Result:** `check` 25 conformant / 0 errors / 0 warnings. `drift` baseline 25 fresh, 0
blind — every concept has invalidators. `noise` worst shared source is
`.claude/commands/import.md` at 34 predicted flags/90d, declared by 2 concepts; no source
is declared by more than 3. Invalidator rule spot-checked by hand on `scene-context`,
`rag-stack`, and `play-turn` — no padding found.

**Size:** bundle grew from ~4.9k words (4 docs) to ~15.9k (25 concepts + generated
indexes). Growth is coverage, not thoroughness: the prior docs described the import
pipeline and two `lib/` modules; roughly 40 source files had no doc at all. Expect the next
pass to subtract.

**Suite:** `uv run --extra dev pytest` → 245 passed, 1 failed, 1 skipped. The failure is
the pre-existing stale test filed in `9ef38ba`; the skip is RAG-dependency-gated. Both
documented in `playbooks/testing.md`.

**Worth acting on** — surfaced while reading, not fixed in this pass (each was a code
change). Status as of the same day, after the fix pass:

- ~~The appearance injection was suppressed whenever the character's name appeared in the
  prompt~~ — fixed 2026-08-13 (`inject_appearances`, `tests/test_image_prompt_injection.py`).
- ~~Consequence `expiry` was a substring test~~ — fixed 2026-08-13 (whole-word match).
- ~~Threat clocks never advanced automatically~~ — fixed 2026-08-13: `gm-time.sh` ticks
  time-clocks; `gm-clock.sh` wrapper added.
- ~~`WorldTick` and `Loremaster` had no caller~~ — wired 2026-08-13:
  `gm-session.sh world-tick` / `gm-lore.sh`.
- ~~`CoarseIndex`'s non-keyword embedder path was dead~~ — fixed 2026-08-13: correct class
  (`LocalEmbedder`), correct embed-then-similarity call, fallback narrowed to
  `ImportError`. Keyword remains the default and the only configuration any caller uses.

## 2026-08-13 — improvement pass (four workstreams)

Same day, on top of the fix pass. All landed with tests and same-commit doc updates:

1. **Kit guard** (`09b0316`) — `ruleset.json` gains a machine-readable `kit` field;
   the three D&D-only skills open with a STEP 0 guard routing non-dnd5e worlds to the
   generic core. Tested prompt, not a hard interlock.
2. **Entity unification** (`b9bbd30`) — `tags.locations` is the only NPC location field
   (`tag_unify` at import normalize; `gm-npc.sh unify-tags` for old campaigns);
   `schemas.validate_character` is the only character validator (kit-aware, name+level
   required). Two gotcha docs rewritten as dated history.
3. **Long-context grounding** (`fd40673`) — `gm-lore.sh --full` returns whole chapter
   spans; `move` auto-briefs on first visit. Deliberately skipped persisting the chapter
   index: segmentation is a cheap regex scan.
4. **Real memory** (`ffb2c8d`) — GM-authored arc entries at session end
   (`gm-recall.sh arc`), memoir leads with them, and recall is embedding-backed when RAG
   deps are installed (content-hash gated re-embeds; keyword fallback verified separately).

Suite green on both dependency profiles (`--extra dev`, `--extra dev --extra rag`).
