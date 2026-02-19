#!/usr/bin/env python3
"""
Campaign management module for DM tools
Handles multi-campaign support with CRUD operations
"""

import sys
import json
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone


class CampaignManager:
    """Manage multiple D&D campaigns"""

    def __init__(self, world_state_dir: str = "world-state"):
        self.world_state_dir = Path(world_state_dir)
        self.campaigns_dir = self.world_state_dir / "campaigns"
        self.active_file = self.world_state_dir / "active-campaign.txt"

        # Ensure directories exist
        self.campaigns_dir.mkdir(parents=True, exist_ok=True)

    def list_campaigns(self) -> List[Dict[str, Any]]:
        """
        List all campaigns with their metadata
        Returns list of dicts with name, path, character info
        """
        campaigns = []

        for campaign_dir in sorted(self.campaigns_dir.iterdir()):
            if not campaign_dir.is_dir():
                continue

            campaign_info = {
                "name": campaign_dir.name,
                "path": str(campaign_dir),
            }

            # Try to read campaign overview for more info
            overview_file = campaign_dir / "campaign-overview.json"
            if overview_file.exists():
                try:
                    with open(overview_file, 'r', encoding='utf-8') as f:
                        overview = json.load(f)
                    campaign_info["campaign_name"] = overview.get("campaign_name", "Unnamed")
                    campaign_info["current_location"] = overview.get("player_position", {}).get("current_location")
                    campaign_info["session_count"] = overview.get("session_count", 0)
                except (json.JSONDecodeError, IOError):
                    campaign_info["campaign_name"] = "Unknown"

            # Try to read character info
            char_file = campaign_dir / "character.json"
            if char_file.exists():
                try:
                    with open(char_file, 'r', encoding='utf-8') as f:
                        char = json.load(f)
                    campaign_info["character"] = {
                        "name": char.get("name", "Unknown"),
                        "race": char.get("race", "?"),
                        "class": char.get("class", "?"),
                        "level": char.get("level", 1)
                    }
                except (json.JSONDecodeError, IOError) as e:
                    print(f"[WARNING] Could not read character for {campaign_dir.name}: {e}", file=sys.stderr)

            campaigns.append(campaign_info)

        return campaigns

    def get_active(self) -> Optional[str]:
        """
        Get the currently active campaign name
        Returns None if no active campaign is set
        """
        if not self.active_file.exists():
            return None

        try:
            campaign_name = self.active_file.read_text().strip()
            # Verify the campaign actually exists
            campaign_path = self.campaigns_dir / campaign_name
            if campaign_path.is_dir():
                return campaign_name
            return None
        except IOError:
            return None

    def set_active(self, name: str) -> bool:
        """
        Set the active campaign by name
        Returns True on success, False if campaign doesn't exist
        """
        campaign_path = self.campaigns_dir / name
        if not campaign_path.is_dir():
            print(f"[ERROR] Campaign '{name}' does not exist")
            return False

        try:
            self.active_file.write_text(name)
            print(f"[SUCCESS] Active campaign set to: {name}")
            return True
        except IOError as e:
            print(f"[ERROR] Failed to set active campaign: {e}")
            return False

    def create(self, name: str, campaign_name: str = None) -> Optional[Path]:
        """
        Create a new campaign with empty state files
        name: folder name (typically character name, lowercase with hyphens)
        campaign_name: display name for the campaign
        Returns the campaign path on success, None on failure
        """
        # Normalize name for folder
        safe_name = name.lower().replace(' ', '-')
        campaign_path = self.campaigns_dir / safe_name

        if campaign_path.exists():
            print(f"[ERROR] Campaign '{safe_name}' already exists")
            return None

        try:
            # Create campaign directory structure
            campaign_path.mkdir(parents=True)
            (campaign_path / "saves").mkdir()
            (campaign_path / "extracted").mkdir()

            # Initialize empty state files
            self._init_empty_files(campaign_path, campaign_name or f"{name}'s Adventure")

            print(f"[SUCCESS] Created campaign: {safe_name}")
            return campaign_path
        except IOError as e:
            print(f"[ERROR] Failed to create campaign: {e}")
            # Clean up on failure
            if campaign_path.exists():
                shutil.rmtree(campaign_path)
            return None

    def delete(self, name: str, confirm: bool = False) -> bool:
        """
        Delete a campaign and all its data
        Requires confirm=True to actually delete
        Returns True on success
        """
        campaign_path = self.campaigns_dir / name

        if not campaign_path.is_dir():
            print(f"[ERROR] Campaign '{name}' does not exist")
            return False

        if not confirm:
            print(f"[WARNING] This will permanently delete campaign '{name}'")
            print(f"  Path: {campaign_path}")
            print("  Use confirm=True to proceed")
            return False

        try:
            # If this is the active campaign, clear active file
            if self.get_active() == name:
                self.active_file.unlink(missing_ok=True)

            shutil.rmtree(campaign_path)
            print(f"[SUCCESS] Deleted campaign: {name}")
            return True
        except IOError as e:
            print(f"[ERROR] Failed to delete campaign: {e}")
            return False

    def get_campaign_path(self, name: str = None) -> Optional[Path]:
        """
        Get the path to a campaign folder
        If name is None, returns path to active campaign
        Returns None if campaign doesn't exist
        """
        if name is None:
            name = self.get_active()
            if name is None:
                return None

        campaign_path = self.campaigns_dir / name
        if campaign_path.is_dir():
            return campaign_path
        return None

    def get_active_campaign_dir(self) -> Optional[Path]:
        """
        Get the directory for the active campaign.
        Returns None if no active campaign is set.
        """
        active = self.get_active()
        if active:
            return self.campaigns_dir / active
        return None

    def get_info(self, name: str = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed info about a campaign
        If name is None, uses active campaign
        """
        if name is None:
            name = self.get_active()
            if name is None:
                print("[ERROR] No active campaign set")
                return None

        campaign_path = self.campaigns_dir / name
        if not campaign_path.is_dir():
            print(f"[ERROR] Campaign '{name}' does not exist")
            return None

        info = {
            "name": name,
            "path": str(campaign_path),
            "is_active": self.get_active() == name
        }

        # Read campaign overview
        overview_file = campaign_path / "campaign-overview.json"
        if overview_file.exists():
            try:
                with open(overview_file, 'r', encoding='utf-8') as f:
                    info["overview"] = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Could not read campaign overview for {name}: {e}", file=sys.stderr)

        # Read character
        char_file = campaign_path / "character.json"
        if char_file.exists():
            try:
                with open(char_file, 'r', encoding='utf-8') as f:
                    info["character"] = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Could not read character for {name}: {e}", file=sys.stderr)

        # Count NPCs, locations, etc.
        for filename in ["npcs.json", "locations.json", "facts.json"]:
            filepath = campaign_path / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        info[filename.replace('.json', '_count')] = len(data)
                    elif isinstance(data, list):
                        info[filename.replace('.json', '_count')] = len(data)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"[WARNING] Could not read {filename} for {name}: {e}", file=sys.stderr)

        # Count saves
        saves_dir = campaign_path / "saves"
        if saves_dir.exists():
            info["saves_count"] = len(list(saves_dir.glob("*.json")))

        return info

    def init_campaign_files(self, campaign_path: Path, campaign_name: str, preserve_existing: bool = False):
        """
        Initialize campaign files in an existing directory.
        Public wrapper for _init_empty_files for use by other modules.

        Args:
            campaign_path: Path to the campaign directory
            campaign_name: Display name for the campaign
            preserve_existing: If True, don't overwrite files that already exist
        """
        self._init_empty_files(campaign_path, campaign_name, preserve_existing)

    def _init_empty_files(self, campaign_path: Path, campaign_name: str, preserve_existing: bool = False):
        """Initialize empty state files for a new campaign

        Args:
            campaign_path: Path to the campaign directory
            campaign_name: Display name for the campaign
            preserve_existing: If True, don't overwrite files that already exist
        """

        # campaign-overview.json
        overview_path = campaign_path / "campaign-overview.json"
        if not preserve_existing or not overview_path.exists():
            from module_loader import ModuleLoader
            default_modules = ModuleLoader(Path(__file__).parent.parent).get_default_modules()
            overview = {
                "campaign_name": campaign_name,
                "genre": "Fantasy",
                "tone": {
                    "horror": 30,
                    "comedy": 30,
                    "drama": 40
                },
                "current_date": "1st of the First Month, Year 1",
                "time_of_day": "Morning",
                "player_position": {
                    "current_location": None,
                    "previous_location": None
                },
                "current_character": None,
                "session_count": 0,
                "modules": default_modules
            }
            with open(overview_path, 'w', encoding='utf-8') as f:
                json.dump(overview, f, indent=2, ensure_ascii=False)

        # npcs.json
        npcs_path = campaign_path / "npcs.json"
        if not preserve_existing or not npcs_path.exists():
            with open(npcs_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2, ensure_ascii=False)

        # locations.json
        locations_path = campaign_path / "locations.json"
        if not preserve_existing or not locations_path.exists():
            with open(locations_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2, ensure_ascii=False)

        # facts.json
        facts_path = campaign_path / "facts.json"
        if not preserve_existing or not facts_path.exists():
            with open(facts_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2, ensure_ascii=False)

        # consequences.json
        consequences_path = campaign_path / "consequences.json"
        if not preserve_existing or not consequences_path.exists():
            with open(consequences_path, 'w', encoding='utf-8') as f:
                json.dump({"active": [], "resolved": []}, f, indent=2, ensure_ascii=False)

        # session-log.md - ALWAYS preserve if exists (append only)
        session_log_path = campaign_path / "session-log.md"
        if not session_log_path.exists():
            with open(session_log_path, 'w', encoding='utf-8') as f:
                f.write(f"# Session Log - {campaign_name}\n\n")
                f.write("*A new adventure begins...*\n\n")
                f.write("---\n\n")


def main():
    """CLI interface for campaign management"""
    import argparse

    parser = argparse.ArgumentParser(description='Campaign management')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # List campaigns
    subparsers.add_parser('list', help='List all campaigns')

    # Get active campaign
    subparsers.add_parser('active', help='Show active campaign')

    # Switch campaign
    switch_parser = subparsers.add_parser('switch', help='Switch active campaign')
    switch_parser.add_argument('name', help='Campaign name to switch to')

    # Create campaign
    create_parser = subparsers.add_parser('create', help='Create new campaign')
    create_parser.add_argument('name', help='Campaign folder name (character name)')
    create_parser.add_argument('--campaign-name', help='Display name for the campaign')

    # Delete campaign
    delete_parser = subparsers.add_parser('delete', help='Delete a campaign')
    delete_parser.add_argument('name', help='Campaign name to delete')
    delete_parser.add_argument('--confirm', action='store_true', help='Confirm deletion')

    # Get campaign info
    info_parser = subparsers.add_parser('info', help='Get campaign info')
    info_parser.add_argument('name', nargs='?', help='Campaign name (defaults to active)')

    # Get campaign path
    path_parser = subparsers.add_parser('path', help='Get campaign directory path')
    path_parser.add_argument('name', nargs='?', help='Campaign name (defaults to active)')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = CampaignManager()

    if args.action == 'list':
        campaigns = manager.list_campaigns()
        if not campaigns:
            print("No campaigns found")
            print("Create one with: dm-campaign.sh create <name>")
        else:
            active = manager.get_active()
            print(f"{'':2}{'NAME':20}{'CHARACTER':25}{'SESSIONS':10}")
            print("-" * 60)
            for c in campaigns:
                marker = "*" if c["name"] == active else " "
                char_info = ""
                if "character" in c:
                    char = c["character"]
                    char_info = f"{char['name']} ({char['race']} {char['class']} L{char['level']})"
                sessions = c.get("session_count", 0)
                print(f"{marker} {c['name']:20}{char_info:25}{sessions}")
            print()
            if active:
                print(f"* = active campaign ({active})")

    elif args.action == 'active':
        active = manager.get_active()
        if active:
            print(active)
        else:
            print("No active campaign set")
            sys.exit(1)

    elif args.action == 'switch':
        if not manager.set_active(args.name):
            sys.exit(1)

    elif args.action == 'create':
        campaign_name = args.campaign_name or f"{args.name}'s Adventure"
        path = manager.create(args.name, campaign_name)
        if not path:
            sys.exit(1)
        print(f"Campaign created at: {path}")

    elif args.action == 'delete':
        if not manager.delete(args.name, confirm=args.confirm):
            sys.exit(1)

    elif args.action == 'info':
        info = manager.get_info(args.name)
        if not info:
            sys.exit(1)
        print(json.dumps(info, indent=2, ensure_ascii=False))

    elif args.action == 'path':
        path = manager.get_campaign_path(args.name)
        if path:
            print(path)
        else:
            print("Campaign not found", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
