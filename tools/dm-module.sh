#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/common.sh"

# Module management for the active campaign
# Tracks which modules are enabled and validates dependencies

MODULES_DIR=".claude/modules"

# Get active campaign using Python campaign manager
ACTIVE_CAMPAIGN=$(uv run python -c "from lib.campaign_manager import CampaignManager; cm = CampaignManager(); active = cm.get_active(); print(active if active else '')" 2>/dev/null || echo "")
if [ -z "$ACTIVE_CAMPAIGN" ]; then
    echo "Error: No active campaign. Run: dm-campaign.sh switch <campaign>"
    exit 1
fi

CAMPAIGN_DIR="world-state/campaigns/$ACTIVE_CAMPAIGN"
OVERVIEW_FILE="$CAMPAIGN_DIR/campaign-overview.json"

# ============================================================================
# Helper Functions
# ============================================================================

# Load module metadata
load_module() {
    local module=$1
    local module_file="$MODULES_DIR/$module/module.json"

    if [ ! -f "$module_file" ]; then
        echo ""
        return 1
    fi
    cat "$module_file"
}

# Check if module is enabled in campaign
is_module_enabled() {
    local module=$1
    jq --arg mod "$module" '.enabled_modules // {} | .[$mod] // false' "$OVERVIEW_FILE" 2>/dev/null || echo "false"
}

# Get all enabled modules for campaign
get_enabled_modules() {
    jq -r '.enabled_modules // {} | keys[]' "$OVERVIEW_FILE" 2>/dev/null || echo ""
}

# Set module enabled status
set_module_enabled() {
    local module=$1
    local enabled=$2

    jq --arg mod "$module" --argjson val "$enabled" \
        '.enabled_modules //= {} | .enabled_modules[$mod] = $val' \
        "$OVERVIEW_FILE" > "$OVERVIEW_FILE.tmp"
    mv "$OVERVIEW_FILE.tmp" "$OVERVIEW_FILE"
}

# Get module dependencies
get_dependencies() {
    local module=$1
    load_module "$module" | jq -r '.dependencies[]? // empty'
}

# Get incompatible modules
get_incompatible() {
    local module=$1
    load_module "$module" | jq -r '.incompatible_with[]? // empty'
}

# Get modules that depend on this one
get_dependent_modules() {
    local target=$1
    for mod in $(ls -d "$MODULES_DIR"/*/ 2>/dev/null | xargs -n1 basename); do
        if get_dependencies "$mod" | grep -q "^$target$"; then
            echo "$mod"
        fi
    done
}

# ============================================================================
# Commands
# ============================================================================

cmd_list() {
    echo "Modules in: $ACTIVE_CAMPAIGN"
    echo "=============================================="
    echo ""

    for module in $(ls -d "$MODULES_DIR"/*/ 2>/dev/null | xargs -n1 basename | sort); do
        local enabled=$(is_module_enabled "$module")
        local status="[ ]"
        [ "$enabled" = "true" ] && status="[✓]"

        local metadata=$(load_module "$module")
        local name=$(echo "$metadata" | jq -r '.name // "Unknown"')
        local deps=$(echo "$metadata" | jq -r '.dependencies[]? // empty' | wc -l)

        printf "  %s %-30s %s\n" "$status" "$module" "($name)"

        if [ "$deps" -gt 0 ]; then
            echo "$metadata" | jq -r '.dependencies[]? // empty' | while read dep; do
                echo "      → requires: $dep"
            done
        fi
    done
}

cmd_enable() {
    local module=$1

    # Check module exists
    if ! load_module "$module" > /dev/null 2>&1; then
        echo "Error: Module not found: $module"
        exit 1
    fi

    # Check if already enabled
    if [ "$(is_module_enabled "$module")" = "true" ]; then
        echo "Module already enabled: $module"
        return 0
    fi

    # Validate dependencies
    echo "Checking dependencies for: $module"
    local missing_deps=()
    while read -r dep; do
        [ -z "$dep" ] && continue
        if [ "$(is_module_enabled "$dep")" != "true" ]; then
            missing_deps+=("$dep")
            echo "  ⚠ Missing: $dep"
        else
            echo "  ✓ Found: $dep"
        fi
    done < <(get_dependencies "$module")

    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo ""
        echo "Cannot enable $module — missing dependencies: ${missing_deps[*]}"
        echo ""
        echo "Enable dependencies first:"
        for dep in "${missing_deps[@]}"; do
            echo "  dm-module.sh enable $dep"
        done
        exit 1
    fi

    # Check incompatibilities
    while read -r incomp; do
        [ -z "$incomp" ] && continue
        if [ "$(is_module_enabled "$incomp")" = "true" ]; then
            echo "Error: Module incompatible with: $incomp (already enabled)"
            exit 1
        fi
    done < <(get_incompatible "$module")

    # Enable module
    set_module_enabled "$module" "true"
    echo "✓ Enabled: $module"
}

cmd_disable() {
    local module=$1

    # Check if enabled
    if [ "$(is_module_enabled "$module")" != "true" ]; then
        echo "Module not enabled: $module"
        return 0
    fi

    # Check for dependent modules
    local dependents=()
    while read -r dep_module; do
        [ -z "$dep_module" ] && continue
        if [ "$(is_module_enabled "$dep_module")" = "true" ]; then
            dependents+=("$dep_module")
        fi
    done < <(get_dependent_modules "$module")

    if [ ${#dependents[@]} -gt 0 ]; then
        echo "Error: Cannot disable $module — required by:"
        for dep in "${dependents[@]}"; do
            echo "  - $dep"
        done
        echo ""
        echo "Disable these modules first:"
        for dep in "${dependents[@]}"; do
            echo "  dm-module.sh disable $dep"
        done
        exit 1
    fi

    # Disable module
    set_module_enabled "$module" "false"
    echo "✓ Disabled: $module"
}

cmd_status() {
    local module=$1

    if ! load_module "$module" > /dev/null 2>&1; then
        echo "Error: Module not found: $module"
        exit 1
    fi

    local metadata=$(load_module "$module")
    local enabled=$(is_module_enabled "$module")
    local status="disabled"
    [ "$enabled" = "true" ] && status="enabled"

    echo "Module: $module"
    echo "Status: $status"
    echo ""

    echo "$metadata" | jq '{
        name: .name,
        version: .version,
        description: .description,
        enabled_by_default: .enabled_by_default,
        dependencies: .dependencies,
        incompatible_with: .incompatible_with,
        category: .category
    }' | sed 's/"//g' | sed 's/: /: /'
}

# ============================================================================
# Main
# ============================================================================

case "${1:-}" in
    list)
        cmd_list
        ;;
    enable)
        if [ -z "${2:-}" ]; then
            echo "Usage: dm-module.sh enable <module>"
            exit 1
        fi
        cmd_enable "$2"
        ;;
    disable)
        if [ -z "${2:-}" ]; then
            echo "Usage: dm-module.sh disable <module>"
            exit 1
        fi
        cmd_disable "$2"
        ;;
    status)
        if [ -z "${2:-}" ]; then
            echo "Usage: dm-module.sh status <module>"
            exit 1
        fi
        cmd_status "$2"
        ;;
    *)
        echo "Usage: dm-module.sh [list|enable|disable|status] [module]"
        echo ""
        echo "Commands:"
        echo "  list              List all modules and their status"
        echo "  enable <module>   Enable module for active campaign"
        echo "  disable <module>  Disable module for active campaign"
        echo "  status <module>   Show module details"
        exit 1
        ;;
esac
