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
    list-verbose)
        uv run python - "$PROJECT_ROOT" <<'PYEOF'
import sys, json, os, glob

root = sys.argv[1]
modules_dir = os.path.join(root, ".claude", "modules")

paths = sorted(glob.glob(os.path.join(modules_dir, "*/module.json")))
for i, path in enumerate(paths, 1):
    with open(path) as f:
        d = json.load(f)

    module_json_path = path
    active_path = os.path.join(os.path.dirname(path), ".active")
    is_active = os.path.exists(active_path) or d.get("enabled_by_default", False)

    status = "✅ Active" if is_active else "❌ Inactive"
    default_note = "  ← on by default" if d.get("enabled_by_default") else ""
    tags = ", ".join(d.get("genre_tags", []))
    cases = " / ".join(d.get("use_cases", [])[:3])

    print(f"  [{i}] {status}  {d['id']}")
    print(f"      {d['name']}")
    print(f"      {d['description']}")
    print(f"      Genres: {tags}")
    print(f"      Use cases: {cases}")
    if default_note:
        print(f"     {default_note}")
    print()
PYEOF
        ;;
    *)
        uv run python lib/module_loader.py "$@"
        ;;
esac
