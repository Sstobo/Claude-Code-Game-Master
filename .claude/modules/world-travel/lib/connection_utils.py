#!/usr/bin/env python3
"""
Canonical connection utilities for location graph management.
Each edge is stored ONCE in the alphabetically-first location.
All modules should use these helpers instead of raw connection access.
"""

from typing import Dict, List, Optional, Tuple, Any


def canonical_pair(a: str, b: str) -> Tuple[str, str]:
    """Return (first, second) in alphabetical order."""
    if a <= b:
        return (a, b)
    return (b, a)


def get_connections(loc_name: str, locations_data: Dict) -> List[Dict]:
    """
    Get ALL connections for a location — both forward (stored here)
    and reverse (stored in other locations pointing to us).

    Reverse connections get bearing flipped by +180.
    """
    result = []

    if loc_name not in locations_data:
        return result

    loc = locations_data[loc_name]
    for conn in loc.get('connections', []):
        result.append(dict(conn))

    for other_name, other_data in locations_data.items():
        if other_name == loc_name:
            continue
        for conn in other_data.get('connections', []):
            if conn.get('to') == loc_name:
                reverse = dict(conn)
                reverse['to'] = other_name
                if 'bearing' in reverse and reverse['bearing'] is not None:
                    reverse['bearing'] = (reverse['bearing'] + 180) % 360
                if 'path' in reverse:
                    reverse['path'] = reverse['path']
                result.append(reverse)

    return result


def get_connection_between(a: str, b: str, locations_data: Dict) -> Optional[Dict]:
    """
    Get connection data between two locations (regardless of storage direction).
    Returns the raw stored dict (with original bearing from owner to target).
    Returns None if no connection exists.
    """
    first, second = canonical_pair(a, b)

    if first in locations_data:
        for conn in locations_data[first].get('connections', []):
            if conn.get('to') == second:
                return conn

    if second in locations_data:
        for conn in locations_data[second].get('connections', []):
            if conn.get('to') == first:
                return conn

    return None


def add_canonical_connection(a: str, b: str, locations_data: Dict, **kwargs) -> None:
    """
    Add connection between a and b, stored in alphabetically-first location.
    kwargs: path, distance_meters, bearing, terrain, etc.

    bearing should be from the owner (first) to the target (second).
    If a > b (caller provides bearing from a to b), we flip it.
    """
    first, second = canonical_pair(a, b)

    if first not in locations_data or second not in locations_data:
        return

    if 'connections' not in locations_data[first]:
        locations_data[first]['connections'] = []

    for conn in locations_data[first]['connections']:
        if conn.get('to') == second:
            return

    conn_data = {'to': second}
    conn_data.update(kwargs)

    if a != first and 'bearing' in conn_data and conn_data['bearing'] is not None:
        conn_data['bearing'] = (conn_data['bearing'] + 180) % 360

    locations_data[first]['connections'].append(conn_data)


def remove_canonical_connection(a: str, b: str, locations_data: Dict) -> None:
    """Remove connection between a and b from wherever it's stored."""
    first, second = canonical_pair(a, b)

    if first in locations_data:
        conns = locations_data[first].get('connections', [])
        locations_data[first]['connections'] = [
            c for c in conns if c.get('to') != second
        ]

    if second in locations_data:
        conns = locations_data[second].get('connections', [])
        locations_data[second]['connections'] = [
            c for c in conns if c.get('to') != first
        ]


def get_unique_edges(locations_data: Dict) -> List[Tuple[str, str, Dict]]:
    """
    Get all unique edges for map rendering — no duplicates.
    Returns list of (loc_a, loc_b, connection_data) tuples.
    """
    seen = set()
    edges = []

    for loc_name, loc_data in locations_data.items():
        for conn in loc_data.get('connections', []):
            to_loc = conn.get('to')
            if not to_loc:
                continue
            edge_key = tuple(sorted([loc_name, to_loc]))
            if edge_key not in seen:
                seen.add(edge_key)
                edges.append((loc_name, to_loc, conn))

    return edges
