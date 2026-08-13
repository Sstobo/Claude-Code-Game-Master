---
slug: identity-onboarding-wiring
title: Wire identity-first onboarding — the tested code gets its first caller
category: bug
kind: afk
priority: p1
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

`lib/identity_onboarding.py` is implemented and tested
(tests/test_identity_onboarding.py) and documented as the default entry path
(docs/flows/onboarding-and-death.md:19-41, CLAUDE.md setup step 3) — but has
no `__main__`, no wrapper, and zero callers. Both pipelines and the
no-character branch (gm.md:433) route to the 5e /create-character instead.

1. Add a `main()` to identity_onboarding.py and a wrapper —
   `gm-player.sh onboard --mode canon|original|nameless` (subcommand on the
   existing wrapper; follow the common.sh + cli_output envelope contract).
2. Route the no-character branch in `.claude/commands/gm.md` and the
   hand-offs in import.md:549 / new-game.md:210 to the three-door onboarding;
   /create-character remains the opt-in full builder.
3. Restamp docs/flows/onboarding-and-death.md — its entry half becomes true;
   reconcile CLAUDE.md step 3 wording.
4. Add the wrapper envelope test (per docs/conventions/tool-wrapper-contract.md:69,
   new managers get no enforcement until one exists).

## Acceptance criteria

- [ ] `bash tools/gm-player.sh onboard --mode original --json` (and canon/nameless) runs from a fixture campaign and persists a valid character.json.
- [ ] gm.md's no-character branch and both pipelines' hand-off name the onboard path, not /create-character, as the default.
- [ ] Existing identity-onboarding tests pass unchanged; a new wrapper-level envelope test exists.
- [ ] docs/flows/onboarding-and-death.md restamped; the three-sources-three-answers contradiction is gone.

## Out of scope

Making /create-character kit-aware (kit-aware-character-creation); the Death
Protocol swap mechanics (already correct in player_manager.become).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
