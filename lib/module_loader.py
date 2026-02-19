#!/usr/bin/env python3
"""
Module Loader for DM System

Discovers, validates, and loads campaign modules.
Single source of truth: campaign-overview.json["modules"] per campaign.
Global defaults come from module.json["enabled_by_default"].
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ModuleLoader:
    """Load and manage DM System modules."""

    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent
        self.project_root = project_root
        self.modules_dir = self.project_root / ".claude" / "modules"
        self.registry_file = self.modules_dir / "registry.json"

    # ------------------------------------------------------------------ #
    # Registry (global module catalogue)
    # ------------------------------------------------------------------ #

    def scan_modules(self) -> Dict[str, Dict]:
        if not self.modules_dir.exists():
            return {}

        modules = {}
        for module_dir in self.modules_dir.iterdir():
            if not module_dir.is_dir():
                continue
            module_json = module_dir / "module.json"
            if not module_json.exists():
                continue
            try:
                with open(module_json, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                module_id = metadata.get("id")
                if module_id:
                    modules[module_id] = metadata
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[WARNING] Failed to load {module_dir.name}: {e}")
        return modules

    def update_registry(self) -> bool:
        modules = self.scan_modules()
        registry = {"version": "1.0.0", "modules": modules}
        try:
            self.modules_dir.mkdir(parents=True, exist_ok=True)
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to write registry: {e}")
            return False

    def load_registry(self) -> Dict[str, Dict]:
        if not self.registry_file.exists():
            self.update_registry()
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f).get("modules", {})
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def get_module(self, module_id: str) -> Optional[Dict]:
        return self.load_registry().get(module_id)

    # ------------------------------------------------------------------ #
    # Campaign-level module state (single source of truth)
    # ------------------------------------------------------------------ #

    def _active_campaign_overview(self) -> Optional[Path]:
        active_file = self.project_root / "world-state" / "active-campaign.txt"
        if not active_file.exists():
            return None
        name = active_file.read_text().strip()
        if not name:
            return None
        return self.project_root / "world-state" / "campaigns" / name / "campaign-overview.json"

    def _load_overview(self, overview_path: Path) -> Dict:
        try:
            with open(overview_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_overview(self, overview_path: Path, data: Dict) -> bool:
        try:
            with open(overview_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save overview: {e}")
            return False

    def get_default_modules(self) -> Dict[str, bool]:
        """Build default modules map from enabled_by_default in each module.json."""
        modules = self.scan_modules()
        return {mid: bool(meta.get("enabled_by_default", False))
                for mid, meta in modules.items()}

    def init_campaign_modules(self, overview_path: Path) -> bool:
        """
        Write 'modules' key into campaign-overview.json using defaults.
        Called when creating a new campaign.
        """
        data = self._load_overview(overview_path)
        if "modules" not in data:
            data["modules"] = self.get_default_modules()
            return self._save_overview(overview_path, data)
        return True

    def get_campaign_modules(self, overview_path: Optional[Path] = None) -> Dict[str, bool]:
        """
        Return {module_id: enabled} for the active (or given) campaign.
        Falls back to defaults if campaign has no 'modules' key yet.
        """
        path = overview_path or self._active_campaign_overview()
        if not path or not path.exists():
            return self.get_default_modules()
        data = self._load_overview(path)
        if "modules" not in data:
            defaults = self.get_default_modules()
            data["modules"] = defaults
            self._save_overview(path, data)
            return defaults
        return data["modules"]

    def check_dependencies_for_campaign(self, module_id: str,
                                         overview_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
        """
        Check if all hard dependencies of a module are enabled in the campaign.
        Returns (ok, missing_deps).
        Uses scan_modules() to always read fresh data from module.json files.
        """
        all_modules = self.scan_modules()
        module = all_modules.get(module_id)
        if not module:
            return False, [f"Module '{module_id}' not found"]
        deps = module.get("dependencies", [])
        if isinstance(deps, dict):
            deps = []
        if not deps:
            return True, []
        campaign_modules = self.get_campaign_modules(overview_path)
        missing = [d for d in deps if not campaign_modules.get(d, False)]
        return len(missing) == 0, missing

    def set_campaign_module(self, module_id: str, enabled: bool,
                            overview_path: Optional[Path] = None) -> bool:
        """Enable or disable a module for the active (or given) campaign.
        When enabling: checks hard dependencies are satisfied.
        When disabling: checks nothing depends on this module.
        """
        path = overview_path or self._active_campaign_overview()
        if not path:
            print("[ERROR] No active campaign")
            return False
        if not path.exists():
            print(f"[ERROR] Campaign overview not found: {path}")
            return False

        all_modules = self.scan_modules()
        if module_id not in all_modules:
            print(f"[ERROR] Module '{module_id}' not found")
            return False

        if enabled:
            ok, missing = self.check_dependencies_for_campaign(module_id, path)
            if not ok:
                for dep in missing:
                    print(f"[ERROR] Required dependency '{dep}' is not enabled.")
                    print(f"        Enable it first: dm-module.sh activate {dep}")
                return False

        if not enabled:
            # Warn if other enabled modules depend on this one
            dependents = []
            campaign_modules = self.get_campaign_modules(path)
            for mid, meta in all_modules.items():
                if mid == module_id:
                    continue
                if not campaign_modules.get(mid, False):
                    continue
                deps = meta.get("dependencies", [])
                if isinstance(deps, dict):
                    continue
                if module_id in deps:
                    dependents.append(mid)
            if dependents:
                print(f"[ERROR] Cannot deactivate '{module_id}' — required by: {', '.join(dependents)}")
                print(f"        Deactivate them first.")
                return False

        data = self._load_overview(path)
        if "modules" not in data:
            data["modules"] = self.get_default_modules()
        data["modules"][module_id] = enabled
        return self._save_overview(path, data)

    def is_module_enabled(self, module_id: str,
                          overview_path: Optional[Path] = None) -> bool:
        """Check if a module is enabled for the active campaign."""
        return self.get_campaign_modules(overview_path).get(module_id, False)

    # ------------------------------------------------------------------ #
    # List (merges global registry + campaign state)
    # ------------------------------------------------------------------ #

    def list_modules(self, filter_status: Optional[str] = None) -> List[Dict]:
        # Always scan fresh so dependency changes in module.json are reflected immediately
        self.update_registry()
        modules = self.load_registry()
        campaign_modules = self.get_campaign_modules()
        result = []
        for module_id, metadata in modules.items():
            enabled = campaign_modules.get(module_id,
                                           bool(metadata.get("enabled_by_default", False)))
            status = "Active" if enabled else "Inactive"
            if filter_status and filter_status.lower() not in status.lower():
                continue

            deps = metadata.get("dependencies", [])
            if isinstance(deps, dict):
                deps = []
            missing_deps = [d for d in deps if not campaign_modules.get(d, False)]

            entry = dict(metadata)
            entry["_status"] = status
            entry["_enabled"] = enabled
            entry["_missing_deps"] = missing_deps
            result.append(entry)
        return result

    # ------------------------------------------------------------------ #
    # Validation / dependencies
    # ------------------------------------------------------------------ #

    def validate_module(self, module_id: str) -> Tuple[bool, str]:
        module = self.get_module(module_id)
        if not module:
            return False, f"Module '{module_id}' not found in registry"
        for field in ["id", "name", "version", "description"]:
            if field not in module:
                return False, f"Missing required field: {field}"
        return True, ""

    def check_dependencies(self, module_id: str, enabled_modules: List[str]) -> Tuple[bool, List[str]]:
        module = self.get_module(module_id)
        if not module:
            return False, [f"Module '{module_id}' not found"]
        deps = module.get("dependencies", [])
        if isinstance(deps, dict):
            deps = []
        missing = [d for d in deps if d not in enabled_modules]
        return len(missing) == 0, missing


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="DM System Module Loader")
    parser.add_argument("action",
                        choices=["scan", "list", "info", "validate", "activate", "deactivate"],
                        help="Action to perform")
    parser.add_argument("--module", help="Module ID")
    parser.add_argument("--filter", help="Filter by status (Active/Inactive)")
    parser.add_argument("--campaign", help="Path to campaign-overview.json (optional)")

    args = parser.parse_args()
    loader = ModuleLoader()
    overview = Path(args.campaign) if args.campaign else None

    if args.action == "scan":
        print("Scanning modules...")
        if loader.update_registry():
            modules = loader.load_registry()
            print(f"[SUCCESS] Found {len(modules)} modules")
            for mid, meta in modules.items():
                print(f"  • {mid} — {meta['name']}")
        else:
            print("[ERROR] Failed to update registry")

    elif args.action == "list":
        modules = loader.list_modules(filter_status=args.filter)
        if not modules:
            print("No modules found")
        else:
            print(f"Available modules ({len(modules)}):\n")
            for m in modules:
                status = m.get("_status", "Unknown")
                enabled = m.get("_enabled", False)
                missing_deps = m.get("_missing_deps", [])
                # Warn if enabled but deps missing
                if enabled and missing_deps:
                    icon = "⚠️ "
                    status_str = f"Active (BROKEN — needs: {', '.join(missing_deps)})"
                elif not enabled and missing_deps:
                    icon = "❌"
                    status_str = f"Inactive (requires: {', '.join(missing_deps)})"
                elif enabled:
                    icon = "✅"
                    status_str = "Active"
                else:
                    icon = "❌"
                    status_str = "Inactive"

                deps = m.get("dependencies", [])
                if isinstance(deps, dict):
                    deps = []

                print(f"  {m['id']}")
                print(f"    Name: {m['name']}")
                print(f"    Status: {icon} {status_str}")
                if deps:
                    print(f"    Requires: {', '.join(deps)}")
                print(f"    Description: {m['description']}")
                print()

    elif args.action == "info":
        if not args.module:
            print("[ERROR] --module required for 'info'")
            sys.exit(1)
        module = loader.get_module(args.module)
        if not module:
            print(f"[ERROR] Module '{args.module}' not found")
            sys.exit(1)
        print(json.dumps(module, indent=2, ensure_ascii=False))

    elif args.action == "validate":
        if not args.module:
            print("[ERROR] --module required for 'validate'")
            sys.exit(1)
        ok, err = loader.validate_module(args.module)
        if ok:
            print(f"[SUCCESS] Module '{args.module}' is valid")
        else:
            print(f"[ERROR] {err}")
            sys.exit(1)

    elif args.action == "activate":
        if not args.module:
            print("[ERROR] --module required for 'activate'")
            sys.exit(1)
        if loader.set_campaign_module(args.module, True, overview):
            print(f"[SUCCESS] Module '{args.module}' activated")
        else:
            sys.exit(1)

    elif args.action == "deactivate":
        if not args.module:
            print("[ERROR] --module required for 'deactivate'")
            sys.exit(1)
        if loader.set_campaign_module(args.module, False, overview):
            print(f"[SUCCESS] Module '{args.module}' deactivated")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
