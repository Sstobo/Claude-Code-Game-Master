#!/bin/bash
# dm-npc.sh - Create and update NPCs (Hybrid Architecture)
# Uses Python modules for validation and data operations

# Source common utilities
source "$(dirname "$0")/common.sh"

# Usage: dm-npc.sh <action> <name> [additional args]
# Examples:
#   dm-npc.sh create "Grimnar" "dwarf blacksmith" "friendly"
#   dm-npc.sh update "Grimnar" "insulted by player"
#   dm-npc.sh status "Grimnar"

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-npc.sh <action> [name] [args]"
    echo ""
    echo "=== NPC Management ==="
    echo "  create <name> <description> <attitude>  Create new NPC"
    echo "  update <name> <event>                   Add event to NPC history"
    echo "  status <name>                           Show NPC details"
    echo "  enhance <name> <description>            Update NPC description"
    echo "  list [--attitude X] [--location Y]      List all NPCs"
    echo ""
    echo "=== Tags ==="
    echo "  tag-location <name> <loc1> [loc2...]    Add location tags"
    echo "  untag-location <name> <loc1> [loc2...]  Remove location tags"
    echo "  tag-quest <name> <quest1> [quest2...]   Add quest tags"
    echo "  untag-quest <name> <quest1> [quest2...] Remove quest tags"
    echo "  tags <name>                             Show NPC tags"
    echo ""
    echo "=== Party Members ==="
    echo "  promote <name>                          Make NPC a party member"
    echo "  demote <name>                           Remove party member status"
    echo "  party                                   List all party members with HP/AC"
    echo ""
    echo "=== Party Member Stats (requires promote first) ==="
    echo "  hp <name> <+/-amount>                   Damage/heal party member"
    echo "  xp <name> <+amount>                     Award XP to party member"
    echo "  set <name> <field> <value>              Set stat (ac, level, class, race, attack, damage, hp_max)"
    echo "  equip <name> <item>                     Add equipment"
    echo "  unequip <name> <item>                   Remove equipment"
    echo "  condition <name> add/remove <cond>      Manage conditions (poisoned, stunned, etc)"
    echo "  feature <name> add/remove <feature>     Manage features (Second Wind, etc)"
    echo ""
    echo "Examples:"
    echo "  dm-npc.sh create \"Carl\" \"A dungeon crawler\" \"friendly\""
    echo "  dm-npc.sh promote \"Carl\"                 # Make Carl a party member"
    echo "  dm-npc.sh set \"Carl\" ac 14               # Set Carl's AC"
    echo "  dm-npc.sh equip \"Carl\" \"Chitin Armor\"    # Give Carl armor"
    echo "  dm-npc.sh hp \"Carl\" -4                   # Carl takes 4 damage"
    echo "  dm-npc.sh party                          # See all party members"
    exit 1
fi

require_active_campaign

ACTION="$1"
shift  # Remove action from arguments

# Special handling for actions that don't require a name
if [ "$ACTION" = "list" ]; then
    $PYTHON_CMD "$LIB_DIR/npc_manager.py" list "$@"
    exit $?
fi

if [ "$ACTION" = "party" ]; then
    $PYTHON_CMD "$LIB_DIR/npc_manager.py" party
    exit $?
fi

# All other actions require a name as first argument
if [ "$#" -lt 1 ]; then
    echo "Error: Action '$ACTION' requires a name argument"
    exit 1
fi

NAME="$1"
shift  # Remove name from arguments

# Delegate to Python module based on action
case "$ACTION" in
    create)
        if [ "$#" -ne 2 ]; then
            echo "Usage: dm-npc.sh create <name> <description> <attitude>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" create "$NAME" "$1" "$2"
        ;;

    update)
        if [ "$#" -ne 1 ]; then
            echo "Usage: dm-npc.sh update <name> <event>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" update "$NAME" "$1"
        ;;

    status)
        STATUS_OUTPUT=$($PYTHON_CMD "$LIB_DIR/npc_manager.py" status "$NAME")
        STATUS_CODE=$?
        echo "$STATUS_OUTPUT"

        # Auto-query RAG for NPC context if vectors exist
        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/dm-campaign.sh" path 2>/dev/null)
        RAG_OUTPUT=""
        RAG_CODE=0
        if [ -d "$CAMPAIGN_DIR/vectors" ]; then
            echo ""
            echo "Source Material Context"
            echo "======================="
            RAG_OUTPUT=$($PYTHON_CMD "$LIB_DIR/entity_enhancer.py" search "$NAME personality dialogue background" -n 4 --excerpt-chars 250)
            RAG_CODE=$?
            echo "$RAG_OUTPUT"
        fi

        STATUS_CHARS=${#STATUS_OUTPUT}
        RAG_CHARS=${#RAG_OUTPUT}
        STATUS_TOKENS=$(estimate_tokens_from_chars "$STATUS_CHARS")
        RAG_TOKENS=$(estimate_tokens_from_chars "$RAG_CHARS")
        log_token_usage "dm-npc-status" "name_chars=${#NAME}" "status_chars=$STATUS_CHARS" "status_tokens_est=$STATUS_TOKENS" "rag_chars=$RAG_CHARS" "rag_tokens_est=$RAG_TOKENS"

        if [ $STATUS_CODE -ne 0 ]; then
            exit $STATUS_CODE
        fi
        if [ $RAG_CODE -ne 0 ]; then
            exit $RAG_CODE
        fi
        ;;

    enhance)
        if [ "$#" -ne 1 ]; then
            echo "Usage: dm-npc.sh enhance <name> <enhanced_description>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" enhance "$NAME" "$1"
        ;;

    tag-location)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-npc.sh tag-location <name> <location1> [location2 ...]"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" tag-location "$NAME" "$@"
        ;;

    untag-location)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-npc.sh untag-location <name> <location1> [location2 ...]"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" untag-location "$NAME" "$@"
        ;;

    tag-quest)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-npc.sh tag-quest <name> <quest1> [quest2 ...]"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" tag-quest "$NAME" "$@"
        ;;

    untag-quest)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-npc.sh untag-quest <name> <quest1> [quest2 ...]"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" untag-quest "$NAME" "$@"
        ;;

    tags)
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" tags "$NAME"
        ;;

    # Party member commands
    promote)
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" promote "$NAME"
        ;;

    demote)
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" demote "$NAME"
        ;;

    hp)
        if [ "$#" -ne 1 ]; then
            echo "Usage: dm-npc.sh hp <name> <+/-amount>"
            echo "Example: dm-npc.sh hp \"Carl\" -4"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" hp "$NAME" "$1"
        ;;

    xp)
        if [ "$#" -ne 1 ]; then
            echo "Usage: dm-npc.sh xp <name> <+amount>"
            echo "Example: dm-npc.sh xp \"Carl\" +100"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" xp "$NAME" "$1"
        ;;

    set)
        if [ "$#" -ne 2 ]; then
            echo "Usage: dm-npc.sh set <name> <field> <value>"
            echo "Fields: ac, level, class, race, attack, damage, hp_max"
            echo "Example: dm-npc.sh set \"Carl\" ac 14"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" set "$NAME" "$1" "$2"
        ;;

    equip)
        if [ "$#" -ne 1 ]; then
            echo "Usage: dm-npc.sh equip <name> <item>"
            echo "Example: dm-npc.sh equip \"Carl\" \"Chitin Armor\""
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" equip "$NAME" "$1"
        ;;

    unequip)
        if [ "$#" -ne 1 ]; then
            echo "Usage: dm-npc.sh unequip <name> <item>"
            echo "Example: dm-npc.sh unequip \"Carl\" \"Torn Shirt\""
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" unequip "$NAME" "$1"
        ;;

    condition)
        if [ "$#" -ne 2 ]; then
            echo "Usage: dm-npc.sh condition <name> add/remove <condition>"
            echo "Example: dm-npc.sh condition \"Carl\" add poisoned"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" condition "$NAME" "$1" "$2"
        ;;

    feature)
        if [ "$#" -ne 2 ]; then
            echo "Usage: dm-npc.sh feature <name> add/remove <feature>"
            echo "Example: dm-npc.sh feature \"Carl\" add \"Second Wind\""
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/npc_manager.py" feature "$NAME" "$1" "$2"
        ;;

    *)
        echo "Error: Unknown action '$ACTION'"
        echo "Run 'dm-npc.sh' without arguments to see all available actions"
        exit 1
        ;;
esac

# Exit with the same status as the Python command
exit $?
