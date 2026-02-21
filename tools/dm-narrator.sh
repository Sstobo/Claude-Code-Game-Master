#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
STYLES_DIR="$PROJECT_DIR/.claude/narrator-styles"

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
    print(d.get('narrator_style', {}).get('id', ''))
except: pass
" "$campaign_dir/campaign-overview.json" 2>/dev/null || true)
    fi

    echo ""
    local i=1
    for f in "$STYLES_DIR"/*.md; do
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
    for f in "$STYLES_DIR"/*.md; do
        [[ -f "$f" ]] || continue
        local id
        id=$(grep -m1 "^## id" "$f" -A1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        if [[ "$id" == "$target" ]]; then
            cat "$f"
            return 0
        fi
    done
    echo "[ERROR] Style not found: $target" >&2
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

    for f in "$STYLES_DIR"/*.md; do
        [[ -f "$f" ]] || continue
        local id
        id=$(grep -m1 "^## id" "$f" -A1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        if [[ "$id" == "$target" ]]; then
            uv run python - "$f" "$campaign_dir/campaign-overview.json" << 'PYEOF'
import sys, json, re

style_file = sys.argv[1]
overview_file = sys.argv[2]

with open(style_file) as f:
    content = f.read()

def extract(key):
    m = re.search(r'^## ' + key + r'\s*\n(.+?)(?=\n## |\Z)', content, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ''

def extract_list(key):
    block = extract(key)
    items = [l.lstrip('- ').strip() for l in block.splitlines() if l.strip().startswith('-')]
    return items

style_id = extract('id')
name = extract('name')
description = extract('description')
voice = extract('voice')
genres = [g.strip() for g in extract('genres').split(',')]
recommended = extract('recommended_for')
forbidden = extract_list('forbidden')

rules_block = extract('rules')

with open(overview_file) as f:
    data = json.load(f)

data['narrator_style'] = {
    'id': style_id,
    'name': name,
    'description': description,
    'voice': voice,
    'genres': genres,
    'recommended_for': recommended,
    'rules_raw': rules_block,
    'forbidden': forbidden
}

with open(overview_file, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'[SUCCESS] Narrator style set to: {style_id}')
PYEOF
            return 0
        fi
    done
    echo "[ERROR] Style not found: $target" >&2
    return 1
}

_recommend() {
    local genre="${2:-}"
    case "$genre" in
        horror|survival|sci-fi|scifi) echo "horror-atmospheric" ;;
        fantasy|epic|mythological)    echo "epic-heroic" ;;
        comedy|roguelike|absurd|any)  echo "sarcastic-puns" ;;
        noir|drama|dark*)             echo "serious-cinematic" ;;
        *)                            echo "sarcastic-puns" ;;
    esac
}

case "$ACTION" in
    list)      _list ;;
    show)      _show "$@" ;;
    apply)     _apply "$@" ;;
    recommend) _recommend "$@" ;;
    *)
        echo "Usage: dm-narrator.sh <list|show <id>|apply <id>|recommend <genre>>"
        exit 1
        ;;
esac
