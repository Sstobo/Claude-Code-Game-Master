## First-Time Setup (Auto-Detect)

**CRITICAL: Run these checks at the START of every session, BEFORE greeting the user.**

### Step 1: Check Installation
```bash
[ -d ".venv" ] && uv run python -c "import anthropic" 2>/dev/null
```
- If this fails → Run `/setup` automatically (do not ask the user)
- Show progress: "Setting up DM Claude..."

### Step 2: Check for Campaigns
```bash
bash tools/dm-campaign.sh list
```
- If no campaigns exist → Show welcome screen asking:
  - "Do you have a document to import?" → Route to `/import`
  - "Create from scratch?" → Route to `/new-game`

### Step 3: Check for Character
- If active campaign exists but no `character.json` → Route to `/create-character`

### Step 4: Ready to Play
- If all checks pass → Greet and offer `/dm`

---
