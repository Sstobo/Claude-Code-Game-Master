#!/bin/bash
#
# gm-extract.sh - Concurrent agent extraction workflow for D&D modules
#
# Usage:
#   gm-extract.sh prepare <document> [campaign-name] - Prepare document for extraction
#   gm-extract.sh merge [campaign-name] [--cleanup]  - Merge results from agents
#   gm-extract.sh save [strategy] [campaign-name]    - Save to world state
#   gm-extract.sh review [campaign-name]             - Review extracted content
#   gm-extract.sh list                               - List all campaign extractions
#   gm-extract.sh clean [campaign-name]              - Clean extraction directory

set -e
source "$(dirname "$0")/common.sh"

# Base directories - use WORLD_STATE_BASE not WORLD_STATE_DIR (which is campaign-specific)
CAMPAIGNS_DIR="$WORLD_STATE_BASE/campaigns"
EXTRACT_DIR="$WORLD_STATE_BASE/extraction-temp"  # Default if no campaign specified

# The campaign a verb operates on: the explicit argument, else the active one.
# A raw `cat active-campaign.txt` used to stand at every call site — under this
# file's `set -e` a missing file made cat return 1 and killed the script with
# zero output, so on a fresh install every verb looked like a silent no-op.
# get_active_campaign (common.sh) always exits 0 and echoes empty when there is
# no campaign, which turns that case into a message.
require_campaign() {
    local campaign_name="$1"
    local verb="$2"
    if [ -z "$campaign_name" ]; then
        campaign_name=$(get_active_campaign)
    fi
    if [ -z "$campaign_name" ]; then
        echo "Error: No campaign specified and no active campaign found." >&2
        echo "  Name one: bash tools/gm-extract.sh $verb <campaign-name>" >&2
        echo "  Or activate one: bash tools/gm-campaign.sh switch <campaign-name> (or run /gm)" >&2
        return 1
    fi
    printf '%s' "$campaign_name"
}

# Directory of an EXISTING campaign. Display names, current slugs and folders
# written under the older slug rule (curse_of_strahd) all resolve through
# lib/campaign_manager.py, which looks at what is actually on disk; re-slugifying
# here would miss the legacy ones and report a real campaign as not found.
# Returns 3 for "no such campaign" and 1 for "the helper could not run at all",
# so `clean` can stay idempotent about the first without swallowing the second.
campaign_dir() {
    local resolved rc=0
    # A campaign is a folder NAME, never a path. "../rag" names a real directory
    # outside campaigns/, and clean would rm -rf it. Refuse loudly here — this is
    # a caller mistake, not "no such campaign".
    case "$1" in
        */*|.|..)
            echo "Error: a campaign is a folder name, not a path: $1" >&2
            return 1
            ;;
    esac
    resolved=$($PYTHON_CMD "$LIB_DIR/campaign_manager.py" resolve "$1" --world-state "$WORLD_STATE_BASE") || rc=$?
    # A non-zero exit is a failure even when something reached stdout: trusting
    # stdout alone would hand back a path built from whatever junk a broken
    # interpreter printed, and clean_temp would rm -rf it. An empty result is
    # just as fatal — joined onto CAMPAIGNS_DIR it resolves to the campaigns
    # ROOT, i.e. every campaign. Refuse rather than guess.
    if [ "$rc" -ne 0 ] || [ -z "$resolved" ]; then
        if [ "$rc" -eq 3 ]; then
            echo "Campaign directory not found for: $1" >&2
            echo "  See what exists: bash tools/gm-campaign.sh list" >&2
            return 3
        fi
        echo "Error: could not derive a campaign slug from: $1" >&2
        echo "  ($PYTHON_CMD could not run lib/campaign_manager.py — run /setup if the venv is missing)" >&2
        return 1
    fi
    printf '%s/%s' "$CAMPAIGNS_DIR" "$resolved"
}

show_usage() {
    cat << EOF
D&D Module Extraction Tool

Commands:
  prepare <file> [name]     Extract text and create chunks for agent processing
                            Optional: specify campaign name (defaults to filename)
  normalize [campaign]      Copy extracted/*.json to campaign root, unwrapping
                            agent wrapper keys into the flat {name:...} runtime shape
  cap [campaign] [limit]    Tier each type: top-N (default 30) by importance stay
                            active, the rest are marked background:true. Nothing
                            is deleted (mention-frequency + plot-reference/party boost)
  stub-npcs [campaign]      Stub plot NPCs the source names but extraction never
                            produced; validate plot taxonomy (before the integrity gate)
  stat-npcs [campaign]      Difficulty-proxy stats for combat NPCs; flag statless
  fix-items [campaign]      Item correctness: cursed flag, type taxonomy, value field
  normalize-connections [campaign]  Canonicalize connection targets; move routing
                            rule-phrases into notes (runs before reconcile)
  reconcile [campaign]      Stub every location ref that doesn't resolve to a node
                            (low_confidence:true); only routing rule-prose is dropped,
                            and that is recorded as a fact (before the integrity gate)
  spine [campaign]          Derive plot arc (sequence + depends_on + through-line)
  seed-clocks [campaign]    Seed threat clocks from headline time-pressure in plots
  seed-opening [campaign]   Set starting position + opening beat from the spine
  integrity [campaign] [--no-strict]  Canonicalize cross-refs to real keys;
                            fail on unresolved (strict by default)
  merge [campaign] [--cleanup]  Combine results from all extraction agents
                            --cleanup: Archive extracted/ folder after merge
  save [strategy] [campaign] Save extracted content to world state
                            Strategies: rename (default), skip, overwrite
  review [campaign]         Review extracted content before saving
  list                      List all campaign extractions
  clean [campaign]          Clear extraction directory
  archive [campaign]        Archive extracted/ folder after merge
  validate [campaign]       Gate the extraction output: exits non-zero (naming the
                            type and the reason) when a file is missing, is invalid
                            JSON, or npcs/locations came back empty. Empty
                            items/plots only warn. Run BEFORE normalize.

Examples:
  $0 prepare "curse_of_strahd.pdf"
  $0 prepare "module.pdf" "temple-of-evil"
  $0 merge "curse-of-strahd"
  $0 review "curse-of-strahd"
  $0 save rename "curse-of-strahd"
  $0 list

Files:
  Input:  PDFs, Word docs, Markdown files
  Output: NPCs and locations added to world state
  Campaigns: $CAMPAIGNS_DIR/<campaign-name>/

Each campaign extraction is stored in its own folder for organization.

EOF
}

prepare_document() {
    local document="$1"
    local campaign_name="$2"

    if [ -z "$document" ]; then
        echo "Error: Document path required"
        show_usage
        exit 1
    fi

    if [ ! -f "$document" ]; then
        echo "Error: File not found: $document"
        exit 1
    fi

    # Check for RAG dependencies (sentence-transformers, chromadb)
    if ! $PYTHON_CMD -c "import sentence_transformers; import chromadb" 2>/dev/null; then
        echo "Error: RAG dependencies not installed."
        echo ""
        echo "Install with: uv pip install 'gm-claude[rag]'"
        echo "  or: uv pip install sentence-transformers chromadb"
        exit 1
    fi

    echo "Preparing document for extraction: $document"

    # Build command with optional campaign name
    if [ -n "$campaign_name" ]; then
        echo "Campaign name: $campaign_name"
        $PYTHON_CMD "$LIB_DIR/agent_extractor.py" prepare "$document" --campaign "$campaign_name"
    else
        $PYTHON_CMD "$LIB_DIR/agent_extractor.py" prepare "$document"
    fi

    echo
    echo "Document prepared for extraction."
    echo
    echo "Next steps:"
    echo "1. Launch extraction agents to process chunks"
    echo "2. Run: $0 merge [campaign-name]"
    echo "3. Run: $0 review [campaign-name]"
    echo "4. Run: $0 save [strategy] [campaign-name]"
}

merge_results() {
    local campaign_name="$1"
    local cleanup="$2"

    echo "Merging extraction results from all agents..."

    # Build command with optional campaign name
    if [ -n "$campaign_name" ]; then
        echo "Campaign: $campaign_name"
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || { list_campaigns; exit 1; }

        # Check for agent results
        if [ ! -d "$CAMPAIGN_DIR/extracted" ] || [ -z "$(ls -A $CAMPAIGN_DIR/extracted 2>/dev/null)" ]; then
            echo "Error: No agent results found in $CAMPAIGN_DIR/extracted/"
            echo "Make sure extraction agents have completed their work."
            exit 1
        fi

        $PYTHON_CMD "$LIB_DIR/agent_extractor.py" merge --campaign "$campaign_name"
    else
        # Check default location
        if [ ! -d "$EXTRACT_DIR/extracted" ] || [ -z "$(ls -A $EXTRACT_DIR/extracted 2>/dev/null)" ]; then
            echo "Error: No agent results found in $EXTRACT_DIR/extracted/"
            echo "Specify a campaign name or check that agents have completed."
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/agent_extractor.py" merge
    fi

    echo
    echo "Results merged successfully."

    # Auto-cleanup if --cleanup flag was passed
    if [ "$cleanup" = "--cleanup" ]; then
        echo
        archive_extracted "$campaign_name"
    else
        echo
        echo "Run '$0 review [campaign-name]' to review content before saving."
        echo "(Optional: '$0 archive [campaign-name]' to archive extracted/ folder)"
    fi
}

save_to_world() {
    local strategy="${1:-rename}"
    local campaign_name="$2"

    echo "Saving extracted content to world state..."
    echo "Conflict strategy: $strategy"

    # Build command with optional campaign name
    if [ -n "$campaign_name" ]; then
        echo "Campaign: $campaign_name"
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1

        if [ ! -f "$CAMPAIGN_DIR/merged-results.json" ]; then
            echo "Error: No merged results found for campaign: $campaign_name"
            echo "Run '$0 merge $campaign_name' first."
            exit 1
        fi

        $PYTHON_CMD "$LIB_DIR/agent_extractor.py" save "$strategy" --campaign "$campaign_name"
    else
        if [ ! -f "$EXTRACT_DIR/merged-results.json" ]; then
            echo "Error: No merged results found."
            echo "Run '$0 merge' first."
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/agent_extractor.py" save "$strategy"
    fi

    echo
    echo "Content saved to world state."
    echo "Check the active campaign's npcs.json and locations.json files"
}

review_content() {
    local campaign_name="$1"

    echo "Reviewing extracted content..."

    # Build command with optional campaign name
    if [ -n "$campaign_name" ]; then
        echo "Campaign: $campaign_name"
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1

        if [ ! -f "$CAMPAIGN_DIR/merged-results.json" ]; then
            echo "Error: No merged results to review for campaign: $campaign_name"
            echo "Run '$0 merge $campaign_name' first."
            exit 1
        fi

        $PYTHON_CMD "$LIB_DIR/agent_extractor.py" review --campaign "$campaign_name"

        echo
        echo "To view full details:"
        echo "  cat $CAMPAIGN_DIR/merged-results.json | jq '.npcs | keys'"
        echo "  cat $CAMPAIGN_DIR/merged-results.json | jq '.locations | keys'"
    else
        if [ ! -f "$EXTRACT_DIR/merged-results.json" ]; then
            echo "Error: No merged results to review."
            echo "Run '$0 merge' first."
            exit 1
        fi

        $PYTHON_CMD "$LIB_DIR/agent_extractor.py" review

        echo
        echo "To view full details:"
        echo "  cat $EXTRACT_DIR/merged-results.json | jq '.npcs | keys'"
        echo "  cat $EXTRACT_DIR/merged-results.json | jq '.locations | keys'"
    fi
}

clean_temp() {
    local campaign_name="$1"

    if [ -n "$campaign_name" ]; then
        echo "Cleaning campaign extraction directory: $campaign_name"
        local rc=0
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || rc=$?
        # Cleaning is idempotent: nothing left to remove is the job already done,
        # so a campaign that isn't there (rc 3) exits 0. A helper that could not
        # run (rc 1) is NOT that case — it means we don't know, so it still fails.
        if [ "$rc" -eq 3 ]; then
            exit 0
        elif [ "$rc" -ne 0 ]; then
            exit 1
        fi

        # Last line of defense before an rm -rf: the target's REAL path must be a
        # direct child of the real campaigns dir — never the root itself, never
        # outside the tree. A string compare passed "campaigns/../rag" straight
        # through, so this resolves both sides before comparing.
        local real_target real_campaigns
        real_target=$(cd "$CAMPAIGN_DIR" 2>/dev/null && pwd -P) || real_target=""
        real_campaigns=$(cd "$CAMPAIGNS_DIR" && pwd -P)
        if [ -z "$real_target" ] || [ "$(dirname "$real_target")" != "$real_campaigns" ]; then
            echo "Error: refusing to clean a path outside $CAMPAIGNS_DIR: $CAMPAIGN_DIR" >&2
            exit 1
        fi

        rm -rf "$CAMPAIGN_DIR"
        echo "Cleaned: $CAMPAIGN_DIR"
    else
        echo "Cleaning default extraction temp directory..."
        if [ -d "$EXTRACT_DIR" ]; then
            rm -rf "$EXTRACT_DIR"/*
            echo "Cleaned: $EXTRACT_DIR"
        fi
    fi

    echo "Extraction directory cleared."
}

archive_extracted() {
    local campaign_name="$1"

    campaign_name=$(require_campaign "$campaign_name" archive) || exit 1
    CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
    EXTRACTED_DIR="$CAMPAIGN_DIR/extracted"

    if [ ! -d "$EXTRACTED_DIR" ]; then
        echo "No extracted/ directory found for campaign: $campaign_name"
        exit 1
    fi

    # Create archive with timestamp
    ARCHIVE_NAME="extracted-archive-$(date +%Y%m%d-%H%M%S)"
    mv "$EXTRACTED_DIR" "$CAMPAIGN_DIR/$ARCHIVE_NAME"

    echo "[SUCCESS] Archived extracted/ to $ARCHIVE_NAME"
    echo "Location: $CAMPAIGN_DIR/$ARCHIVE_NAME"
}

list_campaigns() {
    echo "Available campaign extractions:"
    echo

    if [ -d "$CAMPAIGNS_DIR" ]; then
        # Use nullglob to handle case where no directories exist
        shopt -s nullglob
        local dirs=("$CAMPAIGNS_DIR"/*/)
        shopt -u nullglob

        for dir in "${dirs[@]}"; do
            if [ -d "$dir" ]; then
                campaign_name=$(basename "$dir")
                if [ -f "$dir/metadata.json" ]; then
                    doc_name=$(jq -r '.document_name // "unknown"' "$dir/metadata.json" 2>/dev/null)
                    date=$(jq -r '.extraction_date // "unknown"' "$dir/metadata.json" 2>/dev/null | cut -d'T' -f1)
                    chunks=$(jq -r '.total_chunks // 0' "$dir/metadata.json" 2>/dev/null)
                    echo "  • $campaign_name"
                    echo "    Document: $doc_name"
                    echo "    Date: $date"
                    echo "    Chunks: $chunks"

                    # Check for merged results
                    if [ -f "$dir/merged-results.json" ]; then
                        npcs=$(jq -r '.extraction_summary.npcs_extracted // 0' "$dir/merged-results.json" 2>/dev/null)
                        locs=$(jq -r '.extraction_summary.locations_extracted // 0' "$dir/merged-results.json" 2>/dev/null)
                        echo "    Extracted: $npcs NPCs, $locs locations"
                    fi
                    echo
                fi
            fi
        done
    else
        echo "  No campaigns found."
    fi

    if [ -f "$EXTRACT_DIR/metadata.json" ]; then
        echo "  • [Default extraction]"
        doc_name=$(jq -r '.document_name // "unknown"' "$EXTRACT_DIR/metadata.json" 2>/dev/null)
        echo "    Document: $doc_name"
        echo
    fi
}

validate_extraction() {
    local campaign_name="$1"

    campaign_name=$(require_campaign "$campaign_name" validate) || exit 1
    CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1

    echo "Validating extraction for: $campaign_name"
    echo "================================="
    echo ""

    # This is a GATE: a non-zero exit stops the import before the repair chain
    # touches anything. Counting runs through the same shape rule normalize uses,
    # so a list-shaped file (what extraction_schemas.py declares) counts truthfully
    # instead of reporting EMPTY.
    $PYTHON_CMD - "$CAMPAIGN_DIR/extracted" "$LIB_DIR" "$campaign_name" <<'PY'
import json, sys
from pathlib import Path

extracted, lib_dir, campaign_name = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
sys.path.insert(0, lib_dir)
from minor_stubs import EXTRACTION_TYPES, REQUIRED_NONEMPTY, entry_count, normalize_entity_shape

failures, total = [], 0
for type_name in EXTRACTION_TYPES:
    path = extracted / f"{type_name}.json"
    if not path.exists():
        print(f"  {type_name}: MISSING ({path})")
        failures.append(f"{type_name}: file missing")
        continue
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  {type_name}: INVALID JSON ({e})")
        failures.append(f"{type_name}: invalid JSON")
        continue
    try:
        # A malformed entity is a named failure, never a bare traceback.
        entities, entries = normalize_entity_shape(data, type_name), entry_count(data, type_name)
    except ValueError as e:
        print(f"  INVALID ENTITY - {e}")
        failures.append(str(e))
        continue
    count = len(entities)
    if count and entries != count:
        # Same-name entities collapse onto one key; say so rather than lose them silently.
        print(f"  {type_name}: {entries} entries, {count} unique names")
        total += count
    elif count:
        print(f"  {type_name}: {count} entities")
        total += count
    elif type_name in REQUIRED_NONEMPTY:
        print(f"  {type_name}: EMPTY (0 entities)")
        failures.append(f"{type_name}: 0 entities")
    else:
        # An items- or plots-less book is unusual, not broken. Warn, don't fail.
        print(f"  {type_name}: WARNING - 0 entities (optional type)")

print("")
if failures:
    print("EXTRACTION FAILED: " + "; ".join(failures))
    print("Re-run the extractor agent for each failed type before continuing the import.")
    sys.exit(1)
print(f"All required extraction output present. Total: {total} entities.")
print(f'Ready to normalize: bash tools/gm-extract.sh normalize "{campaign_name}"')
PY
}

normalize_extracted() {
    # Copy extracted/*.json to the campaign root in the flat {name: {...}} shape
    # the runtime managers expect. Extractor agents inconsistently wrap their
    # output (a bare list, a keyed dict, or either nested under a wrapper key
    # beside stray document/metadata keys); minor_stubs.normalize_entity_shape is
    # the one rule that flattens all of them, shared with validate_extraction.
    local campaign_name="$1"

    campaign_name=$(require_campaign "$campaign_name" normalize) || exit 1
    CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1

    if [ ! -d "$CAMPAIGN_DIR/extracted" ]; then
        echo "Error: No extracted/ directory for campaign: $campaign_name"
        echo "Run extraction agents first."
        exit 1
    fi

    echo "Normalizing extraction into campaign root: $campaign_name"
    echo "================================="

    # All four types are normalized in ONE pass so nothing is written until every
    # present file has come through cleanly — a half-written normalize leaves the
    # campaign root part old, part new, with no record of which is which.
    $PYTHON_CMD - "$CAMPAIGN_DIR" "$LIB_DIR" <<'PY'
import json, sys
from pathlib import Path

cdir, lib_dir = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0, lib_dir)
from minor_stubs import EXTRACTION_TYPES, normalize_entity_shape
# Coerce bare-string location connections to {"to": name} dicts so the runtime
# (move, integrity) never sees a string where it indexes conn["to"].
from connection_normalize import coerce_connections
# Collapse extraction-side location_tags into canonical tags.locations so every
# downstream pass (cap, reconcile, integrity) and the whole runtime see ONE field.
from tag_unify import unify_location_tags

staged, notes, errors = {}, [], []
for type_name in EXTRACTION_TYPES:
    src = cdir / "extracted" / f"{type_name}.json"
    if not src.exists():
        notes.append(f"  {type_name}: MISSING (skipped)")
        continue
    try:
        # A list, a keyed dict, or either under a wrapper key all land flat here.
        flat = normalize_entity_shape(json.loads(src.read_text()), type_name)
    except ValueError as e:  # includes JSONDecodeError
        errors.append(f"  {type_name}: {e}")
        continue
    if type_name == "locations":
        n = coerce_connections(flat)
        if n:
            notes.append(f"  {type_name}: coerced {n} string connection(s) to dict shape")
    if type_name == "npcs":
        r = unify_location_tags(flat)
        if r["migrated"]:
            notes.append(f"  {type_name}: unified location_tags -> tags.locations for {len(r['migrated'])} NPC(s)")
    staged[type_name] = flat
    notes.append(f"  {type_name}: {len(flat)} entities -> {type_name}.json (flat)")

print("\n".join(notes))
if errors:
    print("")
    print("NORMALIZE FAILED - nothing written:")
    print("\n".join(errors))
    sys.exit(1)
for type_name, flat in staged.items():
    (cdir / f"{type_name}.json").write_text(json.dumps(flat, indent=2))
print("")
print("Normalized to flat format. Runtime tools can now read these files.")
PY
}

cap_extracted() {
    # Tier each entity type in the campaign root: the top-N most important
    # (mention-frequency + plot-reference/party boost) stay active, the rest are
    # marked background:true in the same file. Nothing is deleted. After normalize.
    local campaign_name="$1"
    local limit="${2:-30}"

    campaign_name=$(require_campaign "$campaign_name" cap) || exit 1
    CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1

    echo "Tiering extracted entities (top-$limit active, rest background): $campaign_name"
    echo "================================="
    $PYTHON_CMD "$LIB_DIR/extraction_cap.py" "$CAMPAIGN_DIR" --limit "$limit"
}

# Main command handling
case "$1" in
    prepare)
        prepare_document "$2" "$3"
        ;;

    normalize)
        normalize_extracted "$2"
        ;;

    cap)
        cap_extracted "$2" "$3"
        ;;

    seed-opening)
        # Set starting position + opening beat + session-log hook from the spine.
        campaign_name=$(require_campaign "$2" "$1") || exit 1
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
        echo "Seeding opening beat: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/opening_seed.py" "$CAMPAIGN_DIR"
        ;;

    spine)
        # Derive plot arc ordering (sequence + depends_on) + through-line.
        campaign_name=$(require_campaign "$2" "$1") || exit 1
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
        echo "Deriving plot spine: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/plot_spine.py" "$CAMPAIGN_DIR"
        ;;

    seed-clocks)
        # Detect headline time pressure in plots and seed threat clocks.
        campaign_name=$(require_campaign "$2" "$1") || exit 1
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
        echo "Seeding threat clocks from plots: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/clock_seed.py" "$CAMPAIGN_DIR" --world-state "$WORLD_STATE_BASE"
        ;;

    stat-npcs)
        # Assign difficulty-proxy stats to combat NPCs; flag non-combatants statless.
        campaign_name=$(require_campaign "$2" "$1") || exit 1
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
        echo "Enriching NPC stats (difficulty proxy): $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/npc_stats.py" "$CAMPAIGN_DIR"
        ;;

    stub-npcs)
        # Stub plot NPCs extraction never produced; validate plot taxonomy.
        campaign_name=$(require_campaign "$2" "$1") || exit 1
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
        echo "Stubbing never-extracted NPC refs + validating plot taxonomy: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/minor_stubs.py" "$CAMPAIGN_DIR"
        ;;

    fix-items)
        # Item correctness: cursed flag, type taxonomy, value field.
        campaign_name=$(require_campaign "$2" "$1") || exit 1
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
        echo "Fixing item correctness: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/item_fixup.py" "$CAMPAIGN_DIR"
        ;;

    normalize-connections)
        # Canonicalize connection targets; move routing rule-phrases into notes.
        campaign_name=$(require_campaign "$2" "$1") || exit 1
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
        echo "Normalizing connection targets: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/connection_normalize.py" "$CAMPAIGN_DIR"
        ;;

    reconcile)
        # Stub every unresolved location reference (low_confidence); drop only
        # routing rule-prose, recorded as a dropped_references fact.
        campaign_name=$(require_campaign "$2" "$1") || exit 1
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
        echo "Reconciling missing locations: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/location_reconcile.py" "$CAMPAIGN_DIR"
        ;;

    integrity)
        # Canonicalize cross-references; fail (exit 1) on unresolved unless --no-strict.
        campaign_name=$(require_campaign "$2" "$1") || exit 1
        CAMPAIGN_DIR=$(campaign_dir "$campaign_name") || exit 1
        echo "Running integrity gate: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/integrity_gate.py" "$CAMPAIGN_DIR" $3
        ;;

    merge)
        # Check for --cleanup flag
        if [ "$3" = "--cleanup" ]; then
            merge_results "$2" "--cleanup"
        elif [ "$2" = "--cleanup" ]; then
            merge_results "" "--cleanup"
        else
            merge_results "$2"
        fi
        ;;

    save)
        # Handle variable argument positions for save
        if [[ "$2" =~ ^(rename|skip|overwrite)$ ]]; then
            save_to_world "$2" "$3"
        else
            save_to_world "rename" "$2"
        fi
        ;;

    review)
        review_content "$2"
        ;;

    list)
        list_campaigns
        ;;

    clean)
        clean_temp "$2"
        ;;

    archive)
        archive_extracted "$2"
        ;;

    validate)
        validate_extraction "$2"
        ;;

    *)
        show_usage
        exit 1
        ;;
esac
