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
            echo "Usage: dm-consequence.sh add <description> <trigger>"
            echo "Triggers: immediate, next visit, 2 days, next session, etc."
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/consequence_manager.py" add "$1" "$2"
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
