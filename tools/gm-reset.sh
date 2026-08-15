#!/bin/bash
# gm-reset.sh - Reset world state for a fresh campaign start
# Archives current world, then cleans for new beginning

# Source common utilities
source "$(dirname "$0")/common.sh"

echo "🔄 Campaign Reset Tool"
echo "======================"
echo ""

# Show which campaign we're working with
ACTIVE_CAMPAIGN=$(get_active_campaign)
if [ -n "$ACTIVE_CAMPAIGN" ]; then
    echo "Active campaign: $ACTIVE_CAMPAIGN"
    echo "Campaign path: $WORLD_STATE_DIR"
else
    echo "No active campaign set. Use 'gm-campaign.sh list' and 'gm-campaign.sh switch <name>' first."
    exit 1
fi
echo ""

ACTION="${1:-}"

# --yes / --confirm: answer every prompt affirmatively (non-interactive use)
ASSUME_YES=0
for arg in "$@"; do
    case "$arg" in
        --yes|--confirm) ASSUME_YES=1 ;;
    esac
done

ARCHIVE_BASE="$WORLD_STATE_BASE/archive"

# Reset keeps the SOURCE, the WORLD and the KIT, clears the STORY.
#   SOURCE (kept): source/current-document.txt, metadata.json, chunks/, vectors/,
#                  extracted*/, canon/, authored/, images/
#   WORLD  (kept): world-bible.json, world-seed.json — world identity, authored
#                  once and never regenerated during play (the bible feeds
#                  ruleset.json via bible_to_campaign_rules)
#   KIT    (kept): ruleset.json, rules.md, chronicler.json
#   STORY (cleared): everything below — blanked when a manager expects the file
#                    to exist, deleted when it is created lazily.
STORY_FILES=(
    plots.json
    items.json
    campaign-memory.json
    combat_state.json
    threat-clocks.json
    world-tick-log.json
    loremaster-cache.json
)
STORY_DIRS=(saves fallen characters)

show_usage() {
    echo "Usage: gm-reset.sh <action> [--yes]"
    echo ""
    echo "Actions:"
    echo "  preview     - Show what would be reset (safe)"
    echo "  archive     - Copy the campaign to world-state/archive/, then reset"
    echo "  hard        - Reset with no backup (destructive!)"
    echo ""
    echo "Options:"
    echo "  --yes       - Skip confirmation prompts (also: --confirm)"
    echo ""
    echo "Examples:"
    echo "  gm-reset.sh preview              # See what exists"
    echo "  gm-reset.sh archive              # Safe reset with backup"
    echo "  gm-reset.sh archive --yes        # Same, no prompt (scripts/CI)"
    echo "  gm-reset.sh hard                 # Nuclear option"
    echo ""
    echo "Reset keeps the SOURCE (source/current-document.txt, metadata.json, chunks/, vectors/,"
    echo "images/), the WORLD (world-bible.json, world-seed.json) and the KIT (ruleset.json,"
    echo "rules.md, chronicler.json); it clears the STORY (characters, NPCs, locations,"
    echo "facts, plots, items, consequences, combat, memory, clocks, session log, saves/,"
    echo "fallen/)."
    echo ""
    echo "Note: This resets the ACTIVE CAMPAIGN only."
    echo "Use 'gm-campaign.sh switch <name>' to change campaigns first."
}

# True when we still need to ask the user. --yes means already answered; a non-tty
# without --yes aborts here rather than hanging on a read nobody can answer.
should_prompt() {
    if [ "$ASSUME_YES" -eq 1 ]; then
        return 1
    fi
    if [ ! -t 0 ]; then
        error "No terminal to confirm on. Re-run with --yes to proceed non-interactively."
        exit 1
    fi
    return 0
}

# Copy the campaign into $1, skipping vectors/ — the ChromaDB index is tens of
# megabytes and is rebuilt from the source document on the next prepare.
# Fails (rather than reporting an empty success) if there was nothing to copy.
copy_campaign_to_archive() {
    local dest="$1" entry copied=0
    [ -d "$WORLD_STATE_DIR" ] || return 1
    shopt -s dotglob nullglob
    for entry in "$WORLD_STATE_DIR"/*; do
        if [ "$(basename "$entry")" != "vectors" ]; then
            cp -R "$entry" "$dest/" || { shopt -u dotglob nullglob; return 1; }
            copied=$((copied + 1))
        fi
    done
    shopt -u dotglob nullglob
    [ "$copied" -gt 0 ]
}

preview_world() {
    require_active_campaign
    echo "📊 Current World State:"
    echo ""
    $PYTHON_CMD "$LIB_DIR/world_stats.py" counts
    echo ""
    echo "📁 Story that would be cleared:"
    echo "  • $WORLD_STATE_DIR/npcs.json"
    echo "  • $WORLD_STATE_DIR/locations.json"
    echo "  • $WORLD_STATE_DIR/facts.json"
    echo "  • $WORLD_STATE_DIR/consequences.json"
    echo "  • $WORLD_STATE_DIR/campaign-overview.json"
    echo "  • $WORLD_STATE_DIR/session-log.md"
    # New format (character.json); the legacy characters/ dir is in STORY_DIRS.
    if [ -f "$WORLD_STATE_DIR/character.json" ]; then
        echo "  • $WORLD_STATE_DIR/character.json"
    fi
    local name
    for name in "${STORY_FILES[@]}"; do
        [ -f "$WORLD_STATE_DIR/$name" ] && echo "  • $WORLD_STATE_DIR/$name"
    done
    for name in "${STORY_DIRS[@]}"; do
        [ -d "$WORLD_STATE_DIR/$name" ] && echo "  • $WORLD_STATE_DIR/$name/"
    done
    echo ""
    echo "📚 Kept (reset keeps the SOURCE, the WORLD and the KIT, clears the STORY):"
    echo "  • Source: source/current-document.txt, metadata.json, chunks/, vectors/, images/"
    echo "  • World:  world-bible.json, world-seed.json"
    echo "  • Kit:    ruleset.json, rules.md, chronicler.json"
}

reset_world() {
    require_active_campaign
    echo "🧹 Resetting world state..."
    echo ""

    # Reset NPCs
    echo '{}' > "$NPCS_FILE"
    echo "  ✓ NPCs cleared"

    # Reset Locations
    echo '{}' > "$LOCATIONS_FILE"
    echo "  ✓ Locations cleared"

    # Reset Facts
    echo '{}' > "$FACTS_FILE"
    echo "  ✓ Facts cleared"

    # Reset Consequences
    echo '{"active": [], "resolved": []}' > "$CONSEQUENCES_FILE"
    echo "  ✓ Consequences cleared"

    # Reset Campaign Overview
    cat > "$CAMPAIGN_OVERVIEW" << 'EOF'
{
  "campaign_name": "New Campaign",
  "genre": "Fantasy",
  "tone": {
    "horror": 30,
    "comedy": 30,
    "drama": 40
  },
  "current_date": "1st of the First Month, Year 1",
  "time_of_day": "Morning",
  "player_position": {
    "current_location": null,
    "previous_location": null
  },
  "current_character": null,
  "session_count": 0
}
EOF
    echo "  ✓ Campaign overview reset"

    # Reset Session Log
    cat > "$SESSION_LOG" << 'EOF'
# Campaign Session Log

*A new adventure begins...*

---

EOF
    echo "  ✓ Session log cleared"

    # Remove character file
    if [ -f "$CHARACTER_FILE" ]; then
        rm -f "$CHARACTER_FILE"
        echo "  ✓ Character removed"
    fi

    # The lazily-created story files — managers recreate them on next write.
    local name
    for name in "${STORY_FILES[@]}"; do
        if [ -f "$WORLD_STATE_DIR/$name" ]; then
            rm -f "$WORLD_STATE_DIR/$name"
            echo "  ✓ ${name%.json} cleared"
        fi
    done
    for name in "${STORY_DIRS[@]}"; do
        if [ -d "$WORLD_STATE_DIR/$name" ]; then
            rm -rf "$WORLD_STATE_DIR/$name"
            echo "  ✓ $name/ cleared"
        fi
    done

    echo ""
    echo "✅ Story reset to blank slate — source (chunks/, vectors/, source/current-document.txt,"
    echo "   images/), world (world-bible.json, world-seed.json) and kit (ruleset.json,"
    echo "   rules.md, chronicler.json) kept."
}

case "$ACTION" in
    preview)
        preview_world
        echo ""
        echo "💡 Run 'gm-reset.sh archive' to safely reset with backup"
        ;;

    archive)
        require_active_campaign

        ARCHIVE_DIR="$ARCHIVE_BASE/${ACTIVE_CAMPAIGN}-$(date +%Y%m%d-%H%M%S)"

        preview_world
        echo ""

        REPLY=""
        if should_prompt; then
            read -p "⚠️  Reset this world? A copy is archived to '$ARCHIVE_DIR' first (y/N) " -n 1 -r
            echo
        else
            REPLY="y"
        fi

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "📦 Archiving current campaign..."
            # Never reset on a failed/partial copy — the archive IS the safety net.
            mkdir -p "$ARCHIVE_DIR" || { error "Could not create archive directory '$ARCHIVE_DIR' — world unchanged."; exit 1; }
            copy_campaign_to_archive "$ARCHIVE_DIR" || { error "Archive failed — world unchanged."; exit 1; }
            echo "  ✓ Archived to: $ARCHIVE_DIR"
            echo "    (vectors/ excluded — the index is rebuilt from the source document on the next prepare)"
            echo ""

            reset_world

            echo ""
            echo "📜 To restore archived campaign:"
            echo "   cp -R \"$ARCHIVE_DIR/.\" \"$WORLD_STATE_DIR/\""
        else
            echo "Reset cancelled. World unchanged."
        fi
        ;;

    hard)
        echo "⚠️  HARD RESET - No backup will be created!"
        echo ""
        preview_world
        echo ""

        CONFIRM="DELETE"
        if should_prompt; then
            read -p "💀 This is DESTRUCTIVE. Type 'DELETE' to confirm: " CONFIRM
        fi

        if [ "$CONFIRM" = "DELETE" ]; then
            reset_world
            echo ""
            echo "💀 World obliterated. Starting fresh."
        else
            echo "Reset cancelled. World unchanged."
        fi
        ;;

    *)
        show_usage
        exit 1
        ;;
esac
