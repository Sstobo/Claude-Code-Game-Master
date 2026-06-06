#!/bin/bash
# dm-recall.sh - Long-term campaign memory
#
#   dm-recall.sh recall "have we met Remex before?"   # surface relevant prior events
#   dm-recall.sh recall "dragon" --provenance our-story
#   dm-recall.sh memoir                                # tiered arc summary + recent
#   dm-recall.sh refresh                               # rebuild the memory index (auto on save)

source "$(dirname "$0")/common.sh"

require_active_campaign

$PYTHON_CMD "$LIB_DIR/campaign_memory.py" "$@"
