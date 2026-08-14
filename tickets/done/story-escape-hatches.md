---
slug: story-escape-hatches
title: Overrides for the story the code forbids — resurrection, style breaks, appearance breaks
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: state-of-the-table
blockedBy: []
claimedBy: fable-sott1
claimedAt: 2026-08-14T14:01:47Z
changedFiles: ['.claude/agents/scene-illustrator.md', docs/flows/onboarding-and-death.md, lib/player_manager.py, lib/image_gen.py, tools/gm-player.sh, tools/gm-image.sh, '.claude/commands/import.md', '.claude/commands/new-game.md', docs/flows/scene-illustration.md, docs/modules/player-character.md, tests/test_story_escape_hatches.py]
resolution: the story the code forbade is reachable — deliberate revive, image-lock escapes, honest style formula
reviewRounds: 2
implementer: null
createdAt: 2026-08-13T21:30:00Z
updatedAt: 2026-08-14T14:50:19Z
---

## Parent

State of the Table (prds/state-of-the-table.md) · Trust the Agent review (artifact 1a6acb14)

## Category

enhancement

## What to build

Right defaults, missing escape hatches:

1. **player_manager.py:463-478 corpse guard** — currently an unconditional
   veto on resurrection (revivify, DCC respawns, divine intervention). Add a
   `revive` verb (`gm-player.sh revive <name> [--hp N] --reason "..."`) that
   clears dead status deliberately and logs the reason; the guard's message
   points at it alongside the Death Protocol. Kit-aware flavor optional
   (a kit may declare death irreversible — then revive warns loudly but the
   GM still decides).
2. **image_gen.py:214-224,249-251** — `--no-style-lock` and
   `--no-appearance-lock` flags on gm-image.sh generate, for dream sequences,
   flashbacks by a different in-world hand, mid-transformation characters.
   Defaults unchanged.
3. **import.md:509 + new-game.md:61 art-style formula** — keep the
   once-per-campaign lock and the "In the style of" prefix (parsed); drop the
   mandatory "two unexpected references" mashup shape to one example
   approach among others.

## Acceptance criteria

- [x] A killed fixture PC can be revived via the new verb with reason logged; modify_hp works again after; kill→revive→kill round-trips.
- [x] gm-image.sh generate --no-style-lock produces a prompt without the chronicler style line; --no-appearance-lock skips injection (unit-test the prompt builder, no API call).
- [x] Style-formula wording softened in both commands; "In the style of" prefix requirement intact.
- [x] Full suite passes; player-character.md + scene-illustration flow restamped where claims move.

## Out of scope

Death Protocol flow itself; chronicler/persona system; image cost gates.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

### 2026-08-14T14:50:19Z — pass [review-story-2]
reviewed: perfect (round 2; all seven closed, no new defect). Sub-threshold
notes: onboarding doc's become() line cite was already stale and restamped
stale — T3 symbol-citation pass territory; hp-less-sheet edge unreachable
by schema.

### 2026-08-14T14:47:33Z — verified (fix round 1) [fable-sott1]
12/12 escape-hatch tests; agent file carries the cooperate-with-the-flag
rule; name-mismatch guard, mutual stamp exclusivity, hp>=1 clamp all
test-pinned; three docs restamped. Implementer full suite green.

### 2026-08-14T14:44:31Z — fail [review-story]
reviewed: needs-changes
1. (major) Flags inert via scene-illustrator — the agent restates style+appearance in prompt text; needs the one-line rule in the agent file.
2. Flow doc contradicts itself two lines apart ('always fires').
3. --no-appearance-lock is frame-wide; per-character omission is the better documented move.
4. revive ignores name in single-character mode — wrong-PC hazard; guard or document.
5. kill doesn't clear revived_* stamps (doc implies exclusivity).
6. HP clamp skipped when max unknown — revive --hp 0 yields alive-at-0.
7. onboarding-and-death.md claims these sources, omits the only dead-state exit — pointer + restamp.

### 2026-08-14T14:40:49Z — verified [fable-sott1]
9/9 escape-hatch tests + injection tests green; revive verb in help; both
image flags present; style formula softened with the lock intact. The one
full-suite failure is the sibling cwd ticket's mid-edit tree (expected,
re-verified at commit). build_prompt extraction keeps injections pure and
testable.

## History

- 2026-08-13T21:30:00Z  created → ready (Trust the Agent review)  [fable-sott1]
- 2026-08-14T14:01:47Z  claimed  [fable-sott1]
- 2026-08-14T14:34:23Z  doc-grounding confirmed  [fable-sott1]
- 2026-08-14T14:40:49Z  verified → in-review  [fable-sott1]
- 2026-08-14T14:44:31Z  review needs-changes (round 1) — fix re-delegated  [fable-sott1]
- 2026-08-14T14:47:33Z  fix round verified — followup review dispatched  [fable-sott1]
- 2026-08-14T14:50:19Z  review perfect → done, committed  [fable-sott1]
