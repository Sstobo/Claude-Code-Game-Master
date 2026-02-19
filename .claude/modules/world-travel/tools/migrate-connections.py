#!/usr/bin/env python3
"""
Migrate bidirectional connections to canonical unidirectional storage.
Each edge stored ONCE in alphabetically-first location.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
from connection_utils import canonical_pair


def metadata_score(conn: dict) -> int:
    score = 0
    if conn.get('distance_meters'):
        score += 3
    if conn.get('terrain') and conn['terrain'] != 'open':
        score += 2
    if conn.get('bearing') is not None:
        score += 2
    if conn.get('path') and conn['path'] != 'traveled':
        score += 1
    return score


def merge_connections(conn_a: dict, conn_b: dict) -> dict:
    if metadata_score(conn_a) >= metadata_score(conn_b):
        best = dict(conn_a)
    else:
        best = dict(conn_b)

    for key in ['distance_meters', 'terrain', 'bearing', 'path']:
        if not best.get(key) and conn_b.get(key):
            best[key] = conn_b[key]
        if not best.get(key) and conn_a.get(key):
            best[key] = conn_a[key]

    return best


def migrate_campaign(locations_file: Path, apply: bool = False) -> dict:
    with open(locations_file, 'r', encoding='utf-8') as f:
        locations = json.load(f)

    stats = {'pairs_found': 0, 'duplicates_removed': 0, 'already_canonical': 0}

    seen_pairs = set()
    removals = []

    for loc_name, loc_data in locations.items():
        if loc_data.get('is_waypoint'):
            continue

        for conn in loc_data.get('connections', []):
            to_loc = conn.get('to')
            if not to_loc or to_loc not in locations:
                continue
            if locations.get(to_loc, {}).get('is_waypoint'):
                continue

            pair = canonical_pair(loc_name, to_loc)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            first, second = pair
            forward = None
            reverse = None

            for c in locations.get(first, {}).get('connections', []):
                if c.get('to') == second:
                    forward = c
                    break

            for c in locations.get(second, {}).get('connections', []):
                if c.get('to') == first:
                    reverse = c
                    break

            if forward and reverse:
                stats['pairs_found'] += 1
                merged = merge_connections(forward, reverse)
                merged['to'] = second

                if 'bearing' in reverse and reverse is merged:
                    pass

                removals.append({
                    'pair': pair,
                    'keep_in': first,
                    'remove_from': second,
                    'merged': merged,
                    'old_forward_score': metadata_score(forward),
                    'old_reverse_score': metadata_score(reverse)
                })
                stats['duplicates_removed'] += 1
            elif forward and not reverse:
                stats['already_canonical'] += 1
            elif not forward and reverse:
                stats['pairs_found'] += 1
                moved = dict(reverse)
                moved['to'] = second
                if 'bearing' in moved and moved['bearing'] is not None:
                    moved['bearing'] = (moved['bearing'] + 180) % 360
                removals.append({
                    'pair': pair,
                    'keep_in': first,
                    'remove_from': second,
                    'merged': moved,
                    'old_forward_score': 0,
                    'old_reverse_score': metadata_score(reverse)
                })
                stats['duplicates_removed'] += 1

    for removal in removals:
        first, second = removal['pair']
        merged = removal['merged']

        print(f"  {first} ↔ {second}:")
        print(f"    Keep in: {first} (score: fwd={removal['old_forward_score']}, rev={removal['old_reverse_score']})")
        if merged.get('distance_meters'):
            print(f"    Distance: {merged['distance_meters']}m, Terrain: {merged.get('terrain', 'open')}")

        if apply:
            locations[first]['connections'] = [
                c for c in locations[first].get('connections', [])
                if c.get('to') != second
            ]
            locations[first]['connections'].append(merged)

            locations[second]['connections'] = [
                c for c in locations[second].get('connections', [])
                if c.get('to') != first
            ]

    if apply and removals:
        with open(locations_file, 'w', encoding='utf-8') as f:
            json.dump(locations, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Saved {locations_file}")

    return stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Migrate connections to canonical storage')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default: dry-run)')
    parser.add_argument('--campaign', help='Specific campaign name (default: all)')
    args = parser.parse_args()

    campaigns_dir = Path(__file__).parent.parent / 'world-state' / 'campaigns'
    if not campaigns_dir.exists():
        print("[ERROR] No campaigns directory found")
        sys.exit(1)

    if args.campaign:
        campaign_dirs = [campaigns_dir / args.campaign]
    else:
        campaign_dirs = sorted(campaigns_dir.iterdir())

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"{'='*60}")
    print(f"  Connection Migration ({mode})")
    print(f"{'='*60}\n")

    total_stats = {'pairs_found': 0, 'duplicates_removed': 0, 'already_canonical': 0}

    for campaign_dir in campaign_dirs:
        locations_file = campaign_dir / 'locations.json'
        if not locations_file.exists():
            continue

        print(f"Campaign: {campaign_dir.name}")
        stats = migrate_campaign(locations_file, apply=args.apply)

        for key in total_stats:
            total_stats[key] += stats[key]

        print(f"  Pairs: {stats['pairs_found']}, Duplicates removed: {stats['duplicates_removed']}, Already canonical: {stats['already_canonical']}")
        print()

    print(f"{'='*60}")
    print(f"  TOTAL: {total_stats['pairs_found']} pairs, {total_stats['duplicates_removed']} duplicates removed, {total_stats['already_canonical']} already canonical")
    if not args.apply:
        print(f"  Run with --apply to save changes")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
