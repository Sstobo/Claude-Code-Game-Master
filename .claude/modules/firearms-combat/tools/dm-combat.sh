#!/usr/bin/env bash
#
# dm-combat.sh - Firearms Combat Resolver
# Automated combat resolution for modern/STALKER campaigns
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$MODULE_ROOT/../../.." && pwd)"

cd "$PROJECT_ROOT"

uv run python "$MODULE_ROOT/lib/firearms_resolver.py" "$@"
