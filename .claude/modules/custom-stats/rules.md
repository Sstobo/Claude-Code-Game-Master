# Survival Stats — DM Rules

> These instructions tell the DM (Claude) when and how to call the survival module.

## When to Call

### After every `dm-session.sh move`

If the move output contains `[ELAPSED]` with hours:

```bash
bash .claude/modules/survival-stats/tools/dm-survival.sh tick --elapsed <hours>
```

### After every `dm-time.sh` with elapsed hours

If time was advanced and `--elapsed` was specified:

```bash
bash .claude/modules/survival-stats/tools/dm-survival.sh tick --elapsed <hours>
```

### During sleep/long rest

```bash
bash .claude/modules/survival-stats/tools/dm-survival.sh tick --elapsed 8 --sleeping
```

The `--sleeping` flag reverses drain for stats that have `sleep_restore_per_hour` configured (e.g., sleep stat restores instead of draining).

## When NOT to Call

- Do NOT call after `dm-session.sh move` if no `[ELAPSED]` line was printed (e.g., teleportation, same-area movement)
- Do NOT call if campaign does NOT have `campaign_rules.time_effects.enabled = true`

## Checking Status

To show the player's current custom stats:

```bash
bash .claude/modules/survival-stats/tools/dm-survival.sh status
```

## Display in Scene Header

When custom stats exist, include them in the status bar:

```
LVL: 5  │  HP: ████████░░░░ 18/24 ✓  │  XP: 1250  │  GP: 27
Hunger: 72/100  │  Thirst: 58/100  │  Rad: 15/500
```

## Activation Check

At session start, check if campaign has `campaign_rules.time_effects.enabled = true`.
If yes, load these rules and follow them for the duration of the session.
