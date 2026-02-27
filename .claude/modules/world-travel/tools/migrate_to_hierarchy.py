#!/usr/bin/env python3
"""Migration: convert _vehicle fields to hierarchy fields in locations.json."""

import sys
import json
import shutil
from pathlib import Path


def _find_project_root() -> Path:
    for p in Path(__file__).parents:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("pyproject.toml not found")


PROJECT_ROOT = _find_project_root()


def migrate_campaign(campaign_dir: Path, dry_run: bool = False) -> dict:
    locations_file = campaign_dir / "locations.json"

    if not locations_file.exists():
        return {"skipped": True, "reason": "no locations.json"}

    with open(locations_file, encoding="utf-8") as f:
        locations = json.load(f)

    changed = 0
    type_set = 0

    anchors: dict = {}
    for name, data in locations.items():
        v = data.get("_vehicle", {})
        if v.get("is_vehicle_anchor"):
            anchors[v.get("vehicle_id")] = name

    for name, data in locations.items():
        v = data.get("_vehicle", {})

        if not v:
            if "type" not in data:
                data["type"] = "world"
                type_set += 1
            continue

        if v.get("is_vehicle_anchor"):
            vehicle_id = v.get("vehicle_id", "")
            dock_room = v.get("dock_room", "")

            rooms = [
                n for n, d in locations.items()
                if d.get("_vehicle", {}).get("vehicle_id") == vehicle_id
                and not d.get("_vehicle", {}).get("is_vehicle_anchor")
            ]

            entry_points = [dock_room] if dock_room and dock_room in locations else []
            if not entry_points and rooms:
                entry_points = [rooms[0]]

            data["type"] = "compound"
            data["mobile"] = True
            data["children"] = rooms
            data["entry_points"] = entry_points
            changed += 1

        elif v.get("map_context") == "local":
            vehicle_id = v.get("vehicle_id", "")
            anchor_name = anchors.get(vehicle_id)

            data["type"] = "interior"
            if anchor_name:
                data["parent"] = anchor_name
                dock_room = locations.get(anchor_name, {}).get("_vehicle", {}).get("dock_room", "")
                if name == dock_room:
                    data["is_entry_point"] = True
                    data["entry_config"] = {"name": "Dock"}

            changed += 1

        else:
            if "type" not in data:
                data["type"] = "world"
                type_set += 1

    for name, data in locations.items():
        if data.get("type") == "compound":
            for child in data.get("children", []):
                if child in locations and "parent" not in locations[child]:
                    locations[child]["parent"] = name

    if changed == 0 and type_set == 0:
        return {"skipped": True, "reason": "nothing to migrate"}

    if not dry_run:
        backup = locations_file.with_suffix(".json.bak")
        shutil.copy2(locations_file, backup)

        with open(locations_file, "w", encoding="utf-8") as f:
            json.dump(locations, f, ensure_ascii=False, indent=2)

    return {
        "migrated": changed,
        "type_set": type_set,
        "dry_run": dry_run,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Migrate _vehicle fields to hierarchy")
    parser.add_argument("--campaign", help="Campaign name (default: active campaign)")
    parser.add_argument("--all", action="store_true", help="Migrate all campaigns")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    campaigns_dir = PROJECT_ROOT / "world-state" / "campaigns"

    if args.all:
        targets = [d for d in campaigns_dir.iterdir() if d.is_dir()]
    elif args.campaign:
        targets = [campaigns_dir / args.campaign]
    else:
        active_file = PROJECT_ROOT / "world-state" / "active-campaign.txt"
        if not active_file.exists():
            print("[ERROR] No active campaign and --campaign not specified")
            sys.exit(1)
        name = active_file.read_text().strip()
        targets = [campaigns_dir / name]

    for campaign_dir in targets:
        if not campaign_dir.exists():
            print(f"[ERROR] Campaign dir not found: {campaign_dir}")
            continue

        result = migrate_campaign(campaign_dir, dry_run=args.dry_run)

        if result.get("skipped"):
            print(f"{campaign_dir.name}: skipped — {result['reason']}")
        else:
            label = "[DRY-RUN] " if args.dry_run else ""
            print(
                f"{label}{campaign_dir.name}: "
                f"migrated={result['migrated']}, type_set={result['type_set']}"
            )


if __name__ == "__main__":
    main()
