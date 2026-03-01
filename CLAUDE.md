# DM System - Developer Rules

## Stack
- Python via `uv run python` (never `python3`)
- Bash wrappers in `tools/` → Python modules in `lib/`
- Tests: `uv run pytest`

## Architecture
- `lib/` — upstream CORE only. No custom features.
- `tools/` — thin bash wrappers + `dispatch_middleware` for module hooks
- `.claude/modules/` — all custom features as self-contained modules
- `.claude/modules/dm-slots/` — vanilla DM rules (27 slot files, loaded in advanced mode only)
- `.claude/modules/infrastructure/` — advanced mode loaders (dm-active-modules-rules.sh, dm-campaign-rules.sh, dm-narrator.sh)
- `.claude/modules/campaign-rules-templates/` — campaign rule templates
- `.claude/modules/narrator-styles/` — narrator style definitions

## Two gameplay modes
- **Vanilla** (`/dm`): loads dm-slots via `dm-active-modules-rules.sh` → `/tmp/dm-rules.md` (pure vanilla slots, no module replacements)
- **Advanced** (`/dm-continue`): loads dm-slots + module rules via `dm-active-modules-rules.sh` → `/tmp/dm-rules.md`, campaign rules via `dm-campaign-rules.sh`, narrator styles. Activated when `campaign-overview.json` has `"advanced_mode": true`

## Module pattern
Each module in `.claude/modules/<name>/`:
- `middleware/<tool>.sh` — intercepts CORE tool calls, handles `--help`
- `lib/` — module Python code
- `tools/` — module-specific CLI
- `module.json` — metadata

## Dev commands
```bash
uv run pytest                                              # run all tests
bash .claude/modules/infrastructure/tools/dm-module.sh list # list active modules
git diff upstream/main -- lib/                              # check CORE purity
```

## Rules
- CORE tools delegate to modules via `dispatch_middleware "tool.sh" "$ACTION" "$@" && exit $?`
- `lib/` diff from upstream: only `ensure_ascii=False`, `require_active_campaign`, `name=None` auto-detect
- Never add features to `lib/` — put them in modules
- `/dm` vanilla: no external rules loaded. `/dm-continue` advanced: loads `.claude/modules/dm-slots/*.md` + module rules via `dm-active-modules-rules.sh`
