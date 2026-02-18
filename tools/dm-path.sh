#!/bin/bash
# dm-path.sh - Path routing (delegates to coordinate-navigation module)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

NAV="$PROJECT_ROOT/.claude/modules/coordinate-navigation"
if [ ! -d "$NAV" ]; then
    echo "[ERROR] coordinate-navigation module not found at: $NAV"
    exit 1
fi

# Translate legacy dm-path.sh commands → dm-navigation.sh path <subcmd>
COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    check|route|analyze)
        bash "$NAV/tools/dm-navigation.sh" path "$COMMAND" "$@"
        ;;
    --help|-h|"")
        echo "Usage: dm-path.sh <command> [args]"
        echo ""
        echo "Commands:"
        echo "  check <from> <to>  - Check if path intersects locations"
        echo "  route <from> <to>  - Find route with waypoints"
        echo "  analyze            - Analyze all connections for intersections"
        echo ""
        echo "Delegates to: .claude/modules/coordinate-navigation/tools/dm-navigation.sh path"
        ;;
    *)
        echo "[ERROR] Unknown command: $COMMAND"
        echo "Valid: check, route, analyze"
        exit 1
        ;;
esac
