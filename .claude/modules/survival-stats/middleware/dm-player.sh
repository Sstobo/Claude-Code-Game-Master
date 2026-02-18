#!/bin/bash
# survival-stats middleware for dm-player.sh
# Handles: custom-stat, custom-stats-list

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$1" = "--help" ]; then
    echo "  custom-stat [name] <stat> [+/-amount]  Get or modify a custom stat"
    echo "  custom-stats-list [name]               List all custom stats"
    exit 1
fi

ACTION="$1"
shift

case "$ACTION" in
    custom-stat|custom-stats-list)
        exec bash "$MODULE_DIR/tools/dm-survival.sh" "$ACTION" "$@"
        ;;
esac

exit 1
