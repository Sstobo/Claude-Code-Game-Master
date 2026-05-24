"""D&D 5E XP table.

Moved verbatim from lib/player_manager.py. XP_THRESHOLDS is the 5e level
thresholds for levels 1-20.
"""
from typing import Optional


XP_THRESHOLDS = [
    0,       # Level 1
    300,     # Level 2
    900,     # Level 3
    2700,    # Level 4
    6500,    # Level 5
    14000,   # Level 6
    23000,   # Level 7
    34000,   # Level 8
    48000,   # Level 9
    64000,   # Level 10
    85000,   # Level 11
    100000,  # Level 12
    120000,  # Level 13
    140000,  # Level 14
    165000,  # Level 15
    195000,  # Level 16
    225000,  # Level 17
    265000,  # Level 18
    305000,  # Level 19
    355000,  # Level 20
]


def xp_threshold(level: int) -> Optional[int]:
    """XP needed to enter `level`. Returns None for levels above the cap."""
    if 1 <= level <= len(XP_THRESHOLDS):
        return XP_THRESHOLDS[level - 1]
    return None


def level_for_xp(xp: int) -> int:
    """Highest level whose threshold `xp` meets. Caps at 20."""
    level = 1
    while level < len(XP_THRESHOLDS) and xp >= XP_THRESHOLDS[level]:
        level += 1
    return level
