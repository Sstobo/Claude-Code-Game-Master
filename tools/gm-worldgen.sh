#!/bin/bash
#
# gm-worldgen.sh - Authored-world creation: consolidate fan-out output + compile canon
#
# Usage:
#   gm-worldgen.sh consolidate [campaign]    Merge authored/*.json into campaign state
#   gm-worldgen.sh compile-canon [campaign]  Concat bible + canon/*.md -> authored-canon.md
#
# Thin wrapper over lib/world_author.py. Embedding (RAG) reuses
# `gm-extract.sh prepare <authored-canon.md> <campaign>`; bible/world validation
# reuse `lib/world_bible.py` / world-check. Run AFTER the parallel author fan-out.

set -e
source "$(dirname "$0")/common.sh"

# Loud, actionable failure for verbs that read campaign state. common.sh's
# require_active_campaign exits before we could append the "how do I fix it"
# lines, so the guidance lives here.
require_campaign() {
    if [ -z "$WORLD_STATE_DIR" ]; then
        error "No active campaign, and no campaign name given."
        echo "  Name one explicitly:  $0 <command> <campaign>" >&2
        echo "  Campaigns on disk:    bash tools/gm-campaign.sh list" >&2
        echo "  Activate one:         bash tools/gm-campaign.sh switch <name>" >&2
        echo "  Or run /gm to start a New Adventure." >&2
        exit 1
    fi
}

show_usage() {
    cat << EOF
Authored-World Generation Tool

Commands:
  consolidate [campaign]    Merge every authored/<axis>.json into the campaign's
                            locations.json / npcs.json / facts.json + world-bible.json
                            (graphs deduped, confirmed flag preserved). Serial,
                            run after the parallel author fan-out.
  compile-canon [campaign]  Concatenate the bible preamble + canon/*.md into
                            authored-canon.md, ready for:
                              bash tools/gm-extract.sh prepare <campaign>/authored-canon.md <campaign>

Add --json for structured output. Campaign defaults to the active campaign.

Examples:
  $0 consolidate
  $0 compile-canon my-world --json
EOF
}

case "$1" in
    consolidate)
        shift
        # An explicit campaign name works pre-activation; otherwise we need an active one.
        case "${1:-}" in ""|--*) require_campaign ;; esac
        $PYTHON_CMD "$LIB_DIR/world_author.py" consolidate "$@"
        ;;
    compile-canon)
        shift
        case "${1:-}" in ""|--*) require_campaign ;; esac
        $PYTHON_CMD "$LIB_DIR/world_author.py" compile-canon "$@"
        ;;
    -h|--help|help|"")
        show_usage
        ;;
    *)
        error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
