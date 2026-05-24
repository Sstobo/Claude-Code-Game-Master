# Python Modules API Reference

This document provides comprehensive API documentation for the Python modules in `/lib/` that implement the Hybrid Evolution Architecture for the DM system.

## Table of Contents
- [json_ops.py](#json_opspy) - JSON file operations with atomic writes
- [validators.py](#validatorspy) - Input validation for D&D 5e data
- [npc_manager.py](#npc_managerpy) - NPC creation and management

---

## json_ops.py

**Purpose**: Provides safe, atomic JSON file operations with error handling for world state management.

### Class: JsonOperations

#### Constructor
```python
JsonOperations(world_state_dir: str = "world-state")
```
- Creates a JSON operations handler
- Automatically creates the world state directory if it doesn't exist

#### Methods

##### `load_json(filename: str, default: Any = None) -> Any`
Load a JSON file with error handling.
- **Returns**: File contents or default value if file doesn't exist/is invalid
- **Example**:
```python
ops = JsonOperations()
npcs = ops.load_json("npcs.json", default={})
```

##### `save_json(filename: str, data: Any, indent: int = 2) -> bool`
Save data to JSON file with atomic write operation.
- **Returns**: True on success, False on failure
- **Note**: Uses temporary file for atomic operation
- **Example**:
```python
ops.save_json("npcs.json", {"Gandalf": {"attitude": "wise"}})
```

##### `update_json(filename: str, updates: Dict, path: List[str] = None) -> bool`
Update JSON file with partial data.
- **Parameters**:
  - `updates`: Dictionary of updates to apply
  - `path`: Optional nested path (e.g., `["npcs", "Gandalf", "stats"]`)
- **Example**:
```python
# Update root level
ops.update_json("campaign.json", {"day": 5})

# Update nested path
ops.update_json("npcs.json", {"hp": 100}, path=["Gandalf", "stats"])
```

##### `append_to_list(filename: str, item: Any, path: List[str] = None) -> bool`
Append item to a list in JSON file.
- **Example**:
```python
# Append to root list
ops.append_to_list("events.json", {"event": "Dragon attack"})

# Append to nested list
ops.append_to_list("npcs.json", {"event": "Met party"}, path=["Gandalf", "events"])
```

##### `check_exists(filename: str, key: str, path: List[str] = None) -> bool`
Check if a key exists in JSON file.
- **Example**:
```python
# Check root level
exists = ops.check_exists("npcs.json", "Gandalf")

# Check nested path
has_stats = ops.check_exists("npcs.json", "hp", path=["Gandalf", "stats"])
```

##### `get_value(filename: str, key: str = None, path: List[str] = None) -> Any`
Get value from JSON file.
- **Example**:
```python
# Get entire file
all_npcs = ops.get_value("npcs.json")

# Get specific key
gandalf = ops.get_value("npcs.json", key="Gandalf")

# Get nested value
hp = ops.get_value("npcs.json", key="hp", path=["Gandalf", "stats"])
```

##### `delete_key(filename: str, key: str, path: List[str] = None) -> bool`
Delete a key from JSON file.
- **Example**:
```python
# Delete from root
ops.delete_key("npcs.json", "Gandalf")

# Delete from nested path
ops.delete_key("npcs.json", "temp_buff", path=["Gandalf", "status"])
```

#### CLI Usage
```bash
# Get value
uv run python lib/json_ops.py get npcs.json --key Gandalf

# Set value
uv run python lib/json_ops.py set campaign.json --key day --value 5

# Update nested
uv run python lib/json_ops.py update npcs.json --path "Gandalf.stats" --value '{"hp": 100}'

# Check existence
uv run python lib/json_ops.py exists npcs.json --key Gandalf
```

---

## validators.py

**Purpose**: Provides consistent validation for D&D 5e game data and user inputs.

### Class: Validators

All methods are static and return a tuple: `(is_valid: bool, error_message: Optional[str])`

#### Validation Methods

##### `validate_name(name: str) -> Tuple[bool, Optional[str]]`
Validate character/location names.
- **Rules**: Alphanumeric, spaces, hyphens, apostrophes only
- **Max length**: 100 characters
- **Example**:
```python
valid, error = Validators.validate_name("Gandalf the Grey")
# Returns: (True, None)

valid, error = Validators.validate_name("Bad@Name!")
# Returns: (False, "Invalid name. Use only letters, numbers, spaces, hyphens, and apostrophes")
```

##### `validate_attitude(attitude: str) -> Tuple[bool, Optional[str]]`
Validate NPC attitudes.
- **Valid values**: friendly, neutral, hostile, suspicious, helpful, indifferent, fearful, respectful, dismissive, curious
- **Example**:
```python
valid, error = Validators.validate_attitude("friendly")
# Returns: (True, None)
```

##### `validate_dice(dice_string: str) -> Tuple[bool, Optional[str]]`
Validate dice notation.
- **Format**: XdY or XdY+Z (e.g., 3d6, 1d20+5)
- **Valid die sizes**: 4, 6, 8, 10, 12, 20, 100
- **Example**:
```python
valid, error = Validators.validate_dice("2d8+3")
# Returns: (True, None)

valid, error = Validators.validate_dice("1d7")
# Returns: (False, "Invalid die size. Valid sizes: [4, 6, 8, 10, 12, 20, 100]")
```


##### `validate_ability(ability: str) -> Tuple[bool, Optional[str]]`
Validate D&D ability scores.
- **Valid abilities**: strength, dexterity, constitution, intelligence, wisdom, charisma
- **Also accepts**: str, dex, con, int, wis, cha
- **Example**:
```python
valid, error = Validators.validate_ability("dex")
# Returns: (True, None)
```

##### `validate_quest_priority(priority: str) -> Tuple[bool, Optional[str]]`
Validate quest priority levels.
- **Valid priorities**: critical, high, medium, low, optional
- **Example**:
```python
valid, error = Validators.validate_quest_priority("high")
# Returns: (True, None)
```

##### `validate_time_of_day(time: str) -> Tuple[bool, Optional[str]]`
Validate time of day.
- **Valid times**: dawn, morning, midday, afternoon, dusk, evening, night, midnight
- **Example**:
```python
valid, error = Validators.validate_time_of_day("dusk")
# Returns: (True, None)
```

#### Utility Methods

##### `escape_for_json(text: str) -> str`
Escape text for safe JSON embedding.
- **Prevents**: JSON injection attacks
- **Example**:
```python
safe_text = Validators.escape_for_json('He said "Hello"\nWorld')
# Returns: 'He said \"Hello\"\\nWorld'
```

##### `sanitize_path(path: str) -> Optional[str]`
Sanitize file paths to prevent directory traversal.
- **Returns**: Sanitized path or None if invalid
- **Example**:
```python
safe_path = Validators.sanitize_path("npcs/gandalf")
# Returns: "npcs/gandalf"

unsafe = Validators.sanitize_path("../../etc/passwd")
# Returns: None
```

#### CLI Usage
```bash
# Validate name
uv run python lib/validators.py name "Gandalf the Grey"

# Validate dice
uv run python lib/validators.py dice "3d6+2"

# Validate alignment
uv run python lib/validators.py alignment "chaotic good"
```

---

## npc_manager.py

**Purpose**: High-level NPC management with validation and tagging support.

### Class: NPCManager

#### Constructor
```python
NPCManager(world_state_dir: str = "world-state")
```
- Creates an NPC manager instance
- Uses JsonOperations and Validators internally

#### Core Methods

##### `create_npc(name: str, description: str, attitude: str) -> bool`
Create a new NPC with validation.
- **Validates**: Name format and attitude value
- **Checks**: NPC doesn't already exist
- **Creates**: Full NPC structure with timestamps and empty tags
- **Example**:
```python
manager = NPCManager()
success = manager.create_npc("Gandalf", "Wise wizard in grey robes", "helpful")
```

##### `update_npc(name: str, event: str) -> bool`
Add an event to NPC's history.
- **Appends**: Timestamped event to NPC's events array
- **Example**:
```python
manager.update_npc("Gandalf", "Gave party the ancient map")
```

##### `get_npc_status(name: str) -> Optional[Dict[str, Any]]`
Get complete NPC information.
- **Returns**: NPC data dictionary or None if not found
- **Example**:
```python
npc_data = manager.get_npc_status("Gandalf")
# Returns: {"description": "...", "attitude": "helpful", "events": [...], "tags": {...}}
```

##### `enhance_npc(name: str, enhanced_description: str) -> bool`
Update NPC description with enhanced details.
- **Example**:
```python
manager.enhance_npc("Gandalf", "Wise wizard in grey robes, carries a staff of power, member of the White Council")
```

#### Tagging Methods

##### `tag_location(name: str, *locations: str) -> bool`
Add location tags to NPC.
- **Example**:
```python
manager.tag_location("Gandalf", "Rivendell", "Shire", "Moria")
```

##### `untag_location(name: str, *locations: str) -> bool`
Remove location tags from NPC.
- **Example**:
```python
manager.untag_location("Gandalf", "Moria")
```

##### `tag_quest(name: str, *quests: str) -> bool`
Add quest tags to NPC.
- **Example**:
```python
manager.tag_quest("Gandalf", "destroy-ring", "defeat-sauron")
```

##### `untag_quest(name: str, *quests: str) -> bool`
Remove quest tags from NPC.
- **Example**:
```python
manager.untag_quest("Gandalf", "defeat-sauron")
```

##### `get_tags(name: str) -> Optional[Dict[str, List[str]]]`
Get all tags for an NPC.
- **Returns**: Dictionary with 'locations' and 'quests' lists
- **Example**:
```python
tags = manager.get_tags("Gandalf")
# Returns: {"locations": ["Rivendell", "Shire"], "quests": ["destroy-ring"]}
```

#### Query Methods

##### `list_npcs(filter_attitude: str = None, filter_location: str = None, filter_quest: str = None) -> Dict[str, Dict]`
List NPCs with optional filtering.
- **Filters**: Can filter by attitude, location tag, or quest tag
- **Example**:
```python
# Get all friendly NPCs
friendly_npcs = manager.list_npcs(filter_attitude="friendly")

# Get NPCs in Rivendell
rivendell_npcs = manager.list_npcs(filter_location="Rivendell")

# Get NPCs involved in destroy-ring quest
quest_npcs = manager.list_npcs(filter_quest="destroy-ring")
```

#### CLI Usage
```bash
# Create NPC
uv run python lib/npc_manager.py create "Gandalf" "Wise wizard" "helpful"

# Update NPC
uv run python lib/npc_manager.py update "Gandalf" "Met the party at the inn"

# Get status
uv run python lib/npc_manager.py status "Gandalf"

# Tag locations
uv run python lib/npc_manager.py tag-location "Gandalf" Rivendell Shire

# List NPCs
uv run python lib/npc_manager.py list --attitude friendly
uv run python lib/npc_manager.py list --location Rivendell
```

---

## Integration Example

Here's how these modules work together in the hybrid architecture:

```bash
#!/bin/bash
# dm-npc-refactored.sh - Bash script using Python modules

# Create NPC using Python module
uv run python lib/npc_manager.py create "$NPC_NAME" "$DESCRIPTION" "$ATTITUDE"

# Validate dice notation
if uv run python lib/validators.py dice "3d6+2"; then
    echo "Valid dice notation"
fi

# Update campaign time using JSON operations
uv run python lib/json_ops.py update campaign-overview.json \
    --key current_time --value "dusk"

# Get NPC data for display
NPC_DATA=$(uv run python lib/npc_manager.py status "$NPC_NAME")
echo "$NPC_DATA" | jq '.events'
```

## Error Handling

All modules follow consistent error handling patterns:

1. **Validation First**: All inputs are validated before operations
2. **Clear Error Messages**: Errors print `[ERROR]` prefixed messages
3. **Success Confirmation**: Successful operations print `[SUCCESS]` messages
4. **Return Codes**: CLI commands return non-zero exit codes on failure
5. **Atomic Operations**: File writes use temp files to prevent corruption
6. **Safe Defaults**: Missing files/keys return safe default values

## Performance Benefits

The hybrid architecture provides:

- **65% code reduction** in bash scripts (proven with dm-npc-refactored.sh)
- **Atomic file operations** prevent corruption during concurrent access
- **Centralized validation** ensures consistency across all tools
- **Reusable components** reduce duplication and maintenance burden
- **Type safety** in Python prevents common bash scripting errors
- **Better error messages** with context and suggestions

## Migration Guide

To migrate existing bash scripts to the hybrid pattern:

1. Identify repetitive JSON operations → Replace with `json_ops.py`
2. Find validation logic → Replace with `validators.py`
3. Extract complex business logic → Create Python modules
4. Keep bash for: argument parsing, user interaction, orchestration
5. Use Python for: computation, validation, data manipulation

See `docs/refactoring-guide.md` for detailed migration instructions.