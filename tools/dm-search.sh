#!/bin/bash
# dm-search.sh - Unified search across world state and RAG vectors

source "$(dirname "$0")/common.sh"

show_usage() {
    cat << EOF
Search Tool - Query world state and source material

Usage:
  dm-search.sh <query> [options]

Options:
  --rag              Include RAG vector results (default if vectors exist)
  --world-only       Search world state only, skip RAG
  --rag-only         Search RAG vectors only, skip world state
  --full             Show full text for world and RAG results
  -n <count>         Number of RAG results (default: 4)
  --tag-location <t> Search NPCs by location tag
  --tag-quest <t>    Search NPCs by quest tag

Examples:
  dm-search.sh "dragon"                   # Search both world + RAG
  dm-search.sh "dragon" --world-only      # World state only
  dm-search.sh "dragon" --rag-only -n 20  # RAG only, 20 results
  dm-search.sh "dragon" --full            # Full untruncated output
  dm-search.sh --tag-location "Thornhaven"

Searches across: NPCs, locations, facts, consequences, plots, and source material.
EOF
}

# Parse arguments
QUERY=""
RAG_ONLY=false
WORLD_ONLY=false
RAG_COUNT=4
FULL_OUTPUT=false
TAG_SEARCH=false
TAG_TYPE=""
TAG_VALUE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --rag)
            shift
            ;;
        --world-only)
            WORLD_ONLY=true
            shift
            ;;
        --rag-only)
            RAG_ONLY=true
            shift
            ;;
        --full)
            FULL_OUTPUT=true
            shift
            ;;
        -n)
            RAG_COUNT="$2"
            shift 2
            ;;
        --tag-location)
            TAG_SEARCH=true
            TAG_TYPE="--tag-location"
            TAG_VALUE="$2"
            shift 2
            ;;
        --tag-quest)
            TAG_SEARCH=true
            TAG_TYPE="--tag-quest"
            TAG_VALUE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            if [ -z "$QUERY" ]; then
                QUERY="$1"
            fi
            shift
            ;;
    esac
done

require_active_campaign

# Validate input
if [ -z "$QUERY" ] && [ "$TAG_SEARCH" = false ]; then
    show_usage
    exit 1
fi

# Handle tag searches (world-only by nature)
if [ "$TAG_SEARCH" = true ]; then
    echo "Searching World State"
    echo "====================="
    WORLD_OUTPUT=$($PYTHON_CMD "$LIB_DIR/search.py" "$TAG_TYPE" "$TAG_VALUE" $([ "$FULL_OUTPUT" = true ] && echo "--full"))
    WORLD_STATUS=$?
    echo "$WORLD_OUTPUT"
    WORLD_CHARS=${#WORLD_OUTPUT}
    WORLD_TOKENS=$(estimate_tokens_from_chars "$WORLD_CHARS")
    log_token_usage "dm-search" "mode=tag" "query_chars=${#TAG_VALUE}" "world_chars=$WORLD_CHARS" "world_tokens_est=$WORLD_TOKENS" "rag_chars=0" "rag_tokens_est=0"
    exit $WORLD_STATUS
fi

# Get campaign directory
CAMPAIGN_DIR=$(bash "$TOOLS_DIR/dm-campaign.sh" path 2>/dev/null)

# Search world state (unless RAG-only)
if [ "$RAG_ONLY" = false ]; then
    echo "Searching World State"
    echo "====================="
    WORLD_OUTPUT=$($PYTHON_CMD "$LIB_DIR/search.py" "$QUERY" $([ "$FULL_OUTPUT" = true ] && echo "--full"))
    WORLD_STATUS=$?
    echo "$WORLD_OUTPUT"
    WORLD_CHARS=${#WORLD_OUTPUT}
else
    WORLD_OUTPUT=""
    WORLD_STATUS=0
    WORLD_CHARS=0
fi

# Search RAG (unless world-only)
RAG_OUTPUT=""
RAG_STATUS=0
RAG_CHARS=0
if [ "$WORLD_ONLY" = false ]; then
    if [ -d "$CAMPAIGN_DIR/vectors" ]; then
        echo ""
        echo "Source Material Matches"
        echo "======================="
        RAG_OUTPUT=$($PYTHON_CMD "$LIB_DIR/entity_enhancer.py" search "$QUERY" -n "$RAG_COUNT" $([ "$FULL_OUTPUT" = true ] && echo "--full"))
        RAG_STATUS=$?
        echo "$RAG_OUTPUT"
        RAG_CHARS=${#RAG_OUTPUT}
    elif [ "$RAG_ONLY" = true ]; then
        echo "No vector store found for this campaign."
        echo "Import a document with /import to enable RAG search."
        exit 1
    fi
fi

WORLD_TOKENS=$(estimate_tokens_from_chars "$WORLD_CHARS")
RAG_TOKENS=$(estimate_tokens_from_chars "$RAG_CHARS")
QUERY_TOKENS=$(estimate_tokens_from_chars "${#QUERY}")
MODE="hybrid"
if [ "$RAG_ONLY" = true ]; then
    MODE="rag-only"
elif [ "$WORLD_ONLY" = true ]; then
    MODE="world-only"
fi
log_token_usage "dm-search" "mode=$MODE" "full=$FULL_OUTPUT" "query_chars=${#QUERY}" "query_tokens_est=$QUERY_TOKENS" "world_chars=$WORLD_CHARS" "world_tokens_est=$WORLD_TOKENS" "rag_chars=$RAG_CHARS" "rag_tokens_est=$RAG_TOKENS" "rag_n=$RAG_COUNT"

if [ $WORLD_STATUS -ne 0 ]; then
    exit $WORLD_STATUS
fi
if [ $RAG_STATUS -ne 0 ]; then
    exit $RAG_STATUS
fi
