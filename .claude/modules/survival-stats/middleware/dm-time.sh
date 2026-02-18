#!/bin/bash
# survival-stats middleware for dm-time.sh
# Handles: --elapsed, --precise-time, --sleeping

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$1" = "--help" ]; then
    echo "  dm-time.sh \"Dawn\" \"5th day\" --elapsed 8 --sleeping"
    echo "  dm-time.sh \"Noon\" \"April 15th\" --precise-time \"12:30\""
    echo "Options: --elapsed <hours>, --precise-time <HH:MM>, --sleeping"
    exit 1
fi

for arg in "$@"; do
    case "$arg" in
        --elapsed|--precise-time|--sleeping)
            exec bash "$MODULE_DIR/tools/dm-survival.sh" time "$@"
            ;;
    esac
done

exit 1
