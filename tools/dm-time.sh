#!/bin/bash
# dm-time.sh - Update campaign time

source "$(dirname "$0")/common.sh"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: dm-time.sh <time_of_day> <date> [options]"
    echo ""
    echo "Examples:"
    echo "  dm-time.sh \"Evening\" \"3rd day of Spring\""
    dispatch_middleware_help "dm-time.sh"
    exit 1
fi

require_active_campaign

dispatch_middleware "dm-time.sh" "$@" || \
    $PYTHON_CMD "$LIB_DIR/time_manager.py" update "$1" "$2"
