## Rest & Recovery

### Short Rest (1 Hour)
```bash
bash tools/dm-time.sh "_" "[date]" --elapsed 1
# Apply healing or feature recovery manually
bash tools/dm-player.sh hp "[character_name]" +[amount]
```

### Long Rest (8 Hours)
```bash
bash tools/dm-time.sh "_" "[next day date]" --elapsed 8 --sleeping
bash tools/dm-note.sh "session_events" "[character] completed a long rest"
```

**NOTE:** `--elapsed` auto-ticks consequences. Never call `dm-consequence.sh tick` manually.

### Healing Potions
- Basic: 2d4+2 HP
- Greater: 4d4+4 HP
- Superior: 8d4+8 HP

---
