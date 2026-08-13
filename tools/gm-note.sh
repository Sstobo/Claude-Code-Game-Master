#!/bin/bash
# gm-note.sh - Record immutable world facts (wrapper for note_manager.py)

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: gm-note.sh <category> <fact>"
    echo "       gm-note.sh categories"
    echo ""
    echo "Categories: session_events, plot_local, plot_regional, plot_world,"
    echo "            player_choices, npc_relations, lore, rules"
    echo ""
    echo "Example: gm-note.sh \"volcano\" \"The volcano god demands royal blood\""
    exit 1
fi

require_active_campaign

# The managers resolve world-state relative to the working directory, so run from
# the project root no matter where the caller invoked this wrapper.
cd "$PROJECT_ROOT" || exit 1

if [ "$1" = "categories" ]; then
    echo "Fact Categories:"
    $PYTHON_CMD "$LIB_DIR/note_manager.py" categories
    exit $?
elif [ "$#" -eq 2 ]; then
    $PYTHON_CMD "$LIB_DIR/note_manager.py" add "$1" "$2"
    exit $?
else
    echo "Usage: gm-note.sh <category> <fact>"
    exit 1
fi
