# /reset - Clear Campaign for Fresh Start

Quick command to reset the world state for a new campaign.

---

## STEP 1: CONFIRM INTENT

Display:
```
⚠️  CAMPAIGN RESET
━━━━━━━━━━━━━━━━━━

This will clear ALL world state:
  • NPCs
  • Locations
  • Facts
  • Consequences
  • Session history
  • Player characters

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
- Copy the whole campaign directory to `world-state/archive/[campaign]-[timestamp]/`
- Clear all world-state files
- Abort without resetting if the copy fails (the archive is the safety net)

### If HARD RESET:
```bash
bash tools/gm-reset.sh hard --yes
```

This will:
- Delete all world-state content permanently
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
```

---

## QUICK RESET (No Confirmation)

If user runs `/reset hard` or `/reset archive` directly:
- Skip confirmation
- Execute immediately: `bash tools/gm-reset.sh archive --yes` / `bash tools/gm-reset.sh hard --yes`
- Show completion message
