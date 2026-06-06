---
slug: combat-state-persistence
title: Persisted combat state + lightweight dm-combat.sh (optional by default)
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: dm-claude-reimagining
blockedBy: [json-returning-wrappers]
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-06T02:24:27Z
updatedAt: 2026-06-06T02:24:27Z
---

## Parent

DM Claude Reimagining (prds/dm-claude-reimagining.md)

## Category

enhancement

## What to build

Fix the one place that violates persist-before-narrate. Combat persists nothing —
initiative, enemy HP, conditions, round live only in the model's working memory
and drift across turns/compaction/resume. Add `combat_state.json` (initiative
order, per-combatant HP/AC/conditions, round) + a lightweight `dm-combat.sh`
(start / add-enemy / hp / condition / next-turn / end). Render the combat header
from this state so HP bars are always truthful; award XP/loot on end. OPTIONAL by
default — trivial skirmishes pay no bookkeeping tax (mirror lightweight-vs-
structured dungeon split).

## Acceptance criteria

- [ ] `combat_state.json` persists initiative, per-combatant HP/AC/conditions, round number.
- [ ] `dm-combat.sh` supports start/add-enemy/hp/condition/next-turn/end (structured JSON output).
- [ ] Combat header renders from persisted state; enemy HP survives a simulated resume.
- [ ] `end` awards XP/loot via the active kit and clears combat state.
- [ ] Combat is OPTIONAL: a narrated skirmish without starting combat state still works.
- [ ] Test: start combat → damage enemy → reload → HP intact; end → state cleared + reward applied.

## Verification

Lane: agent

## Blocked by

json-returning-wrappers

---

## QA Reports

## History

- 2026-06-06T02:24:27Z  created → ready  [ship-it]
