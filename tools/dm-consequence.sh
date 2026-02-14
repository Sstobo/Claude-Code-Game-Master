#!/bin/bash
# dm-consequence.sh - Consequence tracking (thin wrapper for consequence_manager.py)

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-consequence.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  add <description> <trigger>    - Add new consequence"
    echo "  check                          - Check pending consequences"
    echo "  resolve <id>                   - Resolve a consequence"
    echo "  list-resolved                  - List resolved consequences"
    echo ""
    echo "Examples:"
    echo "  dm-consequence.sh add \"Guards searching for party\" \"2 days\""
    echo "  dm-consequence.sh check"
    echo "  dm-consequence.sh resolve abc123"
    exit 1
fi

require_active_campaign

ACTION="$1"
shift

case "$ACTION" in
    add)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-consequence.sh add <description> <trigger> [--hours N]"
            echo ""
            echo "Triggers:"
            echo "  Event-based: 'on meeting', 'after quest', 'immediate'"
            echo "  Time-based:  'in 2 hours', 'in 3 days' + --hours <number>"
            echo ""
            echo "Examples:"
            echo "  dm-consequence.sh add \"NPC arrives\" \"in 24 hours\" --hours 24"
            echo "  dm-consequence.sh add \"Quest expires\" \"on meeting\""
            exit 1
        fi

        DESC="$1"
        TRIGGER="$2"
        shift 2

        HOURS_ARG=""
        if [ "$1" = "--hours" ]; then
            HOURS_ARG="--hours $2"
        fi

        $PYTHON_CMD "$LIB_DIR/consequence_manager.py" add "$DESC" "$TRIGGER" $HOURS_ARG
        ;;

    check)
        $PYTHON_CMD "$LIB_DIR/consequence_manager.py" check
        ;;

    resolve)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-consequence.sh resolve <id>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/consequence_manager.py" resolve "$1"
        ;;

    list-resolved)
        $PYTHON_CMD "$LIB_DIR/consequence_manager.py" list-resolved
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: add, check, resolve, list-resolved"
        exit 1
        ;;
esac

# Propagate Python exit code
exit $?
