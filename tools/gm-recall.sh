#!/bin/bash
# gm-recall.sh - Long-term campaign memory
#
#   gm-recall.sh recall "have we met Remex before?"   # semantic when RAG deps present, keyword fallback
#   gm-recall.sh recall "dragon" --top-k 8            # default top-k is 5
#   gm-recall.sh recall "dragon" --provenance our-story
#   gm-recall.sh arc '{"summary": "...", "who_matters": [...], "open_debts": [...]}'
#                                                      # REQUIRED at session end — long-term memory
#   gm-recall.sh memoir                                # arc entries + recent verbatim
#   gm-recall.sh refresh                               # rebuild the memory index (auto on save)

source "$(dirname "$0")/common.sh"

require_active_campaign

$PYTHON_CMD "$LIB_DIR/campaign_memory.py" "$@"
