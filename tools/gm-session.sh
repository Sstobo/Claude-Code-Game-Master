#!/bin/bash
# gm-session.sh - Session management (thin wrapper for session_manager.py)

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: gm-session.sh <action> [args]"
    echo ""
    echo "Session Actions:"
    echo "  start                    - Begin new session, show world state"
    echo "  end <summary>            - End session with summary"
    echo "  status                   - Show current campaign status"
    echo "  move <location>          - Move party to new location"
    echo "  context                  - Full session context (character, party, consequences, rules)"
    echo "  choices [on|off|toggle]  - Toggle the [A]-[E] action menu (no arg: show state)"
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
    exit 1
fi

ACTION="$1"
shift

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

        # Auto-query RAG for new location context (GM-internal, minimal output)
        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/gm-campaign.sh" path 2>/dev/null)
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

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: start, end, status, move, context, choices, save, restore, list-saves, delete-save, history"
        exit 1
        ;;
esac

# Propagate Python exit code
exit $?
