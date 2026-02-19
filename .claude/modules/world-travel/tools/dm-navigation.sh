#!/bin/bash
# dm-navigation.sh - Coordinate navigation module wrapper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$MODULE_DIR")")")"

source "$PROJECT_ROOT/tools/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-navigation.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  add <name> <position> --from <loc> --bearing <deg> --distance <m> [--terrain <type>]"
    echo "                                            - Add location with coordinates"
    echo "  move <location> [--speed-multiplier X]     - Move party with distance-based time calc"
    echo "  connect <from> <to> <path> [--terrain <type>] [--distance <m>]"
    echo "                                            - Create connection with metadata"
    echo "  decide <from> <to>                        - Interactive route decision"
    echo "  routes <from> <to>                        - Show all possible routes"
    echo "  block <location> <from_deg> <to_deg> <reason> - Block direction range"
    echo "  unblock <location> <from_deg> <to_deg>         - Unblock direction range"
    echo "  path check <from> <to>                    - Check if path intersects other locations"
    echo "  path route <from> <to>                    - Find route with waypoints"
    echo "  path analyze                              - Analyze all connections for intersections"
    echo "  migrate [--apply] [--campaign NAME]       - Migrate connections to canonical storage"
    echo ""
    echo "Examples:"
    echo "  dm-navigation.sh add \"Temple\" \"1km north\" --from \"Village\" --bearing 0 --distance 1000"
    echo "  dm-navigation.sh move \"Temple\" --speed-multiplier 1.5"
    echo "  dm-navigation.sh connect \"Village\" \"Temple\" \"Overgrown path\" --terrain forest --distance 1000"
    echo "  dm-navigation.sh decide \"Village\" \"Temple\""
    echo "  dm-navigation.sh routes \"Village\" \"Temple\""
    echo "  dm-navigation.sh path check \"Village\" \"Temple\""
    echo "  dm-navigation.sh migrate --apply"
    exit 1
fi

require_active_campaign

CAMPAIGN_DIR=$(bash "$TOOLS_DIR/dm-campaign.sh" path)
ACTION="$1"
shift

case "$ACTION" in
    add)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-navigation.sh add <name> <position> --from <loc> --bearing <deg> --distance <m> [--terrain <type>]"
            exit 1
        fi
        $PYTHON_CMD "$MODULE_DIR/lib/navigation_manager.py" add "$CAMPAIGN_DIR" "$@"
        ;;

    move)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-navigation.sh move <location> [--speed-multiplier X]"
            exit 1
        fi
        $PYTHON_CMD "$MODULE_DIR/lib/navigation_manager.py" move "$CAMPAIGN_DIR" "$@"
        ;;

    connect)
        if [ "$#" -lt 3 ]; then
            echo "Usage: dm-navigation.sh connect <from> <to> <path> [--terrain <type>] [--distance <m>]"
            exit 1
        fi
        $PYTHON_CMD "$MODULE_DIR/lib/navigation_manager.py" connect "$CAMPAIGN_DIR" "$@"
        ;;

    decide)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-navigation.sh decide <from> <to>"
            exit 1
        fi
        $PYTHON_CMD "$MODULE_DIR/lib/navigation_manager.py" decide "$CAMPAIGN_DIR" "$1" "$2"
        ;;

    routes)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-navigation.sh routes <from> <to>"
            exit 1
        fi
        $PYTHON_CMD "$MODULE_DIR/lib/navigation_manager.py" routes "$CAMPAIGN_DIR" "$1" "$2"
        ;;

    block)
        if [ "$#" -lt 4 ]; then
            echo "Usage: dm-navigation.sh block <location> <from_deg> <to_deg> <reason>"
            exit 1
        fi
        $PYTHON_CMD "$MODULE_DIR/lib/navigation_manager.py" block "$CAMPAIGN_DIR" "$1" "$2" "$3" "$4"
        ;;

    unblock)
        if [ "$#" -lt 3 ]; then
            echo "Usage: dm-navigation.sh unblock <location> <from_deg> <to_deg>"
            exit 1
        fi
        $PYTHON_CMD "$MODULE_DIR/lib/navigation_manager.py" unblock "$CAMPAIGN_DIR" "$1" "$2" "$3"
        ;;

    path)
        SUBCMD="${1:-}"
        shift || true
        case "$SUBCMD" in
            check)
                if [ "$#" -lt 2 ]; then
                    echo "Usage: dm-navigation.sh path check <from> <to>"
                    exit 1
                fi
                $PYTHON_CMD -c "
import json, sys
sys.path.insert(0, '$MODULE_DIR/lib')
from path_intersect import check_path_intersection
with open('$CAMPAIGN_DIR/locations.json') as f:
    locs = json.load(f)
hits = check_path_intersection('$1', '$2', locs)
if hits:
    print('Path intersects:')
    for loc in hits:
        print(f'  • {loc}')
    print()
    print('Suggested: $1 → ' + ' → '.join(hits) + ' → $2')
else:
    print('✓ Direct path is clear')
"
                ;;
            route)
                if [ "$#" -lt 2 ]; then
                    echo "Usage: dm-navigation.sh path route <from> <to>"
                    exit 1
                fi
                $PYTHON_CMD -c "
import json, sys
sys.path.insert(0, '$MODULE_DIR/lib')
from path_intersect import find_route_with_waypoints
with open('$CAMPAIGN_DIR/locations.json') as f:
    locs = json.load(f)
route = find_route_with_waypoints('$1', '$2', locs)
print('Route: ' + ' → '.join(route))
if len(route) > 2:
    print('Via:')
    for wp in route[1:-1]:
        print(f'  • {wp}')
"
                ;;
            analyze)
                $PYTHON_CMD -c "
import json, sys
sys.path.insert(0, '$MODULE_DIR/lib')
from path_intersect import check_path_intersection
with open('$CAMPAIGN_DIR/locations.json') as f:
    locs = json.load(f)
found = False
for loc_name, loc_data in locs.items():
    for conn in loc_data.get('connections', []):
        to_loc = conn.get('to')
        if not to_loc or to_loc not in locs:
            continue
        hits = check_path_intersection(loc_name, to_loc, locs)
        if hits:
            found = True
            print(f'{loc_name} → {to_loc}: intersects {hits}')
if not found:
    print('✓ No path intersections detected')
"
                ;;
            *)
                echo "Unknown path subcommand: $SUBCMD"
                echo "Valid: check, route, analyze"
                exit 1
                ;;
        esac
        ;;

    migrate)
        $PYTHON_CMD "$MODULE_DIR/tools/migrate-connections.py" "$@"
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: add, move, connect, decide, routes, block, unblock, path, migrate"
        exit 1
        ;;
esac

exit $?
