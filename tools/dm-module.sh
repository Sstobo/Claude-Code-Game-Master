#!/usr/bin/env bash
#
# dm-module.sh - Module Management
# List, scan, and manage DM System modules
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

ACTION="${1:-}"

case "$ACTION" in
    activate)
        MODULE="${2:-}"
        if [ -z "$MODULE" ]; then
            echo "Usage: dm-module.sh activate <module-id>"
            exit 1
        fi
        uv run python lib/module_loader.py activate --module "$MODULE"
        ;;
    deactivate)
        MODULE="${2:-}"
        if [ -z "$MODULE" ]; then
            echo "Usage: dm-module.sh deactivate <module-id>"
            exit 1
        fi
        uv run python lib/module_loader.py deactivate --module "$MODULE"
        ;;
    *)
        uv run python lib/module_loader.py "$@"
        ;;
esac
