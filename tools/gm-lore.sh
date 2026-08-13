#!/bin/bash
# gm-lore.sh - Grounded scene brief from the source book (Loremaster)
#
#   gm-lore.sh "The Sunken Crypt"              Chapter pointers + excerpt (cached per location)
#   gm-lore.sh "The Sunken Crypt" --full       ...plus the ENTIRE chapter span (long-context read)
#   gm-lore.sh "The Sunken Crypt" --important  Force a fresh deep read on a big beat
#
# Finds the relevant CHAPTER via the coarse index, returns pointers + a grounded
# excerpt. Cached per location — routine revisits are free. Needs the retained
# book text (current-document.txt) in the campaign dir; without it, chapters
# come back empty. Accepts --json.

source "$(dirname "$0")/common.sh"

require_active_campaign

$PYTHON_CMD "$LIB_DIR/loremaster.py" "$@"
