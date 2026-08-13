---
type: Module
title: The World Bible
description: The fidelity spine a world is played from — what it must contain, the draft-then-confirm gate, and the mechanical artifacts drafted out of it.
sources:
  - { resource: /lib/world_bible.py }
  - { resource: /lib/book_bible.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# The World Bible

`world-bible.json` is what makes playing Dune feel like Dune rather than d20-fantasy in a
desert. It is authored once (drafted from the book on `/import`, written from the seed on
`/new-game`) and then read constantly: the **voice** block reaches the model every beat,
and the **signature systems** become the campaign rules the GM is told to follow exactly.

## The bible is upstream of two mechanical artifacts

Neither is authored by hand — both are drafted from the bible, and both live somewhere
else afterward:

| Drafted by | Produces | Lands in |
|---|---|---|
| `bible_to_campaign_rules` | `signature_systems` + tone, wrapped in a "follow them exactly" instruction | `campaign-overview.json` → `campaign_rules` |
| `draft_ruleset_from_bible` | a World Kit skeleton | `ruleset.json` |

The drafted ruleset is deliberately **thin**: empty attributes, `hp` as the only vital,
`d20-vs-dc`, and `milestone` progression as "the safest book-native option"
(`lib/book_bible.py:65-81`). It also hardcodes `rules_doc: "rules.md"` and three active
agents. A book that wants XP or a resource axis needs the model chosen at draft time —
nothing later infers it. See [game core and World Kit](game-core-and-world-kit.md).

## Voice is grounded by a verbatim filter

`draft_voice` keeps a sample passage **only if it appears verbatim in the source text**
(`lib/book_bible.py:94-95`). This is the mechanism that stops an imported book's voice
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

`validate_bible` requires `name`, `voice`, `tone`, `themes`, `factions`, `geography`,
`signature_systems`, with factions and geography shaped as graphs. Missing keys fail
validation but do **not** block play; only the confirm flag does.

## Chapter segmentation is shared, and prefers real markers

`segment_into_chapters` is the bible's own splitter and is also what
[the coarse index](rag-stack.md) builds on. It needs **two or more** chapter markers
before it will split on them (`lib/book_bible.py:30`); with fewer, the entire book becomes
one span, then gets cut into 20,000-character windows. A PDF whose chapter headings didn't
survive extraction therefore yields arbitrary windows with first-line titles — still
usable for retrieval, useless for citing "chapter 4".

## Related

- [Importing a book](../flows/import-a-book.md) — where the bible is drafted and confirmed
- [Authoring a world](../flows/author-a-world.md) — where it is written from a seed instead
- [Scene context](scene-context.md) — how the voice block reaches the model
