#!/bin/bash
# dm-context.sh - Unified scene context (one front door for search/enhance/scene)
#
# Usage:
#   dm-context.sh                          Context for the current location
#   dm-context.sh "Over City Village"      Context for a specific location
#   dm-context.sh "Warehouse" --entity "Mordecai" --entity "Katia"
#   dm-context.sh --json                   Structured JSON envelope
#
# Returns world-state facts (location, NPCs present, named entities) plus grounded
# source passages from RAG when the campaign has a vector store.

source "$(dirname "$0")/common.sh"

require_active_campaign

$PYTHON_CMD "$LIB_DIR/scene_context.py" "$@"
