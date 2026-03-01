#!/bin/bash
# dm-time.sh - Update campaign time (wrapper for time_manager.py)

source "$(dirname "$0")/common.sh"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: dm-time.sh <time_of_day> <date>"
    echo "Example: dm-time.sh \"Dawn\" \"16th day of Harvestmoon, Year 1247\""
    exit 1
fi

require_active_campaign

dispatch_middleware "dm-time.sh" "$1" "$2" "$@" && exit $?

$PYTHON_CMD -m lib.time_manager update "$1" "$2"
CORE_RC=$?
dispatch_middleware_post "dm-time.sh" "$1" "$2" "$@"
exit $CORE_RC
