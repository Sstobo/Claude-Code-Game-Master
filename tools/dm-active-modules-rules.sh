#!/usr/bin/env bash
# Собирает правила DM из слотов (.claude/dm/slots/) с учётом активных модулей:
# - Если модуль заменяет слот → вместо слота грузится rules.md модуля
# - Если модуль аддон → добавляется в конец после всех слотов

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ACTIVE=$(cat "$PROJECT_ROOT/world-state/active-campaign.txt" 2>/dev/null || echo "")
[ -z "$ACTIVE" ] && exit 0

OVERVIEW="$PROJECT_ROOT/world-state/campaigns/$ACTIVE/campaign-overview.json"
[ -f "$OVERVIEW" ] || exit 0

MODE="full"
[ "${1:-}" = "--modules-only" ] && MODE="modules"
[ "${1:-}" = "--core-only" ] && MODE="core"

uv run python - "$PROJECT_ROOT" "$OVERVIEW" "$MODE" << 'PYEOF'
import json, sys, os

project_root = sys.argv[1]
overview_path = sys.argv[2]
mode = sys.argv[3]  # full | modules | core

with open(overview_path) as f:
    d = json.load(f)

mods = d.get('modules', {})
enabled = [k for k, v in mods.items() if v]

# Collect slot replacements and addons from active modules
slot_replacements = {}  # slot_name -> (module_id, rules_content)
addons = []             # (module_id, rules_content)

for mod in enabled:
    manifest_path = f"{project_root}/.claude/modules/{mod}/module.json"
    rules_path = f"{project_root}/.claude/modules/{mod}/rules.md"
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        with open(rules_path) as f:
            rules = f.read()
    except FileNotFoundError:
        continue

    replaces = manifest.get('replaces', [])
    if replaces:
        for slot in replaces:
            if slot in slot_replacements:
                existing_mod, existing_rules = slot_replacements[slot]
                combined = (
                    f"⚠️ CONFLICT: Both '{existing_mod}' and '{mod}' replace slot '{slot}'. "
                    f"Both included — check module compatibility.\n\n"
                    f"--- FROM: {existing_mod} ---\n{existing_rules}\n\n"
                    f"--- FROM: {mod} ---\n{rules}"
                )
                slot_replacements[slot] = (f"{existing_mod}+{mod}", combined)
            else:
                slot_replacements[slot] = (mod, rules)
    else:
        addons.append((mod, rules))

if mode == "modules":
    for slot_id, (mod_id, mod_rules) in slot_replacements.items():
        print(f"\n---\n# MODULE RULES [{slot_id}]: {mod_id}\n")
        print(mod_rules)
    for mod_id, mod_rules in addons:
        print(f"\n---\n# MODULE RULES: {mod_id}\n")
        print(mod_rules)
    sys.exit(0)

# Read slots in alphabetical order (skip _preamble — print it first)
slots_dir = f"{project_root}/.claude/dm/slots"
if not os.path.isdir(slots_dir):
    sys.exit(0)

slot_files = sorted(f for f in os.listdir(slots_dir) if f.endswith('.md') and f != '_preamble.md')

# Print preamble first
preamble = f"{slots_dir}/_preamble.md"
if os.path.exists(preamble):
    with open(preamble) as f:
        print(f.read())

# Print each slot
for filename in slot_files:
    slot_id = filename[:-3]

    if mode == "core":
        # Core mode: skip replaced slots, print only pure core
        if slot_id not in slot_replacements:
            with open(f"{slots_dir}/{filename}") as f:
                print(f.read())
    else:
        # Full mode: slot replaced by module or core
        if slot_id in slot_replacements:
            mod_id, mod_rules = slot_replacements[slot_id]
            print(f"\n---\n# MODULE RULES [{slot_id}]: {mod_id}\n")
            print(mod_rules)
        else:
            with open(f"{slots_dir}/{filename}") as f:
                print(f.read())

if mode != "core":
    for mod_id, mod_rules in addons:
        print(f"\n---\n# MODULE RULES: {mod_id}\n")
        print(mod_rules)

PYEOF
