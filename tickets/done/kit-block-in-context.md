---
slug: kit-block-in-context
title: Kit ambient in scene context; signature systems rendered; STEP-0 guards retired
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: trust-the-agent
blockedBy: [core-prompt-detox]
claimedBy: gk-t8n2wp
claimedAt: 2026-08-14T19:17:09Z
changedFiles: [lib/session_manager.py, lib/world_kit.py, tests/test_kit_block.py, tests/test_lean_core.py, .claude/skills/gm-combat/SKILL.md, .claude/skills/gm-levelup/SKILL.md, .claude/skills/gm-spellcasting/SKILL.md, .claude/skills/gm-skills/SKILL.md, .claude/skills/gm-social/SKILL.md, .claude/skills/gm-conditions/SKILL.md, docs/modules/scene-context.md, docs/modules/game-core-and-world-kit.md, docs/conventions/lean-core-and-skill-routing.md]
reviewRounds: 1
resolution: KIT block in context; signature_systems render; skills defer to the block
updatedAt: 2026-08-14T19:32:00Z
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

- [x] `gm-session.sh context` output for a dnd5e campaign and for the conan campaign each contain a KIT block naming their kit, resolution, and progression models.
- [x] Signature systems from `ruleset.json` appear in the rules block for a kit-bearing campaign; a legacy campaign without them still renders `campaign_rules`.
- [x] `tests/test_lean_core.py` (kit-guard assertions) updated and passing; no skill instructs a `world_kit.py info` call for what context now carries.
- [x] Both claiming module docs restamped.

## Out of scope

Resolution-model dispatch and vitals tracking (executable-world-kit); the
CLAUDE.md diet (Tier 3); gm-kit.sh wrapper (Tier 2).

## Verification

Lane: agent

## Blocked by

core-prompt-detox (session_manager.py one-writer chain)

---

## QA Reports

### 2026-08-14T19:32:00Z — pass [e7b048de]
reviewed: perfect. KIT block in context; signature_systems preferred; skills defer; no world_kit.py info.

### 2026-08-14T19:22:00Z — verified [gk-t8n2wp]
KIT block on DCC (custom/d20/resource-axis) and dnd5e tmp campaign; signature_systems list+dict in rules; campaign_rules fallback; skills defer to KIT block. 38 tests passed (kit_block+lean_core+get_full_context+gm_md_slim).

### 2026-08-14T17:56:17Z — fail [gk-a8r14q]
blocked: file collision on CLAUDE.md / lib/session_manager.py — live-session uncommitted edits; user parked until those files are clean

## History

- 2026-08-14T19:32:00Z  done: KIT block in context; signature_systems render; skills defer to the block  [gk-t8n2wp]
- 2026-08-14T19:22:00Z  verified → in-review, review dispatched  [gk-t8n2wp]
- 2026-08-14T19:17:09Z  doc-grounding confirmed — user pre-confirmed "do ALL of this now"  [gk-t8n2wp]
- 2026-08-14T19:17:09Z  claimed  [gk-t8n2wp]
- 2026-08-14T18:52:00Z  blocked → ready; parent trust-the-agent; blockedBy core-prompt-detox  [gk-t8n2wp]
- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-14T17:56:17Z  ready → blocked  file collision on CLAUDE.md + lib/session_manager.py  [gk-a8r14q]
