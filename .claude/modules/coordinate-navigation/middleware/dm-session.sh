#!/bin/bash
# coordinate-navigation middleware for dm-session.sh
# Handles: move action (with distance/time calculation)

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$1" = "--help" ]; then
    echo "  move <location> [--speed-multiplier X]  Move with distance/time calculation"
    exit 1
fi

[ "$1" = "move" ] || exit 1

shift  # remove 'move'
exec bash "$MODULE_DIR/tools/dm-navigation.sh" move "$@"
