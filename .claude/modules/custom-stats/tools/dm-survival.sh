#!/usr/bin/env bash
#
# dm-survival.sh - Survival Stats Module
# Apply time effects to custom stats, check stat consequences, manage custom stats, advance time
#
# Usage:
#   bash .claude/modules/survival-stats/tools/dm-survival.sh tick --elapsed 2
#   bash .claude/modules/survival-stats/tools/dm-survival.sh tick --elapsed 8 --sleeping
#   bash .claude/modules/survival-stats/tools/dm-survival.sh status
#   bash .claude/modules/survival-stats/tools/dm-survival.sh custom-stat hunger
#   bash .claude/modules/survival-stats/tools/dm-survival.sh custom-stat hunger +10
#   bash .claude/modules/survival-stats/tools/dm-survival.sh custom-stat "Меченый" thirst -5
#   bash .claude/modules/survival-stats/tools/dm-survival.sh custom-stats-list
#   bash .claude/modules/survival-stats/tools/dm-survival.sh custom-stats-list "Меченый"
#   bash .claude/modules/survival-stats/tools/dm-survival.sh time "Evening" "3rd day" --elapsed 4
#   bash .claude/modules/survival-stats/tools/dm-survival.sh time "Noon" "3rd day" --precise-time "12:30"
#   bash .claude/modules/survival-stats/tools/dm-survival.sh time "Morning" "4th day" --elapsed 8 --sleeping
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

cd "$PROJECT_ROOT"

uv run python .claude/modules/custom-stats/lib/survival_engine.py "$@"
