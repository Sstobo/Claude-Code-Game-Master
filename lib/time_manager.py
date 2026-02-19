#!/usr/bin/env python3
"""Time management module for DM tools."""

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

    def update_time(self, time_of_day: str, date: str,
                    elapsed_hours: float = 0.0) -> dict:
        """Update campaign time. If elapsed_hours > 0, advances total_hours_elapsed
        and triggers timed consequences. Returns {'elapsed': float}."""
        data = self.json_ops.load_json("campaign-overview.json")
        data['time_of_day'] = time_of_day
        data['current_date'] = date

        if elapsed_hours > 0:
            prev = data.get('total_hours_elapsed', 0.0)
            data['total_hours_elapsed'] = round(prev + elapsed_hours, 2)

        if not self.json_ops.save_json("campaign-overview.json", data):
            print("[ERROR] Failed to update time")
            return {'elapsed': 0.0}

        print(f"[SUCCESS] Time updated to: {time_of_day}, {date}")
        if elapsed_hours > 0:
            print(f"[TIME] +{elapsed_hours}h elapsed "
                  f"(total: {data['total_hours_elapsed']}h)")
            self._tick_consequences(elapsed_hours)

        return {'elapsed': elapsed_hours}

    def _tick_consequences(self, elapsed_hours: float):
        """Delegate consequence ticking to ConsequenceManager."""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from consequence_manager import ConsequenceManager
            mgr = ConsequenceManager()
            mgr.tick(elapsed_hours)
        except Exception as e:
            print(f"[WARNING] Could not tick consequences: {e}")

    def get_time(self) -> dict:
        """Get current campaign time."""
        data = self.json_ops.load_json("campaign-overview.json")
        return {
            'time_of_day': data.get('time_of_day', 'Unknown'),
            'current_date': data.get('current_date', 'Unknown'),
            'total_hours_elapsed': data.get('total_hours_elapsed', 0.0),
        }


def main():
    """CLI interface for time management."""
    import argparse

    parser = argparse.ArgumentParser(description="DM time management")
    subparsers = parser.add_subparsers(dest='action')

    upd = subparsers.add_parser('update', help='Update campaign time')
    upd.add_argument('time_of_day', help='Time of day (Morning, Noon, Evening, Night, ...)')
    upd.add_argument('date', help='Current in-game date')
    upd.add_argument('--elapsed', type=float, default=0.0,
                     help='Hours elapsed since last update (triggers consequence tick)')

    subparsers.add_parser('get', help='Show current time')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    try:
        manager = TimeManager()

        if args.action == 'update':
            manager.update_time(args.time_of_day, args.date, args.elapsed)

        elif args.action == 'get':
            t = manager.get_time()
            print(f"Time: {t['time_of_day']}")
            print(f"Date: {t['current_date']}")
            print(f"Total hours elapsed: {t['total_hours_elapsed']}")

    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
