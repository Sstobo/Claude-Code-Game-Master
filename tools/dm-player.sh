#!/bin/bash
# dm-player.sh - Player character management

source "$(dirname "$0")/common.sh"

require_active_campaign

ACTION=$1
shift

dispatch_middleware "dm-player.sh" "$ACTION" "$@" && exit $?

case "$ACTION" in
    show)
        $PYTHON_CMD "$LIB_DIR/player_manager.py" show ${1:+"$1"}
        ;;

    list)
        $PYTHON_CMD "$LIB_DIR/player_manager.py" list
        ;;

    save-json)
        if [ -z "$*" ]; then
            echo "Usage: dm-player.sh save-json '<json_data>'"
            exit 1
        fi
        echo "$*" | $PYTHON_CMD "$PROJECT_ROOT/features/character-creation/save_character.py" --stdin
        ;;

    set)
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh set <character_name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" set "$1"
        ;;

    xp)
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: dm-player.sh xp <character_name> <+amount>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" xp "$1" "$2"
        ;;

    level-check)
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh level-check <character_name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" level-check "$1"
        ;;

    hp)
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh hp [character_name] <+/-amount>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" hp "$@"
        ;;

    get)
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh get <character_name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" get "$1"
        ;;

    gold)
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh gold <character_name> [+/-amount]"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" gold "$1" ${2:+"$2"}
        ;;

    inventory)
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: dm-player.sh inventory <character_name> <add|remove|list> [item]"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" inventory "$@"
        ;;

    loot)
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh loot <character_name> --gold <amount> --items \"Item1\" ..."
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" loot "$@"
        ;;

    condition)
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: dm-player.sh condition <character_name> <add|remove|list> [condition]"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" condition "$@"
        ;;

    *)
        echo "Usage: dm-player.sh <action> [args]"
        echo ""
        echo "Actions: show, get, list, set, xp, hp, gold, inventory, loot, condition,"
        echo "         level-check, save-json"
        dispatch_middleware_help "dm-player.sh"
        ;;
esac

exit $?
