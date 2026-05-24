#!/usr/bin/env bash
# Audit lib/ for residual 5E vocabulary. NOT a strict gate — output may include
# false positives in docstrings or comments. Curate and act as needed.
#
# Run: bash tools/audit-lib-purity.sh

set -u

PATTERN='(PARTY_MEMBER_DEFAULTS|XP_THRESHOLDS|charmed|frightened|acrobatics|lawful good|bludgeoning)'

# Case-sensitive, .py only, strip comment-only lines so noise is reduced.
matches=$(grep -rnE --include="*.py" "$PATTERN" lib/ 2>/dev/null | grep -v "^[^:]*:[[:space:]]*#" || true)

if [ -n "$matches" ]; then
    echo "=== lib-purity audit: matches found ==="
    echo "$matches"
    echo ""
    echo "Review each — docstrings and example comments are accepted."
    exit 0   # advisory, not a hard fail
fi

echo "lib-purity audit: clean (no 5E vocab in lib/ .py code)"
