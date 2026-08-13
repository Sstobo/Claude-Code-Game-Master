---
type: Gotcha
title: The open/flat character-shape trap
description: Builders work in the open shape, disk holds flat — asserting one against the other's home has produced a duplicate validator and a long-lived red test.
sources:
  - { resource: /lib/character_schema.py }
  - { resource: /lib/schemas.py }
  - { resource: /lib/identity_onboarding.py }
  - { resource: /tests/test_identity_onboarding.py }
generated: { by: claude-fable-5, at: 2026-08-13T14:46:10Z }
---

# The open/flat shape trap, and the stale test it produced

## One validator now (since 2026-08-13)

`schemas.validate_character(data, kit=None)` is THE character validator: it accepts either
shape (normalizing via `to_flat` first) and carries the kit check (stats must be within
the active kit's declared attributes). Until 2026-08-13 a second
`validate_character` lived in `character_schema` that accepted **only** the open shape —
it reported a loaded flat sheet as entirely missing, and which contract you got depended
on which module you imported from. Deleted; a comment marks the grave.

The underlying trap survives the consolidation, which is why this gotcha does:
**builders work in the open shape, disk holds flat.** `IdentityOnboarding.build()`
returns open; `character.json` is always flat. Asserting one shape against the other's
home always looks like a code bug first.

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
