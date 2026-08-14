---
slug: kit-block-in-context
title: Kit ambient in scene context; signature systems rendered; STEP-0 guards retired
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: trust-the-agent
blockedBy: [core-prompt-detox]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
reviewRounds: null
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-14T18:52:00Z
---

## Parent

Trust the Agent (prds/trust-the-agent.md)

## Category

enhancement

## What to build

`gm-session.sh context` contains no kit information (grep lib/session_manager.py
for `world_kit`: zero hits), so three skills pay a STEP-0 tool call to
re-derive the kit while gm-social/gm-conditions/gm-skills hand out 5e DCs to
every world unguarded. Separately, `ruleset.signature_systems` — "the heart of
the kit" — is read by nothing; the rules block renders only the hand-copied
`campaign-overview.campaign_rules` (lib/session_manager.py:661-665).

1. Add a KIT block to the top of `get_full_context`: kit name, resolution
   model, progression model, vitals, skill list — read from `ruleset.json` via
   `WorldKit` (add accessors as needed).
2. Add `WorldKit.signature_systems()` (settle the list-vs-dict shape; the
   conan ruleset's dict form is the migration case) and render YOUR WORLD'S
   RULES from it, falling back to `campaign_rules` for legacy campaigns.
3. Trim the STEP-0 kit guards in gm-combat/gm-levelup/gm-spellcasting to one
   line deferring to the context's KIT block; add a kit-deference line to
   gm-skills, gm-social, gm-conditions (their DC ladders and condition lists
   apply only when the KIT block says dnd5e).
4. Update `docs/modules/scene-context.md` and
   `docs/modules/game-core-and-world-kit.md` in the same commit.

## Acceptance criteria

- [ ] `gm-session.sh context` output for a dnd5e campaign and for the conan campaign each contain a KIT block naming their kit, resolution, and progression models.
- [ ] Signature systems from `ruleset.json` appear in the rules block for a kit-bearing campaign; a legacy campaign without them still renders `campaign_rules`.
- [ ] `tests/test_lean_core.py` (kit-guard assertions) updated and passing; no skill instructs a `world_kit.py info` call for what context now carries.
- [ ] Both claiming module docs restamped.

## Out of scope

Resolution-model dispatch and vitals tracking (executable-world-kit); the
CLAUDE.md diet (Tier 3); gm-kit.sh wrapper (Tier 2).

## Verification

Lane: agent

## Blocked by

core-prompt-detox (session_manager.py one-writer chain)

---

## QA Reports

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-14T18:52:00Z  blocked → ready; parent trust-the-agent; blockedBy core-prompt-detox  [gk-t8n2wp]
- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
