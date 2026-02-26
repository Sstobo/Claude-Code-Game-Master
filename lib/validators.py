#!/usr/bin/env python3
"""
Input validation module for DM tools
Provides consistent validation across all tools
"""

import re
from typing import Optional, List, Tuple


class Validators:
    """Input validation for DM system"""

    @staticmethod
    def validate_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate name/identifier
        Allows: alphanumeric, spaces, hyphens, apostrophes
        Returns: (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Name cannot be empty"

        # Check length
        if len(name) > 100:
            return False, "Name too long (max 100 characters)"

        # Check characters
        pattern = r"^[a-zA-Z0-9\s\-']+$"
        if not re.match(pattern, name):
            return False, "Invalid name. Use only letters, numbers, spaces, hyphens, and apostrophes"

        return True, None

    @staticmethod
    def validate_attitude(attitude: str) -> Tuple[bool, Optional[str]]:
        """
        Validate NPC attitude
        Returns: (is_valid, error_message)
        """
        valid_attitudes = [
            'friendly', 'neutral', 'hostile', 'suspicious', 'helpful',
            'indifferent', 'fearful', 'respectful', 'dismissive', 'curious'
        ]

        attitude_lower = attitude.lower().strip()
        if attitude_lower not in valid_attitudes:
            return False, f"Invalid attitude. Choose from: {', '.join(valid_attitudes)}"

        return True, None

    @staticmethod
    def validate_dice(dice_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate dice notation (e.g., 3d6, 1d20+5, 2d8-2)
        Returns: (is_valid, error_message)
        """
        pattern = r'^(\d+)d(\d+)(?:k[hl]\d+)?([+-]\d+)?$'
        if not re.match(pattern, dice_string):
            return False, "Invalid dice notation. Use format: XdY, XdY+Z, or XdYkh1+Z (e.g., 3d6, 1d20+5, 2d20kh1+3)"

        match = re.match(pattern, dice_string)
        num_dice = int(match.group(1))
        die_size = int(match.group(2))

        if num_dice < 1 or num_dice > 100:
            return False, "Number of dice must be between 1 and 100"

        valid_die_sizes = [4, 6, 8, 10, 12, 20, 100]
        if die_size not in valid_die_sizes:
            return False, f"Invalid die size. Valid sizes: {valid_die_sizes}"

        return True, None

    @staticmethod
    def validate_damage_type(damage_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate D&D damage type
        Returns: (is_valid, error_message)
        """
        valid_types = [
            'acid', 'bludgeoning', 'cold', 'fire', 'force', 'lightning',
            'necrotic', 'piercing', 'poison', 'psychic', 'radiant',
            'slashing', 'thunder'
        ]

        damage_lower = damage_type.lower().strip()
        if damage_lower not in valid_types:
            return False, f"Invalid damage type. Valid types: {', '.join(valid_types)}"

        return True, None

    @staticmethod
    def validate_skill(skill: str) -> Tuple[bool, Optional[str]]:
        """
        Validate D&D skill name
        Returns: (is_valid, error_message)
        """
        valid_skills = [
            'acrobatics', 'animal handling', 'arcana', 'athletics',
            'deception', 'history', 'insight', 'intimidation',
            'investigation', 'medicine', 'nature', 'perception',
            'performance', 'persuasion', 'religion', 'sleight of hand',
            'stealth', 'survival'
        ]

        skill_lower = skill.lower().strip()
        if skill_lower not in valid_skills:
            return False, f"Invalid skill. Valid skills: {', '.join(valid_skills)}"

        return True, None

    @staticmethod
    def validate_alignment(alignment: str) -> Tuple[bool, Optional[str]]:
        """
        Validate D&D alignment
        Returns: (is_valid, error_message)
        """
        valid_alignments = [
            'lawful good', 'neutral good', 'chaotic good',
            'lawful neutral', 'true neutral', 'chaotic neutral',
            'lawful evil', 'neutral evil', 'chaotic evil',
            'unaligned'
        ]

        alignment_lower = alignment.lower().strip()
        # Handle "neutral" as "true neutral"
        if alignment_lower == 'neutral':
            alignment_lower = 'true neutral'

        if alignment_lower not in valid_alignments:
            return False, f"Invalid alignment. Valid alignments: {', '.join(valid_alignments)}"

        return True, None

    @staticmethod
    def validate_condition(condition: str) -> Tuple[bool, Optional[str]]:
        """
        Validate D&D condition
        Returns: (is_valid, error_message)
        """
        valid_conditions = [
            'blinded', 'charmed', 'deafened', 'exhaustion', 'frightened',
            'grappled', 'incapacitated', 'invisible', 'paralyzed',
            'petrified', 'poisoned', 'prone', 'restrained', 'stunned',
            'unconscious'
        ]

        condition_lower = condition.lower().strip()
        if condition_lower not in valid_conditions:
            return False, f"Invalid condition. Valid conditions: {', '.join(valid_conditions)}"

        return True, None

    @staticmethod
    def validate_ability(ability: str) -> Tuple[bool, Optional[str]]:
        """
        Validate D&D ability score name
        Returns: (is_valid, error_message)
        """
        valid_abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        # Also accept abbreviations
        abbreviations = ['str', 'dex', 'con', 'int', 'wis', 'cha']

        ability_lower = ability.lower().strip()
        if ability_lower not in valid_abilities and ability_lower not in abbreviations:
            return False, f"Invalid ability. Valid abilities: {', '.join(valid_abilities)}"

        return True, None

    @staticmethod
    def validate_quest_priority(priority: str) -> Tuple[bool, Optional[str]]:
        """
        Validate quest priority level
        Returns: (is_valid, error_message)
        """
        valid_priorities = ['critical', 'high', 'medium', 'low', 'optional']

        priority_lower = priority.lower().strip()
        if priority_lower not in valid_priorities:
            return False, f"Invalid priority. Valid priorities: {', '.join(valid_priorities)}"

        return True, None

    @staticmethod
    def validate_time_of_day(time: str) -> Tuple[bool, Optional[str]]:
        """
        Validate time of day
        Returns: (is_valid, error_message)
        """
        valid_times = [
            'dawn', 'morning', 'midday', 'afternoon',
            'dusk', 'evening', 'night', 'midnight'
        ]

        time_lower = time.lower().strip()
        if time_lower not in valid_times:
            return False, f"Invalid time. Valid times: {', '.join(valid_times)}"

        return True, None

    @staticmethod
    def validate_plot_type(plot_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate plot type
        Returns: (is_valid, error_message)
        """
        valid_types = ['main', 'side', 'mystery', 'threat']

        type_lower = plot_type.lower().strip()
        if type_lower not in valid_types:
            return False, f"Invalid plot type. Valid types: {', '.join(valid_types)}"

        return True, None

    @staticmethod
    def validate_plot_status(status: str) -> Tuple[bool, Optional[str]]:
        """
        Validate plot status
        Returns: (is_valid, error_message)
        """
        valid_statuses = ['active', 'completed', 'failed', 'dormant']

        status_lower = status.lower().strip()
        if status_lower not in valid_statuses:
            return False, f"Invalid plot status. Valid statuses: {', '.join(valid_statuses)}"

        return True, None

    @staticmethod
    def escape_for_json(text: str) -> str:
        """
        Escape text for safe JSON embedding
        Prevents JSON injection attacks
        """
        # Escape backslashes first, then quotes
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        return text

    @staticmethod
    def sanitize_path(path: str) -> Optional[str]:
        """
        Sanitize file paths to prevent directory traversal
        Returns None if path is invalid
        """
        # Remove any directory traversal attempts
        if '..' in path or path.startswith('/'):
            return None

        # Only allow alphanumeric, spaces, hyphens, underscores, and forward slashes
        if not re.match(r'^[a-zA-Z0-9\s\-_/]+$', path):
            return None

        return path


def main():
    """CLI interface for validation"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Input validation')
    parser.add_argument('type', choices=[
        'name', 'attitude', 'dice', 'damage_type', 'skill',
        'alignment', 'condition', 'ability', 'priority', 'time',
        'plot_type', 'plot_status'
    ])
    parser.add_argument('value', help='Value to validate')

    args = parser.parse_args()
    validator = Validators()

    # Map validation types to methods
    validators_map = {
        'name': validator.validate_name,
        'attitude': validator.validate_attitude,
        'dice': validator.validate_dice,
        'damage_type': validator.validate_damage_type,
        'skill': validator.validate_skill,
        'alignment': validator.validate_alignment,
        'condition': validator.validate_condition,
        'ability': validator.validate_ability,
        'priority': validator.validate_quest_priority,
        'time': validator.validate_time_of_day,
        'plot_type': validator.validate_plot_type,
        'plot_status': validator.validate_plot_status
    }

    is_valid, error_msg = validators_map[args.type](args.value)

    if is_valid:
        print(f"[SUCCESS] Valid {args.type}: {args.value}")
        sys.exit(0)
    else:
        print(f"[ERROR] {error_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()