---
type: Playbook
title: Running the tests
description: How to run the suite, why one failure and one skip are expected, and the hermetic-campaign fixture every state test depends on.
sources:
  - { resource: /tests/conftest.py }
  - { resource: /pyproject.toml }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# Running the tests

```bash
uv run --extra dev pytest          # pytest lives in the dev extra, not core
uv run --extra dev pytest -rs      # ...and show why anything skipped
```

`uv run pytest` alone fails with `Failed to spawn: pytest` on a fresh venv — the dev extra
is not installed by default. `pyproject.toml` sets `testpaths = ["tests"]`,
`pythonpath = ["."]`, and `addopts = "-q"`, so tests import `lib.*` without any path
juggling and the default output is quiet.

## Two non-failures to expect

Measured 2026-08-13 at `58c7cd4`: **245 passed, 1 failed, 1 skipped.**

- **The failure is known and the test is wrong**, not the code:
  `test_identity_onboarding.py::test_build_dispatches_and_saves` asserts a nested
  `identity` key on a file that is now persisted flat. Filed as a `p2` in commit `9ef38ba`.
  See [two validate_character functions](../gotchas/identity-onboarding-schema-drift.md).
- **The skip is dependency-gated:** `test_creation_grounding.py:127` skips without
  `sentence_transformers`. Install the `rag` extra to run it —
  `uv run --extra dev --extra rag pytest`.

Re-derive the counts rather than trusting them; a second failure means something real
broke.

## Everything state-related runs against a hermetic campaign copy

`tests/conftest.py` ships one fixture, `dcc_world`. It `copytree`s the checked-in Dungeon
Crawler Carl campaign under `tests/fixtures/world-state/` into a per-test `tmp_path` and
returns the path. Managers take that path as their `world_state_dir`, so a test that writes
touches only its own copy.

Two consequences worth holding on to:

- **Never point a test at a live campaign.** The fixture exists precisely because the
  managers write on read in places — see the migrate-on-load behaviour in
  [the player character sheet](../modules/player-character.md).
- **The fixture is a real imported campaign, not a synthetic minimum.** It has 16 NPCs,
  a bible, a ruleset, and real tag drift (an NPC tagged both `Tutorial Guild Hall` and
  `tutorial-guild-hall`). That makes it a good grounding target and a bad place to assume
  clean data.

The wrapper tests (`test_json_wrappers_*.py`) go one level further and run each manager as
a **subprocess**, asserting the `--json` envelope parses — the contract in
[the tool wrapper contract](../conventions/tool-wrapper-contract.md).

## Related

- [Install and setup](install-and-setup.md)
