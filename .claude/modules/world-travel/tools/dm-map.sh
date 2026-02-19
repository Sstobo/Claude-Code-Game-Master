#!/bin/bash
# dm-map.sh - Map visualization module wrapper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$MODULE_DIR")")")"

source "$PROJECT_ROOT/tools/common.sh"

if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: dm-map.sh [options]"
    echo ""
    echo "Options:"
    echo "  --gui                  - Open interactive GUI map (Pygame)"
    echo "  --minimap              - Show compact minimap view (ASCII)"
    echo "  --color                - Use ANSI colors"
    echo "  --width <cols>         - Map width in characters (default: 80)"
    echo "  --height <rows>        - Map height in characters (default: 40)"
    echo "  --no-labels            - Hide location labels"
    echo "  --no-compass           - Hide compass rose"
    echo "  --radius <n>           - Minimap radius in cells (default: 5)"
    echo ""
    echo "Examples:"
    echo "  dm-map.sh                     - Show full ASCII map"
    echo "  dm-map.sh --color             - Show colored ASCII map"
    echo "  dm-map.sh --gui               - Open interactive GUI map"
    echo "  dm-map.sh --minimap           - Show compact minimap"
    exit 0
fi

require_active_campaign

USE_GUI=false
FILTERED_ARGS=()

for arg in "$@"; do
    if [ "$arg" == "--gui" ]; then
        USE_GUI=true
    else
        FILTERED_ARGS+=("$arg")
    fi
done

if [ "$USE_GUI" == "true" ]; then
    $PYTHON_CMD "$MODULE_DIR/lib/map_gui.py" "${FILTERED_ARGS[@]}"
else
    $PYTHON_CMD "$MODULE_DIR/lib/map_renderer.py" "$@"
fi

exit $?
