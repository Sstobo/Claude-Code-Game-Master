#!/usr/bin/env bash
#
# dm-inventory.sh - Unified Inventory Manager
# Delegates to inventory-system module
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

INV="$PROJECT_ROOT/.claude/modules/inventory-system"
if [ -d "$INV" ]; then
    bash "$INV/tools/dm-inventory.sh" "$@"
else
    echo "[ERROR] inventory-system module not found at: .claude/modules/inventory-system"
    exit 1
fi
