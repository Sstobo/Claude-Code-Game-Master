#!/usr/bin/env python3
"""
Base class for all entity managers in the DM system.
Provides common initialization and CRUD patterns.
"""

import sys
from typing import Dict, Optional, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from json_ops import JsonOperations
from validators import Validators
from campaign_manager import CampaignManager
from entity_aliases import resolve_entity_name


class EntityManager:
    """Base class providing common initialization and CRUD patterns.

    All entity managers (NPC, Location, Plot, etc.) inherit from this class
    to ensure consistent campaign directory handling and JSON operations.
    """

    def __init__(self, world_state_dir: str = None):
        """Initialize the entity manager with campaign context.

        Args:
            world_state_dir: Base world state directory. Defaults to "world-state".

        Raises:
            RuntimeError: If no active campaign is set.
        """
        base_dir = world_state_dir or "world-state"
        self.campaign_mgr = CampaignManager(base_dir)

        # Get the active campaign directory
        active_dir = self.campaign_mgr.get_active_campaign_dir()

        if active_dir is None:
            raise RuntimeError("No active campaign. Run /new-game or /import first.")

        self.campaign_dir = active_dir
        self.json_ops = JsonOperations(str(active_dir))
        self.validators = Validators()

    def _load_entities(self, filename: str) -> dict:
        """Load entities from JSON file.

        Args:
            filename: Name of the JSON file (e.g., "npcs.json")

        Returns:
            Dictionary of entities, or empty dict if file doesn't exist.
        """
        return self.json_ops.load_json(filename) or {}

    def _save_entities(self, filename: str, data: dict) -> bool:
        """Save entities to JSON file.

        Args:
            filename: Name of the JSON file
            data: Complete entity dictionary to save

        Returns:
            True on success, False on failure.
        """
        return self.json_ops.save_json(filename, data)

    def _entity_exists(self, filename: str, name: str) -> bool:
        """Check if an entity exists.

        Args:
            filename: Name of the JSON file
            name: Entity name/key to check

        Returns:
            True if entity exists, False otherwise.
        """
        return self.json_ops.check_exists(filename, name)

    def _add_entity(self, filename: str, name: str, data: dict) -> bool:
        """Add a new entity.

        Args:
            filename: Name of the JSON file
            name: Entity name/key
            data: Entity data dictionary

        Returns:
            True on success, False on failure.
        """
        return self.json_ops.update_json(filename, {name: data})

    def _update_entity(self, filename: str, name: str, updates: dict) -> bool:
        """Update an existing entity.

        Args:
            filename: Name of the JSON file
            name: Entity name/key
            updates: Dictionary of fields to update

        Returns:
            True on success, False on failure.
        """
        entities = self._load_entities(filename)
        if name not in entities:
            return False

        entities[name].update(updates)
        return self._save_entities(filename, entities)

    def _delete_entity(self, filename: str, name: str) -> bool:
        """Delete an entity.

        Args:
            filename: Name of the JSON file
            name: Entity name/key to delete

        Returns:
            True on success, False on failure.
        """
        entities = self._load_entities(filename)
        if name not in entities:
            return False

        del entities[name]
        return self._save_entities(filename, entities)

    def _get_entity(self, filename: str, name: str) -> Optional[dict]:
        """Get a single entity by name.

        Exact match first, then alias-aware resolution (case/title/parenthetical
        drift, explicit `aliases`). Returns the entity dict if found, else None.
        """
        entities = self._load_entities(filename)
        if name in entities:
            return entities[name]
        key = resolve_entity_name(name, entities)
        return entities.get(key) if key else None

    def _find_entity_name(self, filename: str, name: str) -> Optional[str]:
        """Find the actual entity key via alias-aware resolution.

        Resolution order: exact -> case-insensitive -> explicit aliases ->
        normalized (title/parenthetical-insensitive) equality. None if unresolved.
        """
        entities = self._load_entities(filename)
        return resolve_entity_name(name, entities)

    def get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return self.json_ops.get_timestamp()

    @property
    def campaign_name(self) -> Optional[str]:
        """Get the name of the active campaign."""
        return self.campaign_mgr.get_active()
