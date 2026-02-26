#!/bin/bash
# dm-campaign.sh - Multi-campaign management for DM tools
# Thin CLI wrapper - logic in lib/campaign_manager.py

# Source common utilities
source "$(dirname "$0")/common.sh"

ACTION=$1
shift

show_usage() {
    echo "Campaign Manager"
    echo "================"
    echo ""
    echo "Usage: dm-campaign.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  list                  - List all campaigns"
    echo "  switch <name>         - Switch to a different campaign"
    echo "  create <name>         - Create a new campaign"
    echo "  delete <name>         - Delete a campaign (requires confirmation)"
    echo "  info [name]           - Show campaign details (defaults to active)"
    echo "  active                - Show active campaign name"
    echo "  path [name]           - Show campaign directory path"
    echo ""
    echo "Examples:"
    echo "  dm-campaign.sh list                     # See all campaigns"
    echo "  dm-campaign.sh create conan             # Create campaign for Conan"
    echo "  dm-campaign.sh switch theron            # Switch to Theron's campaign"
    echo "  dm-campaign.sh info                     # Info about current campaign"
    echo ""
    echo "Current active campaign: $(get_active_campaign)"
}

case "$ACTION" in
    "list")
        $PYTHON_CMD "$LIB_DIR/campaign_manager.py" list
        ;;

    "switch")
        if [ -z "$1" ]; then
            echo "Usage: dm-campaign.sh switch <campaign_name>"
            echo ""
            echo "Available campaigns:"
            $PYTHON_CMD "$LIB_DIR/campaign_manager.py" list
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/campaign_manager.py" switch "$1"
        ;;

    "create")
        if [ -z "$1" ]; then
            echo "Usage: dm-campaign.sh create <name> [--campaign-name \"Display Name\"]"
            echo ""
            echo "Example: dm-campaign.sh create conan --campaign-name \"The Barbarian's Destiny\""
            exit 1
        fi
        NAME="$1"
        shift
        $PYTHON_CMD "$LIB_DIR/campaign_manager.py" create "$NAME" "$@"
        ;;

    "delete")
        if [ -z "$1" ]; then
            echo "Usage: dm-campaign.sh delete <campaign_name>"
            exit 1
        fi
        CAMPAIGN_NAME="$1"

        # Show info about what will be deleted
        echo "Campaign to delete: $CAMPAIGN_NAME"
        $PYTHON_CMD "$LIB_DIR/campaign_manager.py" info "$CAMPAIGN_NAME"
        echo ""

        read -p "Are you sure you want to DELETE this campaign? (type 'yes' to confirm): " CONFIRM

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
