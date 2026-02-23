#!/bin/bash
# dm-time.sh - Update campaign time

source "$(dirname "$0")/common.sh"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: dm-time.sh <time_of_day> <date> [--elapsed <hours>]"
    echo ""
    echo "Examples:"
    echo "  dm-time.sh \"Evening\" \"3rd day of Spring\""
    echo "  dm-time.sh \"Night\" \"3rd day of Spring\" --elapsed 4"
    echo "  dm-time.sh \"Morning\" \"4th day of Spring\" --elapsed 8"
    echo ""
    echo "  --elapsed <hours>  Hours passed. Auto-ticks timed consequences."
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
