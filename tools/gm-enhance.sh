#!/bin/bash
# gm-enhance.sh - Entity enhancement using RAG
# Queries the vector store for passages about an entity and applies enhancements

source "$(dirname "$0")/common.sh"

show_usage() {
    echo "Usage: gm-enhance.sh <command> [args]"
    echo ""
    echo "Commands:"
    echo "  find <name>              Find entity across all types"
    echo "  query <name>             Get RAG passages for entity"
    echo "  apply <name>             Apply enhancements (after approval)"
    echo "  summary <name>           Get full enhancement summary"
    echo "  list-unenhanced [type]   List entities needing enhancement"
    echo "  batch                    Enhance all unenhanced ACTIVE entities (background tier
                           skipped; enhance on promote). Run after /import"
    echo "  dungeon-check <name>     Check if dungeon has room structure"
    echo "  scene <location>         Get scene context for gameplay (quick RAG)"
    echo ""
    echo "Options:"
    echo "  --type <type>            Entity type: npc, location, item, plot"
    echo "  --context <text>         Context passage to add (can be repeated)"
    echo "  --description <text>     New description to set"
    echo "  -n, --num <count>        Max results (default: 10)"
    echo ""
    echo "Examples:"
    echo "  gm-enhance.sh find \"Grimjaw\""
    echo "  gm-enhance.sh query \"The Rusty Blade Inn\" --type location"
    echo "  gm-enhance.sh dungeon-check \"Goblin Caves\""
    echo "  gm-enhance.sh scene \"Thunder River frontier\""
    echo ""
    echo "Workflow:"
    echo "  1. Use 'find' to locate a specific entity"
    echo "  2. Use 'query' for entity-specific passages"
    echo "  3. Use 'apply' with --context to add passages"
    echo ""
    echo "For direct RAG search, use: gm-search.sh --rag-only <query>"
    echo ""
    echo "Note: Requires a populated vector store (run /import first)"
}

if [ $# -lt 1 ]; then
    show_usage
    exit 1
fi

COMMAND="$1"
shift

# Every command below queries campaign state; only help runs without a campaign.
case "$COMMAND" in
    help|--help|-h) ;;
    *) require_active_campaign ;;
esac

case "$COMMAND" in
    find)
        if [ $# -lt 1 ]; then
            echo "Usage: gm-enhance.sh find <name>"
            exit 1
        fi
        echo "Finding Entity"
        echo "=============="
        $PYTHON_CMD "$LIB_DIR/entity_enhancer.py" find "$@"
        ;;

    query)
        if [ $# -lt 1 ]; then
            echo "Usage: gm-enhance.sh query <name> [--type type] [-n count]"
            exit 1
        fi
        echo "Querying Source Passages"
        echo "========================"
        $PYTHON_CMD "$LIB_DIR/entity_enhancer.py" query "$@"
        ;;

    apply)
        if [ $# -lt 1 ]; then
            echo "Usage: gm-enhance.sh apply <name> --context <text> [--description <text>]"
            exit 1
        fi
        echo "Applying Enhancements"
        echo "====================="
        $PYTHON_CMD "$LIB_DIR/entity_enhancer.py" apply "$@"
        ;;

    summary)
        if [ $# -lt 1 ]; then
            echo "Usage: gm-enhance.sh summary <name>"
            exit 1
        fi
        echo "Enhancement Summary"
        echo "==================="
        $PYTHON_CMD "$LIB_DIR/entity_enhancer.py" summary "$@"
        ;;

    list-unenhanced|list)
        echo "Unenhanced Entities"
        echo "==================="
        $PYTHON_CMD "$LIB_DIR/entity_enhancer.py" list-unenhanced "$@"
        ;;

    dungeon-check)
        if [ $# -lt 1 ]; then
            echo "Usage: gm-enhance.sh dungeon-check <dungeon-name>"
            exit 1
        fi
        echo "Dungeon Structure Check"
        echo "======================="
        $PYTHON_CMD "$LIB_DIR/entity_enhancer.py" dungeon-check "$@"
        ;;

    scene)
        if [ $# -lt 1 ]; then
            echo "Usage: gm-enhance.sh scene <location>"
            exit 1
        fi
        # Route to Python for GM-internal context (minimal output, auto-enhance)
        # Use "$@" to preserve argument boundaries for multi-word location names
        $PYTHON_CMD "$LIB_DIR/entity_enhancer.py" scene "$@"
        ;;

    batch)
        # Call Python batch directly for proper handling
        $PYTHON_CMD "$LIB_DIR/entity_enhancer.py" batch "$@"
        ;;

    help|--help|-h)
        show_usage
        ;;

    *)
        echo "Unknown command: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac
