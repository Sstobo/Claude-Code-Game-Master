#!/bin/bash
# gm-plot.sh - Manage plot hooks and storylines
# Uses Python modules for validation and data operations

# Source common utilities
source "$(dirname "$0")/common.sh"

# Usage: gm-plot.sh <action> [args]

if [ "$#" -lt 1 ]; then
    echo "Usage: gm-plot.sh <action> [args]"
    echo ""
    echo "=== Plot Management ==="
    echo "  add <name> [--type T] [--description \"...\"] [--status dormant]"
    echo "             [--objective \"...\"]... [--npc \"...\"]... [--location \"...\"]..."
    echo "                                   Seed a NEW plot thread (dormant by default)"
    echo "  list [--type X] [--status Y]     List plots (filter by type/status)"
    echo "  show <name>                      Show full plot details"
    echo "  search <query>                   Search plots by name, NPCs, locations"
    echo "  update <name> <event>            Add progress event to plot"
    echo "  complete <name> [outcome]        Mark plot as completed"
    echo "  fail <name> [reason]             Mark plot as failed"
    echo "  threads                          Active story threads (GM dashboard)"
    echo "  counts                           Show plot statistics"
    echo ""
    # Types come from the canonical taxonomy in lib/schemas.py (PLOT_TYPE_SORT), in rank order
    PLOT_TYPE_LIST=$($PYTHON_CMD -c "import sys; sys.path.insert(0, '$LIB_DIR'); from schemas import PLOT_TYPE_SORT; print(', '.join(sorted(PLOT_TYPE_SORT, key=PLOT_TYPE_SORT.get)))" 2>/dev/null)
    echo "Types: ${PLOT_TYPE_LIST:-see PLOT_TYPE_SORT in lib/schemas.py}"
    echo "Status: active, completed, failed, dormant"
    echo ""
    echo "Examples:"
    echo "  gm-plot.sh list                              # List all plots"
    echo "  gm-plot.sh list --type main --status active  # Active main plots only"
    echo "  gm-plot.sh show \"The Eight Day Countdown\"    # Full plot details"
    echo "  gm-plot.sh search \"Mordecai\"                 # Find plots with Mordecai"
    echo "  gm-plot.sh update \"Murder Mystery\" \"Found first clue at docks\""
    echo "  gm-plot.sh complete \"Side Quest\" \"Rescued the merchant\""
    exit 1
fi

require_active_campaign

ACTION="$1"
shift  # Remove action from arguments

# Delegate to Python module based on action
case "$ACTION" in
    add)
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" add "$@"
        ;;
    list)
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" list "$@"
        ;;

    show)
        if [ "$#" -lt 1 ]; then
            echo "Usage: gm-plot.sh show <name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" show "$1"
        ;;

    search)
        if [ "$#" -lt 1 ]; then
            echo "Usage: gm-plot.sh search <query>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" search "$1"
        ;;

    update)
        if [ "$#" -lt 2 ]; then
            echo "Usage: gm-plot.sh update <name> <event>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" update "$1" "$2"
        ;;

    complete)
        if [ "$#" -lt 1 ]; then
            echo "Usage: gm-plot.sh complete <name> [outcome]"
            exit 1
        fi
        NAME="$1"
        OUTCOME="${2:-}"
        if [ -n "$OUTCOME" ]; then
            $PYTHON_CMD "$LIB_DIR/plot_manager.py" complete "$NAME" "$OUTCOME"
        else
            $PYTHON_CMD "$LIB_DIR/plot_manager.py" complete "$NAME"
        fi
        ;;

    fail)
        if [ "$#" -lt 1 ]; then
            echo "Usage: gm-plot.sh fail <name> [reason]"
            exit 1
        fi
        NAME="$1"
        REASON="${2:-}"
        if [ -n "$REASON" ]; then
            $PYTHON_CMD "$LIB_DIR/plot_manager.py" fail "$NAME" "$REASON"
        else
            $PYTHON_CMD "$LIB_DIR/plot_manager.py" fail "$NAME"
        fi
        ;;

    counts)
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" counts
        ;;

    threads)
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" threads
        ;;

    *)
        echo "Error: Unknown action '$ACTION'"
        echo "Run 'gm-plot.sh' without arguments to see all available actions"
        exit 1
        ;;
esac

# Exit with the same status as the Python command
exit $?
