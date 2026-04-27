# AGENTS.md — Operating directives for any AI agent in this repo

This file mirrors the DM behavioral directives in `CLAUDE.md` for non-Claude
agent harnesses (Cursor, Aider, Ollama-hosted models, DeepSeek, Kimi, etc.).
The same rules apply regardless of which model is driving the DM role.

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
   - Context has been cleared or compacted by the harness
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

---

## Why this exists

Different harnesses read different config files. Claude Code reads `CLAUDE.md`;
many other harnesses read `AGENTS.md` (some read both). Mirroring the directives
in both files ensures rules-loading happens regardless of which harness drives.

If your harness reads neither file, you should manually:

1. Run the rules assembly command above
2. Read `/tmp/dm-rules.md`
3. Treat its contents as authoritative for the duration of the session

---

## Token cost

Loading the assembled rules is ~3-5K tokens, once per session. Compared to the
cost of agents producing format-broken output that the user has to correct or
re-prompt, this is the cheaper path.

**Not recommended for Haiku-class / small models.** They tend not to follow
meta-directives like this reliably. Use Sonnet/Opus or capable open-weight
models (Kimi 2.6+, DeepSeek v3+, Qwen 2.5+, etc.).
