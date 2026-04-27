# Quick Reference: Dungeon Crawler Carl Book 2 Plot Extraction

## File Location
```
world-state/campaigns/dungeon-crawler-carl/extracted/plots.json
```

## File Size & Format
- **Size:** 76 KB
- **Lines:** 2,529
- **Format:** JSON
- **Encoding:** UTF-8

## Data Summary

### Total Elements Extracted: 2,269

| Category | Count |
|----------|-------|
| Plot Points | 265 |
| Quests & Objectives | 396 |
| Conflicts | 596 |
| Locations | 423 |
| Items & Artifacts | 492 |
| Themes | 9 |

## Main Characters
- **Carl** - Protagonist (249 appearances)
- **Donut** - Companion (768 appearances) 
- **Mordecai** - Mage Companion (401 appearances)

## Core Themes
1. Betrayal
2. Redemption
3. Power & Corruption
4. Friendship & Loyalty
5. Survival
6. Mystery
7. Danger & Conflict
8. Sacrifice
9. Growth & Learning

## JSON Top-Level Keys

```json
{
  "metadata": {...},           // Source and extraction info
  "summary": {...},             // Statistics
  "themes_identified": [],      // 9 themes
  "main_characters": {},        // Character stats
  "plot_points": [],            // 100 samples
  "quests_and_objectives": [],  // 80 samples
  "conflicts_and_antagonists":[], // 60 samples
  "key_items": [],              // 60 samples
  "key_locations": {}           // 30 locations
}
```

## Usage Scenarios

### Find Related Content
- Search by chunk number to see context
- Use location mentions to map world
- Reference character appearances for timeline

### Build Encounters
- Review conflicts for enemy types
- Check locations for arena descriptions
- Look up items for treasure placement

### Create Quests
- Extract objectives from quests_and_objectives
- Cross-reference locations for journey planning
- Use conflicts for combat encounters

## Sample Data Access

**Get a plot point:**
```
plots.json → plot_points[0]
  → "snippet": "description of story moment"
  → "chunk": "chunk_###.txt"
  → "page": "##"
```

**Get a quest:**
```
plots.json → quests_and_objectives[0]
  → "snippet": "quest description"
  → "keyword": "quest type"
  → "chunk": "chunk_###.txt"
```

**Get a location:**
```
plots.json → key_locations["Location Name"]
  → "mentions": ## (frequency)
  → "context": ["usage example 1", "usage example 2"]
  → "first_mention": "chunk_###.txt"
```

## Processing Notes
- All entries include source chunk reference
- Page numbers preserved where available
- Context snippets provided for each element
- Locations tracked with mention frequency
- Character appearances quantified

## Last Updated
2026-02-22

## Related Files
- `EXTRACTION_REPORT.md` - Full detailed report
- `extract_plots_comprehensive.py` - Source script
- `world-state/campaigns/dungeon-crawler-carl/chunks/` - Source data

