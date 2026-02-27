#!/bin/bash
# inventory-system middleware for dm-inventory.sh
# Delegates all inventory commands to inventory-system module
# This is the ONLY handler for dm-inventory.sh (no core fallback)

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

exec bash "$MODULE_DIR/tools/dm-inventory.sh" "$@"
