#!/bin/bash
# dm-session.sh - Session management (thin wrapper for session_manager.py)

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: dm-session.sh <action> [args]"
    echo ""
    echo "Session Actions:"
    echo "  start                    - Begin new session, show world state"
    echo "  end <summary>            - End session with summary"
    echo "  status                   - Show current campaign status"
    echo "  move <location>          - Move party to new location"
    dispatch_middleware_help "dm-session.sh"
    echo "  context                  - Full session context (character, party, consequences, rules)"
    echo ""
    echo "Save System (JSON snapshots):"
    echo "  save <name>              - Create named save point"
    echo "  restore <save-name>      - Restore from save point"
    echo "  list-saves               - List all save points"
    echo "  delete-save <name>       - Delete a save point"
    echo "  history                  - Show session history"
    echo ""
    echo "Examples:"
    echo "  dm-session.sh start"
    echo "  dm-session.sh end \"Defeated the dragon, found treasure\""
    echo "  dm-session.sh save \"before-boss-fight\""
    echo "  dm-session.sh restore 20250127-before-boss-fight"
    echo "  dm-session.sh context"
    exit 1
fi

ACTION="$1"
shift

case "$ACTION" in
    start)
        echo "Starting D&D Session"
        echo "======================"
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" start
        RESULT=$?
        if [ $RESULT -ne 0 ]; then exit $RESULT; fi
        echo ""
        echo "Pending Consequences:"
        bash "$TOOLS_DIR/dm-consequence.sh" check

        # Auto-query RAG for current location context (DM-internal, minimal output)
        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/dm-campaign.sh" path 2>/dev/null)
        if [ -d "$CAMPAIGN_DIR/vectors" ]; then
            LOCATION=$($PYTHON_CMD "$LIB_DIR/session_manager.py" status 2>/dev/null | grep -o '"current_location": "[^"]*"' | cut -d'"' -f4)
            if [ -n "$LOCATION" ] && [ "$LOCATION" != "null" ]; then
                echo ""
                # Minimal DM context - silently queries/auto-enhances
                # Note: scene command is quiet when no RAG exists; real errors will show
                CONTEXT=$(bash "$TOOLS_DIR/dm-enhance.sh" scene "$LOCATION")
                if [ -n "$CONTEXT" ]; then
                    echo "$CONTEXT"
                fi
            fi
        fi
        ;;

    end)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-session.sh end <summary>"
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
        bash "$TOOLS_DIR/dm-consequence.sh" check
        ;;

    status)
        echo "Campaign Status"
        echo "==============="
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" status
        ;;

    move)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-session.sh move <location>"
            exit 1
        fi
        echo "Moving Party"
        echo "============"
        echo ""
        dispatch_middleware "dm-session.sh" move "$@" || \
            $PYTHON_CMD "$LIB_DIR/session_manager.py" move "$@"
        RESULT=$?
        if [ $RESULT -ne 0 ]; then exit $RESULT; fi

        echo ""
        echo "Pending Consequences:"
        bash "$TOOLS_DIR/dm-consequence.sh" check

        # Auto-query RAG for new location context (DM-internal, minimal output)
        CAMPAIGN_DIR=$(bash "$TOOLS_DIR/dm-campaign.sh" path 2>/dev/null)
        if [ -d "$CAMPAIGN_DIR/vectors" ]; then
            echo ""
            # Minimal DM context - silently queries/auto-enhances
            # Note: scene command is quiet when no RAG exists; real errors will show
            CONTEXT=$(bash "$TOOLS_DIR/dm-enhance.sh" scene "$@")
            if [ -n "$CONTEXT" ]; then
                echo "$CONTEXT"
            fi
        fi
        ;;

    context)
        # Full session context — one command to load everything the DM needs
        CONTEXT_OUTPUT=$($PYTHON_CMD "$LIB_DIR/session_manager.py" context "$@")
        CONTEXT_STATUS=$?
        echo "$CONTEXT_OUTPUT"
        CONTEXT_CHARS=${#CONTEXT_OUTPUT}
        CONTEXT_TOKENS=$(estimate_tokens_from_chars "$CONTEXT_CHARS")
        FULL_FLAG=false
        for arg in "$@"; do [ "$arg" = "--full" ] && FULL_FLAG=true; done
        log_token_usage "dm-session-context" "full=$FULL_FLAG" "output_chars=$CONTEXT_CHARS" "output_tokens_est=$CONTEXT_TOKENS"
        exit $CONTEXT_STATUS
        ;;

    save)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-session.sh save <name>"
            echo ""
            echo "Existing saves:"
            $PYTHON_CMD "$LIB_DIR/session_manager.py" list-saves
            exit 1
        fi
        echo "Creating Save Point"
        echo "==================="
        echo ""
        $PYTHON_CMD "$LIB_DIR/session_manager.py" save "$@"
        ;;

    restore)
        if [ "$#" -lt 1 ]; then
            echo "Usage: dm-session.sh restore <save-name>"
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
            echo "Usage: dm-session.sh delete-save <name>"
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

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: start, end, status, move, context, save, restore, list-saves, delete-save, history"
        exit 1
        ;;
esac

# Propagate Python exit code
exit $?
