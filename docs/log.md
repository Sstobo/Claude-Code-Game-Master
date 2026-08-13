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
