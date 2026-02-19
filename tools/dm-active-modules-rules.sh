#!/usr/bin/env bash
# Читает modules из campaign-overview.json активной кампании
# и выводит rules.md только для включённых модулей

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ACTIVE=$(cat "$PROJECT_ROOT/world-state/active-campaign.txt" 2>/dev/null || echo "")
[ -z "$ACTIVE" ] && exit 0

OVERVIEW="$PROJECT_ROOT/world-state/campaigns/$ACTIVE/campaign-overview.json"
[ -f "$OVERVIEW" ] || exit 0

MODULES=$(uv run python -c "
import json, sys
with open('$OVERVIEW') as f:
    d = json.load(f)
mods = d.get('modules', {})
enabled = [k for k, v in mods.items() if v]
print(' '.join(enabled))
" 2>/dev/null)

for mod in $MODULES; do
    f="$PROJECT_ROOT/.claude/modules/$mod/rules.md"
    [ -f "$f" ] || continue
    echo ""
    echo "---"
    echo "# MODULE RULES: $mod"
    cat "$f"
done
