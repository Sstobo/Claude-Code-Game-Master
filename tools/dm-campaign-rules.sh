#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATES_DIR="$PROJECT_DIR/.claude/campaign-rules-templates"

ACTION="${1:-list}"

_list() {
    local active_id=""
    local campaign_dir
    campaign_dir=$(bash "$SCRIPT_DIR/dm-campaign.sh" path 2>/dev/null || true)
    if [[ -n "$campaign_dir" && -f "$campaign_dir/campaign-overview.json" ]]; then
        active_id=$(uv run python -c "
import sys, json
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get('campaign_rules_template', {}).get('id', ''))
except: pass
" "$campaign_dir/campaign-overview.json" 2>/dev/null || true)
    fi

    echo ""
    local i=1
    for f in "$TEMPLATES_DIR"/*.md; do
        [[ -f "$f" ]] || continue
        local id name description genres recommended
        id=$(grep -m1 "^## id" "$f" -A1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        name=$(grep -m1 "^## name" "$f" -A1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        description=$(grep -m1 "^## description" "$f" -A1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        genres=$(grep -m1 "^## genres" "$f" -A1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        recommended=$(grep -m1 "^## recommended_for" "$f" -A1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

        local marker="  "
        [[ "$id" == "$active_id" ]] && marker="* "

        echo "  [$i] ${marker}${id}"
        echo "      ${name}"
        echo "      ${description}"
        echo "      Genres: ${genres}"
        echo "      Best for: ${recommended}"
        echo ""
        i=$((i+1))
    done
}

_show() {
    local target="${2:-}"
    for f in "$TEMPLATES_DIR"/*.md; do
        [[ -f "$f" ]] || continue
        local id
        id=$(grep -m1 "^## id" "$f" -A1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        if [[ "$id" == "$target" ]]; then
            cat "$f"
            return 0
        fi
    done
    echo "[ERROR] Template not found: $target" >&2
    return 1
}

_apply() {
    local target="${2:-}"
    local campaign_dir
    campaign_dir=$(bash "$SCRIPT_DIR/dm-campaign.sh" path 2>/dev/null)

    if [[ -z "$campaign_dir" ]]; then
        echo "[ERROR] No active campaign" >&2
        return 1
    fi

    for f in "$TEMPLATES_DIR"/*.md; do
        [[ -f "$f" ]] || continue
        local id
        id=$(grep -m1 "^## id" "$f" -A1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        if [[ "$id" == "$target" ]]; then
            uv run python - "$f" "$campaign_dir/campaign-overview.json" "$campaign_dir/campaign-rules.md" << 'PYEOF'
import sys, json, re

template_file = sys.argv[1]
overview_file = sys.argv[2]
rules_output_file = sys.argv[3]

with open(template_file) as f:
    content = f.read()

def extract(key):
    m = re.search(r'^## ' + key + r'\s*\n(.+?)(?=\n## |\Z)', content, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ''

template_id = extract('id')
name = extract('name')
description = extract('description')
genres = [g.strip() for g in extract('genres').split(',')]
recommended = extract('recommended_for')
rules_block = extract('rules')

with open(overview_file) as f:
    data = json.load(f)

data['campaign_rules_template'] = {
    'id': template_id,
    'name': name,
    'description': description,
    'genres': genres,
    'recommended_for': recommended,
}

with open(overview_file, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

import os
if os.path.exists(rules_output_file):
    print(f'[SKIP] campaign-rules.md already exists — not overwritten. Edit it manually.')
    print(f'[TIP]  Delete it first if you want a fresh template: rm {rules_output_file}')
else:
    with open(rules_output_file, 'w') as f:
        f.write(f'# Campaign Rules: {name}\n\n')
        f.write(f'> Template: `{template_id}`\n\n')
        f.write(rules_block)
        f.write('\n')
    print(f'[SUCCESS] campaign-rules.md created from template: {template_id}')

print(f'[SUCCESS] Campaign rules template set to: {template_id}')
PYEOF
            return 0
        fi
    done
    echo "[ERROR] Template not found: $target" >&2
    return 1
}

_recommend() {
    local genre="${2:-}"
    case "$genre" in
        horror|investigation|coc|scp|delta-green|lovecraft)
            echo "horror-investigation" ;;
        survival|stalker|fallout|metro|post-apocalyptic|zone)
            echo "survival-zone" ;;
        space|sci-fi|scifi|ftl|expanse|mass-effect)
            echo "space-travel" ;;
        political|intrigue|court|noble|vampire|masquerade|thrones)
            echo "political-intrigue" ;;
        civilization|tribal|empire|4x|strategy)
            echo "civilization" ;;
        *)
            echo "survival-zone" ;;
    esac
}

_read() {
    local campaign_dir
    campaign_dir=$(bash "$SCRIPT_DIR/dm-campaign.sh" path 2>/dev/null)

    if [[ -z "$campaign_dir" ]]; then
        echo "[ERROR] No active campaign" >&2
        return 1
    fi

    local rules_file="$campaign_dir/campaign-rules.md"
    if [[ ! -f "$rules_file" ]]; then
        echo "[INFO] No campaign-rules.md found in active campaign." >&2
        echo "[INFO] Use 'apply <id>' to create one from a template." >&2
        return 1
    fi

    cat "$rules_file"
}

case "$ACTION" in
    list)      _list ;;
    show)      _show "$@" ;;
    apply)     _apply "$@" ;;
    recommend) _recommend "$@" ;;
    read)      _read ;;
    *)
        echo "Usage: dm-campaign-rules.sh <list|show <id>|apply <id>|recommend <genre>|read>"
        exit 1
        ;;
esac
