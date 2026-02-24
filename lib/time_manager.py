#!/usr/bin/env python3
"""Time management module for DM tools."""

import sys
import re
from pathlib import Path
from lib.campaign_manager import CampaignManager
from lib.json_ops import JsonOperations

TIME_OF_DAY_MAP = {
    "Night": "03:00", "Early Morning": "06:00", "Morning": "08:00",
    "Late Morning": "10:00", "Noon": "12:00", "Afternoon": "14:00",
    "Evening": "18:00", "Late Evening": "21:00",
}

CLOCK_TO_TOD = [
    (6, "Night"), (8, "Early Morning"), (10, "Morning"),
    (12, "Late Morning"), (13, "Noon"), (17, "Afternoon"),
    (21, "Evening"), (24, "Late Evening"),
]


def _parse_clock(s: str) -> tuple[int, int] | None:
    m = re.match(r'^(\d{1,2}):(\d{2})$', s.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def _tod_from_hour(h: int) -> str:
    for threshold, label in CLOCK_TO_TOD:
        if h < threshold:
            return label
    return "Night"


def _fmt_clock(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"


def _fmt_total(total_hours: float) -> str:
    days = int(total_hours // 24)
    hours = total_hours - days * 24
    if days > 0:
        return f"day {days + 1}, {hours:.1f}h"
    return f"{hours:.1f}h"


class TimeManager:
    """Manage campaign time state."""

    def __init__(self, world_state_dir: str = "world-state"):
        self.campaign_mgr = CampaignManager(world_state_dir)
        self.campaign_dir = self.campaign_mgr.get_active_campaign_dir()

        if self.campaign_dir is None:
            raise RuntimeError("No active campaign. Run /new-game or /import first.")

        self.json_ops = JsonOperations(str(self.campaign_dir))

    def _get_clock(self, data: dict) -> tuple[int, int]:
        raw = data.get('clock')
        if raw:
            parsed = _parse_clock(raw)
            if parsed:
                return parsed
        tod = data.get('time_of_day', 'Morning')
        fallback = TIME_OF_DAY_MAP.get(tod, '08:00')
        parsed = _parse_clock(fallback)
        return parsed if parsed else (8, 0)

    def update_time(self, time_of_day: str, date: str,
                    elapsed_hours: float = 0.0) -> dict:
        data = self.json_ops.load_json("campaign-overview.json")
        old_h, old_m = self._get_clock(data)

        if elapsed_hours > 0:
            total_min = old_h * 60 + old_m + int(elapsed_hours * 60)
            new_h = (total_min // 60) % 24
            new_m = total_min % 60
            auto_tod = _tod_from_hour(new_h)
            data['clock'] = _fmt_clock(new_h, new_m)
            data['time_of_day'] = auto_tod
            data['current_date'] = date
            prev = data.get('total_hours_elapsed', 0.0)
            data['total_hours_elapsed'] = round(prev + elapsed_hours, 2)
        else:
            clock_parsed = _parse_clock(time_of_day)
            if clock_parsed:
                data['clock'] = _fmt_clock(*clock_parsed)
                data['time_of_day'] = _tod_from_hour(clock_parsed[0])
            else:
                if time_of_day in TIME_OF_DAY_MAP:
                    data['clock'] = TIME_OF_DAY_MAP[time_of_day]
                data['time_of_day'] = time_of_day
            data['current_date'] = date

        if not self.json_ops.save_json("campaign-overview.json", data):
            print("[ERROR] Failed to update time")
            return {'elapsed': 0.0}

        clock_str = data.get('clock', '??:??')
        print(f"[SUCCESS] Time: {data['time_of_day']}, {date} [{clock_str}]")
        if elapsed_hours > 0:
            print(f"[TIME] +{elapsed_hours}h elapsed "
                  f"(total: {_fmt_total(data['total_hours_elapsed'])})")
            self._tick_consequences(elapsed_hours)

        return {'elapsed': elapsed_hours}

    def advance_to(self, target_clock: str, date: str) -> dict:
        data = self.json_ops.load_json("campaign-overview.json")
        old_h, old_m = self._get_clock(data)
        parsed = _parse_clock(target_clock)
        if not parsed:
            print(f"[ERROR] Invalid time format: {target_clock} (use HH:MM)")
            return {'elapsed': 0.0}
        new_h, new_m = parsed

        old_total = old_h * 60 + old_m
        new_total = new_h * 60 + new_m
        if new_total <= old_total:
            new_total += 24 * 60

        elapsed_min = new_total - old_total
        elapsed_hours = round(elapsed_min / 60, 2)

        data['clock'] = _fmt_clock(new_h, new_m)
        data['time_of_day'] = _tod_from_hour(new_h)
        data['current_date'] = date
        prev = data.get('total_hours_elapsed', 0.0)
        data['total_hours_elapsed'] = round(prev + elapsed_hours, 2)

        if not self.json_ops.save_json("campaign-overview.json", data):
            print("[ERROR] Failed to update time")
            return {'elapsed': 0.0}

        print(f"[SUCCESS] Time: {data['time_of_day']}, {date} [{data['clock']}]")
        print(f"[TIME] +{elapsed_hours}h elapsed "
              f"(total: {_fmt_total(data['total_hours_elapsed'])})")
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
        h, m = self._get_clock(data)
        return {
            'time_of_day': data.get('time_of_day', 'Unknown'),
            'clock': data.get('clock', _fmt_clock(h, m)),
            'current_date': data.get('current_date', 'Unknown'),
            'total_hours_elapsed': data.get('total_hours_elapsed', 0.0),
        }


def main():
    """CLI interface for time management."""
    import argparse

    parser = argparse.ArgumentParser(description="DM time management")
    subparsers = parser.add_subparsers(dest='action')

    upd = subparsers.add_parser('update', help='Update campaign time')
    upd.add_argument('time_of_day', help='Time of day or HH:MM clock')
    upd.add_argument('date', nargs='+', help='Current in-game date')
    upd.add_argument('--elapsed', type=float, default=0.0,
                     help='Hours elapsed (auto-advances clock & ticks consequences)')
    upd.add_argument('--to', dest='advance_to', default=None,
                     help='Advance to specific time HH:MM (auto-calculates elapsed)')

    subparsers.add_parser('get', help='Show current time')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    try:
        manager = TimeManager()

        if args.action == 'update':
            date_str = ' '.join(args.date)
            if args.advance_to:
                manager.advance_to(args.advance_to, date_str)
            elif args.elapsed > 0:
                manager.update_time(args.time_of_day, date_str, args.elapsed)
            else:
                manager.update_time(args.time_of_day, date_str)

        elif args.action == 'get':
            t = manager.get_time()
            print(f"Time: {t['time_of_day']} [{t.get('clock', '??:??')}]")
            print(f"Date: {t['current_date']}")
            print(f"Total hours elapsed: {t['total_hours_elapsed']}")

    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
