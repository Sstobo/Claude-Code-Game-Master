#!/bin/bash
# dm-hierarchy.sh - Hierarchical location management

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$MODULE_DIR/../../.." && pwd)"

source "$PROJECT_ROOT/tools/common.sh"

HIERARCHY_PY="$MODULE_DIR/lib/hierarchy_manager.py"

require_active_campaign

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-hierarchy.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  create-compound <name> [--parent <name>] [--entry <name>] [--mobile]"
    echo "  add-room <name> --parent <name> [--connect <name>...] [--entry] [--entry-config <json>]"
    echo "  enter <compound> [--via <entry_point>]"
    echo "  exit"
    echo "  move <target>"
    echo "  tree [compound]"
    echo "  entry-config <name> [--update <json>]"
    echo "  validate"
    exit 1
fi

ACTION="$1"
shift

case "$ACTION" in
    create-compound)
        NAME="$1"
        if [ -z "$NAME" ]; then
            echo "Usage: dm-hierarchy.sh create-compound <name> [--parent <name>] [--entry <name>] [--mobile]"
            exit 1
        fi
        shift
        $PYTHON_CMD "$HIERARCHY_PY" create-compound "$NAME" "$@"
        ;;
    add-room)
        NAME="$1"
        if [ -z "$NAME" ]; then
            echo "Usage: dm-hierarchy.sh add-room <name> --parent <name> [--connect <name>...] [--entry] [--entry-config <json>]"
            exit 1
        fi
        shift
        $PYTHON_CMD "$HIERARCHY_PY" add-room "$NAME" "$@"
        ;;
    enter)
        COMPOUND="$1"
        if [ -z "$COMPOUND" ]; then
            echo "Usage: dm-hierarchy.sh enter <compound> [--via <entry_point>]"
            exit 1
        fi
        shift
        ARGS=()
        while [ $# -gt 0 ]; do
            case "$1" in
                --via) ARGS+=("--entry-point"); shift; ARGS+=("$1") ;;
                *) ARGS+=("$1") ;;
            esac
            shift
        done
        $PYTHON_CMD "$HIERARCHY_PY" enter "$COMPOUND" "${ARGS[@]}"
        ;;
    exit)
        $PYTHON_CMD "$HIERARCHY_PY" exit
        ;;
    move)
        TARGET="$1"
        if [ -z "$TARGET" ]; then
            echo "Usage: dm-hierarchy.sh move <target>"
            exit 1
        fi
        $PYTHON_CMD "$HIERARCHY_PY" move "$TARGET"
        ;;
    tree)
        $PYTHON_CMD "$HIERARCHY_PY" tree "$@"
        ;;
    entry-config)
        NAME="$1"
        if [ -z "$NAME" ]; then
            echo "Usage: dm-hierarchy.sh entry-config <name> [--update <json>]"
            exit 1
        fi
        shift
        $PYTHON_CMD "$HIERARCHY_PY" entry-config "$NAME" "$@"
        ;;
    validate)
        $PYTHON_CMD "$HIERARCHY_PY" validate
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Run 'dm-hierarchy.sh' without args for help"
        exit 1
        ;;
esac
