## Dice Rolling

**ONE RULE**: Always use `uv run python lib/dice.py "[notation]"`

**NEVER** write inline Python for dice rolls.

```bash
# Standard roll
uv run python lib/dice.py "1d20+5"

# Advantage (roll 2, keep highest)
uv run python lib/dice.py "2d20kh1+5"

# Disadvantage (roll 2, keep lowest)
uv run python lib/dice.py "2d20kl1+5"

# Multiple dice
uv run python lib/dice.py "3d6"
```

**Roll each check separately** - do NOT batch multiple rolls into one command.

---
