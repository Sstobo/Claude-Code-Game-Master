#!/bin/bash
# Player Character management for D&D campaign
# Thin CLI wrapper - logic in lib/player_manager.py

# Source common utilities
source "$(dirname "$0")/common.sh"

require_active_campaign

ACTION=$1
shift

case "$ACTION" in
    "show")
        if [ -z "$1" ]; then
            $PYTHON_CMD "$LIB_DIR/player_manager.py" show
        else
            $PYTHON_CMD "$LIB_DIR/player_manager.py" show "$1"
        fi
        ;;

    "list")
        $PYTHON_CMD "$LIB_DIR/player_manager.py" list
        ;;

    "save-json")
        # Save character from JSON data
        CHARACTER_JSON="$*"
        if [ -z "$CHARACTER_JSON" ]; then
            echo "Usage: dm-player.sh save-json '<json_data>'"
            echo "Example: dm-player.sh save-json '{\"name\":\"Thorin\",\"race\":\"Dwarf\",\"class\":\"Fighter\",\"level\":1}'"
            exit 1
        fi
        $PYTHON_CMD "$PROJECT_ROOT/features/character-creation/save_character.py" "$CHARACTER_JSON"
        ;;

    "set")
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh set <character_name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" set "$1"
        ;;

    "xp")
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: dm-player.sh xp <character_name> <+amount>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" xp "$1" "$2"
        ;;

    "level-check")
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh level-check <character_name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" level-check "$1"
        ;;

    "hp")
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: dm-player.sh hp <character_name> <+/-amount>"
            echo "Example: dm-player.sh hp conan -3  (take 3 damage)"
            echo "Example: dm-player.sh hp conan +5  (heal 5 HP)"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" hp "$1" "$2"
        ;;

    "get")
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh get <character_name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" get "$1"
        ;;

    "gold")
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh gold <character_name> [+/-amount]"
            echo "Example: dm-player.sh gold theron +50  (gain 50 gold)"
            echo "Example: dm-player.sh gold theron -10  (spend 10 gold)"
            echo "Example: dm-player.sh gold theron      (show current gold)"
            exit 1
        fi
        if [ -z "$2" ]; then
            $PYTHON_CMD "$LIB_DIR/player_manager.py" gold "$1"
        else
            $PYTHON_CMD "$LIB_DIR/player_manager.py" gold "$1" "$2"
        fi
        ;;

    "inventory")
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: dm-player.sh inventory <character_name> <action> [item]"
            echo ""
            echo "Actions:"
            echo "  add <item>    - Add item to inventory"
            echo "  remove <item> - Remove item from inventory"
            echo "  list          - Show all items"
            echo ""
            echo "Example: dm-player.sh inventory theron add \"Health Potion\""
            echo "Example: dm-player.sh inventory theron remove \"Dagger\""
            echo "Example: dm-player.sh inventory theron list"
            exit 1
        fi
        if [ "$2" = "list" ]; then
            $PYTHON_CMD "$LIB_DIR/player_manager.py" inventory "$1" "$2"
        else
            if [ -z "$3" ]; then
                echo "Error: Item name required for $2"
                exit 1
            fi
            $PYTHON_CMD "$LIB_DIR/player_manager.py" inventory "$1" "$2" "$3"
        fi
        ;;

    "loot")
        if [ -z "$1" ]; then
            echo "Usage: dm-player.sh loot <character_name> --gold <amount> --items \"Item1\" \"Item2\" ..."
            echo ""
            echo "Examples:"
            echo "  dm-player.sh loot Tandy --gold 47 --items \"Silvered Shortsword\" \"Potion of Healing\""
            echo "  dm-player.sh loot Tandy --items \"Scroll of Fireball\""
            echo "  dm-player.sh loot Tandy --gold 100"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" loot "$@"
        ;;

    "condition")
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: dm-player.sh condition <character_name> <action> [condition]"
            echo ""
            echo "Actions:"
            echo "  add <condition>    - Add condition to character"
            echo "  remove <condition> - Remove condition from character"
            echo "  list               - Show current conditions"
            echo ""
            echo "Example: dm-player.sh condition Tandy add poisoned"
            echo "Example: dm-player.sh condition Tandy remove poisoned"
            echo "Example: dm-player.sh condition Tandy list"
            exit 1
        fi
        if [ "$2" = "list" ]; then
            $PYTHON_CMD "$LIB_DIR/player_manager.py" condition "$1" "$2"
        else
            if [ -z "$3" ]; then
                echo "Error: Condition name required for $2"
                exit 1
            fi
            $PYTHON_CMD "$LIB_DIR/player_manager.py" condition "$1" "$2" "$3"
        fi
        ;;

    *)
        echo "D&D Player Character Manager"
        echo "Usage: dm-player.sh <action> [args]"
        echo ""
        echo "Actions:"
        echo "  show [name]                  - Show player(s) summary"
        echo "  get <name>                   - Get full character JSON"
        echo "  list                         - List all player IDs"
        echo "  set <name>                   - Set character as current active PC"
        echo "  xp <name> +<amount>          - Award XP to character"
        echo "  hp <name> <+/-amount>        - Modify character HP"
        echo "  gold <name> [+/-amount]      - Modify or show character gold"
        echo "  inventory <name> <action>    - Manage inventory (add/remove/list)"
        echo "  condition <name> <action>    - Manage conditions (add/remove/list)"
        echo "  loot <name> --gold X --items - Batch add items + gold at once"
        echo "  level-check <name>           - Check XP and level status"
        echo "  save-json '<json>'           - Save complete character from JSON"
        echo ""
        echo "Note: Character is stored in the active campaign's character.json"
        ;;
esac

# Propagate Python exit code
exit $?
