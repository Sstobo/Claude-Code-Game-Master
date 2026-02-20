#!/usr/bin/env bash
# Outputs creation-rules.md from all active modules.
# Used by /new-game to load module-specific world-building instructions.
# Only includes modules that have a creation-rules.md file.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ACTIVE=$(cat "$PROJECT_ROOT/world-state/active-campaign.txt" 2>/dev/null || echo "")
[ -z "$ACTIVE" ] && exit 0

OVERVIEW="$PROJECT_ROOT/world-state/campaigns/$ACTIVE/campaign-overview.json"
[ -f "$OVERVIEW" ] || exit 0

uv run python - "$PROJECT_ROOT" "$OVERVIEW" << 'PYEOF'
import json, sys, os

project_root = sys.argv[1]
overview_path = sys.argv[2]

with open(overview_path) as f:
    d = json.load(f)

mods = d.get('modules', {})
enabled = [k for k, v in mods.items() if v]

found = []
for mod in enabled:
    rules_path = f"{project_root}/.claude/modules/{mod}/creation-rules.md"
    if not os.path.exists(rules_path):
        continue
    with open(rules_path) as f:
        content = f.read()
    found.append((mod, content))

if not found:
    sys.exit(0)

print("# MODULE CREATION RULES\n")
print("The following active modules have world-building instructions.")
print("Follow them during the corresponding phases of /new-game.\n")

for mod_id, content in found:
    print(f"\n---\n## MODULE: {mod_id}\n")
    print(content)

PYEOF
