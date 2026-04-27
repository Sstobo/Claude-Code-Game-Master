#!/usr/bin/env python3
"""
Simple dice rolling library for D&D
Supports standard notation: 1d20, 3d6+2, 2d20kh1 (advantage), etc.
"""

import random
import re
from typing import List, Tuple, Dict

# Import colors for formatted output
try:
    from lib.colors import Colors, format_roll_result
except ImportError:
    # Fallback if running directly
    try:
        from colors import Colors, format_roll_result
    except ImportError:
        # No colors available - use plain text
        class Colors:
            RESET = ""
            RED = ""
            GREEN = ""
            YELLOW = ""
            CYAN = ""
            BOLD = ""
            BOLD_RED = ""
            BOLD_GREEN = ""
            BOLD_YELLOW = ""
            BOLD_CYAN = ""
            DIM = ""

        def format_roll_result(notation, rolls, total, is_crit=False, is_fumble=False):
            rolls_str = '+'.join(str(r) for r in rolls)
            base = f"🎲 {notation}: [{rolls_str}] = {total}"
            if is_crit:
                base += " ⚔️ CRITICAL HIT!"
            elif is_fumble:
                base += " 💀 CRITICAL MISS!"
            return base

class DiceRoller:
    def __init__(self):
        # Regex patterns for different dice notations
        self.simple_pattern = re.compile(r'(\d+)d(\d+)([+-]\d+)?')
        self.advantage_pattern = re.compile(r'(\d+)d(\d+)kh(\d+)')  # keep highest
        self.disadvantage_pattern = re.compile(r'(\d+)d(\d+)kl(\d+)')  # keep lowest
        
    def roll(self, notation: str) -> Dict:
        """
        Roll dice based on notation and return detailed results
        
        Returns dict with:
        - notation: original notation
        - rolls: individual die results
        - total: final total
        - natural_20: True if d20 rolled natural 20
        - natural_1: True if d20 rolled natural 1
        """
        notation = notation.strip()
        
        # Check for advantage (keep highest)
        match = self.advantage_pattern.match(notation)
        if match:
            count, sides, keep = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if sides < 1:
                raise ValueError(f"Invalid die size: d{sides} (must be at least 1)")
            rolls = sorted([random.randint(1, sides) for _ in range(count)], reverse=True)
            kept = rolls[:keep]
            return {
                'notation': notation,
                'rolls': rolls,
                'kept': kept,
                'discarded': rolls[keep:],
                'total': sum(kept),
                'type': 'advantage'
            }
        
        # Check for disadvantage (keep lowest)
        match = self.disadvantage_pattern.match(notation)
        if match:
            count, sides, keep = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if sides < 1:
                raise ValueError(f"Invalid die size: d{sides} (must be at least 1)")
            rolls = sorted([random.randint(1, sides) for _ in range(count)])
            kept = rolls[:keep]
            return {
                'notation': notation,
                'rolls': rolls,
                'kept': kept,
                'discarded': rolls[keep:],
                'total': sum(kept),
                'type': 'disadvantage'
            }
        
        # Standard roll
        match = self.simple_pattern.match(notation)
        if match:
            count, sides = int(match.group(1)), int(match.group(2))
            if sides < 1:
                raise ValueError(f"Invalid die size: d{sides} (must be at least 1)")
            modifier = int(match.group(3)) if match.group(3) else 0

            rolls = [random.randint(1, sides) for _ in range(count)]
            total = sum(rolls) + modifier
            
            result = {
                'notation': notation,
                'rolls': rolls,
                'modifier': modifier,
                'total': total,
                'type': 'standard'
            }
            
            # Check for natural 20/1 on d20
            if sides == 20 and count == 1:
                if rolls[0] == 20:
                    result['natural_20'] = True
                elif rolls[0] == 1:
                    result['natural_1'] = True
                    
            return result
        
        raise ValueError(f"Invalid dice notation: {notation}")
    
    def format_result(self, result: Dict) -> str:
        """Format a roll result for display with colors"""
        if result['type'] == 'advantage':
            kept_str = '+'.join(str(r) for r in result['kept'])
            discarded_str = '+'.join(str(r) for r in result['discarded'])
            return f"🎲 {result['notation']}: {Colors.CYAN}[{kept_str}]{Colors.RESET} {Colors.DIM}(discarded: {discarded_str}){Colors.RESET} = {Colors.CYAN}{result['total']}{Colors.RESET}"

        elif result['type'] == 'disadvantage':
            kept_str = '+'.join(str(r) for r in result['kept'])
            discarded_str = '+'.join(str(r) for r in result['discarded'])
            return f"🎲 {result['notation']}: {Colors.CYAN}[{kept_str}]{Colors.RESET} {Colors.DIM}(discarded: {discarded_str}){Colors.RESET} = {Colors.CYAN}{result['total']}{Colors.RESET}"

        else:  # standard
            is_crit = result.get('natural_20', False)
            is_fumble = result.get('natural_1', False)

            rolls_str = '+'.join(str(r) for r in result['rolls'])
            base = f"🎲 {result['notation']}: {Colors.CYAN}[{rolls_str}]{Colors.RESET}"

            if result['modifier'] != 0:
                mod_str = f"{result['modifier']:+d}"
                base += f" {mod_str}"

            base += f" = {Colors.CYAN}{result['total']}{Colors.RESET}"

            if is_crit:
                base += f" ⚔️ {Colors.BOLD_GREEN}CRITICAL HIT!{Colors.RESET}"
            elif is_fumble:
                base += f" 💀 {Colors.BOLD_RED}CRITICAL MISS!{Colors.RESET}"

            return base


# Module-level convenience functions
_roller = DiceRoller()

def roll(notation: str) -> int:
    """Quick roll that returns just the total. Use for simple checks."""
    return _roller.roll(notation)['total']

def roll_detailed(notation: str) -> Dict:
    """Roll with full details (rolls, modifiers, crits, etc.)"""
    return _roller.roll(notation)

def roll_formatted(notation: str) -> str:
    """Roll and return formatted string for display."""
    result = _roller.roll(notation)
    return _roller.format_result(result)


def main():
    """CLI interface for dice rolling"""
    import sys

    # Fix encoding for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) < 2:
        print("Usage: dice.py <notation>")
        print("Examples: 1d20, 3d6+2, 2d20kh1 (advantage), 2d20kl1 (disadvantage)")
        sys.exit(1)

    roller = DiceRoller()
    notation = sys.argv[1]

    try:
        result = roller.roll(notation)
        print(roller.format_result(result))
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()