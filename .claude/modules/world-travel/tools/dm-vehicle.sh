#!/bin/bash
# dm-vehicle.sh - Vehicle management (ship, transport, etc.)

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$MODULE_DIR/../../.." && pwd)"

source "$PROJECT_ROOT/tools/common.sh"

VEHICLE_PY="$MODULE_DIR/lib/vehicle_manager.py"

require_active_campaign

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-vehicle.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  create <name> <type> <anchor_location>     Register vehicle at existing location"
    echo "  add-room <vehicle_id> <room> --from <room> --bearing <deg> --distance <m>"
    echo "  move <vehicle_id> <destination>            Move vehicle to existing location"
    echo "  move <vehicle_id> --x <X> --y <Y>         Move vehicle to coordinates"
    echo "  board <vehicle_id> [--room <room>]         Board vehicle (enter)"
    echo "  exit                                        Exit vehicle to global map"
    echo "  status [<vehicle_id>]                      Show vehicle status"
    echo "  map <vehicle_id>                            ASCII map of internal rooms"
    echo "  list                                        List all vehicles"
    exit 1
fi

ACTION="$1"
shift

case "$ACTION" in
    create)
        NAME="$1"
        TYPE="$2"
        ANCHOR="$3"
        if [ -z "$NAME" ] || [ -z "$TYPE" ] || [ -z "$ANCHOR" ]; then
            echo "Usage: dm-vehicle.sh create <name> <type> <anchor_location>"
            exit 1
        fi
        $PYTHON_CMD "$VEHICLE_PY" register "$NAME" "$TYPE" "$ANCHOR"
        ;;
    add-room)
        VEHICLE_ID="$1"
        ROOM="$2"
        shift 2
        if [ -z "$VEHICLE_ID" ] || [ -z "$ROOM" ]; then
            echo "Usage: dm-vehicle.sh add-room <vehicle_id> <room> --from <room> --bearing <deg> --distance <m>"
            exit 1
        fi
        $PYTHON_CMD "$VEHICLE_PY" add-room "$VEHICLE_ID" "$ROOM" "$@"
        ;;
    move)
        VEHICLE_ID="$1"
        shift
        if [ -z "$VEHICLE_ID" ]; then
            echo "Usage: dm-vehicle.sh move <vehicle_id> <destination|--x X --y Y>"
            exit 1
        fi
        $PYTHON_CMD "$VEHICLE_PY" move-vehicle "$VEHICLE_ID" "$@"
        ;;
    board)
        VEHICLE_ID="$1"
        shift
        if [ -z "$VEHICLE_ID" ]; then
            echo "Usage: dm-vehicle.sh board <vehicle_id> [--room <room>]"
            exit 1
        fi
        $PYTHON_CMD "$VEHICLE_PY" board "$VEHICLE_ID" "$@"
        ;;
    exit)
        $PYTHON_CMD "$VEHICLE_PY" exit-vehicle
        ;;
    status)
        $PYTHON_CMD "$VEHICLE_PY" status "$@"
        ;;
    map)
        VEHICLE_ID="$1"
        if [ -z "$VEHICLE_ID" ]; then
            echo "Usage: dm-vehicle.sh map <vehicle_id>"
            exit 1
        fi
        $PYTHON_CMD "$VEHICLE_PY" map-internal "$VEHICLE_ID"
        ;;
    list)
        $PYTHON_CMD "$VEHICLE_PY" list-vehicles
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Run 'dm-vehicle.sh' without args for help"
        exit 1
        ;;
esac
