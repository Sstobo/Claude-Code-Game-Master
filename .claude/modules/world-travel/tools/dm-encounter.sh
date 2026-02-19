#!/bin/bash
# dm-encounter.sh - Encounter system management (module)

# Get MODULE_ROOT (this script is in .claude/modules/world-travel/tools/)
MODULE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$MODULE_ROOT/../../.." && pwd)"

# Source common.sh from CORE
source "$PROJECT_ROOT/tools/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-encounter.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  toggle                          - Enable/disable encounter system"
    echo "  status                          - Show current settings"
    echo "  set-base-dc <dc>               - Set base DC for encounter checks"
    echo "  set-distance-mod <modifier>    - Set distance modifier (DC per km)"
    echo "  set-stat <stat_name>           - Set stat used for checks (stealth, dex, custom:awareness)"
    echo "  set-time-mod <time> <modifier> - Set time DC modifier"
    echo "  check <from> <to> <distance> [terrain] - Manual encounter check"
    echo ""
    echo "Examples:"
    echo "  dm-encounter.sh toggle"
    echo "  dm-encounter.sh set-base-dc 18"
    echo "  dm-encounter.sh set-stat custom:awareness"
    echo "  dm-encounter.sh check \"Village\" \"Ruins\" 2000 open"
    exit 1
fi

require_active_campaign

ACTION="$1"
shift

case "$ACTION" in
    toggle)
        if [ -z "$CAMPAIGN_DIR" ]; then
            echo "[ERROR] No active campaign"
            exit 1
        fi
        OVERVIEW="$CAMPAIGN_DIR/campaign-overview.json"

        if [ ! -f "$OVERVIEW" ]; then
            echo "[ERROR] Campaign overview not found"
            exit 1
        fi

        CURRENT=$(jq -r '.campaign_rules.encounter_system.enabled // false' "$OVERVIEW")

        if [ "$CURRENT" == "true" ]; then
            jq '.campaign_rules.encounter_system.enabled = false' "$OVERVIEW" > "$OVERVIEW.tmp" && mv "$OVERVIEW.tmp" "$OVERVIEW"
            echo "[SUCCESS] Encounter system DISABLED"
        else
            # Create default configuration if not exists
            jq '.campaign_rules.encounter_system = {
                "enabled": true,
                "min_distance_meters": 300,
                "base_dc": 16,
                "distance_modifier": 2,
                "stat_to_use": "stealth",
                "use_luck": false,
                "time_dc_modifiers": {
                    "Morning": 0,
                    "Day": 0,
                    "Evening": 2,
                    "Night": 4
                }
            }' "$OVERVIEW" > "$OVERVIEW.tmp" && mv "$OVERVIEW.tmp" "$OVERVIEW"
            echo "[SUCCESS] Encounter system ENABLED"
        fi
        ;;

    status)
        if [ -z "$CAMPAIGN_DIR" ]; then
            echo "[ERROR] No active campaign"
            exit 1
        fi
        OVERVIEW="$CAMPAIGN_DIR/campaign-overview.json"
        echo "Encounter System Status"
        echo "======================="
        if [ -f "$OVERVIEW" ]; then
            jq -r '.campaign_rules.encounter_system // {}' "$OVERVIEW"
        else
            echo "No encounter system configured"
        fi
        ;;

    set-base-dc)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-encounter.sh set-base-dc <dc>"
            exit 1
        fi
        NEW_DC="$1"
        OVERVIEW="$CAMPAIGN_DIR/campaign-overview.json"
        jq ".campaign_rules.encounter_system.base_dc = $NEW_DC" "$OVERVIEW" > "$OVERVIEW.tmp" && mv "$OVERVIEW.tmp" "$OVERVIEW"
        echo "[SUCCESS] Base DC set to $NEW_DC"
        ;;

    set-distance-mod)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-encounter.sh set-distance-mod <modifier>"
            exit 1
        fi
        NEW_MOD="$1"
        OVERVIEW="$CAMPAIGN_DIR/campaign-overview.json"
        jq ".campaign_rules.encounter_system.distance_modifier = $NEW_MOD" "$OVERVIEW" > "$OVERVIEW.tmp" && mv "$OVERVIEW.tmp" "$OVERVIEW"
        echo "[SUCCESS] Distance modifier set to $NEW_MOD"
        ;;

    set-stat)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-encounter.sh set-stat <stat_name>"
            echo "Examples: stealth, dex, custom:awareness"
            exit 1
        fi
        STAT_NAME="$1"
        OVERVIEW="$CAMPAIGN_DIR/campaign-overview.json"
        jq ".campaign_rules.encounter_system.stat_to_use = \"$STAT_NAME\"" "$OVERVIEW" > "$OVERVIEW.tmp" && mv "$OVERVIEW.tmp" "$OVERVIEW"
        echo "[SUCCESS] Encounter stat set to $STAT_NAME"
        ;;

    set-time-mod)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-encounter.sh set-time-mod <time_of_day> <modifier>"
            exit 1
        fi
        TIME="$1"
        MOD="$2"
        OVERVIEW="$CAMPAIGN_DIR/campaign-overview.json"
        jq ".campaign_rules.encounter_system.time_dc_modifiers.\"$TIME\" = $MOD" "$OVERVIEW" > "$OVERVIEW.tmp" && mv "$OVERVIEW.tmp" "$OVERVIEW"
        echo "[SUCCESS] Time modifier for '$TIME' set to $MOD"
        ;;

    check)
        if [ "$#" -lt 3 ]; then
            echo "Usage: dm-encounter.sh check <from> <to> <distance_m> [terrain]"
            exit 1
        fi
        FROM_LOC="$1"
        TO_LOC="$2"
        DISTANCE="$3"
        TERRAIN="${4:-open}"

        $PYTHON_CMD "$MODULE_ROOT/lib/encounter_engine.py" "$FROM_LOC" "$TO_LOC" "$DISTANCE" "$TERRAIN"
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: toggle, status, set-base-dc, set-distance-mod, set-stat, set-time-mod, check"
        exit 1
        ;;
esac

exit $?
