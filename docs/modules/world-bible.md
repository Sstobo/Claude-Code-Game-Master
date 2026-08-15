---
type: Module
title: The World Bible
description: The fidelity spine a world is played from — what it must contain, the draft-then-confirm gate, and the mechanical artifacts drafted out of it.
sources:
  - { resource: /lib/world_bible.py }
  - { resource: /lib/book_bible.py }
  - { resource: /tools/gm-extract.sh }
generated: { by: claude-opus-4-8[1m], at: 2026-08-15T15:41:00Z }
verified: { by: claude-fable-5, at: 2026-08-13T15:15:27Z }
---

# The World Bible

`world-bible.json` is what makes playing Dune feel like Dune rather than d20-fantasy in a
desert. It is authored once (drafted from the book by `gm-extract.sh draft-bible` on
`/import`, written from the seed on `/new-game`) and then read constantly: the **voice**
block reaches the model every beat, and the **signature systems** become the campaign
rules the GM is told to follow exactly.

## Half deterministic, half authored — and the seam is the point

`draft_bible` (`lib/book_bible.py:163`) writes only what the source can prove: the
verbatim-filtered voice block and the skeleton keys `validate_bible` demands. It also
scaffolds an empty `index` — the named-thing roster, four buckets (`npcs`, `locations`,
`items`, `monsters`), each entry a `{"name","note"}` pair with a one-sentence note (a
later ticket populates it; the drafter only lays the empty structure). `tone`, `themes`,
`factions`, `geography` and `signature_systems` are the **model's** authorship, merged in
by re-running the same verb with `--fields-json`. That is why the verb is idempotent:
scaffold, read the book, merge, merge again.

As of 2026-08-15 the bible no longer persists a `chapters` array. `draft_bible` used to
write one derived from `segment_into_chapters`; it stopped, in favor of the `index`. The
splitter itself is untouched — see "Chapter segmentation is shared" below.

It refuses to touch a bible whose `confirmed` flag is absent or true
(`lib/book_bible.py:173`) — the same rule `WorldBible.is_confirmed` reads, so a
hand-authored or approved bible can never be flattened by a re-import.

## The bible is upstream of two mechanical artifacts

Neither is authored by hand — both are drafted from the bible, and both live somewhere
else afterward:

| Drafted by | Produces | Lands in |
|---|---|---|
| `bible_to_campaign_rules` | `signature_systems` + tone, wrapped in a "follow them exactly" instruction | `campaign-overview.json` → `campaign_rules` |
| `draft_ruleset_from_bible` | a World Kit skeleton | `ruleset.json` |

Both are reachable from the shell as `gm-extract.sh campaign-rules` and
`gm-extract.sh draft-ruleset`, which is how `/import` calls them.

The drafted ruleset is deliberately **thin**: `hp` as the only vital, `d20-vs-dc`, and
`milestone` progression as "the safest book-native option" (`lib/book_bible.py:76-101`).
Three things the source decides are passed in rather than inferred — the attribute list,
the progression model, and `kit`. Nothing later infers them, and a kit with no attributes
is indistinguishable from the `DEFAULT_RULESET` fallback.

`kit` is the machine-readable router, and `dnd5e` is the only value that unlocks the D&D
mechanics skills and puts `spell-caster` in `active_agents` (`lib/book_bible.py:90-91`).
Every other book is `custom` — its magic is a signature system, not spell slots. A
`ruleset.json` written before the field existed has no `kit`; `WorldKit.kit()` reads that
as `custom` (`lib/world_kit.py:74`), which is the right answer for every non-D&D import.
See [game core and World Kit](game-core-and-world-kit.md).

## Voice is grounded by a verbatim filter

`draft_voice` keeps a sample passage **only if it appears verbatim in the source text**
(`lib/book_bible.py:113-114`). This is the mechanism that stops an imported book's voice
from being the model's impression of the author instead of the author. Two consequences:

- A near-miss passage — reflowed whitespace, smart quotes, an OCR artifact — is silently
  dropped. An empty `sample_passages` after a voice pass usually means the passages were
  paraphrased or the text was normalized, not that the book has no voice.
- `/new-game` worlds have no source text to check against, so their voice block is
  authored rather than filtered.

## The confirm gate blocks fresh drafts only

`is_confirmed()` returns `True` when the flag is **absent** (`lib/world_bible.py:85`).
That default is the whole design: hand-authored and legacy bibles are playable
immediately, and only a freshly auto-drafted bible carrying `confirmed: false` is held
for human review. A campaign with no bible at all is playable — that is the `/new-game`
path before consolidation.

The gate is closed by a person, not by the pipeline: `world_bible.py review` prints the
draft and `world_bible.py confirm` stamps it, and both `/import` and `/new-game` put a
human between them. Nothing in the runtime confirms a bible on its own.

`validate_bible` requires `name`, `voice`, `tone`, `themes`, `factions`, `geography`,
`signature_systems`, with factions and geography shaped as graphs. Missing keys fail
validation but do **not** block play; only the confirm flag does.

## Chapter segmentation is shared, and prefers real markers

`segment_into_chapters` still lives in `lib/book_bible.py`, but as of 2026-08-15 it feeds
only [the coarse index](rag-stack.md) (`lib/rag/coarse_index.py:47`) — it no longer
populates the bible. It needs **two or more** chapter markers before it will split on them
(`lib/book_bible.py:41`); with fewer, the entire book becomes one span, then gets cut into
20,000-character windows. A PDF whose chapter headings didn't survive extraction therefore
yields arbitrary windows with first-line titles — still usable for retrieval, useless for
citing "chapter 4".

## Related

- [Importing a book](../flows/import-a-book.md) — where the bible is drafted and confirmed
- [Authoring a world](../flows/author-a-world.md) — where it is written from a seed instead
- [Scene context](scene-context.md) — how the voice block reaches the model
