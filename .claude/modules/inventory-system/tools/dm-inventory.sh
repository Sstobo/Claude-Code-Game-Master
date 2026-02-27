#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$MODULE_ROOT/../../.." && pwd)"
cd "$PROJECT_ROOT"
uv run python "$MODULE_ROOT/lib/inventory_manager.py" "$@"
