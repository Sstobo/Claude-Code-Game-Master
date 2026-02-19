#!/usr/bin/env bash
# world-travel middleware for dm-session.sh
# Handles move: navigation calc + auto encounter check

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$MODULE_DIR/../../.." && pwd)"

if [ "$1" = "--help" ]; then
    echo "  move <location> [--speed-multiplier X]  Move with distance/time + encounter check"
    exit 1
fi

[ "$1" = "move" ] || exit 1

shift  # remove 'move'
DESTINATION="$1"

# Run navigation move (calculates distance/time, moves party)
# Capture output and exit code
NAV_OUTPUT=$(bash "$MODULE_DIR/tools/dm-navigation.sh" move "$@" 2>&1)
NAV_RC=$?
echo "$NAV_OUTPUT"

[ $NAV_RC -eq 0 ] || exit 0  # navigation handled it (even if error)

# Extract distance_meters from navigation output JSON if present
DISTANCE_METERS=$(echo "$NAV_OUTPUT" | python3 -c "
import sys, json, re
text = sys.stdin.read()
# Try to find JSON in output
m = re.search(r'\{[^}]+\"distance_meters\"[^}]+\}', text)
if m:
    try:
        d = json.loads(m.group())
        print(d.get('distance_meters', 0))
        sys.exit(0)
    except:
        pass
print(0)
" 2>/dev/null)

TERRAIN=$(echo "$NAV_OUTPUT" | python3 -c "
import sys, json, re
text = sys.stdin.read()
m = re.search(r'\{[^}]+\"terrain\"[^}]+\}', text)
if m:
    try:
        d = json.loads(m.group())
        print(d.get('terrain', 'open'))
        sys.exit(0)
    except:
        pass
print('open')
" 2>/dev/null)

# Auto encounter check if distance known and encounter-system rules apply
if [ -n "$DISTANCE_METERS" ] && [ "$DISTANCE_METERS" -gt 0 ] 2>/dev/null; then
    # Get previous location for from/to
    ACTIVE=$(cat "$PROJECT_ROOT/world-state/active-campaign.txt" 2>/dev/null)
    FROM_LOC=""
    if [ -n "$ACTIVE" ]; then
        FROM_LOC=$(python3 -c "
import json
try:
    with open('$PROJECT_ROOT/world-state/campaigns/$ACTIVE/campaign-overview.json') as f:
        d = json.load(f)
    print(d.get('player_position', {}).get('previous_location') or '')
except:
    print('')
" 2>/dev/null)
    fi

    echo ""
    bash "$MODULE_DIR/tools/dm-encounter.sh" check "${FROM_LOC:-unknown}" "$DESTINATION" "$DISTANCE_METERS" "${TERRAIN:-open}"
fi

exit 0
