#!/bin/bash
# common-advanced.sh - Advanced module middleware dispatch functions
# Source this file in advanced tool wrappers to enable module hooks.

# Get project root from the sourcing script's context
# (PROJECT_ROOT must already be set before sourcing this)

# Check if a module is enabled for the active campaign
# Usage: _module_enabled <module-id>
# Returns 0 if enabled, 1 if disabled
_module_enabled() {
    local module_id="$1"
    local enabled
    enabled=$(uv run python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/.claude/modules')
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
        local module_id
        module_id=$(basename "$(dirname "$(dirname "$mw")")")
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
dispatch_middleware_help() {
    local tool="$1"
    for mw in "$PROJECT_ROOT"/.claude/modules/*/middleware/"$tool"; do
        [ -f "$mw" ] || continue
        bash "$mw" --help 2>/dev/null || true
    done
}
