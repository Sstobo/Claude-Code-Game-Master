---
type: Convention
title: The tool wrapper contract
description: Every capability is a bash wrapper over a Python manager over per-campaign JSON — and every manager speaks the same --json envelope.
sources:
  - { resource: /tools/common.sh }
  - { resource: /lib/cli_output.py }
  - { resource: /lib/json_ops.py }
  - { resource: /tests/test_json_wrappers_player.py }
generated: { by: claude-opus-5, at: 2026-08-13T13:52:08Z }
---

# The tool wrapper contract

Three layers, no exceptions: **`tools/gm-*.sh` → `lib/*.py` → per-campaign JSON**. The
wrapper resolves the interpreter and the campaign; the manager holds the logic; state lives
on disk as plain JSON under `world-state/campaigns/<name>/`.

Always invoke as `bash tools/gm-<tool>.sh <command>`, never the Python directly — the
wrapper is what supplies the campaign resolution below.

## What `common.sh` guarantees before a manager runs

Every wrapper sources it, and inherits:

- **`PYTHON_CMD`** — `uv run python` if `uv` is on PATH, else `python3`, else `python`.
  This is why project instructions say never to call bare `python`: the wrapper already
  chose, and choosing differently skips the venv.
- **Path anchoring** — `PROJECT_ROOT` is derived from the script's own location, so tools
  work from any working directory.
- **`require_active_campaign`** — multi-campaign support is a single file,
  `world-state/active-campaign.txt`. Every tool reads it; nothing takes a campaign
  argument by default.

## The `--json` envelope is the machine contract

`lib/cli_output.py` defines two shapes and nothing else:

```json
{"ok": true,  "data": …}
{"ok": false, "error": "…", "code": null}
```

The rationale is in the module's own docstring: it exists to kill stdout-scraping, without
adding an MCP process. The wiring pattern for a new manager is fixed —
`wants_json()` to detect, `strip_json_flag()` before argparse (so argparse never sees
`--json`), `emit()` / `emit_error()` to output. `emit_error` returns `1` so callers write
`sys.exit(emit_error(...))`.

One trap the existing code already works around: a manager whose logic `print()`s human
text must suppress that in JSON mode or the envelope is preceded by garbage.
`consequence_manager` does this with `contextlib.redirect_stdout`
(`lib/consequence_manager.py:362-367`). Any manager that prints inside its logic needs the
same treatment.

`DM_JSON=1` turns the envelope on globally, which is the easy way to script a whole
sequence.

## Input validation is a manager concern, not a wrapper one

`lib/validators.py` holds the shared input guards (names, attitudes, dice notation) that
managers call before writing. The wrapper layer validates almost nothing — `common.sh` has
a `validate_name`, but the real trust boundary is inside the Python. A manager that skips
`Validators` writes whatever it was handed straight to disk.

## Enforcement point

`tests/test_json_wrappers_*.py` (player, npc, session, consequence) run each manager as a
subprocess and assert the envelope parses with `ok: true` and the expected `data`. That is
a genuine guard for the four managers covered — and only those four. A new manager gets no
envelope enforcement until a matching test exists; adding one is part of adding the tool.

## Related

- [A play turn](../flows/play-turn.md) — where these calls sit in the loop
- [Persist before narrate](persist-before-narrate.md) — when to call them
