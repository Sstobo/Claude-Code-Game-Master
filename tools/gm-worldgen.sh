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

# These verbs run during world creation, before the campaign is activated, so an
# explicitly named campaign is enough — it may sit anywhere among the flags.
# Only a call with no name at all needs an active campaign.
require_campaign_unless_named() {
    local arg
    for arg in "$@"; do
        case "$arg" in
            ""|--*) ;;
            *) return 0 ;;
        esac
    done
    # This is the one wrapper where naming a campaign is itself a fix, so the
    # shared guard's repair list gets a third entry. It runs in a subshell
    # because require_active_campaign exits — the subshell absorbs that, leaving
    # the hint under the other two lines instead of dangling above the headline.
    if ! ( require_active_campaign ); then
        echo "  Or name it here:    bash tools/gm-worldgen.sh <command> <campaign>" >&2
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
        require_campaign_unless_named "$@"
        $PYTHON_CMD "$LIB_DIR/world_author.py" consolidate "$@"
        ;;
    compile-canon)
        shift
        require_campaign_unless_named "$@"
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
