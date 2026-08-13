# /reset - Clear Campaign for Fresh Start

Quick command to reset the world state for a new campaign.

---

## STEP 1: CONFIRM INTENT

Display:
```
⚠️  CAMPAIGN RESET
━━━━━━━━━━━━━━━━━━

Reset keeps the SOURCE, the WORLD and the KIT, and clears the STORY.

Cleared:
  • Player character (and characters/, fallen/)
  • NPCs, locations, items
  • Facts, plots, consequences
  • Combat state, campaign memory, threat clocks
  • Session history, world-tick log, loremaster cache
  • Snapshot saves

Kept:
  • Source: current-document.txt, metadata.json, chunks/, vectors/, images/
  • World: world-bible.json, world-seed.json
  • Kit: ruleset.json, rules.md, chronicler.json

Options:
1. ARCHIVE - Copy current world to world-state/archive/, then reset (safe)
2. HARD RESET - Delete everything permanently (destructive)
3. CANCEL - Abort reset

What would you like?
```

---

## STEP 2: EXECUTE BASED ON CHOICE

### If ARCHIVE:
```bash
bash tools/gm-reset.sh archive --yes
```

`--yes` is required: the tool has no terminal when run through the Bash tool, and
STEP 1 already got the player's confirmation in chat.

This will:
- Copy the campaign directory to `world-state/archive/[campaign]-[timestamp]/`, minus
  `vectors/` (the ChromaDB index is rebuilt from the source document on the next prepare)
- Clear the story files listed above, keeping the source, the world and the kit
- Abort without resetting if the copy fails (the archive is the safety net)

### If HARD RESET:
```bash
bash tools/gm-reset.sh hard --yes
```

This will:
- Clear the same story files, keeping the source, the world and the kit
- No backup created
- Cannot be undone

### If CANCEL:
Display:
```
Reset cancelled. Your world is safe.
```

---

## STEP 3: CONFIRM COMPLETION

After successful reset, display:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  World Reset Complete

  Ready for /new-game or /gm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If archived, also show the archive path the tool printed:
```
  Archived to: world-state/archive/[campaign]-[timestamp]/

  To restore later:
  cp -R "world-state/archive/[campaign]-[timestamp]/." "world-state/campaigns/[campaign]/"

  (The archive has no vectors/ — the live campaign keeps its index, so a restore
  is playable as-is.)
```

---

## QUICK RESET (No Confirmation)

If user runs `/reset hard` or `/reset archive` directly:
- Skip confirmation
- Execute immediately: `bash tools/gm-reset.sh archive --yes` / `bash tools/gm-reset.sh hard --yes`
- Show completion message
