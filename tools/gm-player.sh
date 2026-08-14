#!/bin/bash
# Player Character management
# Thin CLI wrapper - logic in lib/player_manager.py

# Source common utilities
source "$(dirname "$0")/common.sh"

require_active_campaign

ACTION=$1
shift

case "$ACTION" in
    "show")
        # Optional [name] and optional --json (full record). Pass all through.
        $PYTHON_CMD "$LIB_DIR/player_manager.py" show "$@"
        ;;

    "list")
        $PYTHON_CMD "$LIB_DIR/player_manager.py" list
        ;;

    "save-json")
        # Save character from JSON data
        CHARACTER_JSON="$*"
        if [ -z "$CHARACTER_JSON" ]; then
            echo "Usage: gm-player.sh save-json '<json_data>'"
            echo "Example: gm-player.sh save-json '{\"name\":\"Thorin\",\"race\":\"Dwarf\",\"class\":\"Fighter\",\"level\":1}'"
            exit 1
        fi
        $PYTHON_CMD "$PROJECT_ROOT/features/character-creation/save_character.py" "$CHARACTER_JSON"
        ;;

    "onboard")
        # Identity-first entry: one question, three doors. Default over /create-character.
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh onboard canon <npc_name>"
            echo "       gm-player.sh onboard original <name> [\"one-line concept\"]"
            echo "       gm-player.sh onboard nameless"
            echo ""
            echo "Refuses to overwrite an existing PC; add --replace to hand the story to"
            echo "someone new (the outgoing sheet is archived to the campaign's fallen/)."
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/identity_onboarding.py" onboard "$@"
        ;;

    "set")
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh set <character_name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" set "$1"
        ;;

    "xp")
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: gm-player.sh xp <character_name> <+amount>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" xp "$1" "$2"
        ;;

    "award")
        # Discretionary spectacle XP (kit-aware, level-scaled; co-awards followers).
        # Name optional (defaults to active PC). Requires --tier; --reason optional.
        $PYTHON_CMD "$LIB_DIR/player_manager.py" award "$@"
        ;;

    "level-check")
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh level-check <character_name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" level-check "$1"
        ;;

    "hp")
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: gm-player.sh hp <character_name> <+/-amount>"
            echo "Example: gm-player.sh hp conan -3  (take 3 damage)"
            echo "Example: gm-player.sh hp conan +5  (heal 5 HP)"
            exit 1
        fi
        NAME="$1"; AMT="$2"; shift 2
        $PYTHON_CMD "$LIB_DIR/player_manager.py" hp "$NAME" "$AMT" "$@"
        ;;

    "vital")
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh vital <vital_name> [<+/-amount> | set <value>]"
            echo "Example: gm-player.sh vital vigor -2      (spend 2 vigor)"
            echo "Example: gm-player.sh vital corruption +1 (gain 1 corruption)"
            echo "Example: gm-player.sh vital vigor set 5   (set vigor to 5)"
            echo "Example: gm-player.sh vital corruption    (show current)"
            echo "Vitals are whatever the World Kit declares (ruleset.json stat_schema.vitals)."
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" vital "$@"
        ;;

    "get")
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh get <character_name>"
            exit 1
        fi
        NAME="$1"; shift
        $PYTHON_CMD "$LIB_DIR/player_manager.py" get "$NAME" "$@"
        ;;

    "kill")
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh kill <character_name> [--cause \"<how>\"]"
            echo "Example: gm-player.sh kill Tandy --cause \"crushed by the Iron Tangle\""
            exit 1
        fi
        NAME="$1"; shift
        $PYTHON_CMD "$LIB_DIR/player_manager.py" kill "$NAME" "$@"
        ;;

    "revive")
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh revive <character_name> [--hp N] [--reason \"<how>\"]"
            echo "Bring a dead character back: status alive, HP restored (default 1), death stamps cleared."
            echo "Example: gm-player.sh revive Tandy --hp 12 --reason \"the Sunken Priest paid her debt\""
            exit 1
        fi
        NAME="$1"; shift
        $PYTHON_CMD "$LIB_DIR/player_manager.py" revive "$NAME" "$@"
        ;;

    "become")
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh become <party_member_name>"
            echo "Take over a party member as the active PC (Death Protocol hand-off)."
            echo "Archives the fallen PC to the campaign's fallen/ dir."
            exit 1
        fi
        NAME="$1"; shift
        $PYTHON_CMD "$LIB_DIR/player_manager.py" become "$NAME" "$@"
        ;;

    "gold")
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh gold <character_name> [+/-amount]"
            echo "Example: gm-player.sh gold theron +50  (gain 50 gold)"
            echo "Example: gm-player.sh gold theron -10  (spend 10 gold)"
            echo "Example: gm-player.sh gold theron      (show current gold)"
            exit 1
        fi
        if [ -z "$2" ]; then
            $PYTHON_CMD "$LIB_DIR/player_manager.py" gold "$1"
        else
            $PYTHON_CMD "$LIB_DIR/player_manager.py" gold "$1" "$2"
        fi
        ;;

    "inventory")
        # All positionals are optional: defaults to the active PC and `list`.
        # Forms: `inventory` · `inventory list` · `inventory <name> <action> [item]`.
        $PYTHON_CMD "$LIB_DIR/player_manager.py" inventory "$@"
        ;;

    "loot")
        if [ -z "$1" ]; then
            echo "Usage: gm-player.sh loot <character_name> --gold <amount> --items \"Item1\" \"Item2\" ..."
            echo ""
            echo "Examples:"
            echo "  gm-player.sh loot Tandy --gold 47 --items \"Silvered Shortsword\" \"Potion of Healing\""
            echo "  gm-player.sh loot Tandy --items \"Scroll of Fireball\""
            echo "  gm-player.sh loot Tandy --gold 100"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/player_manager.py" loot "$@"
        ;;

    "condition")
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "Usage: gm-player.sh condition <character_name> <action> [condition]"
            echo ""
            echo "Actions:"
            echo "  add <condition>    - Add condition to character"
            echo "  remove <condition> - Remove condition from character"
            echo "  list               - Show current conditions"
            echo ""
            echo "Example: gm-player.sh condition Tandy add poisoned"
            echo "Example: gm-player.sh condition Tandy remove poisoned"
            echo "Example: gm-player.sh condition Tandy list"
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

    "appearance")
        $PYTHON_CMD "$LIB_DIR/player_manager.py" appearance "$@"
        ;;

    "set-appearance")
        $PYTHON_CMD "$LIB_DIR/player_manager.py" set-appearance "$@"
        ;;

    *)
        echo "Player Character Manager"
        echo "Usage: gm-player.sh <action> [args]"
        echo ""
        echo "Actions:"
        echo "  show [name] [--json]         - Show summary (or full record with --json)"
        echo "  get <name>                   - Get full character JSON"
        echo "  list                         - List all player IDs"
        echo "  onboard <mode> [args]        - Identity-first entry (canon <npc> | original <name> [concept] | nameless; --replace to swap PCs)"
        echo "  set <name>                   - Set character as current active PC"
        echo "  xp <name> +<amount>          - Award XP to character"
        echo "  award [name] --tier T        - Spectacle XP for a clever/effective/unique/punishing beat (T=minor|major|legendary; --reason \"...\"; co-awards followers)"
        echo "  hp <name> <+/-amount>        - Modify character HP"
        echo "  vital <vital> <+/-N|set N>   - Read/change a kit vital (vigor, corruption, ...)"
        echo "  kill <name> [--cause ...]    - Mark PC dead (then run Death Protocol)"
        echo "  revive <name> [--hp N]       - Bring a dead PC back (--reason \"...\"; HP defaults to 1)"
        echo "  become <party_member>        - Take over a party member as the active PC"
        echo "  gold <name> [+/-amount]      - Modify or show character gold"
        echo "  inventory [name] [action]    - Manage inventory (add/remove/list; defaults to active PC + list)"
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
