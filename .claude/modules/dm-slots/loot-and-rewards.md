## Loot & Rewards

After combat or significant achievement, handle loot and recording:

### 1. Handle Loot [PERSIST BEFORE NARRATING]

```bash
bash tools/dm-player.sh gold "[character]" +[amount]
bash tools/dm-player.sh inventory "[character]" add "[item_name]"
```

**Inventory System:**
- **Stackable Items**: Consumables with quantities (Medkit x3, Ammo 9mm x60, Vodka x2)
- **Unique Items**: Weapons, armor, quest items (one entry per item, no quantities)
- Auto-migrates from old format on first use (creates `.backup`)
- Transactions are atomic - all changes succeed or all fail

### 2. Record & Advance
```bash
bash tools/dm-note.sh "combat" "[Character] defeated [X] [enemies] at [location]"
bash tools/dm-time.sh "[new_time]" "[date]"
bash tools/dm-consequence.sh check
```

---
