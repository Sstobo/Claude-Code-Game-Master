#!/bin/bash
# dm-plot.sh - Manage plot hooks and storylines

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-plot.sh <action> [args]"
    echo ""
    echo "=== Plot Management ==="
    echo "  add <name> <desc> [--type X] [--npcs A B] [--locations A B] [--objectives A B] [--rewards X] [--consequences X]"
    echo "                                   Create a new plot/quest"
    echo "  list [--type X] [--status Y]     List plots (filter by type/status)"
    echo "  show <name>                      Show full plot details"
    echo "  search <query>                   Search plots by name, NPCs, locations"
    echo "  update <name> <event>            Add progress event to plot"
    echo "  complete <name> [outcome]        Mark plot as completed"
    echo "  fail <name> [reason]             Mark plot as failed"
    echo "  threads                          Active story threads (DM dashboard)"
    echo "  counts                           Show plot statistics"
    dispatch_middleware_help "dm-plot.sh"
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
shift

dispatch_middleware "dm-plot.sh" "$ACTION" "$@" && exit $?

case "$ACTION" in
    add)
        $PYTHON_CMD "$LIB_DIR/plot_manager.py" add "$@"
        ;;

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

exit $?
