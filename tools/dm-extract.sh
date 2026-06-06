#!/bin/bash
#
# dm-extract.sh - Concurrent agent extraction workflow for D&D modules
#
# Usage:
#   dm-extract.sh prepare <document> [campaign-name] - Prepare document for extraction
#   dm-extract.sh merge [campaign-name] [--cleanup]  - Merge results from agents
#   dm-extract.sh save [strategy] [campaign-name]    - Save to world state
#   dm-extract.sh review [campaign-name]             - Review extracted content
#   dm-extract.sh list                               - List all campaign extractions
#   dm-extract.sh clean [campaign-name]              - Clean extraction directory

set -e
source "$(dirname "$0")/common.sh"

# Base directories - use WORLD_STATE_BASE not WORLD_STATE_DIR (which is campaign-specific)
CAMPAIGNS_DIR="$WORLD_STATE_BASE/campaigns"
EXTRACT_DIR="$WORLD_STATE_BASE/extraction-temp"  # Default if no campaign specified

show_usage() {
    cat << EOF
D&D Module Extraction Tool

Commands:
  prepare <file> [name]     Extract text and create chunks for agent processing
                            Optional: specify campaign name (defaults to filename)
  normalize [campaign]      Copy extracted/*.json to campaign root, unwrapping
                            agent wrapper keys into the flat {name:...} runtime shape
  cap [campaign] [limit]    Cap each type to top-N (default 30) by importance
                            (mention-frequency + plot-reference/party boost)
  fix-items [campaign]      Item correctness: cursed flag, type taxonomy, value field
  normalize-connections [campaign]  Canonicalize connection targets; move routing
                            rule-phrases into notes (runs before reconcile)
  reconcile [campaign]      Stub or drop location refs that don't resolve to a node
                            (runs before the integrity gate)
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
  validate [campaign]       Check extraction output files for completeness

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
        echo "Install with: uv pip install 'dm-claude[rag]'"
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
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"

        # Check if campaign directory exists
        if [ ! -d "$CAMPAIGN_DIR" ]; then
            echo "Error: Campaign directory not found: $CAMPAIGN_DIR"
            echo "Available campaigns:"
            list_campaigns
            exit 1
        fi

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
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"

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
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"

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
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"

        if [ -d "$CAMPAIGN_DIR" ]; then
            rm -rf "$CAMPAIGN_DIR"
            echo "Cleaned: $CAMPAIGN_DIR"
        else
            echo "Campaign directory not found: $CAMPAIGN_DIR"
        fi
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

    if [ -z "$campaign_name" ]; then
        # Try to get active campaign
        campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        if [ -z "$campaign_name" ]; then
            echo "Error: No campaign specified and no active campaign found."
            echo "Usage: dm-extract.sh archive <campaign-name>"
            exit 1
        fi
    fi

    CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"
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

    if [ -z "$campaign_name" ]; then
        # Try to get active campaign
        campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        if [ -z "$campaign_name" ]; then
            echo "Error: No campaign specified and no active campaign found."
            echo "Usage: dm-extract.sh validate <campaign-name>"
            exit 1
        fi
    fi

    CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"

    if [ ! -d "$CAMPAIGN_DIR" ]; then
        echo "Error: Campaign directory not found: $CAMPAIGN_DIR"
        exit 1
    fi

    echo "Validating extraction for: $campaign_name"
    echo "================================="
    echo ""

    all_valid=true
    total_entities=0

    for type in npcs locations items plots; do
        file="$CAMPAIGN_DIR/extracted/${type}.json"
        if [ ! -f "$file" ]; then
            echo "  $type: ❌ MISSING"
            all_valid=false
        elif ! $PYTHON_CMD -c "import json; json.load(open('$file'))" 2>/dev/null; then
            echo "  $type: ❌ INVALID JSON"
            all_valid=false
        else
            # Get count from appropriate key based on type
            case "$type" in
                npcs) key="npcs" ;;
                locations) key="locations" ;;
                items) key="items" ;;
                plots) key="plot_hooks" ;;
            esac
            count=$($PYTHON_CMD -c "import json; d=json.load(open('$file')); print(len(d.get('$key', d)))" 2>/dev/null || echo "0")
            if [ "$count" -eq 0 ]; then
                echo "  $type: ⚠️  EMPTY (0 entities)"
            else
                echo "  $type: ✓ $count entities"
                total_entities=$((total_entities + count))
            fi
        fi
    done

    echo ""
    if [ "$all_valid" = true ]; then
        if [ "$total_entities" -eq 0 ]; then
            echo "⚠️  All files valid but EMPTY. Extraction may have failed silently."
            exit 1
        else
            echo "✓ All files valid. Total: $total_entities entities."
            echo "Ready for merge: bash tools/dm-extract.sh merge \"$campaign_name\""
        fi
    else
        echo "❌ Some files missing or invalid."
        echo "Re-run extraction for failed types or use fallback extraction."
        exit 1
    fi
}

normalize_extracted() {
    # Copy extracted/*.json to the campaign root in the flat {name: {...}} shape
    # the runtime managers expect. Extractor agents inconsistently wrap their
    # output (e.g. {"npcs": {...}}, plus stray document/metadata keys on items);
    # this unwraps using the same d.get(key, d) heuristic as validate_extraction.
    local campaign_name="$1"

    if [ -z "$campaign_name" ]; then
        campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        if [ -z "$campaign_name" ]; then
            echo "Error: No campaign specified and no active campaign found."
            echo "Usage: dm-extract.sh normalize <campaign-name>"
            exit 1
        fi
    fi

    CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"

    if [ ! -d "$CAMPAIGN_DIR/extracted" ]; then
        echo "Error: No extracted/ directory for campaign: $campaign_name"
        echo "Run extraction agents first."
        exit 1
    fi

    echo "Normalizing extraction into campaign root: $campaign_name"
    echo "================================="

    for type in npcs locations items plots; do
        case "$type" in
            npcs) key="npcs" ;;
            locations) key="locations" ;;
            items) key="items" ;;
            plots) key="plot_hooks" ;;
        esac
        $PYTHON_CMD - "$CAMPAIGN_DIR/extracted/${type}.json" "$CAMPAIGN_DIR/${type}.json" "$key" "$type" <<'PY'
import json, sys
src, dst, key, type_name = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
try:
    d = json.load(open(src))
except FileNotFoundError:
    print(f"  {type_name}: MISSING (skipped)")
    sys.exit(0)
# Unwrap a {key: {...}} wrapper if present; otherwise the file is already flat.
flat = d.get(key, d) if isinstance(d, dict) else d
if not isinstance(flat, dict):
    print(f"  {type_name}: unexpected shape, copied verbatim")
    flat = d
json.dump(flat, open(dst, "w"), indent=2)
print(f"  {type_name}: {len(flat)} entities -> {type_name}.json (flat)")
PY
    done

    echo ""
    echo "Normalized to flat format. Runtime tools can now read these files."
}

cap_extracted() {
    # Cap each entity type in the campaign root to the top-N most important
    # (mention-frequency + plot-reference/party boost). Run after normalize.
    local campaign_name="$1"
    local limit="${2:-30}"

    if [ -z "$campaign_name" ]; then
        campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        if [ -z "$campaign_name" ]; then
            echo "Error: No campaign specified and no active campaign found."
            echo "Usage: dm-extract.sh cap <campaign-name> [limit]"
            exit 1
        fi
    fi

    CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"
    if [ ! -d "$CAMPAIGN_DIR" ]; then
        echo "Error: Campaign directory not found: $CAMPAIGN_DIR"
        exit 1
    fi

    echo "Capping extracted entities to top-$limit per type: $campaign_name"
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
        campaign_name="$2"
        if [ -z "$campaign_name" ]; then
            campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        fi
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"
        if [ ! -d "$CAMPAIGN_DIR" ]; then
            echo "Error: Campaign directory not found: $CAMPAIGN_DIR"; exit 1
        fi
        echo "Seeding opening beat: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/opening_seed.py" "$CAMPAIGN_DIR"
        ;;

    spine)
        # Derive plot arc ordering (sequence + depends_on) + through-line.
        campaign_name="$2"
        if [ -z "$campaign_name" ]; then
            campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        fi
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"
        if [ ! -d "$CAMPAIGN_DIR" ]; then
            echo "Error: Campaign directory not found: $CAMPAIGN_DIR"; exit 1
        fi
        echo "Deriving plot spine: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/plot_spine.py" "$CAMPAIGN_DIR"
        ;;

    seed-clocks)
        # Detect headline time pressure in plots and seed threat clocks.
        campaign_name="$2"
        if [ -z "$campaign_name" ]; then
            campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        fi
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"
        if [ ! -d "$CAMPAIGN_DIR" ]; then
            echo "Error: Campaign directory not found: $CAMPAIGN_DIR"; exit 1
        fi
        echo "Seeding threat clocks from plots: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/clock_seed.py" "$CAMPAIGN_DIR" --world-state "$WORLD_STATE_BASE"
        ;;

    fix-items)
        # Item correctness: cursed flag, type taxonomy, value field.
        campaign_name="$2"
        if [ -z "$campaign_name" ]; then
            campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        fi
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"
        if [ ! -d "$CAMPAIGN_DIR" ]; then
            echo "Error: Campaign directory not found: $CAMPAIGN_DIR"; exit 1
        fi
        echo "Fixing item correctness: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/item_fixup.py" "$CAMPAIGN_DIR"
        ;;

    normalize-connections)
        # Canonicalize connection targets; move routing rule-phrases into notes.
        campaign_name="$2"
        if [ -z "$campaign_name" ]; then
            campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        fi
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"
        if [ ! -d "$CAMPAIGN_DIR" ]; then
            echo "Error: Campaign directory not found: $CAMPAIGN_DIR"; exit 1
        fi
        echo "Normalizing connection targets: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/connection_normalize.py" "$CAMPAIGN_DIR"
        ;;

    reconcile)
        # Stub or drop location references that don't resolve to a real node.
        campaign_name="$2"
        if [ -z "$campaign_name" ]; then
            campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        fi
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"
        if [ ! -d "$CAMPAIGN_DIR" ]; then
            echo "Error: Campaign directory not found: $CAMPAIGN_DIR"; exit 1
        fi
        echo "Reconciling missing locations: $campaign_name"
        echo "================================="
        $PYTHON_CMD "$LIB_DIR/location_reconcile.py" "$CAMPAIGN_DIR"
        ;;

    integrity)
        # Canonicalize cross-references; fail (exit 1) on unresolved unless --no-strict.
        campaign_name="$2"
        if [ -z "$campaign_name" ]; then
            campaign_name=$(cat "$WORLD_STATE_BASE/active-campaign.txt" 2>/dev/null)
        fi
        CAMPAIGN_DIR="$CAMPAIGNS_DIR/$(echo "$campaign_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')"
        if [ ! -d "$CAMPAIGN_DIR" ]; then
            echo "Error: Campaign directory not found: $CAMPAIGN_DIR"; exit 1
        fi
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
