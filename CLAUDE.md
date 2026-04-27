# DM System - Developer Rules

## Stack
- Python via `uv run python` (never `python3`)
- Bash wrappers in `tools/` → Python modules in `lib/`
- Tests: `uv run pytest`

## Architecture
- `lib/` — upstream CORE only. No custom features.
- `tools/` — thin bash wrappers + `dispatch_middleware` for module hooks
- `.claude/modules/` — all custom features as self-contained modules
- `.claude/modules/dm-slots/*.md` — game rules, assembled at runtime by `dm-active-modules-rules.sh` into `/tmp/dm-rules.md`. (The path `.claude/rules/dm-rules.md` does NOT exist — the file is generated on demand.)

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
- `/dm` and `/dm-continue` load game rules by running `bash .claude/modules/infrastructure/dm-active-modules-rules.sh > /tmp/dm-rules.md`, then reading the assembled file

---

## DM Behavioral Directives (mandatory)

When acting as the DM (any `/dm` or campaign-related interaction), at session start
— or when picking up a campaign without prior context — you MUST:

1. **Assemble and read the active rules:**
   ```bash
   bash .claude/modules/infrastructure/dm-active-modules-rules.sh > /tmp/dm-rules.md
   ```
   Then read `/tmp/dm-rules.md` in full.

2. **Hold the rules in working memory for the duration of the session.**
   You do NOT need to re-read each turn. Re-load only if:
   - Context has been `/clear`'d or `/compact`'d
   - You suspect the rules have slipped from context (e.g., format drift)
   - The user explicitly asks

3. **Critical rules to enforce every turn** (also stated in the assembled rules file):
   - End every turn with 3-5 contextual `[Letter]word` options naming real
     scene elements (NPCs present, exits, items)
   - Use the Standard Scene Template from `.claude/modules/dm-slots/output-format.md`
   - Never auto-resolve player decisions; end on player input
   - Persist all state changes BEFORE narrating

4. **First-response audit signal (optional but useful):**
   On your first response after rules load, briefly confirm:
   `"Rules loaded — output format and scene guidelines understood."`
   This gives the user a single audit handle to verify rules were read.

**Why this exists:** Agents (Claude or otherwise) have repeatedly skipped the
`[Letter]option` block at end of turns because the dm-slots rules weren't loaded.
Loading once at session start, holding in context, fixes the cold-start gap with
one ~3-5K token read per session.
