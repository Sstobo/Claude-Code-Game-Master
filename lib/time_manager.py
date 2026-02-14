#!/usr/bin/env python3
"""Time management module for DM tools."""

import json
import sys
from pathlib import Path
from lib.campaign_manager import CampaignManager
from lib.json_ops import JsonOperations


class TimeManager:
    """Manage campaign time state."""

    def __init__(self, world_state_dir: str = "world-state", require_active_campaign: bool = True):
        if not require_active_campaign and world_state_dir != "world-state":
            # Direct campaign directory (for testing)
            self.campaign_dir = Path(world_state_dir)
            self.json_ops = JsonOperations(str(self.campaign_dir))
            self.campaign_mgr = None
        else:
            # Normal flow: require active campaign
            self.campaign_mgr = CampaignManager(world_state_dir)
            self.campaign_dir = self.campaign_mgr.get_active_campaign_dir()

            if self.campaign_dir is None:
                raise RuntimeError("No active campaign. Run /new-game or /import first.")

            self.json_ops = JsonOperations(str(self.campaign_dir))

    def update_time(self, time_of_day: str, date: str, elapsed_hours: int = 0, precise_time: str = None) -> bool:
        """
        Update campaign time and optionally apply time effects.

        Args:
            time_of_day: Descriptive time (e.g., "Evening", "Dawn")
            date: Campaign date string
            elapsed_hours: Hours that passed (manual, for time effects)
            precise_time: Exact time in HH:MM format (auto-calculates elapsed)

        Returns:
            bool: Success status
        """
        data = self.json_ops.load_json("campaign-overview.json")

        # Calculate elapsed_hours from precise_time if provided
        if precise_time:
            old_precise_time = data.get('precise_time')
            if old_precise_time:
                # Parse and calculate difference
                from datetime import datetime
                try:
                    old_dt = datetime.strptime(old_precise_time, "%H:%M")
                    new_dt = datetime.strptime(precise_time, "%H:%M")
                    elapsed_seconds = (new_dt - old_dt).total_seconds()

                    # Handle day rollover (negative elapsed)
                    if elapsed_seconds < 0:
                        elapsed_seconds += 24 * 3600

                    elapsed_hours = int(elapsed_seconds / 3600)
                    print(f"[AUTO] Calculated elapsed time: {elapsed_hours}h ({old_precise_time} → {precise_time})")
                except ValueError:
                    print(f"[WARNING] Invalid time format, using manual elapsed")

        # 1. Update time
        data['time_of_day'] = time_of_day
        data['current_date'] = date
        if precise_time:
            data['precise_time'] = precise_time

        results = {
            'time_updated': True,
            'custom_stats_changed': [],
            'consequences_triggered': [],
            'stat_consequences': []
        }

        # 2. Apply time effects if elapsed_hours > 0
        if elapsed_hours > 0:
            time_effects = data.get('campaign_rules', {}).get('time_effects', {})

            if time_effects.get('enabled'):
                # Apply custom stat changes
                stat_changes = self._apply_time_effects(elapsed_hours, time_effects)
                results['custom_stats_changed'] = stat_changes

                # Check stat consequences (hunger=0 → damage)
                stat_consequences = self._check_stat_consequences(elapsed_hours, time_effects)
                results['stat_consequences'] = stat_consequences

                # Check time-based consequences
                triggered = self._check_time_consequences(elapsed_hours)
                results['consequences_triggered'] = triggered

        # 3. Save updated campaign data
        if not self.json_ops.save_json("campaign-overview.json", data):
            print(f"[ERROR] Failed to update time")
            return False

        # 4. Print report
        self._print_time_report(time_of_day, date, precise_time, results)

        return True

    def add_time_hours(self, hours: float) -> bool:
        """
        Add hours to current time (helper method for testing).

        Args:
            hours: Hours to add

        Returns:
            bool: Success status
        """
        data = self.json_ops.load_json("campaign-overview.json")
        current_time = data.get('precise_time', '12:00')
        current_date = data.get('current_date', 'Day 1')

        # Parse current time
        from datetime import datetime, timedelta
        try:
            dt = datetime.strptime(current_time, "%H:%M")
            dt += timedelta(hours=hours)
            new_time = dt.strftime("%H:%M")

            # Determine time_of_day from hour
            hour = dt.hour
            if 5 <= hour < 12:
                time_of_day = "Morning"
            elif 12 <= hour < 17:
                time_of_day = "Day"
            elif 17 <= hour < 21:
                time_of_day = "Evening"
            else:
                time_of_day = "Night"

            return self.update_time(time_of_day, current_date, elapsed_hours=int(hours), precise_time=new_time)
        except Exception as e:
            print(f"[ERROR] Failed to add time: {e}")
            return False

    def get_time(self) -> dict:
        """Get current campaign time."""
        data = self.json_ops.load_json("campaign-overview.json")
        return {
            'time_of_day': data.get('time_of_day', 'Unknown'),
            'current_date': data.get('current_date', 'Unknown'),
            'precise_time': data.get('precise_time')
        }

    def _apply_time_effects(self, elapsed_hours: int, time_effects: dict) -> list:
        """Apply custom stat changes based on time_effects rules"""
        from lib.player_manager import PlayerManager

        # Check if we're in test mode (no campaign_mgr)
        if self.campaign_mgr is None:
            player_mgr = PlayerManager(str(self.campaign_dir), require_active_campaign=False)
        else:
            player_mgr = PlayerManager(str(self.campaign_dir.parent.parent))

        # Load active character
        campaign = self.json_ops.load_json("campaign-overview.json")
        char_name = campaign.get('current_character')

        if not char_name:
            return []

        changes = []
        rules = time_effects.get('rules', [])

        for rule in rules:
            stat = rule['stat']
            change_per_hour = rule.get('per_hour', 0)
            total_change = int(change_per_hour * elapsed_hours)

            if total_change != 0:
                # Use keyword arguments to be explicit
                result = player_mgr.modify_custom_stat(name=char_name, stat=stat, amount=total_change)
                if result.get('success'):
                    changes.append({
                        'stat': stat,
                        'old': result['old_value'],
                        'new': result['new_value'],
                        'change': total_change
                    })

        return changes

    def _check_stat_consequences(self, elapsed_hours: int, time_effects: dict) -> list:
        """Check and apply stat-based consequences (e.g., hunger=0 → damage)"""
        from lib.player_manager import PlayerManager

        # Check if we're in test mode (no campaign_mgr)
        if self.campaign_mgr is None:
            player_mgr = PlayerManager(str(self.campaign_dir), require_active_campaign=False)
        else:
            player_mgr = PlayerManager(str(self.campaign_dir.parent.parent))

        campaign = self.json_ops.load_json("campaign-overview.json")
        char_name = campaign.get('current_character')

        if not char_name:
            return []

        char = player_mgr.get_player(char_name)
        if not char:
            return []

        custom_stats = char.get('custom_stats', {})
        stat_consequences = time_effects.get('stat_consequences', {})

        triggered = []

        for consequence_name, consequence_data in stat_consequences.items():
            condition = consequence_data['condition']
            stat = condition['stat']
            operator = condition['operator']
            threshold = condition['value']

            if stat not in custom_stats:
                continue

            current_value = custom_stats[stat]['current']

            # Check condition
            met = False
            if operator == '<=':
                met = current_value <= threshold
            elif operator == '>=':
                met = current_value >= threshold
            elif operator == '==':
                met = current_value == threshold

            if met:
                # Apply effects
                for effect in consequence_data.get('effects', []):
                    effect_type = effect['type']

                    if effect_type == 'hp_damage':
                        damage = effect['amount']
                        if effect.get('per_hour'):
                            damage *= elapsed_hours
                        player_mgr.modify_hp(char_name, damage)

                    elif effect_type == 'condition':
                        player_mgr.modify_condition(char_name, 'add', effect['name'])

                    elif effect_type == 'message':
                        triggered.append({
                            'type': 'stat_consequence',
                            'name': consequence_name,
                            'message': effect['text']
                        })

        return triggered

    def _check_time_consequences(self, elapsed_hours: int) -> list:
        """Check and trigger time-based consequences"""
        data = self.json_ops.load_json("consequences.json")

        active = data.get('active', [])
        triggered = []
        remaining = []

        for consequence in active:
            trigger_hours = consequence.get('trigger_hours')

            if trigger_hours is None:
                # Event-based trigger, keep as-is
                remaining.append(consequence)
                continue

            # Update elapsed hours
            hours_elapsed = consequence.get('hours_elapsed', 0) + elapsed_hours
            consequence['hours_elapsed'] = hours_elapsed

            # Check if triggered
            if hours_elapsed >= trigger_hours:
                triggered.append({
                    'id': consequence['id'],
                    'consequence': consequence['consequence'],
                    'trigger': consequence['trigger']
                })

                # Move to resolved
                consequence['resolved'] = self.json_ops.get_timestamp()
                if 'resolved' not in data:
                    data['resolved'] = []
                data['resolved'].append(consequence)
            else:
                remaining.append(consequence)

        # Save updated consequences
        data['active'] = remaining
        self.json_ops.save_json("consequences.json", data)

        return triggered

    def _print_time_report(self, time_of_day: str, date: str, precise_time: str, results: dict):
        """Print formatted report of time update results"""
        time_str = f"{time_of_day}"
        if precise_time:
            time_str += f" ({precise_time})"

        print(f"[SUCCESS] Time updated to: {time_str}, {date}")

        # Custom stats changes
        if results['custom_stats_changed']:
            print("\nCustom Stats:")
            for change in results['custom_stats_changed']:
                stat = change['stat']
                old = change['old']
                new = change['new']
                delta = change['change']
                print(f"  {stat}: {old} → {new} ({delta:+d})")

        # Stat consequences (hunger=0 → damage)
        if results['stat_consequences']:
            print("\nStat Consequences:")
            for sc in results['stat_consequences']:
                print(f"  ⚠️ {sc['name']}: {sc['message']}")

        # Time consequences triggered
        if results['consequences_triggered']:
            print("\nTriggered Events:")
            for tc in results['consequences_triggered']:
                print(f"  ⚠️ [{tc['id']}] {tc['consequence']}")


def main():
    """CLI interface for time management."""
    import argparse

    parser = argparse.ArgumentParser(description='Campaign time management')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Update time
    update_parser = subparsers.add_parser('update', help='Update campaign time')
    update_parser.add_argument('time_of_day', help='Descriptive time (e.g., "Evening", "Dawn")')
    update_parser.add_argument('date', help='Campaign date')
    update_parser.add_argument('--elapsed', type=int, default=0, help='Hours elapsed (manual)')
    update_parser.add_argument('--precise-time', help='Exact time HH:MM (auto-calculates elapsed)')

    # Get time
    subparsers.add_parser('get', help='Get current campaign time')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    try:
        manager = TimeManager()

        if args.action == 'update':
            if not manager.update_time(
                args.time_of_day,
                args.date,
                elapsed_hours=args.elapsed,
                precise_time=args.precise_time
            ):
                sys.exit(1)

        elif args.action == 'get':
            time_info = manager.get_time()
            print(f"Time: {time_info['time_of_day']}")
            print(f"Date: {time_info['current_date']}")
            if time_info.get('precise_time'):
                print(f"Precise: {time_info['precise_time']}")

    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
