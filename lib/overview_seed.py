#!/usr/bin/env python3
"""Author per-book campaign-overview fields + campaign_rules; fix dangling rules_doc.

Import copies/creates ruleset.json but leaves campaign-overview as the default
scaffold (genre "Fantasy", no campaign_rules), so the book's signature systems live
nowhere the DM tooling reads (WorldKit.campaign_rules() reads overview.campaign_rules).
A sibling-kit copy can also leave ruleset.rules_doc pointing at a file that doesn't
exist. These helpers seed real overview content and null a dangling pointer.
"""

import json
from pathlib import Path


def seed_overview(campaign_dir, fields: dict = None, campaign_rules: dict = None) -> dict:
    """Merge `fields` into campaign-overview.json and set `campaign_rules`.

    Returns the written overview. Existing keys are overwritten only for the keys
    provided (player_position, session_count, etc. are preserved otherwise).
    """
    path = Path(campaign_dir) / "campaign-overview.json"
    overview = json.loads(path.read_text()) if path.exists() else {}
    if fields:
        overview.update(fields)
    if campaign_rules is not None:
        overview["campaign_rules"] = campaign_rules
    path.write_text(json.dumps(overview, indent=2))
    return overview


def fix_rules_doc(campaign_dir) -> dict:
    """Resolve a dangling ruleset.rules_doc: null it if the target file is missing.

    Returns {"rules_doc": <final value>, "changed": bool}.
    """
    cdir = Path(campaign_dir)
    path = cdir / "ruleset.json"
    if not path.exists():
        return {"rules_doc": None, "changed": False}
    ruleset = json.loads(path.read_text())
    doc = ruleset.get("rules_doc")
    if doc and not (cdir / doc).exists():
        ruleset["rules_doc"] = None
        path.write_text(json.dumps(ruleset, indent=2))
        return {"rules_doc": None, "changed": True}
    return {"rules_doc": doc, "changed": False}


def set_rules_doc(campaign_dir, filename: str = "rules.md") -> dict:
    """Point ruleset.rules_doc at `filename` (only if the file exists in the campaign).

    Returns {"rules_doc": <value>, "changed": bool}.
    """
    cdir = Path(campaign_dir)
    rs_path = cdir / "ruleset.json"
    if not rs_path.exists() or not (cdir / filename).exists():
        return {"rules_doc": None, "changed": False}
    ruleset = json.loads(rs_path.read_text())
    changed = ruleset.get("rules_doc") != filename
    ruleset["rules_doc"] = filename
    rs_path.write_text(json.dumps(ruleset, indent=2))
    return {"rules_doc": filename, "changed": changed}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed campaign-overview + fix rules_doc")
    parser.add_argument("campaign_dir")
    parser.add_argument("--fields-json", help="JSON object of overview fields to set")
    parser.add_argument("--rules-json", help="JSON object for campaign_rules")
    parser.add_argument("--fix-rules-doc", action="store_true")
    args = parser.parse_args()

    if args.fields_json or args.rules_json:
        fields = json.loads(args.fields_json) if args.fields_json else None
        rules = json.loads(args.rules_json) if args.rules_json else None
        seed_overview(args.campaign_dir, fields, rules)
        print("overview seeded")
    if args.fix_rules_doc:
        r = fix_rules_doc(args.campaign_dir)
        print(f"rules_doc: {r['rules_doc']} (changed={r['changed']})")


if __name__ == "__main__":
    main()
