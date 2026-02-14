#!/bin/bash
# dm-path.sh - Path routing with intersection detection

source "$(dirname "$0")/common.sh"

if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: dm-path.sh <command> [args]"
    echo ""
    echo "Commands:"
    echo "  check <from> <to>     - Check if path intersects locations"
    echo "  route <from> <to>     - Find route with waypoints"
    echo "  analyze               - Analyze all connections for intersections"
    echo ""
    echo "Examples:"
    echo "  dm-path.sh check 'Village' 'Ruins'"
    echo "  dm-path.sh route 'Town' 'Village'"
    echo "  dm-path.sh analyze"
    exit 0
fi

require_active_campaign

COMMAND="$1"
shift

case "$COMMAND" in
    check)
        FROM="$1"
        TO="$2"
        if [ -z "$FROM" ] || [ -z "$TO" ]; then
            error "Usage: dm-path.sh check <from> <to>"
        fi

        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/dm-campaign.sh" path)
        $PYTHON_CMD -c "
import json
import sys
sys.path.insert(0, '$LIB_DIR')
from path_intersect import check_path_intersection

with open('$CAMPAIGN_DIR/locations.json') as f:
    locs = json.load(f)

intersections = check_path_intersection('$FROM', '$TO', locs)

if intersections:
    print('⚠️  Path intersects locations:')
    for loc in intersections:
        print(f'   • {loc}')
    print('')
    print('💡 Suggested route: $FROM → ' + ' → '.join(intersections) + ' → $TO')
else:
    print('✓ Direct path is clear')
"
        ;;

    route)
        FROM="$1"
        TO="$2"
        if [ -z "$FROM" ] || [ -z "$TO" ]; then
            error "Usage: dm-path.sh route <from> <to>"
        fi

        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/dm-campaign.sh" path)
        $PYTHON_CMD -c "
import json
import sys
sys.path.insert(0, '$LIB_DIR')
from path_intersect import find_route_with_waypoints

with open('$CAMPAIGN_DIR/locations.json') as f:
    locs = json.load(f)

route = find_route_with_waypoints('$FROM', '$TO', locs)

print('🗺️  Route: ' + ' → '.join(route))

if len(route) > 2:
    print('')
    print('⚠️  This path passes through:')
    for waypoint in route[1:-1]:
        diam = locs[waypoint].get('diameter_meters', 10)
        print(f'   • {waypoint} ({diam}m diameter)')
"
        ;;

    analyze)
        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/dm-campaign.sh" path)
        $PYTHON_CMD -c "
import json
import sys
sys.path.insert(0, '$LIB_DIR')
from path_intersect import check_path_intersection

with open('$CAMPAIGN_DIR/locations.json') as f:
    locs = json.load(f)

print('🔍 Analyzing all connections for intersections...')
print('=' * 60)

found_any = False

for loc_name, loc_data in locs.items():
    for conn in loc_data.get('connections', []):
        to_loc = conn.get('to')
        if to_loc not in locs:
            continue

        intersections = check_path_intersection(loc_name, to_loc, locs)

        if intersections:
            found_any = True
            print(f'\\n📍 {loc_name} → {to_loc}:')
            print(f'   Intersects: {\", \".join(intersections)}')
            via_route = \" → \".join(intersections)
            print(f'   Suggested route: {loc_name} → {via_route} → {to_loc}')

if not found_any:
    print('\\n✓ No path intersections detected')
    print('All connections are direct paths')
"
        ;;

    *)
        error "Unknown command: $COMMAND"
        echo "Run 'dm-path.sh --help' for usage"
        exit 1
        ;;
esac
