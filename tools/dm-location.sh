#!/bin/bash
# dm-location.sh - Location management (thin wrapper for location_manager.py)

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-location.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  add <name> <position>        - Add new location"
    echo "  connect <from> <to> [path]   - Connect two locations"
    echo "  describe <name> <desc>       - Set location description"
    echo "  get <name>                   - Get location info"
    echo "  list                         - List all locations"
    echo "  connections <name>           - Show location connections"
    echo "  remove <name>                - Delete location (must have no children)"
    echo "  rename <old> <new>           - Rename location (updates all references)"
    dispatch_middleware_help "dm-location.sh"
    echo ""
    echo "Examples:"
    echo "  dm-location.sh add \"Volcano Temple\" \"north of village\""
    echo "  dm-location.sh connect \"Village\" \"Volcano Temple\" \"rocky path\""
    echo "  dm-location.sh remove \"Old Tavern\""
    echo "  dm-location.sh rename \"Станция Кестрел\" \"Кестрел\""
    exit 1
fi

require_active_campaign

ACTION="$1"
shift

dispatch_middleware "dm-location.sh" "$ACTION" "$@" && exit $?

case "$ACTION" in
    add)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-location.sh add <name> <position>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" add "$@"
        ;;

    connect)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-location.sh connect <from> <to> [path]"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" connect "$@"
        ;;

    describe)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-location.sh describe <name> <description>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" describe "$1" "$2"
        ;;

    get)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-location.sh get <name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" get "$1"
        ;;

    list)
        echo "Locations"
        echo "========="
        $PYTHON_CMD "$LIB_DIR/location_manager.py" list
        ;;

    connections)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-location.sh connections <name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" connections "$1"
        ;;

    remove)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-location.sh remove <name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" remove "$1"
        ;;

    rename)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-location.sh rename <old_name> <new_name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" rename "$1" "$2"
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: add, connect, describe, get, list, connections, remove, rename"
        exit 1
        ;;
esac

exit $?
