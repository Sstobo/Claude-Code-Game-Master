# /dm - Dungeon Master: Campaign Selection

## YOUR ONLY JOB HERE

Show the campaign menu. Nothing else. Do not load rules. Do not narrate. Do not greet.

---

## Step 1: List campaigns

```bash
bash tools/dm-campaign.sh list
```

## Step 2: Display menu

```
================================================================
  ╔═══════════════════════════════════════════════════════════╗
  ║           SELECT YOUR ADVENTURE                           ║
  ╚═══════════════════════════════════════════════════════════╝
================================================================

  SAVED CAMPAIGNS
  ────────────────────────────────────────────────────────────
  [1] Campaign Name
      Character (Race Class L#) · X sessions · Last: Location

  [2] ...

  ────────────────────────────────────────────────────────────
  [N] ✨ NEW ADVENTURE

================================================================
```

## Step 3: Wait for input

- **Number** → `bash tools/dm-campaign.sh switch <name>` → invoke `/dm-continue`
- **N** → show new adventure menu:

```
  [1] 🌍 CREATE WORLD     → invoke `/new-game`
  [2] 📜 IMPORT DOCUMENT  → invoke `/import`
  [3] ⚔️  ONE-SHOT        → invoke `/dm-continue` (one-shot mode)
```

That's it. Selection made → hand off to the right skill.
