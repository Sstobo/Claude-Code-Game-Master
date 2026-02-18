#!/usr/bin/env python3
"""Time management module for DM tools."""

import json
import sys
from pathlib import Path
from lib.campaign_manager import CampaignManager
from lib.json_ops import JsonOperations


class TimeManager:
    """Manage campaign time state."""

    def __init__(self, world_state_dir: str = "world-state"):
        self.campaign_mgr = CampaignManager(world_state_dir)
        self.campaign_dir = self.campaign_mgr.get_active_campaign_dir()

        if self.campaign_dir is None:
            raise RuntimeError("No active campaign. Run /new-game or /import first.")

        self.json_ops = JsonOperations(str(self.campaign_dir))

    def update_time(self, time_of_day: str, date: str) -> bool:
        """Update the campaign time and date."""
        data = self.json_ops.load_json("campaign-overview.json")

        data['time_of_day'] = time_of_day
        data['current_date'] = date

        if not self.json_ops.save_json("campaign-overview.json", data):
            print(f"[ERROR] Failed to update time")
            return False

        print(f"[SUCCESS] Time updated to: {time_of_day}, {date}")
        return True

    def get_time(self) -> dict:
        """Get current campaign time."""
        data = self.json_ops.load_json("campaign-overview.json")
        return {
            'time_of_day': data.get('time_of_day', 'Unknown'),
            'current_date': data.get('current_date', 'Unknown')
        }


def main():
    """CLI interface for time management."""
    if len(sys.argv) < 2:
        print("Usage: python -m lib.time_manager update <time_of_day> <date>")
        print("       python -m lib.time_manager get")
        sys.exit(1)

    action = sys.argv[1]

    try:
        manager = TimeManager()

        if action == 'update':
            if len(sys.argv) < 4:
                print("Usage: python -m lib.time_manager update <time_of_day> <date>")
                sys.exit(1)
            time_of_day = sys.argv[2]
            date = sys.argv[3]
            if not manager.update_time(time_of_day, date):
                sys.exit(1)

        elif action == 'get':
            time_info = manager.get_time()
            print(f"Time: {time_info['time_of_day']}")
            print(f"Date: {time_info['current_date']}")

        else:
            print(f"Unknown action: {action}")
            sys.exit(1)

    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
