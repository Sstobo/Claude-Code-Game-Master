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

show_usage() {
    echo "Usage: gm-reset.sh <action> [--yes]"
    echo ""
    echo "Actions:"
    echo "  preview     - Show what would be reset (safe)"
    echo "  archive     - Copy the campaign to world-state/archive/, then reset"
    echo "  hard        - Delete everything and start fresh (destructive!)"
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

preview_world() {
    require_active_campaign
    echo "📊 Current World State:"
    echo ""
    $PYTHON_CMD "$LIB_DIR/world_stats.py" counts
    echo ""
    echo "📁 Files that would be reset:"
    echo "  • $WORLD_STATE_DIR/npcs.json"
    echo "  • $WORLD_STATE_DIR/locations.json"
    echo "  • $WORLD_STATE_DIR/facts.json"
    echo "  • $WORLD_STATE_DIR/consequences.json"
    echo "  • $WORLD_STATE_DIR/campaign-overview.json"
    echo "  • $WORLD_STATE_DIR/session-log.md"
    # Check for new format (character.json) vs legacy (characters/)
    if [ -f "$WORLD_STATE_DIR/character.json" ]; then
        echo "  • $WORLD_STATE_DIR/character.json"
    elif [ -d "$WORLD_STATE_DIR/characters" ]; then
        echo "  • $WORLD_STATE_DIR/characters/*.json"
    fi
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

    echo ""
    echo "✅ World state reset to blank slate"
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
            cp -R "$WORLD_STATE_DIR/." "$ARCHIVE_DIR/" || { error "Archive failed — world unchanged."; exit 1; }
            echo "  ✓ Archived to: $ARCHIVE_DIR"
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
