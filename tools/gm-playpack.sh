#!/bin/bash
# gm-playpack.sh — primer, one room, one name from the book
# The campaign file is a journal. The book is the binder.

source "$(dirname "$0")/common.sh"

show_usage() {
    echo "Usage: gm-playpack.sh <action> [args]"
    echo ""
    echo "  set --json '{...}'     Write play_pack fields on the overview"
    echo "  show                   Print the pack + PRIMER block"
    echo "  stage                  Persist room / exits / present NPCs"
    echo "  from-book <name>       Persist exactly one name from the book"
    echo "      --kind npc|location|auto"
    echo "      --description \"...\"   (else RAG blurb)"
    echo ""
    echo "Play pack fields: whose_story, room, present, exits, hook, offstage, primer"
}

require_active_campaign

if [ -z "$1" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

CAMPAIGN_DIR=$(bash tools/gm-campaign.sh path)
$PYTHON_CMD "$LIB_DIR/play_pack.py" "$CAMPAIGN_DIR" "$@"
