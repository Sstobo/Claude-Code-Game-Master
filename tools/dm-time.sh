#!/bin/bash
# dm-time.sh - Update campaign time (wrapper for time_manager.py)

source "$(dirname "$0")/common.sh"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: dm-time.sh <time_of_day> <date> [OPTIONS]"
    echo ""
    echo "Examples:"
    echo "  dm-time.sh \"Evening\" \"3rd day of Spring\""
    echo "  dm-time.sh \"Midnight\" \"4th day\" --elapsed 8"
    echo "  dm-time.sh \"Noon\" \"April 15th\" --precise-time \"12:30\""
    echo ""
    echo "Options:"
    echo "  --elapsed HOURS           Hours that passed (manual)"
    echo "  --precise-time HH:MM      Exact time (auto-calculates elapsed)"
    echo ""
    echo "Note: If both are given, --precise-time takes priority"
    exit 1
fi

require_active_campaign

TIME_OF_DAY="$1"
DATE="$2"
shift 2

# Build arguments for Python
ARGS=("$TIME_OF_DAY" "$DATE")

# Parse optional parameters
while [ "$#" -gt 0 ]; do
    case "$1" in
        --elapsed)
            ARGS+=("--elapsed" "$2")
            shift 2
            ;;
        --precise-time)
            ARGS+=("--precise-time" "$2")
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

$PYTHON_CMD -m lib.time_manager update "${ARGS[@]}"
exit $?
