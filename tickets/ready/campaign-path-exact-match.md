---
slug: campaign-path-exact-match
title: _resolve_name trusts is_dir() so macOS case-insensitivity returns case-variant paths
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T18:53:00Z
updatedAt: 2026-08-13T18:53:00Z
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

- [ ] `gm-campaign.sh path "Conan"` returns the canonical-case path (world-state/campaigns/conan) on a case-insensitive filesystem (test via CampaignManager with a fixture).
- [ ] Exact-case, slugged, and legacy-slug lookups still resolve (existing test_slug_unify.py passes).
- [ ] Full suite passes.

## Out of scope

Renaming existing campaign directories; slug rules (settled).

## Verification

Lane: agent

## Blocked by

None (land after import-extraction-repair commits to avoid file overlap on lib/campaign_manager.py).

---

## QA Reports

## History

- 2026-08-13T18:53:00Z  created → ready (from impl-import observation)  [fable-sott1]
