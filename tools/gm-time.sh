#!/bin/bash
# gm-time.sh - Update campaign time (wrapper for time_manager.py)

source "$(dirname "$0")/common.sh"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: gm-time.sh <time_of_day> <date>"
    echo "Example: gm-time.sh \"Dawn\" \"16th day of Harvestmoon, Year 1247\""
    exit 1
fi

require_active_campaign

$PYTHON_CMD "$LIB_DIR/time_manager.py" update "$1" "$2"
RESULT=$?
if [ $RESULT -ne 0 ]; then exit $RESULT; fi

# Pressure: time passing advances every advance_on=time threat clock.
$PYTHON_CMD "$LIB_DIR/threat_clocks.py" tick-time

# Reactivity: time passing can fire on_time consequences (e.g. nightfall, deadlines).
echo ""
bash "$TOOLS_DIR/gm-consequence.sh" tick
exit 0
