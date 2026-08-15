#!/bin/bash
# gm-session.sh - Session management (thin wrapper for session_manager.py)

source "$(dirname "$0")/common.sh"

show_usage() {
    echo "Usage: gm-session.sh <action> [args]"
    echo ""
    echo "Session Actions:"
    echo "  start                    - Begin new session, show world state"
    echo "  end <summary>            - End session with summary"
    echo "  status                   - Show current campaign status"
    echo "  move <location>          - Move party to new location"
    echo "  context                  - Full session context (character, party, consequences, rules)"
    echo "  choices [on|off|toggle]  - Toggle the [A]-[E] action menu (no arg: show state)"
    echo "  dice [on|off|toggle]     - Toggle player rolling their own dice (no arg: show state)"
    echo "  world-tick '<json>'      - Persist off-screen developments (warns if >3, rollback-able)"
    echo "  world-tick-rollback      - Undo the most recent world tick"
    echo "  world-tick-log           - Show world-tick history"
    echo ""
    echo "Save System (JSON snapshots):"
    echo "  save <name>              - Create named save point"
    echo "  restore <save-name>      - Restore from save point"
    echo "  list-saves               - List all save points"
    echo "  delete-save <name>       - Delete a save point"
    echo "  history                  - Show session history"
    echo ""
    echo "Examples:"
    echo "  gm-session.sh start"
    echo "  gm-session.sh end \"Defeated the dragon, found treasure\""
    echo "  gm-session.sh save \"before-boss-fight\""
    echo "  gm-session.sh restore 20250127-before-boss-fight"
    echo "  gm-session.sh context"
}

if [ "$#" -lt 1 ]; then
    show_usage
    exit 1
fi

ACTION="$1"
shift

# Every action the case below handles, in one place: the guard and the
# unknown-action message both read this, so they cannot drift apart.
VALID_ACTIONS="start end status move context choices dice world-tick world-tick-rollback world-tick-log save restore list-saves delete-save history"

is_valid_action() {
    local valid
    for valid in $VALID_ACTIONS; do
        [ "$valid" = "$ACTION" ] && return 0
    done
    return 1
}

# Usage and a mistyped verb are answered before the guard — a typo should report
# itself as a typo, not as a missing campaign. Everything else reads state.
case "$ACTION" in
    help|--help|-h)
        show_usage
        exit 0
        ;;
esac

if is_valid_action; then
    require_active_campaign
else
    echo "Unknown action: $ACTION"
    echo "Valid actions: $VALID_ACTIONS"
    exit 1
fi

case "$ACTION" in
    start)
        # Banner names the active World Kit, not D&D — each book plays as its own game.
        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/gm-campaign.sh" path 2>/dev/null)
        KIT_NAME=""
        if [ -f "$CAMPAIGN_DIR/ruleset.json" ]; then
            KIT_NAME=$($PYTHON_CMD -c "import json,sys; print(json.load(open(sys.argv[1])).get('name','') or '')" "$CAMPAIGN_DIR/ruleset.json" 2>/dev/null)
        fi
        if [ -n "$KIT_NAME" ]; then
            BANNER="Starting $KIT_NAME Session"
        else
            BANNER="Starting Session"
        fi
        echo "$BANNER"
        printf '%*s\n' "${#BANNER}" '' | tr ' ' '='
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" start
        RESULT=$?
        if [ $RESULT -ne 0 ]; then exit $RESULT; fi
        echo ""
        echo "Pending Consequences:"
        bash "$TOOLS_DIR/gm-consequence.sh" check

        # Auto-query RAG for current location context (GM-internal, minimal output)
        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/gm-campaign.sh" path 2>/dev/null)
        if [ -d "$CAMPAIGN_DIR/vectors" ]; then
            LOCATION=$($PYTHON_CMD "$LIB_DIR/session_manager.py" status 2>/dev/null | grep -o '"current_location": "[^"]*"' | cut -d'"' -f4)
            if [ -n "$LOCATION" ] && [ "$LOCATION" != "null" ]; then
                echo ""
                # Minimal GM context - silently queries/auto-enhances
                # Note: scene command is quiet when no RAG exists; real errors will show
                CONTEXT=$(bash "$TOOLS_DIR/gm-enhance.sh" scene "$LOCATION")
                if [ -n "$CONTEXT" ]; then
                    echo "$CONTEXT"
                fi
            fi
        fi
        ;;

    end)
        if [ "$#" -lt 1 ]; then
            echo "Usage: gm-session.sh end <summary>"
            exit 1
        fi
        echo "Ending Session"
        echo "=============="
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" end "$@"
        RESULT=$?
        if [ $RESULT -ne 0 ]; then exit $RESULT; fi
        echo ""
        echo "Pending Consequences:"
        bash "$TOOLS_DIR/gm-consequence.sh" check
        echo ""
        echo "Arc entry (REQUIRED — this is what long-term memory recalls):"
        echo "  bash tools/gm-recall.sh arc '{\"summary\": \"what changed this session\","
        echo "    \"who_matters\": [\"...\"], \"open_debts\": [\"...\"]}'"
        echo ""
        echo "World tick: optionally advance a few SMALL off-screen developments"
        echo "  (grounded in plots/RAG) with: gm-session.sh world-tick '<json list>'"
        echo "  Applies all; warns if more than 3. Rollback with world-tick-rollback."
        ;;

    world-tick)
        # Persist GM-proposed off-screen developments (all applied, warn if >cap, rollback-able).
        $PYTHON_CMD "$LIB_DIR/world_tick.py" apply "$@"
        ;;

    world-tick-rollback)
        $PYTHON_CMD "$LIB_DIR/world_tick.py" rollback "$@"
        ;;

    world-tick-log)
        $PYTHON_CMD "$LIB_DIR/world_tick.py" history "$@"
        ;;

    status)
        echo "Campaign Status"
        echo "==============="
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" status "$@"
        ;;

    move)
        if [ "$#" -lt 1 ]; then
            echo "Usage: gm-session.sh move <location>"
            exit 1
        fi
        echo "Moving Party"
        echo "============"
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" move "$@"
        RESULT=$?
        if [ $RESULT -ne 0 ]; then exit $RESULT; fi

        echo ""
        # Reactivity: fire any consequences whose triggers match the new scene.
        bash "$TOOLS_DIR/gm-consequence.sh" tick

        # Grounded lore brief on FIRST visit to a place with retained book text.
        # The loremaster cache gates this: revisits are silent, so the deep read
        # fires once per location. (--full is the GM's explicit follow-up.)
        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/gm-campaign.sh" path 2>/dev/null)
        if [ -f "$CAMPAIGN_DIR/source/current-document.txt" ] || [ -f "$CAMPAIGN_DIR/current-document.txt" ] || [ -f "$CAMPAIGN_DIR/book-text.txt" ]; then
            # ponytail: grep-for-key on the JSON cache, jq-free; a false hit just skips one auto-brief
            if ! grep -qF "\"$1\":" "$CAMPAIGN_DIR/loremaster-cache.json" 2>/dev/null; then
                echo ""
                echo "First visit — grounding in the source (gm-lore.sh \"$1\" --full for the whole chapter):"
                $PYTHON_CMD "$LIB_DIR/loremaster.py" "$1" 2>/dev/null || true
            fi
        fi

        # Auto-query RAG for new location context (GM-internal, minimal output)
        if [ -d "$CAMPAIGN_DIR/vectors" ]; then
            echo ""
            # Minimal GM context - silently queries/auto-enhances
            # Note: scene command is quiet when no RAG exists; real errors will show
            CONTEXT=$(bash "$TOOLS_DIR/gm-enhance.sh" scene "$@")
            if [ -n "$CONTEXT" ]; then
                echo "$CONTEXT"
            fi
        fi
        ;;

    context)
        # Full session context — one command to load everything the GM needs
        CONTEXT_OUTPUT=$($PYTHON_CMD "$LIB_DIR/session_manager.py" context "$@")
        CONTEXT_STATUS=$?
        echo "$CONTEXT_OUTPUT"
        CONTEXT_CHARS=${#CONTEXT_OUTPUT}
        CONTEXT_TOKENS=$(estimate_tokens_from_chars "$CONTEXT_CHARS")
        FULL_FLAG=false
        for arg in "$@"; do [ "$arg" = "--full" ] && FULL_FLAG=true; done
        log_token_usage "gm-session-context" "full=$FULL_FLAG" "output_chars=$CONTEXT_CHARS" "output_tokens_est=$CONTEXT_TOKENS"
        exit $CONTEXT_STATUS
        ;;

    save)
        if [ "$#" -lt 1 ]; then
            echo "Usage: gm-session.sh save <name>"
            echo ""
            echo "Existing saves:"
            $PYTHON_CMD "$LIB_DIR/session_manager.py" list-saves
            exit 1
        fi
        echo "Creating Save Point"
        echo "==================="
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" save "$@"
        # Refresh long-term campaign memory on save (best-effort; never blocks).
        $PYTHON_CMD "$LIB_DIR/campaign_memory.py" refresh >/dev/null 2>&1 || true
        ;;

    restore)
        if [ "$#" -lt 1 ]; then
            echo "Usage: gm-session.sh restore <save-name>"
            echo ""
            echo "Available saves:"
            $PYTHON_CMD "$LIB_DIR/session_manager.py" list-saves
            exit 1
        fi
        echo "Restoring from Save"
        echo "==================="
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" restore "$1"
        ;;

    list-saves)
        echo "Save Points"
        echo "==========="
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" list-saves
        ;;

    delete-save)
        if [ "$#" -lt 1 ]; then
            echo "Usage: gm-session.sh delete-save <name>"
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/session_manager.py" delete-save "$1"
        ;;

    history)
        echo "Session History"
        echo "==============="
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" history
        ;;

    choices)
        $PYTHON_CMD "$LIB_DIR/session_manager.py" choices "$@"
        ;;

    dice)
        $PYTHON_CMD "$LIB_DIR/session_manager.py" dice "$@"
        ;;
esac

# Propagate Python exit code
exit $?
