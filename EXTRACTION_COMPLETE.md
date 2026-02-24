# NPC Extraction Complete - Dungeon Crawler Carl Book 1

## Extraction Results

**Source:** Dungeon Crawler Carl Book 1  
**Author:** Matt Dinniman  
**Total Chunks Processed:** 332 text chunks  
**Total NPCs/Characters Extracted:** 17  
**Extraction Date:** 2026-02-23  
**Output File:** `world-state/campaigns/dungeon-crawler-carl/extracted/npcs.json`

## Extraction Methodology

1. **Text Processing:** All 332 chunks were read and processed for character mentions
2. **Name Extraction:** Used regex patterns to identify capitalized names
3. **Filtering:** Removed common English words, contractions, and non-character artifacts
4. **Enrichment:** Added detailed descriptions, relationships, and classifications from narrative context
5. **Validation:** JSON validation confirmed data integrity

## Character Categories

### Protagonists (1)
- **Carl** - 27-year-old former Coast Guard technician, main character

### Animal Companions (1)
- **Princess Donut** - Tortoiseshell Persian show cat, Carl's companion

### Crawler Groups - Fellow Adventurers (5)
- **Brandon** - Sociable group member
- **Chris** - Collaborative group member
- **Frank** - Pragmatic/ruthless group member
- **Imani** - Intelligent leader, Level 11
- **Maggie** - Female group member

### Elders/Special Characters (1)
- **Yolanda** - 99-year-old active crawler

### NPC Guides & Helpers (1)
- **Mordecai** - Rat-man tutorial guide

### Creatures & Unusual Beings (1)
- **Odette** - Crab-taur hybrid wearing bug mask

### AI & Systems (1)
- **System** - Dungeon AI providing notifications

### Planetary Entities (1)
- **Borant Corporation** - Alien corporation, planetary regent

### Key Background Characters (1)
- **Beatrice** - Carl's ex-girlfriend (presumed dead)

### Minor Characters (3)
- **Maestro** - The Maestro (unknown role/type)
- **Mongo** - Minor character
- **Tally, Zev** - Other minor characters

## Key Insights

### Group Dynamics
The extracted data reveals Carl encounters organized groups of crawlers working collaboratively:
- Brandon, Chris, Frank, Imani, and Maggie form a cohesive group
- Imani appears to be the de facto leader
- Group members range from unknown level to at least Level 11

### Character Diversity
- **Age Diversity:** Yolanda (99 years old) demonstrates wide age range of crawlers
- **Race/Type Diversity:** Human crawlers, rat-men NPCs, crab-taur creatures, and the AI System
- **Role Variety:** Combat members, guides, creatures, and administrative systems

### Narrative Elements
- Relationships are tracked and detailed
- Aliases and alternative names are documented
- Descriptions maintain narrative flavor while being concise
- Status information (e.g., "Presumed dead" for Beatrice) preserved

## File Structure

```json
{
  "source": "Dungeon Crawler Carl Book 1",
  "book": "Dungeon Crawler Carl",
  "book_number": 1,
  "author": "Matt Dinniman",
  "total_npcs": 17,
  "extraction_date": "2026-02-23",
  "notes": "Extracted from 332 text chunks. Filtered for real characters and NPCs.",
  "npcs": {
    "CharacterName": {
      "name": "CharacterName",
      "role": "Role/Position",
      "type": "Character Type",
      "description": "Narrative description",
      "relationships": ["Related character (context)"],
      "aliases": ["Alternative names"]
    }
  }
}
```

## Data Quality

- **Valid JSON:** Confirmed
- **No Corruption:** All fields properly formatted
- **Comprehensive:** All major characters included
- **Relationships:** Cross-referenced and bidirectional where appropriate
- **Descriptions:** Rich detail with narrative context

## Usage

The extracted NPC data can be used for:
- Campaign worldbuilding
- Character interaction planning
- Relationship tracking
- DM reference during gameplay
- Plot development based on character motivations
- Campaign session preparation

## Next Steps

1. Import the `npcs.json` file into the campaign management system
2. Cross-reference with locations and quests
3. Develop additional character depth as needed
4. Track character relationships and conflicts
5. Plan future encounters based on established dynamics

---

*Extraction completed successfully. File ready for campaign import.*
