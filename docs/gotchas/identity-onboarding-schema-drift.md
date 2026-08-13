---
type: Gotcha
title: Two validate_character functions, and one stale test
description: The same function name means two different contracts — and asserting the open shape against the flat file has already produced one long-lived red test.
sources:
  - { resource: /lib/character_schema.py }
  - { resource: /lib/schemas.py }
  - { resource: /lib/identity_onboarding.py }
  - { resource: /tests/test_identity_onboarding.py }
generated: { by: claude-fable-5, at: 2026-08-13T14:28:15Z }
---

# Two `validate_character` functions, and one stale test

## Same name, opposite contracts

| Function | Accepts | Behaviour on a flat sheet |
|---|---|---|
| `character_schema.validate_character(char, kit=None)` | **open shape only** | reports every required key missing |
| `schemas.validate_character(data)` | **either** — calls `to_flat` first (`lib/schemas.py:257`) | works |

`schemas.validate_character` is the one to call on anything loaded from disk;
`character_schema.validate_character` is for validating a builder's output before it is
flattened, and is the only one that can check attributes against a World Kit's stat
schema. Importing "the" validator without checking which module it came from is a coin
flip.

## The stale test this caused (fixed 2026-08-13)

`test_build_dispatches_and_saves` failed with `KeyError: 'identity'` from 2026-06-07
(filed in commit `9ef38ba`) until 2026-08-13: it saved a character, reloaded
`character.json`, and asserted the **open** shape (`reloaded["identity"]["name"]`) on a
file that `save_character` persists flat (`lib/identity_onboarding.py:83-89` states this
in its own docstring; flat has been canonical since `efd1cb7`). The code was right and the
test was stale — the fix asserted the flat keys. The confusion pattern survives the fix,
which is why this gotcha does: `build()` returns open, disk holds flat, and asserting one
shape against the other's home always looks like a code bug first.

The suite is fully green as of 2026-08-13. See [testing](../playbooks/testing.md).

## Related

- [The player character sheet](../modules/player-character.md) — the flat/open split in full
- [Onboarding and death hand-off](../flows/onboarding-and-death.md)
