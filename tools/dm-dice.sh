#!/usr/bin/env bash
#
# Dice rolling tool for D&D
# Wraps lib/dice.py for CLI usage
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source common utilities
source "$SCRIPT_DIR/common.sh"

# Show usage
show_usage() {
    cat <<EOF
Usage: dm-dice.sh <command> [options]

Commands:
  roll <notation>     Roll dice (e.g., 1d20, 3d6+2, 2d20kh1)
  help               Show this help message

Dice Notation:
  NdS+M    Roll N dice of S sides, add modifier M
  2d20kh1  Roll 2d20, keep highest (advantage)
  2d20kl1  Roll 2d20, keep lowest (disadvantage)

Examples:
  dm-dice.sh roll 1d20+5      # Attack roll with +5 modifier
  dm-dice.sh roll 2d6+3       # Damage roll
  dm-dice.sh roll 2d20kh1     # Attack with advantage
  dm-dice.sh roll 4d6         # Fireball damage
EOF
}

# Roll dice
cmd_roll() {
    local notation="${1:-}"

    if [[ -z "$notation" ]]; then
        error "Usage: dm-dice.sh roll <notation>"
        exit 1
    fi

    # Call Python dice module
    uv run python "$PROJECT_ROOT/lib/dice.py" "$notation"
}

# Main dispatch
case "${1:-}" in
    roll)
        shift
        cmd_roll "$@"
        ;;
    help|--help|-h)
        show_usage
        exit 0
        ;;
    *)
        error "Unknown command: ${1:-}"
        show_usage
        exit 1
        ;;
esac
