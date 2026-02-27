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


class EntityManager:
    """Base class providing common initialization and CRUD patterns.

    All entity managers (NPC, Location, Plot, etc.) inherit from this class
    to ensure consistent campaign directory handling and JSON operations.
    """

    def __init__(self, world_state_dir: str = None, require_active_campaign: bool = True):
        """Initialize the entity manager with campaign context.

        Args:
            world_state_dir: Base world state directory OR direct campaign directory path.
                           Defaults to "world-state".
            require_active_campaign: If True, requires active campaign.
                                   If False, uses world_state_dir as direct campaign path.
                                   Useful for testing.

        Raises:
            RuntimeError: If require_active_campaign=True and no active campaign is set.
        """
        if not require_active_campaign and world_state_dir:
            # Direct campaign directory (for testing)
            self.campaign_dir = Path(world_state_dir)
            self.json_ops = JsonOperations(str(self.campaign_dir))
            self.validators = Validators()
            self.campaign_mgr = None
        else:
            # Normal flow: require active campaign
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

        Returns the entity dict if found, None otherwise.
        """
        entities = self._load_entities(filename)
        return entities.get(name)

    def _find_entity_name(self, filename: str, name: str) -> Optional[str]:
        """Find actual entity key using case-insensitive matching.

        Returns the actual key name if found (exact match preferred), None otherwise.
        """
        entities = self._load_entities(filename)
        if name in entities:
            return name
        name_lower = name.lower()
        for key in entities:
            if key.lower() == name_lower:
                return key
        return None

    def get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return self.json_ops.get_timestamp()

    @property
    def campaign_name(self) -> Optional[str]:
        """Get the name of the active campaign."""
        return self.campaign_mgr.get_active()
