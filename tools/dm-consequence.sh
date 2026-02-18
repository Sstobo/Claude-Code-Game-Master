#!/bin/bash
# dm-consequence.sh - Consequence tracking

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-consequence.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  add <description> <trigger>  - Add consequence"
    echo "  check                        - Check pending consequences"
    echo "  resolve <id>                 - Resolve a consequence"
    echo "  list-resolved                - List resolved consequences"
    dispatch_middleware_help "dm-consequence.sh"
    exit 1
fi

require_active_campaign

ACTION="$1"
shift

case "$ACTION" in
    add)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-consequence.sh add <description> <trigger>"
            exit 1
        fi
        dispatch_middleware "dm-consequence.sh" add "$@" || \
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

exit $?
