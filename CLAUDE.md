# DM System - Developer Rules

## Stack
- Python via `uv run python` (never `python3`)
- Bash wrappers in `tools/` → Python modules in `lib/`
- Tests: `uv run pytest`

## Architecture
- `lib/` — upstream CORE only. No custom features.
- `tools/` — thin bash wrappers + `dispatch_middleware` for module hooks
- `.claude/modules/` — all custom features as self-contained modules
- `.claude/rules/dm-rules.md` — game rules (loaded by `/dm` skill only)

## Module pattern
Each module in `.claude/modules/<name>/`:
- `middleware/<tool>.sh` — intercepts CORE tool calls, handles `--help`
- `lib/` — module Python code
- `tools/` — module-specific CLI
- `module.json` — metadata

## Dev commands
```bash
uv run pytest                    # run all tests
bash tools/dm-module.sh list     # list active modules
git diff upstream/main -- lib/   # check CORE purity
```

## Rules
- CORE tools delegate to modules via `dispatch_middleware "tool.sh" "$ACTION" "$@" && exit $?`
- `lib/` diff from upstream: only `ensure_ascii=False`, `require_active_campaign`, `name=None` auto-detect
- Never add features to `lib/` — put them in modules
- `/dm` loads game rules from `.claude/rules/dm-rules.md` via skill
