#!/usr/bin/env python3
"""Post-extraction item correctness pass: cursed flag, type taxonomy, value field.

Extractor heuristics over-flag `cursed` from lore keywords, overload the `wondrous`
type across keys/portals/boxes/coupons, and stuff box-contents into `value`. This
deterministic pass:
  - clears `cursed` unless the item's MECHANICS (not its lore description) state an
    actual penalty/binding to the bearer;
  - reclassifies `wondrous`/blank types into key/portal/lootbox/coupon by keyword;
  - nulls non-price `value` (moving substantive text into mechanics).
Repeatable on every import, not a hand-edit.
"""

import json
import re
import sys
from pathlib import Path

# Bearer-harm / binding language in MECHANICS that justifies cursed:true.
_PENALTY_RE = re.compile(
    r"disadvantage|cannot be removed|can'?t be removed|bound until|drains? your|"
    r"you take \d|at the cost of|penalty to|-\d+\s|backfire|lose \d|reduces your",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(r"\d+\s*(gp|gold|cp|sp|pp|credits?|coins?)", re.IGNORECASE)

_TYPE_KEYWORDS = [
    ("key", ("key",)),
    ("portal", ("portal", "subspace")),
    ("lootbox", ("loot box", "lootbox", " box", "box of", "chest", "coupon box")),
    ("coupon", ("coupon", "voucher")),
]


def _text(item, *fields):
    return " ".join(str(item.get(f, "")) for f in fields)


def fix_cursed(item: dict) -> bool:
    """Clear cursed unless mechanics state a real penalty. Returns True if changed."""
    if not item.get("cursed"):
        return False
    mech = _text(item, "mechanics")
    if _PENALTY_RE.search(mech):
        return False  # legitimately cursed
    item["cursed"] = False
    return True


def fix_type(item: dict) -> bool:
    """Reclassify overloaded 'wondrous'/blank types via name+description keywords."""
    cur = str(item.get("type", "")).lower()
    if cur not in ("", "wondrous", "wondrous item"):
        return False
    hay = _text(item, "name", "description").lower()
    for new_type, kws in _TYPE_KEYWORDS:
        if any(k in hay for k in kws):
            item["type"] = new_type
            return True
    return False


def fix_value(item: dict) -> bool:
    """Null a non-price value; preserve substantive text in mechanics."""
    val = item.get("value")
    if not val or not isinstance(val, str):
        return False
    if _PRICE_RE.search(val):
        return False  # a real price, keep
    # non-price (e.g. box-contents) -> move to mechanics, null value
    if len(val) > 12:
        mech = item.get("mechanics", "")
        item["mechanics"] = (mech + " " if mech else "") + f"(Contents/notes: {val})"
    item["value"] = ""
    return True


def fix_items(items: dict) -> dict:
    report = {"cursed_cleared": [], "retyped": [], "value_cleared": []}
    for name, item in (items or {}).items():
        if not isinstance(item, dict):
            continue
        if fix_cursed(item):
            report["cursed_cleared"].append(name)
        if fix_type(item):
            report["retyped"].append({"item": name, "type": item["type"]})
        if fix_value(item):
            report["value_cleared"].append(name)
    return report


def run_fixup(campaign_dir) -> dict:
    path = Path(campaign_dir) / "items.json"
    items = json.loads(path.read_text()) if path.exists() else {}
    report = fix_items(items)
    if items:
        path.write_text(json.dumps(items, indent=2))
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Item correctness fixup")
    parser.add_argument("campaign_dir")
    args = parser.parse_args()
    r = run_fixup(args.campaign_dir)
    print(f"  cursed cleared: {len(r['cursed_cleared'])}  {r['cursed_cleared'][:6]}")
    print(f"  retyped: {len(r['retyped'])}")
    print(f"  value cleared: {len(r['value_cleared'])}")


if __name__ == "__main__":
    main()
