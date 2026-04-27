#!/bin/bash
# npc-enhancements middleware for dm-npc.sh
# Handles: relate, unrelate, relations, tag-faction, untag-faction, list-factions, faction-members

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$MODULE_DIR/../../.." && pwd)"

# Set PYTHONPATH so module libs can import campaign_manager, etc.
export PYTHONPATH="$PROJECT_ROOT/lib${PYTHONPATH:+:$PYTHONPATH}"

if [ "$1" = "--help" ]; then
    echo ""
    echo "=== NPC Relationships ==="
    echo "  relate <a> <b> <type> [notes]        Set bidirectional relationship"
    echo "  unrelate <a> <b>                      Remove relationship"
    echo "  relations <name>                      Show all relationships for an NPC"
    echo ""
    echo "=== Factions ==="
    echo "  tag-faction <name> <faction> [more...]  Add faction tags to NPC"
    echo "  untag-faction <name> <faction> [more...] Remove faction tags from NPC"
    echo "  list-factions                          List all known factions"
    echo "  faction-members <faction>              List all NPCs in a faction"
    exit 1
fi

ACTION="$1"
shift

case "$ACTION" in
    relate)
        if [ "$#" -lt 3 ]; then
            echo "Usage: dm-npc.sh relate <npc_a> <npc_b> <type> [notes]"
            echo "Types: ally, enemy, contact, rival, family, mentor, protege, subordinate, superior, acquaintance"
            exit 0
        fi
        NOTES="${4:-}"
        uv run python "$MODULE_DIR/lib/npc_relationships.py" set "$1" "$2" "$3" "$NOTES"
        exit 0
        ;;

    unrelate)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-npc.sh unrelate <npc_a> <npc_b>"
            exit 0
        fi
        uv run python "$MODULE_DIR/lib/npc_relationships.py" remove "$1" "$2"
        exit 0
        ;;

    relations)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-npc.sh relations <name>"
            exit 0
        fi
        uv run python "$MODULE_DIR/lib/npc_relationships.py" format "$1"
        exit 0
        ;;

    tag-faction)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-npc.sh tag-faction <name> <faction1> [faction2 ...]"
            exit 0
        fi
        uv run python "$MODULE_DIR/lib/npc_factions.py" tag "$1" "${@:2}"
        exit 0
        ;;

    untag-faction)
        if [ "$#" -lt 2 ]; then
            echo "Usage: dm-npc.sh untag-faction <name> <faction1> [faction2 ...]"
            exit 0
        fi
        uv run python "$MODULE_DIR/lib/npc_factions.py" untag "$1" "${@:2}"
        exit 0
        ;;

    list-factions)
        uv run python "$MODULE_DIR/lib/npc_factions.py" list
        exit 0
        ;;

    faction-members)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-npc.sh faction-members <faction>"
            exit 0
        fi
        uv run python "$MODULE_DIR/lib/npc_factions.py" members "$1"
        exit 0
        ;;
esac

exit 1
