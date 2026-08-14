---
slug: campaign-path-exact-match
title: _resolve_name trusts is_dir() so macOS case-insensitivity returns case-variant paths
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-14T13:41:28Z
changedFiles: [lib/campaign_manager.py, tests/test_slug_unify.py]
resolution: resolution returns the canonical on-disk spelling; trailing slashes normalized; symmetric slug defect fixed
reviewRounds: 1
implementer: null
createdAt: 2026-08-13T18:53:00Z
updatedAt: 2026-08-14T13:54:32Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

Found during import-extraction-repair (pre-existing): `_resolve_name`'s first
branch trusts `Path.is_dir()`, and macOS's case-insensitive filesystem matches
case variants — `gm-campaign.sh path "Conan"` returns
`world-state/campaigns/Conan` (wrong case) instead of `.../conan`. Resolves to
the right directory on macOS and falls through correctly on Linux, so nothing
breaks today, but path strings leak wrong-case forms into logs, env vars, and
any case-sensitive downstream comparison (e.g. the import.md Step 2 slug
assertion compares slugified forms specifically to dodge this).

Fix: test exact membership in the directory listing (name in
os.listdir(campaigns_dir)) instead of `is_dir()` for the first branch; keep
the slug and legacy-slug fallbacks as-is. Test with a case-variant lookup on
a fixture dir.

## Acceptance criteria

- [x] `gm-campaign.sh path "Conan"` returns the canonical-case path (world-state/campaigns/conan) on a case-insensitive filesystem (test via CampaignManager with a fixture).
- [x] Exact-case, slugged, and legacy-slug lookups still resolve (existing test_slug_unify.py passes).
- [x] Full suite passes.

## Out of scope

Renaming existing campaign directories; slug rules (settled).

## Verification

Lane: agent

## Blocked by

None (land after import-extraction-repair commits to avoid file overlap on lib/campaign_manager.py).

---

## QA Reports

### 2026-08-14T13:54:32Z — pass [review-case]
reviewed: perfect (side-by-side old/new comparison on macOS; traversal guard
and tie-breaks proven unchanged). Informational notes recorded: slug-branch
symlink acceptance is pre-existing and low-impact; the case params only bite
on case-insensitive filesystems (the trailing-slash param is the platform-
independent guard); unreadable-dir PermissionError practically unreachable.

### 2026-08-14T13:51:38Z — verified [fable-sott1]
18/18 resolver tests; live probe returns canonical 'conan' for 'Conan';
symmetric slug-branch defect fixed too; import-a-book.md claims verified
still true (no restamp needed). Implementer full suite 514 passed.

## History

- 2026-08-13T18:53:00Z  created → ready (from impl-import observation)  [fable-sott1]
- 2026-08-14T13:41:28Z  claimed  [fable-sott1]
- 2026-08-14T13:46:09Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-14T13:51:38Z  verified → in-review  [fable-sott1]
- 2026-08-14T13:54:32Z  review perfect → done, committed  [fable-sott1]
