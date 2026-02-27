#!/usr/bin/env python3
"""
Encounter Engine — standalone module for random encounters with waypoints.

Imports CORE's JsonOperations, dice, TimeManager, PlayerManager.
CORE has zero knowledge of this module.
DM (Claude) calls this via dm-encounter.sh during/after travel.
"""

import sys
import json
import math
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.json_ops import JsonOperations
from lib.dice import roll as dice_roll
from lib.time_manager import TimeManager
from lib.player_manager import PlayerManager
MODULE_LIB = Path(__file__).parent
sys.path.insert(0, str(MODULE_LIB))
from connection_utils import add_canonical_connection


class EncounterEngine:
    def __init__(self, campaign_dir: str):
        self.campaign_dir = Path(campaign_dir)
        self.json_ops = JsonOperations(str(self.campaign_dir))
        # Lazy init managers (they may fail if campaign not ready)
        self._time_mgr = None
        self._player_mgr = None

    @property
    def time_mgr(self):
        if self._time_mgr is None:
            self._time_mgr = TimeManager(str(self.campaign_dir))
        return self._time_mgr

    @property
    def player_mgr(self):
        if self._player_mgr is None:
            self._player_mgr = PlayerManager(str(self.campaign_dir))
        return self._player_mgr

    def is_enabled(self) -> bool:
        """Check if encounter system is enabled"""
        overview = self.json_ops.load_json("campaign-overview.json") or {}
        rules = overview.get('campaign_rules', {}).get('encounter_system', {})
        return rules.get('enabled', False)

    def get_rules(self) -> dict:
        """Get encounter system rules"""
        overview = self.json_ops.load_json("campaign-overview.json") or {}
        return overview.get('campaign_rules', {}).get('encounter_system', {})

    def calculate_segments(self, distance_meters: float) -> int:
        """How many segments (checks) for given distance"""
        distance_km = distance_meters / 1000

        if distance_km < 1:
            return 1
        elif distance_km < 3:
            return 1
        elif distance_km < 6:
            return 2
        else:
            return 3

    def calculate_dc(self, segment_distance_km: float, time_of_day: str) -> int:
        """
        Calculate DC for AVOIDING encounter
        Longer distance → higher DC → harder to avoid
        """
        rules = self.get_rules()

        base_dc = rules.get('base_dc', 15)
        dist_mod = rules.get('distance_modifier', 2)
        time_mods = rules.get('time_dc_modifiers', {})
        time_mod = time_mods.get(time_of_day, 0)

        # Longer distance = HARDER to avoid (plus!)
        dc = base_dc + int(segment_distance_km * dist_mod) + time_mod

        # Max DC 30 (needs nat 20 to avoid)
        return min(30, dc)

    def get_character_modifier(self) -> int:
        """Get character modifier for check"""
        rules = self.get_rules()
        stat_name = rules.get('stat_to_use', 'stealth')

        # Read character directly via json_ops (without player_mgr)
        character = self.json_ops.load_json('character.json')
        if not character:
            return 0

        # If custom stat
        if stat_name.startswith('custom:'):
            custom_stat = stat_name.replace('custom:', '')
            custom_stats = character.get('custom_stats', {})
            stat_value = custom_stats.get(custom_stat, {}).get('current', 10)
            # Assume custom stats work like abilities (0-100 → -5 to +5)
            return (stat_value - 50) // 10

        # If skill
        if stat_name.startswith('skill:'):
            skill_name = stat_name.replace('skill:', '')
            skills = character.get('skills', {})
            return skills.get(skill_name, 0)

        # If standard D&D stat
        abilities = character.get('abilities', {})
        stat_value = abilities.get(stat_name, 10)
        return (stat_value - 10) // 2

    def roll_encounter_check(self, segment_km: float, segment_num: int,
                            total_segments: int, time_of_day: str) -> dict:
        """Perform one encounter check"""
        dc = self.calculate_dc(segment_km, time_of_day)
        modifier = self.get_character_modifier()

        roll = dice_roll("1d20")
        total = roll + modifier
        triggered = total < dc

        return {
            'segment': segment_num,
            'total_segments': total_segments,
            'segment_km': segment_km,
            'roll': roll,
            'modifier': modifier,
            'dc': dc,
            'total': total,
            'triggered': triggered,
            'time_of_day': time_of_day
        }

    def roll_encounter_nature(self) -> dict:
        """Determine encounter nature (1-20)"""
        rules = self.get_rules()
        roll = dice_roll("1d20")

        # Optional: add luck modifier
        if rules.get('use_luck', False):
            character = self.player_mgr.get_player()
            if character:
                luck = character.get('abilities', {}).get('luck', 10)
                luck_mod = (luck - 10) // 2
                roll += luck_mod

        # Interpretation
        if roll <= 5:
            category = "Dangerous"
        elif roll <= 10:
            category = "Neutral"
        elif roll <= 15:
            category = "Beneficial"
        else:
            category = "Special"

        return {
            'roll': roll,
            'category': category
        }

    def check_journey(self, from_loc: str, to_loc: str,
                     distance_meters: float, terrain: str,
                     speed_kmh: float = 4.0) -> dict:
        """
        Full journey check with waypoints

        Returns:
        {
            'waypoints': [
                {
                    'segment': 1,
                    'distance_traveled_m': 1667,
                    'time_elapsed_min': 25,
                    'encounter': {...} or None,
                    'current_time': "08:25",
                    'can_turn_back': True
                },
                ...
            ],
            'total_distance_m': 5000,
            'total_time_min': 75,
            'total_encounters': 2
        }
        """
        rules = self.get_rules()
        min_distance = rules.get('min_distance_meters', 300)

        # If too close - skip
        if distance_meters < min_distance:
            return {
                'skipped': True,
                'reason': f'Too short (< {min_distance}m)',
                'waypoints': [],
                'total_distance_m': distance_meters,
                'total_time_min': (distance_meters / 1000) / speed_kmh * 60,
                'total_encounters': 0,
                'from_location': from_loc,
                'to_location': to_loc,
                'terrain': terrain
            }

        # Determine number of segments
        num_segments = self.calculate_segments(distance_meters)
        segment_distance_m = distance_meters / num_segments
        segment_distance_km = segment_distance_m / 1000

        # Time per segment (in minutes)
        segment_time_min = (segment_distance_km / speed_kmh) * 60

        # Current time
        overview = self.json_ops.load_json("campaign-overview.json") or {}
        current_time = overview.get('precise_time', '08:00')
        time_of_day = overview.get('time_of_day', 'Day')

        waypoints = []
        total_encounters = 0
        cumulative_distance = 0
        cumulative_time = 0

        for i in range(num_segments):
            segment_num = i + 1

            # Perform encounter check
            check_result = self.roll_encounter_check(
                segment_km=segment_distance_km,
                segment_num=segment_num,
                total_segments=num_segments,
                time_of_day=time_of_day
            )

            # Update progress
            cumulative_distance += segment_distance_m
            cumulative_time += segment_time_min

            # Calculate current time
            hours, minutes = map(int, current_time.split(':'))
            new_time = datetime(2000, 1, 1, hours, minutes) + timedelta(minutes=cumulative_time)
            new_time_str = new_time.strftime("%H:%M")

            waypoint = {
                'segment': segment_num,
                'distance_traveled_m': int(cumulative_distance),
                'distance_remaining_m': int(distance_meters - cumulative_distance),
                'time_elapsed_min': int(cumulative_time),
                'current_time': new_time_str,
                'check': check_result,
                'encounter': None,
                'can_turn_back': segment_num < num_segments  # Last segment - arrived
            }

            # If encounter triggered
            if check_result['triggered']:
                nature = self.roll_encounter_nature()
                waypoint['encounter'] = nature
                total_encounters += 1

            waypoints.append(waypoint)

        return {
            'skipped': False,
            'waypoints': waypoints,
            'total_distance_m': distance_meters,
            'total_time_min': int(cumulative_time),
            'total_encounters': total_encounters,
            'from_location': from_loc,
            'to_location': to_loc,
            'terrain': terrain
        }

    def create_waypoint_location(self, from_loc: str, to_loc: str,
                                waypoint_data: dict, journey: dict) -> str:
        """Create temporary waypoint location"""
        segment = waypoint_data['segment']
        total_segments = waypoint_data['check']['total_segments']

        # Unique name
        waypoint_name = f"waypoint_{from_loc.lower().replace(' ', '_')}_{to_loc.lower().replace(' ', '_')}_seg{segment}"

        # Coordinates - segment midpoint
        locations = self.json_ops.load_json("locations.json") or {}
        from_coords = locations.get(from_loc, {}).get('coordinates', {'x': 0, 'y': 0})
        to_coords = locations.get(to_loc, {}).get('coordinates', {'x': 0, 'y': 0})

        # Progress in percent - SEGMENT MIDPOINT, not end!
        # For segment N of total_segments waypoint at segment middle
        segment_progress = (segment - 0.5) / total_segments
        progress_ratio = segment_progress

        waypoint_x = from_coords['x'] + (to_coords['x'] - from_coords['x']) * progress_ratio
        waypoint_y = from_coords['y'] + (to_coords['y'] - from_coords['y']) * progress_ratio

        # Recalculate distances for segment midpoint
        waypoint_distance_traveled = int(journey['total_distance_m'] * progress_ratio)
        waypoint_distance_remaining = journey['total_distance_m'] - waypoint_distance_traveled

        waypoint = {
            "is_waypoint": True,
            "original_journey": {
                "from": from_loc,
                "to": to_loc,
                "segment": segment,
                "total_segments": total_segments,
                "progress_meters": waypoint_distance_traveled,
                "remaining_meters": waypoint_distance_remaining,
                "terrain": journey['terrain']
            },
            "coordinates": {
                "x": int(waypoint_x),
                "y": int(waypoint_y)
            },
            "diameter_meters": 10,
            "description": f"Stopped midway between {from_loc} and {to_loc}",
            "connections": []
        }

        locations[waypoint_name] = waypoint

        add_canonical_connection(waypoint_name, from_loc, locations,
            path="turn back",
            distance_meters=waypoint_distance_traveled,
            bearing=180,
            terrain=journey['terrain'])

        add_canonical_connection(waypoint_name, to_loc, locations,
            path="continue forward",
            distance_meters=waypoint_distance_remaining,
            bearing=0,
            terrain=journey['terrain'])

        self.json_ops.save_json("locations.json", locations)

        return waypoint_name

    def cleanup_waypoint(self, waypoint_name: str):
        """Remove waypoint after leaving"""
        locations = self.json_ops.load_json("locations.json") or {}

        if waypoint_name in locations and locations[waypoint_name].get('is_waypoint'):
            del locations[waypoint_name]
            self.json_ops.save_json("locations.json", locations)
            print(f"[CLEANUP] Removed waypoint: {waypoint_name}")

    def is_waypoint(self, location_name: str) -> bool:
        """Check if location is a waypoint"""
        locations = self.json_ops.load_json("locations.json") or {}
        return locations.get(location_name, {}).get('is_waypoint', False)

    def get_waypoint_options(self, waypoint_name: str) -> dict:
        """Get waypoint options (forward/back)"""
        locations = self.json_ops.load_json("locations.json") or {}
        waypoint = locations.get(waypoint_name, {})

        if not waypoint.get('is_waypoint'):
            return None

        journey = waypoint['original_journey']

        return {
            'forward': {
                'to': journey['to'],
                'distance_m': journey['remaining_meters'],
                'segment_start': journey['segment']
            },
            'back': {
                'to': journey['from'],
                'distance_m': journey['progress_meters']
            }
        }

    def format_journey_output(self, journey: dict) -> str:
        """Format journey output for DM"""
        if journey.get('skipped'):
            from_loc = journey.get('from_location', 'Unknown')
            to_loc = journey.get('to_location', 'Unknown')
            return f"""
[TRAVEL] {from_loc} → {to_loc}
Distance: {journey['total_distance_m']}m
Time: {journey['total_time_min']} minutes

{journey['reason']} - No encounter checks.
"""

        output = []
        output.append("=" * 70)
        output.append(f"  JOURNEY: {journey['from_location']} → {journey['to_location']}")
        output.append("=" * 70)
        output.append(f"Total distance: {journey['total_distance_m']}m ({journey['total_distance_m']/1000:.1f}km)")
        output.append(f"Terrain: {journey['terrain']}")
        output.append(f"Segments: {len(journey['waypoints'])}")
        output.append("")

        for wp in journey['waypoints']:
            check = wp['check']
            output.append("-" * 70)
            output.append(f"SEGMENT {wp['segment']}/{check['total_segments']}")
            output.append(f"Progress: {wp['distance_traveled_m']}m / {journey['total_distance_m']}m")
            output.append(f"Time: {wp['current_time']} (+{wp['time_elapsed_min']} min elapsed)")
            output.append("")
            output.append(f"🎲 Encounter Check:")
            output.append(f"  Roll: {check['roll']} + {check['modifier']} = {check['total']} vs DC {check['dc']}")
            output.append(f"  Result: {'✗ ENCOUNTER TRIGGERED' if check['triggered'] else '✓ AVOIDED'}")

            if wp['encounter']:
                enc = wp['encounter']
                output.append("")
                output.append(f"🎲 Encounter Nature: {enc['roll']} → {enc['category']}")
                output.append("")
                output.append("DM: Describe what happens...")
                output.append("")

                if wp['can_turn_back']:
                    output.append("Player is at a waypoint:")
                    output.append("  [F]orward - Continue journey")
                    output.append("  [B]ack - Return to " + journey['from_location'])

            output.append("")

        output.append("=" * 70)
        output.append(f"Journey complete: {journey['total_encounters']} encounter(s)")
        output.append("=" * 70)

        return "\n".join(output)


def main():
    import sys

    if len(sys.argv) < 4:
        print("Usage: encounter_engine.py <from_loc> <to_loc> <distance_m> [terrain]")
        sys.exit(1)

    # Get active campaign
    active_campaign_file = Path("world-state/active-campaign.txt")
    if not active_campaign_file.exists():
        print("[ERROR] No active campaign")
        sys.exit(1)

    campaign_name = active_campaign_file.read_text().strip()
    campaign_dir = f"world-state/campaigns/{campaign_name}"

    from_loc = sys.argv[1]
    to_loc = sys.argv[2]
    distance_m = float(sys.argv[3])
    terrain = sys.argv[4] if len(sys.argv) > 4 else "open"

    engine = EncounterEngine(campaign_dir)

    if not engine.is_enabled():
        print("[INFO] Encounter system is disabled")
        sys.exit(0)

    journey = engine.check_journey(from_loc, to_loc, distance_m, terrain)
    print(engine.format_journey_output(journey))


if __name__ == "__main__":
    main()
