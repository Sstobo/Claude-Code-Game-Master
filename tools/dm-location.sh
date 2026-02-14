#!/bin/bash
# dm-location.sh - Location management (thin wrapper for location_manager.py)

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-location.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  add <name> <position> [--from <loc>] [--bearing <deg>] [--distance <m>] [--terrain <type>]"
    echo "                                     - Add new location with auto-calculated coordinates"
    echo "  connect <from> <to> <path>         - Connect two locations"
    echo "  describe <name> <description>      - Set location description"
    echo "  get <name>                         - Get location info"
    echo "  list                               - List all locations"
    echo "  connections <name>                 - Show location connections"
    echo ""
    echo "Navigation & Pathfinding:"
    echo "  decide <from> <to>                 - Decide route between locations"
    echo "  routes <from> <to>                 - Show all possible routes"
    echo "  block <location> <from_deg> <to_deg> <reason> - Block direction range"
    echo "  unblock <location> <from_deg> <to_deg>        - Unblock direction range"
    echo "  split [--dry-run]                  - Auto-split paths through intermediate locations"
    echo ""
    echo "Examples:"
    echo "  dm-location.sh add \"Volcano Temple\" \"north of village\""
    echo "  dm-location.sh add \"Temple\" \"1km north\" --from \"Village\" --bearing 0 --distance 1000"
    echo "  dm-location.sh connect \"Village\" \"Volcano Temple\" \"rocky path\""
    echo "  dm-location.sh describe \"Volcano Temple\" \"Ancient obsidian structure\""
    echo "  dm-location.sh decide \"Village\" \"Temple\""
    echo "  dm-location.sh block \"Village\" 160 200 \"Steep cliff\""
    exit 1
fi

require_active_campaign

ACTION="$1"
shift

case "$ACTION" in
    add)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-location.sh add <name> <position> [--from <loc>] [--bearing <deg>] [--distance <m>] [--terrain <type>]"
            exit 1
        fi
        # Pass all arguments to Python
        $PYTHON_CMD "$LIB_DIR/location_manager.py" add "$@"
        ;;

    connect)
        if [ "$#" -lt 3 ]; then
            echo "Usage: dm-location.sh connect <from> <to> <path>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" connect "$1" "$2" "$3"
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

    decide)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-location.sh decide <from> <to>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" decide "$1" "$2"
        ;;

    routes)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-location.sh routes <from> <to>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" routes "$1" "$2"
        ;;

    block)
        if [ "$#" -lt 4 ]; then
            echo "Usage: dm-location.sh block <location> <from_deg> <to_deg> <reason>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" block "$1" "$2" "$3" "$4"
        ;;

    unblock)
        if [ "$#" -lt 3 ]; then
            echo "Usage: dm-location.sh unblock <location> <from_deg> <to_deg>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/location_manager.py" unblock "$1" "$2" "$3"
        ;;

    split)
        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/dm-campaign.sh" path)
        if [ "$1" == "--dry-run" ]; then
            $PYTHON_CMD "$LIB_DIR/path_split.py" "$CAMPAIGN_DIR" --dry-run
        else
            $PYTHON_CMD "$LIB_DIR/path_split.py" "$CAMPAIGN_DIR" --apply
        fi
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: add, connect, describe, get, list, connections, decide, routes, block, unblock, split"
        exit 1
        ;;
esac

# Propagate Python exit code
exit $?
