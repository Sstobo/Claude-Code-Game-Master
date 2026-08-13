#!/bin/bash
# gm-campaign.sh - Multi-campaign management for GM tools
# Thin CLI wrapper - logic in lib/campaign_manager.py

# Source common utilities
source "$(dirname "$0")/common.sh"

ACTION=$1
shift

show_usage() {
    echo "Campaign Manager"
    echo "================"
    echo ""
    echo "Usage: gm-campaign.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  list                  - List all campaigns"
    echo "  switch <name>         - Switch to a different campaign"
    echo "  create <name>         - Create a new campaign"
    echo "  delete <name> [--yes] - Delete a campaign (requires confirmation)"
    echo "  info [name]           - Show campaign details (defaults to active)"
    echo "  active                - Show active campaign name"
    echo "  path [name]           - Show campaign directory path"
    echo ""
    echo "Examples:"
    echo "  gm-campaign.sh list                     # See all campaigns"
    echo "  gm-campaign.sh create conan             # Create campaign for Conan"
    echo "  gm-campaign.sh switch theron            # Switch to Theron's campaign"
    echo "  gm-campaign.sh info                     # Info about current campaign"
    echo ""
    echo "Current active campaign: $(get_active_campaign)"
}

case "$ACTION" in
    "list")
        $PYTHON_CMD "$LIB_DIR/campaign_manager.py" list
        ;;

    "switch")
        if [ -z "$1" ]; then
            echo "Usage: gm-campaign.sh switch <campaign_name>"
            echo ""
            echo "Available campaigns:"
            $PYTHON_CMD "$LIB_DIR/campaign_manager.py" list
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/campaign_manager.py" switch "$1"
        ;;

    "create")
        if [ -z "$1" ]; then
            echo "Usage: gm-campaign.sh create <name> [--campaign-name \"Display Name\"]"
            echo ""
            echo "Example: gm-campaign.sh create conan --campaign-name \"The Barbarian's Destiny\""
            exit 1
        fi
        NAME="$1"
        shift
        $PYTHON_CMD "$LIB_DIR/campaign_manager.py" create "$NAME" "$@"
        ;;

    "delete")
        # A flag in the name slot means the name was omitted — never treat it as one.
        case "${1:-}" in
            ""|-*)
                echo "Usage: gm-campaign.sh delete <campaign_name> [--yes]"
                exit 1
                ;;
        esac
        CAMPAIGN_NAME="$1"
        shift

        # --yes / --confirm: delete without prompting (non-interactive use)
        ASSUME_YES=0
        for arg in "$@"; do
            case "$arg" in
                --yes|--confirm) ASSUME_YES=1 ;;
            esac
        done

        # Show info about what will be deleted
        echo "Campaign to delete: $CAMPAIGN_NAME"
        $PYTHON_CMD "$LIB_DIR/campaign_manager.py" info "$CAMPAIGN_NAME"
        echo ""

        CONFIRM="yes"
        if [ "$ASSUME_YES" -eq 0 ]; then
            if [ ! -t 0 ]; then
                error "No terminal to confirm on. Re-run with --yes to delete non-interactively."
                exit 1
            fi
            read -p "Are you sure you want to DELETE this campaign? (type 'yes' to confirm): " CONFIRM
        fi

        if [ "$CONFIRM" = "yes" ]; then
            $PYTHON_CMD "$LIB_DIR/campaign_manager.py" delete "$CAMPAIGN_NAME" --confirm
        else
            echo "Deletion cancelled."
        fi
        ;;

    "info")
        if [ -z "$1" ]; then
            $PYTHON_CMD "$LIB_DIR/campaign_manager.py" info
        else
            $PYTHON_CMD "$LIB_DIR/campaign_manager.py" info "$1"
        fi
        ;;

    "active")
        $PYTHON_CMD "$LIB_DIR/campaign_manager.py" active
        ;;

    "path")
        if [ -z "$1" ]; then
            $PYTHON_CMD "$LIB_DIR/campaign_manager.py" path
        else
            $PYTHON_CMD "$LIB_DIR/campaign_manager.py" path "$1"
        fi
        ;;

    "")
        show_usage
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo ""
        show_usage
        exit 1
        ;;
esac
