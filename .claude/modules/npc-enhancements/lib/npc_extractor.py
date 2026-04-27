#!/usr/bin/env python3
"""
Session log auto-extraction — scans session log for new NPC names.

Algorithm:
1. Split text into tokens
2. Find capitalized words NOT at the start of a sentence
3. Filter out stop words (common English, days, months, known D&D terms)
4. Filter out already-known NPCs from npcs.json
5. Bigram check for multi-word names ("High Priestess")
6. Return candidates with confidence scores
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Words that are commonly capitalized but are not NPC names
STOP_WORDS: Set[str] = {
    "I", "A", "An", "The", "It", "Its", "He", "She", "They", "We", "You",
    "This", "That", "These", "Those",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "Yes", "No", "OK", "Okay", "Hello", "Hi", "Goodbye", "Please", "Thanks",
    "Left", "Right", "Up", "Down", "North", "South", "East", "West",
    "Level", "Gold", "HP", "AC", "XP", "DM", "NPC", "PC",
    "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
    "First", "Second", "Third", "Next", "Last", "Previous",
    "Once", "Then", "Now", "Here", "There", "Where", "What", "Why", "How",
    "Also", "Still", "Even", "Just", "Already",
    "Act", "Scene", "Chapter", "Page",
    "Morning", "Afternoon", "Evening", "Night", "Today", "Tomorrow", "Yesterday",
    "Room", "Door", "Way", "Time", "Thing",
    # D&D and campaign specific common terms
    "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma",
    "Str", "Dex", "Con", "Int", "Wis", "Cha",
    "Fire", "Water", "Earth", "Air",
    "Lawful", "Chaotic", "Neutral", "Good", "Evil",
    "Dragon", "Demon", "Devil", "Undead",
}

# D&D classes and races that get capitalized
KNOWN_TYPES: Set[str] = {
    "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk",
    "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard",
    "Artificer", "Dwarf", "Elf", "Halfling", "Human", "Gnome",
    "Half-Elf", "Half-Orc", "Dragonborn", "Tiefling", "Orc", "Goblin",
}


def _get_npcs_path() -> Path:
    from campaign_manager import CampaignManager
    mgr = CampaignManager()
    return mgr.get_active_campaign_dir() / "npcs.json"


def _get_session_log_path() -> Path:
    from campaign_manager import CampaignManager
    mgr = CampaignManager()
    return mgr.get_active_campaign_dir() / "session-log.md"


def _load_existing_npcs() -> Set[str]:
    """Return set of existing NPC names (case-insensitive)."""
    path = _get_npcs_path()
    if not path.exists():
        return set()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {n.lower() for n in data.keys()}
    except (ValueError, IOError):
        return set()


def extract_candidates(text: str, existing_npcs: Set[str] = None) -> List[Dict]:
    """
    Extract potential new NPC names from text.

    Returns list of dicts: [{name, confidence, count}]
    """
    if existing_npcs is None:
        existing_npcs = _load_existing_npcs()

    # Split sentences to detect sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)

    candidates: Dict[str, int] = {}

    for sentence in sentences:
        stripped = sentence.strip()
        if not stripped:
            continue

        tokens = re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)?", stripped)

        # Bigram check: look for consecutive capitalized words
        for i in range(len(tokens)):
            # Single token check
            token = tokens[i]
            if not _is_candidate_token(token, sentence, tokens, i, existing_npcs):
                continue
            candidates[token] = candidates.get(token, 0) + 1

        # Check for multi-word names (consecutive capitalized tokens)
        for i in range(len(tokens) - 1):
            if (_is_candidate_token(tokens[i], sentence, tokens, i, existing_npcs) and
                    _is_candidate_token(tokens[i + 1], sentence, tokens, i + 1, existing_npcs)):
                bigram = f"{tokens[i]} {tokens[i + 1]}"
                # Skip if either word alone is already a known npc
                solo_known_a = tokens[i].lower() in existing_npcs or tokens[i] in STOP_WORDS
                solo_known_b = tokens[i + 1].lower() in existing_npcs or tokens[i + 1] in STOP_WORDS
                if not (solo_known_a or solo_known_b):
                    candidates[bigram] = candidates.get(bigram, 0) + 1

    # Convert to result list with confidence
    result = []
    for name, count in sorted(candidates.items(), key=lambda x: -x[1]):
        if count >= 3:
            confidence = "high"
        elif count == 2:
            confidence = "medium"
        else:
            confidence = "low"
        result.append({"name": name, "confidence": confidence, "count": count})

    return result


def _is_candidate_token(token: str, sentence: str, all_tokens: List[str], index: int, existing_npcs: Set[str]) -> bool:
    """Check if a token is a candidate NPC name."""
    # Must start with uppercase
    if not token or not token[0].isupper():
        return False

    # Skip single letters
    if len(token) <= 1:
        return False

    # Skip stop words
    if token in STOP_WORDS or token in KNOWN_TYPES:
        return False

    # Skip if it's the first word of a sentence (likely not a name)
    if index == 0 or (all_tokens and index > 0 and all_tokens[index - 1] in ('.', '!', '?')):
        # Check if previous token ended a sentence
        prev_end = False
        if index > 0:
            prev_word = all_tokens[index - 1]
            prev_end = prev_word.endswith('.') or prev_word.endswith('!') or prev_word.endswith('?')
        if prev_end or index == 0:
            return False

    # Skip if already known
    if token.lower() in existing_npcs:
        return False

    # Skip all-uppercase (likely acronyms)
    if token.isupper() and len(token) <= 4:
        return False

    return True


def extract_from_session_log() -> List[Dict]:
    """Extract candidate NPCs from the session log."""
    log_path = _get_session_log_path()
    if not log_path.exists():
        return []

    text = log_path.read_text(encoding='utf-8')
    existing = _load_existing_npcs()
    return extract_candidates(text, existing)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--log":
        candidates = extract_from_session_log()
        print(json.dumps(candidates, indent=2))
    elif len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        existing = _load_existing_npcs()
        candidates = extract_candidates(text, existing)
        print(json.dumps(candidates, indent=2))
    else:
        print("Usage: npc_extractor.py --log")
        print("       npc_extractor.py <text>")
        sys.exit(1)
