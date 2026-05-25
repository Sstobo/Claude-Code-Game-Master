"""D&D 5E XP table.

Moved verbatim from lib/player_manager.py. XP_THRESHOLDS is the 5e level
thresholds for levels 1-20.
"""
from typing import Any, Dict, Optional


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


def normalize_advancement(char: Dict[str, Any]) -> None:
    """Convert char['xp'] int -> {'current', 'next_level'} dict. No-op if already a dict."""
    xp = char.get('xp', 0)
    if isinstance(xp, dict):
        return
    level = char.get('level', 1)
    current = xp if isinstance(xp, int) else 0
    next_thresh = xp_threshold(level + 1)
    char['xp'] = {
        'current': current,
        'next_level': next_thresh if next_thresh is not None else current,
    }


def advance(char: Dict[str, Any], amount: int) -> Dict[str, Any]:
    """Award XP. Mutates char['xp'] and char['level']. Returns result dict."""
    normalize_advancement(char)
    old_level = char.get('level', 1)
    old_xp = char['xp']['current']
    char['xp']['current'] = old_xp + amount
    current_xp = char['xp']['current']
    new_level = level_for_xp(current_xp)
    level_changed = new_level > old_level
    if level_changed:
        char['level'] = new_level
    next_thresh = xp_threshold(new_level + 1)
    char['xp']['next_level'] = next_thresh if next_thresh is not None else current_xp
    cap = next_thresh if next_thresh is not None else 'MAX'
    if level_changed:
        summary = f"Level up! {old_level} -> {new_level}"
    else:
        summary = f"XP: {old_xp} -> {current_xp}/{cap}"
    return {
        'amount': amount,
        'level_changed': level_changed,
        'old_level': old_level,
        'new_level': new_level,
        'current_xp': current_xp,
        'summary': summary,
    }


def advancement_status(char: Dict[str, Any]) -> str:
    """Read-only display of current advancement state."""
    normalize_advancement(char)
    level = char.get('level', 1)
    current = char['xp']['current']
    if level >= 20:
        return f"Level {level} | XP: MAX"
    next_level = char['xp']['next_level']
    return f"Level {level} | XP: {current}/{next_level}"
