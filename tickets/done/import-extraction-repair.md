---
slug: import-extraction-repair
title: Repair the /import extraction path (agent prompts, campaign switch, one slug)
category: bug
kind: afk
priority: p0
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-13T16:06:15Z
changedFiles: ['.claude/agents/extractor-plots.md (schema line)', '.claude/agents/extractor-npcs.md', '.claude/agents/extractor-locations.md', '.claude/agents/extractor-items.md', '.claude/agents/extractor-plots.md', '.claude/commands/import.md', lib/campaign_manager.py, lib/agent_extractor.py, tools/gm-extract.sh, tests/test_slug_unify.py, docs/flows/import-a-book.md]
resolution: extractor prompts load, extraction targets the right campaign, one slug rule everywhere
reviewRounds: 3
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-13T18:54:01Z
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

- [x] All four extractor agent files have their full prompt in the markdown body; no `instructions:` frontmatter key remains.
- [x] In import.md, the active campaign is switched before any extractor launch; `gm-search.sh --rag-only` during extraction resolves to the campaign being imported.
- [x] A test proves `"Baldur's Gate: Book 1"` produces the same single directory slug through campaign create, extractor sanitize, and the gm-extract.sh path.
- [x] Existing import-related tests still pass (`uv run --extra dev pytest`).
- [x] `docs/flows/import-a-book.md` no longer describes the pre-fix behavior; restamped.
- [x] (review) _slugify never returns empty for non-empty input; gm-extract.sh clean cannot resolve to world-state/campaigns itself.
- [x] (review) A dotted name ("Curse of Strahd v2.0") lands in one directory across create, extraction_dir, and the CLI; switch succeeds on it.
- [x] (review) import.md Step 2 fails loudly if the campaign switch did not take.
- [x] (review) extractor-plots.md output schema includes threat and mystery.
- [x] (review-2) Every $CAMPAIGN_DIR in import.md derives from gm-campaign.sh path / slugify — never a raw <campaign-name> under world-state/campaigns/.

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

### 2026-08-13T18:54:01Z — pass [review-import-3]
reviewed: perfect (final followup; all path derivation via gm-campaign.sh path,
mechanical Step-2 assertion, coherent flow). Three review rounds total —
each caught a real defect class (empty-slug rm -rf, stem divergence,
unslugged Step 6.5 path).

### 2026-08-13T18:49:27Z — fail [review-import-2]
reviewed: needs-changes (round 2; all six prior criteria confirmed holding)
1. import.md:341 — Step 6.5 hand-builds CAMPAIGN_DIR from the raw display name;
ruleset.json/rules.md/overview_seed write to the unslugged path while the Step
6.6 WorldKit verify reads the active slugged path — one name, two directories.
Fix: CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path) as line 478 already does.
Nit: Step 2 mismatch branch should exit 1, not just echo.

### 2026-08-13T18:45:45Z — verified (fix round 1) [fable-sott1]
15/15 slug tests; empty-slug impossible (hash fallback, verified on 龍の伝説);
campaign_slug guards interpreter failure loudly; clean_temp refuses the
campaigns root; _sanitize_name no longer stems; import.md asserts the switch;
extractor-plots schema can emit threat/mystery; addendum covered (legacy-dir
resolution via slugified-name fallback in _resolve_name). Implementer full
suite 323 passed.

### 2026-08-13T18:39:02Z — fail [review-import]
reviewed: needs-changes
1. campaign_manager._slugify returns EMPTY for non-ASCII/punct-only names → gm-extract.sh clean resolves CAMPAIGN_DIR to campaigns/ root and rm -rf deletes every campaign.
2. agent_extractor._sanitize_name still stems the campaign name (dot names diverge: curse-of-strahd-v2 vs -v2-0; double-stem on the filepath site) → two directories + failed switch → extraction reads the wrong vector store.
3. import.md:80 switch unasserted — a failed switch proceeds against the old campaign.
Nits: gm-migrate-campaigns.sh still has the old slug rule (legacy script, noted for T3 dead-code sweep); test table lacks dot/slash cases and one test locks in the stem behavior.
+ Routed from review-plots: extractor-plots.md's output schema line still can't emit threat/mystery (file owned by this ticket's scope).

### 2026-08-13T18:33:16Z — verified [fable-sott1]
Orchestrator-verified: zero instructions: frontmatter keys across the four
extractors, prompts in body; campaign switch at import.md Step 2 (line 80);
slugify CLI produces collapsed slugs; tests/test_slug_unify.py 4/4;
implementer full suite 289 passed. import-a-book.md restamped after body
re-read (ingest done in-ticket).

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-13T16:06:15Z  claimed  [fable-sott1]
- 2026-08-13T18:04:14Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-13T18:33:16Z  verified → in-review  [fable-sott1]
- 2026-08-13T18:39:02Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-13T18:45:45Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-13T18:49:27Z  review needs-changes (round 2) — final fix cycle  [fable-sott1]
- 2026-08-13T18:52:06Z  final fix verified — followup review 2 dispatched  [fable-sott1]
- 2026-08-13T18:54:01Z  review perfect → done, committed  [fable-sott1]
