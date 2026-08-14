---
slug: identity-onboarding-wiring
title: Wire identity-first onboarding — the tested code gets its first caller
category: bug
kind: afk
priority: p1
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-14T13:41:28Z
changedFiles: [lib/identity_onboarding.py, tools/gm-player.sh, '.claude/commands/gm.md', '.claude/commands/import.md', '.claude/commands/new-game.md', docs/flows/onboarding-and-death.md, tests/test_json_wrappers_onboard.py]
resolution: the three-door onboarding is the wired default entry — guarded, alias-aware, and become()-parity
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T15:47:00Z
updatedAt: 2026-08-14T14:01:29Z
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

- [x] `bash tools/gm-player.sh onboard --mode original --json` (and canon/nameless) runs from a fixture campaign and persists a valid character.json.
- [x] gm.md's no-character branch and both pipelines' hand-off name the onboard path, not /create-character, as the default.
- [x] Existing identity-onboarding tests pass unchanged; a new wrapper-level envelope test exists.
- [x] docs/flows/onboarding-and-death.md restamped; the three-sources-three-answers contradiction is gone.
- [x] (review) onboard refuses/archives when character.json exists (no silent clobber).
- [x] (review) canon door resolves aliases like become() does.
- [x] (review) onboard sets current_character on the overview.
- [x] (review) a canon-onboarded NPC is flagged so context stops voicing them.

## Out of scope

Making /create-character kit-aware (kit-aware-character-creation); the Death
Protocol swap mechanics (already correct in player_manager.become).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T14:01:29Z — pass [review-onboard-2]
reviewed: perfect (round 2; reviewer notes the allow-list lift is STRONGER
than become()'s strip-after-flatten). Non-blocking notes recorded: inline
slug duplication in archive_character; gm.md 'below' wording. CLAUDE.md
step-3 suggested line still pending the GM session's file (in QA above).

### 2026-08-14T13:58:58Z — verified (fix round 1) [fable-sott1]
15/15 onboarding tests; refusal-without---replace, fallen/ archive,
current_character write, alias-aware canon door, PC flag trio + alive
status all test-pinned. Implementer full suite 517 passed.

### 2026-08-14T13:53:38Z — fail [review-onboard]
reviewed: needs-changes
1. save_character overwrites an existing PC silently (become() archives to fallen/ first).
2. Canon door exact-match only; become() is alias-aware one call away.
3. current_character never set — session start/status/world_stats report None.
4. Canon NPC stays in npcs.json unflagged — double-tracked, context voices the PC.
Non-blocking: third-positional swallow; status/died_at not normalized on canon; generated-newer-than-verified stamp note.

### 2026-08-14T13:51:05Z — verified [fable-sott1]
Wrapper envelope tests pass on a hermetic world; all three surfaces name
onboard as the default entry; one save path (open-to-flat stays in
identity_onboarding's own save). CLAUDE.md step-3 suggested line held for
the user (file owned by the GM session): see QA note below. Implementer
full suite green.

Suggested CLAUDE.md step-3 line (not applied):
3. Active campaign but no character.json -> identity-first onboarding: ask
"Who are you in this world?" and persist with `bash tools/gm-player.sh
onboard canon "<npc>" | original "<name>" "<concept>" | nameless`
(/create-character is the opt-in full builder).

## History

- 2026-08-13T15:47:00Z  created → ready  [team-lead]
- 2026-08-14T13:41:28Z  claimed  [fable-sott1]
- 2026-08-14T13:46:09Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-14T13:51:05Z  verified → in-review  [fable-sott1]
- 2026-08-14T13:53:38Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-14T13:58:58Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-14T14:01:29Z  review perfect → done, committed  [fable-sott1]
