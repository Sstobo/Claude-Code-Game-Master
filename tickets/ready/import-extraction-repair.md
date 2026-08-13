---
slug: import-extraction-repair
title: Repair the /import extraction path (agent prompts, campaign switch, one slug)
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T15:47:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Three surgical fixes so `/import` extraction actually runs:

1. **Agent prompts into bodies.** The four extractor agents
   (`.claude/agents/extractor-npcs.md`, `-locations.md`, `-items.md`,
   `-plots.md`) keep their entire prompt inside an `instructions:` frontmatter
   key with an empty markdown body. The loader only reads the body. Move each
   prompt into the body (matching the shape of `world-author.md`), keeping
   only recognized frontmatter keys (name/description/tools).
2. **Switch campaign before extraction.** `gm-search.sh --rag-only` resolves
   the ACTIVE campaign (tools/gm-search.sh:89,111), but `/import` doesn't
   switch until Step 7 (import.md:457). Move `gm-campaign.sh switch` to
   immediately after `gm-extract.sh prepare` in Step 2 of
   `.claude/commands/import.md`, and remove the now-redundant late switch.
3. **One slug function.** Three diverge today: `CampaignManager._slugify`
   (lib/campaign_manager.py:30 — no stripping), `AgentExtractor._sanitize_name`
   (lib/agent_extractor.py:658), and gm-extract.sh's inline tr|sed. Harden
   `_slugify` (lowercase, strip non-alphanumerics to dashes, collapse, trim),
   make the other two call it (shell path via a tiny `python -c` or a
   `campaign_manager.py slugify` CLI verb).

Update `docs/flows/import-a-book.md` claims that these fixes falsify, restamped
per OKF convention, in the same commit.

## Acceptance criteria

- [ ] All four extractor agent files have their full prompt in the markdown body; no `instructions:` frontmatter key remains.
- [ ] In import.md, the active campaign is switched before any extractor launch; `gm-search.sh --rag-only` during extraction resolves to the campaign being imported.
- [ ] A test proves `"Baldur's Gate: Book 1"` produces the same single directory slug through campaign create, extractor sanitize, and the gm-extract.sh path.
- [ ] Existing import-related tests still pass (`uv run --extra dev pytest`).
- [ ] `docs/flows/import-a-book.md` no longer describes the pre-fix behavior; restamped.

## Out of scope

The world-bible/kit wiring (import-bible-kit-wiring), shard-parallel
extraction, and the resumable import driver (Tier 2). Do not rewrite the
extractor prompt content beyond relocation.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
