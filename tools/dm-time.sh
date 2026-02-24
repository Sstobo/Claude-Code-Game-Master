#!/bin/bash
# dm-time.sh - Update campaign time

source "$(dirname "$0")/common.sh"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: dm-time.sh <time_of_day|HH:MM> <date> [options]"
    echo ""
    echo "Examples:"
    echo "  dm-time.sh \"Утро\" \"18 октября 2024\"              # Set time of day"
    echo "  dm-time.sh \"Утро\" \"18 октября 2024\" --elapsed 4  # Advance clock by 4h"
    echo "  dm-time.sh \"_\" \"18 октября 2024\" --to 14:30       # Advance to 14:30"
    echo "  dm-time.sh \"08:00\" \"18 октября 2024\"              # Set exact clock"
    echo ""
    echo "  --elapsed <hours>  Hours passed. Auto-advances clock & ticks consequences."
    echo "  --to <HH:MM>       Advance to exact time. Auto-calculates elapsed hours."
    echo "  --sleeping          Module hook: marks rest period."
    dispatch_middleware_help "dm-time.sh"
    exit 1
fi

require_active_campaign

dispatch_middleware "dm-time.sh" "$@" && exit $?

# Filter out --sleeping before passing to CORE (modules handle it in post-hook)
CORE_ARGS=()
for arg in "${@:3}"; do
    [ "$arg" = "--sleeping" ] || CORE_ARGS+=("$arg")
done

# CORE runs, then post-hooks fire
$PYTHON_CMD "$LIB_DIR/time_manager.py" update "$1" "$2" "${CORE_ARGS[@]}"
CORE_RC=$?
[ $CORE_RC -eq 0 ] && dispatch_middleware_post "dm-time.sh" "$@"
exit $CORE_RC
