---
slug: subagent-fanout-cap
title: Extractor agent definitions must forbid self-spawning
category: bug
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
reviewRounds: null
implementer: null
createdAt: 2026-08-13T16:20:00Z
updatedAt: 2026-08-13T16:20:00Z
---

## Parent

State of the Table (prds/state-of-the-table.md)

## Category

bug

## What to build

The Conan import launched 4 extractor agents - within the project's 6-agent
cap. Two of them silently spawned their own reader fleets to split the
1005-chunk corpus: the plots extractor spawned 6, the NPC extractor spawned 6.
Real total: ~16 agent instances, ~525k subagent tokens, roughly 4x the intended
budget. The nesting was invisible until the agents' completion reports
mentioned it.

Agents handed a large corpus will fan out unless told not to. The cap has to be
stated inside the subagent's own definition, not just honored by the caller.

1. Add an explicit no-self-spawn instruction to the four `extractor-*` agent
   definitions in `.claude/agents/`.
2. State the same constraint in the `/import` flow's agent-launch step so the
   prompt carries it too.
3. Document the rule where fan-out is described, so future agent authors
   inherit it.

## Acceptance criteria

- [ ] All four extractor agent definitions instruct the agent to do the work itself and not spawn subagents.
- [ ] The import flow's launch step includes the same constraint in the prompt it sends.
- [ ] The convention is documented once, in the place agent authors will read.

## Out of scope

Changing the 6-agent cap, and the extractor sampling strategy.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T16:20:00Z  created → ready  [gm-session]
