#!/bin/bash
# dm-plot.sh - Manage plot hooks and storylines
# Uses Python modules for validation and data operations

# Source common utilities
source "$(dirname "$0")/common.sh"

# Usage: dm-plot.sh <action> [args]

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-plot.sh <action> [args]"
    echo ""
    echo "=== Plot Management ==="
    echo "  list [--type X] [--status Y]     List plots (filter by type/status)"
    echo "  show <name>                      Show full plot details"
    echo "  search <query>                   Search plots by name, NPCs, locations"
    echo "  add <title>                      Create a new plot (interactive)"
    echo "  update <name> <event>            Add progress event to plot"
    echo "  objectives <name> [add|complete] Manage quest objectives"
    echo "  complete <name> [outcome]        Mark plot as completed"
    echo "  fail <name> [reason]             Mark plot as failed"
    echo "  threads                          Active story threads (DM dashboard)"
    echo "  counts                           Show plot statistics"
    echo ""
    echo "Types: main, side, mystery, threat"
    echo "Status: active, completed, failed, dormant"
    echo ""
    echo "Examples:"
    echo "  dm-plot.sh list                              # List all plots"
    echo "  dm-plot.sh list --type main --status active  # Active main plots only"
    echo "  dm-plot.sh show \"The Eight Day Countdown\"    # Full plot details"
    echo "  dm-plot.sh search \"Mordecai\"                 # Find plots with Mordecai"
    echo "  dm-plot.sh update \"Murder Mystery\" \"Found first clue at docks\""
    echo "  dm-plot.sh complete \"Side Quest\" \"Rescued the merchant\""
    exit 1
fi

require_active_campaign

ACTION="$1"
shift  # Remove action from arguments

# Delegate to Python module based on action
case "$ACTION" in
    list)
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" list "$@"
        ;;

    show)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-plot.sh show <name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" show "$1"
        ;;

    search)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-plot.sh search <query>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" search "$1"
        ;;

    add)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-plot.sh add <title>"
            echo ""
            echo "Creates a new plot with interactive prompts for:"
            echo "  - Description"
            echo "  - Type (main, side, mystery, threat)"
            echo "  - Objective(s)"
            echo "  - Stakes"
            echo "  - NPCs involved"
            echo "  - Locations"
            echo "  - Rewards"
            exit 1
        fi
        TITLE="$1"
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" add "$TITLE"
        ;;

    objectives)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-plot.sh objectives <name> [add|complete <objective>]"
            echo ""
            echo "Examples:"
            echo "  dm-plot.sh objectives \"The Heist\"          # Show objectives"
            echo "  dm-plot.sh objectives \"The Heist\" add \"Reconnaissance\""
            echo "  dm-plot.sh objectives \"The Heist\" complete \"Find the map\""
            exit 1
        fi
        PLOT_NAME="$1"
        ACTION_OBJ="${2:-}"
        OBJ_TEXT="${3:-}"

        if [ -z "$ACTION_OBJ" ]; then
            # Just show the plot (which includes objectives)
            $PYTHON_CMD "$LIB_DIR/plot_manager.py" show "$PLOT_NAME"
        elif [ "$ACTION_OBJ" = "add" ]; then
            if [ -z "$OBJ_TEXT" ]; then
                echo "Usage: dm-plot.sh objectives <name> add <objective>"
                exit 1
            fi
            $PYTHON_CMD "$LIB_DIR/plot_manager.py" objectives "$PLOT_NAME" add "$OBJ_TEXT"
        elif [ "$ACTION_OBJ" = "complete" ]; then
            if [ -z "$OBJ_TEXT" ]; then
                echo "Usage: dm-plot.sh objectives <name> complete <objective>"
                exit 1
            fi
            $PYTHON_CMD "$LIB_DIR/plot_manager.py" objectives "$PLOT_NAME" complete "$OBJ_TEXT"
        else
            echo "Error: Unknown sub-action '$ACTION_OBJ' (use 'add' or 'complete')"
            exit 1
        fi
        ;;

    update)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-plot.sh update <name> <event>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" update "$1" "$2"
        ;;

    complete)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-plot.sh complete <name> [outcome]"
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
            echo "Usage: dm-plot.sh fail <name> [reason]"
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
        echo "Run 'dm-plot.sh' without arguments to see all available actions"
        exit 1
        ;;
esac

# Exit with the same status as the Python command
exit $?
