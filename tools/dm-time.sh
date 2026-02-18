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
    echo "  dm-time.sh \"Dawn\" \"5th day\" --elapsed 8 --sleeping"
    echo ""
    echo "Options:"
    echo "  --elapsed HOURS           Hours that passed (manual) → requires survival-stats module"
    echo "  --precise-time HH:MM      Exact time (auto-calculates elapsed) → requires survival-stats module"
    echo "  --sleeping                Mark as rest period (stat drain paused) → requires survival-stats module"
    echo ""
    echo "Note: --elapsed, --precise-time, --sleeping delegate to survival-stats module"
    exit 1
fi

require_active_campaign

TIME_OF_DAY="$1"
DATE="$2"
shift 2

# Check if any survival-stats flags are present
HAS_SURVIVAL_FLAGS=false
for arg in "$@"; do
    if [ "$arg" = "--elapsed" ] || [ "$arg" = "--precise-time" ] || [ "$arg" = "--sleeping" ]; then
        HAS_SURVIVAL_FLAGS=true
        break
    fi
done

if [ "$HAS_SURVIVAL_FLAGS" = true ]; then
    SURV="$PROJECT_ROOT/.claude/modules/survival-stats"
    if [ -d "$SURV" ]; then
        bash "$SURV/tools/dm-survival.sh" time "$TIME_OF_DAY" "$DATE" "$@"
    else
        echo "[ERROR] --elapsed/--precise-time/--sleeping require the survival-stats module"
        echo "  Module not found at: .claude/modules/survival-stats"
        exit 1
    fi
else
    $PYTHON_CMD "$LIB_DIR/time_manager.py" update "$TIME_OF_DAY" "$DATE"
fi
exit $?
