#!/bin/bash
# common.sh - Common utilities and environment setup for all DM tools
# This file should be sourced by all other scripts: source "$(dirname "$0")/common.sh"

# Detect Python executable - prefer uv, fallback to python3/python
find_python() {
    # Try to find uv first
    if command -v uv >/dev/null 2>&1; then
        echo "uv run python"
    elif command -v python3 >/dev/null 2>&1; then
        echo "python3"
    elif command -v python >/dev/null 2>&1; then
        echo "python"
    else
        echo "Error: No Python interpreter found. Please install Python 3.11+" >&2
        exit 1
    fi
}

# Set up Python command
PYTHON_CMD=$(find_python)

# Get project root directory (parent of tools/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Tool directories
TOOLS_DIR="$PROJECT_ROOT/tools"
LIB_DIR="$PROJECT_ROOT/lib"

# Base world state directory
WORLD_STATE_BASE="$PROJECT_ROOT/world-state"

# Get active campaign directory
# Returns the campaign-specific directory if an active campaign is set,
# otherwise returns empty string and prints error
get_campaign_dir() {
    local active_file="$WORLD_STATE_BASE/active-campaign.txt"
    if [ -f "$active_file" ]; then
        local campaign_name
        campaign_name=$(cat "$active_file" | tr -d '[:space:]')
        if [ -n "$campaign_name" ] && [ -d "$WORLD_STATE_BASE/campaigns/$campaign_name" ]; then
            echo "$WORLD_STATE_BASE/campaigns/$campaign_name"
            return 0
        fi
    fi
    # No active campaign - return empty string
    echo ""
    return 1
}

# Get the active campaign name (or empty string if none)
get_active_campaign() {
    local active_file="$WORLD_STATE_BASE/active-campaign.txt"
    if [ -f "$active_file" ]; then
        local campaign_name
        campaign_name=$(cat "$active_file" | tr -d '[:space:]')
        if [ -n "$campaign_name" ] && [ -d "$WORLD_STATE_BASE/campaigns/$campaign_name" ]; then
            echo "$campaign_name"
            return 0
        fi
    fi
    echo ""
}

# Campaigns directory
CAMPAIGNS_DIR="$WORLD_STATE_BASE/campaigns"

# Ensure base directories exist
mkdir -p "$WORLD_STATE_BASE"
mkdir -p "$CAMPAIGNS_DIR"

# Set paths dynamically based on active campaign
WORLD_STATE_DIR=$(get_campaign_dir)

# Only set file paths if we have an active campaign
if [ -n "$WORLD_STATE_DIR" ]; then
    NPCS_FILE="$WORLD_STATE_DIR/npcs.json"
    LOCATIONS_FILE="$WORLD_STATE_DIR/locations.json"
    FACTS_FILE="$WORLD_STATE_DIR/facts.json"
    CONSEQUENCES_FILE="$WORLD_STATE_DIR/consequences.json"
    SESSION_LOG="$WORLD_STATE_DIR/session-log.md"
    CAMPAIGN_OVERVIEW="$WORLD_STATE_DIR/campaign-overview.json"
    CHARACTER_FILE="$WORLD_STATE_DIR/character.json"
else
    # No active campaign - set empty paths (tools should check and error)
    NPCS_FILE=""
    LOCATIONS_FILE=""
    FACTS_FILE=""
    CONSEQUENCES_FILE=""
    SESSION_LOG=""
    CAMPAIGN_OVERVIEW=""
    CHARACTER_FILE=""
fi

# Helper to check if campaign is active and exit with error if not
require_active_campaign() {
    if [ -z "$WORLD_STATE_DIR" ]; then
        error "No active campaign. Run /new-game or /import first."
        exit 1
    fi
}

# Common timestamp function
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Safe JSON string escape function
escape_json() {
    local text="$1"
    # Use Python for proper JSON escaping to avoid injection
    echo "$text" | $PYTHON_CMD -c "import sys, json; print(json.dumps(sys.stdin.read().strip()))" | sed 's/^"//;s/"$//'
}

# Validate name/identifier (alphanumeric, spaces, hyphens, apostrophes only)
validate_name() {
    local name="$1"
    local pattern="^[[:alnum:][:space:]'-]+$"
    if [[ ! "$name" =~ $pattern ]]; then
        echo "Error: Invalid name. Use only letters, numbers, spaces, hyphens, and apostrophes." >&2
        return 1
    fi
    return 0
}

# Color output functions (only if terminal supports it)
if [ -t 1 ] && [ "${TERM}" != "dumb" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    PURPLE=''
    CYAN=''
    BOLD=''
    NC=''
fi

# Status output functions
success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" >&2
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Approximate token count from character count (rule of thumb: ~4 chars/token)
estimate_tokens_from_chars() {
    local chars="$1"
    if [ -z "$chars" ] || [ "$chars" -le 0 ] 2>/dev/null; then
        echo "0"
        return 0
    fi
    echo $(((chars + 3) / 4))
}

# Log token usage estimates for high-cost tool calls
# Format: timestamp<TAB>campaign=<name><TAB>command=<name><TAB>k=v...
log_token_usage() {
    local command_name="$1"
    shift

    local usage_dir="$WORLD_STATE_BASE/usage"
    local usage_log="$usage_dir/token-usage.log"
    local campaign_name
    campaign_name=$(get_active_campaign)
    if [ -z "$campaign_name" ]; then
        campaign_name="none"
    fi

    mkdir -p "$usage_dir"
    printf "%s\tcampaign=%s\tcommand=%s\t%s\n" \
        "$(get_timestamp)" \
        "$campaign_name" \
        "$command_name" \
        "$*" >> "$usage_log"
}

# Check if required environment variables are set
check_env() {
    local var_name="$1"
    local var_value="${!var_name}"
    if [ -z "$var_value" ]; then
        warning "$var_name not set in environment"
        return 1
    fi
    return 0
}

# Check if a module is enabled for the active campaign
# Usage: _module_enabled <module-id>
# Returns 0 if enabled, 1 if disabled
_module_enabled() {
    local module_id="$1"
    uv run python "$PROJECT_ROOT/lib/module_loader.py" info --module "$module_id" > /dev/null 2>&1 || return 1
    local enabled
    enabled=$(uv run python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/lib')
from module_loader import ModuleLoader
loader = ModuleLoader()
print('1' if loader.is_module_enabled('$module_id') else '0')
" 2>/dev/null)
    [ "$enabled" = "1" ]
}

# Dispatch to module middleware
# Usage: dispatch_middleware <tool-name> [args...]
# Returns 0 if a middleware handled the call, 1 if CORE should handle
dispatch_middleware() {
    local tool="$1"
    shift
    for mw in "$PROJECT_ROOT"/.claude/modules/*/middleware/"$tool"; do
        [ -f "$mw" ] || continue
        # Extract module id from path (.claude/modules/<id>/middleware/tool.sh)
        local module_id
        module_id=$(basename "$(dirname "$(dirname "$mw")")")
        # Skip if disabled in active campaign
        if ! _module_enabled "$module_id"; then
            continue
        fi
        bash "$mw" "$@"
        local rc=$?
        if [ $rc -eq 0 ]; then
            return 0
        fi
    done
    return 1
}

# Post-hook: called AFTER CORE runs. All enabled middlewares get a chance.
# Exit code of middleware is ignored (always continues).
# Usage: dispatch_middleware_post <tool-name> [args...]
dispatch_middleware_post() {
    local tool="$1"
    shift
    for mw in "$PROJECT_ROOT"/.claude/modules/*/middleware/"${tool}.post"; do
        [ -f "$mw" ] || continue
        local module_id
        module_id=$(basename "$(dirname "$(dirname "$mw")")")
        if ! _module_enabled "$module_id"; then
            continue
        fi
        bash "$mw" "$@" || true
    done
}

# Print help additions from all middleware for a tool
# Usage: dispatch_middleware_help <tool-name>
# Each middleware prints its help lines when called with --help, exits 1 to continue
dispatch_middleware_help() {
    local tool="$1"
    for mw in "$PROJECT_ROOT"/.claude/modules/*/middleware/"$tool"; do
        [ -f "$mw" ] || continue
        bash "$mw" --help 2>/dev/null || true
    done
}

# Load .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi
