---
type: Gotcha
title: Two validate_character functions, and one stale test
description: The same function name means two different contracts, and a red test in the suite is the test's fault, not the code's.
sources:
  - { resource: /lib/character_schema.py }
  - { resource: /lib/schemas.py }
  - { resource: /lib/identity_onboarding.py }
  - { resource: /tests/test_identity_onboarding.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
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

## The failing test asserts a shape that stopped being written

`tests/test_identity_onboarding.py::test_build_dispatches_and_saves` fails with
`KeyError: 'identity'`. It saves a character, reloads `character.json`, and asserts
`reloaded["identity"]["name"]` (`tests/test_identity_onboarding.py:53-54`).

**The code is right and the test is stale.** `IdentityOnboarding.build` deliberately works
in the open shape — that is the internal builder shape — and `save_character` persists
`to_flat(char)`, which its own docstring states (`lib/identity_onboarding.py:83-89`). The
flat shape has been canonical since commit `efd1cb7`. The other tests in the file assert
against `build()`'s return value, not the reloaded file, and pass.

The fix is to assert `reloaded["name"] == "Kira"`. Filed as a `p2` bug in commit `9ef38ba`
(`tickets/needs-triage/identity-onboarding-schema-drift.md`); still open as of
2026-08-13, and still the only known red test.

Consequence for anyone running the suite: **one pre-existing failure is expected.** See
[testing](../playbooks/testing.md).

## Related

- [The player character sheet](../modules/player-character.md) — the flat/open split in full
- [Onboarding and death hand-off](../flows/onboarding-and-death.md)
