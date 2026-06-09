#!/bin/bash
# gm-image.sh - Generate a scene illustration with gpt-image-2 (image_gen.py)
#
# The GM calls this at high-impact beats (new location, boss reveal, big loot) to
# show the player a real image. The PNG is saved into the active campaign's
# images/ folder; we print a clickable file:// link (VS Code linkifies it) for
# the player to open. Every generation is logged with an estimated cost in
# _gen-log.jsonl.
#
#   gm-image.sh generate --prompt "..." [--title "..."] [--quality low|medium|high]
#                        [--size 1536x1024]
#   gm-image.sh log                     # show this campaign's generation/spend log

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 1 ]; then
    echo "Usage: gm-image.sh <action> [args]"
    echo ""
    echo "Actions:"
    echo "  generate --prompt <text>   - Generate + save a scene image (gpt-image-2)"
    echo "      --title <text>           Scene title (used in the filename)"
    echo "      --quality low|medium|high  Default: medium (~\$0.04 landscape)"
    echo "      --size 1536x1024           Default: 1536x1024 (cinematic landscape)"
    echo "      --character <name>         Auto-inject that character's visual_appearance (repeatable)"
    echo "  appearance <name>          - Print a character's visual_appearance bible line (PC or NPC)"
    echo "  chronicler                 - Show this campaign's in-world chronicler"
    echo "      --name <text>            Set the chronicler's name"
    echo "      --style <text>           Set the locked art-style signature (auto-added to every prompt)"
    echo "      --persona <text>         Set the chronicler's voice/persona"
    echo "  log                        - Show this campaign's generation/spend log"
    echo ""
    echo "Examples:"
    echo "  gm-image.sh chronicler --name \"Astreus\" --style \"rough Frazetta-esque ink wash, sword-and-sorcery woodcut\" --persona \"a drunk court-scholar who follows your deeds and exaggerates the gore\""
    echo "  gm-image.sh generate --title \"The Sunken Crypt\" --prompt \"A flooded stone crypt lit by green torchlight, dark fantasy, cinematic\""
    echo "  gm-image.sh log"
    exit 1
fi

ACTION="$1"
shift

case "$ACTION" in
    generate)
        require_active_campaign

        PROMPT="" ; TITLE="" ; QUALITY="medium" ; SIZE="1536x1024" ; CHARS=()
        while [ "$#" -gt 0 ]; do
            case "$1" in
                --prompt)    PROMPT="$2" ; shift 2 ;;
                --title)     TITLE="$2"  ; shift 2 ;;
                --quality)   QUALITY="$2"; shift 2 ;;
                --size)      SIZE="$2"   ; shift 2 ;;
                --character) CHARS+=(--character "$2") ; shift 2 ;;
                *) error "Unknown flag: $1" ; exit 1 ;;
            esac
        done

        if [ -z "$PROMPT" ]; then
            error "Missing --prompt (describe the scene to illustrate)."
            exit 1
        fi

        if ! check_env OPENAI_API_KEY; then
            error "OPENAI_API_KEY not set. Add it to .env (OPENAI_API_KEY=sk-...) to enable images."
            exit 1
        fi

        # image_gen.py emits a JSON result on success; capture it.
        RESULT=$($PYTHON_CMD "$LIB_DIR/image_gen.py" \
            --prompt "$PROMPT" --title "$TITLE" --quality "$QUALITY" --size "$SIZE" \
            "${CHARS[@]}" --json)
        STATUS=$?
        if [ "$STATUS" -ne 0 ]; then
            exit "$STATUS"  # image_gen.py already printed the actionable error
        fi

        IMG_PATH=$(echo "$RESULT" | $PYTHON_CMD -c "import sys,json; print(json.load(sys.stdin)['path'])")
        SHORT_PATH=$(echo "$RESULT" | $PYTHON_CMD -c "import sys,json; d=json.load(sys.stdin); print(d.get('short_path') or d['path'])")
        COST=$(echo "$RESULT" | $PYTHON_CMD -c "import sys,json; c=json.load(sys.stdin)['cost']; print('%.3f'%c if c is not None else '?')")

        log_token_usage "gm-image.generate" "quality=$QUALITY" "size=$SIZE" "est_cost_usd=$COST"

        # Short symlink so the file:// link stays on one line and stays clickable
        # (the deep campaign path wraps in the terminal, which breaks the click target).
        success "Image generated: ${TITLE:-untitled}"
        echo "  open: file://$SHORT_PATH"
        echo "  est cost: \$$COST ($QUALITY $SIZE)"
        ;;

    chronicler)
        require_active_campaign

        NAME="" ; STYLE="" ; PERSONA="" ; ANY_SET=0
        while [ "$#" -gt 0 ]; do
            case "$1" in
                --name)    NAME="$2"    ; ANY_SET=1 ; shift 2 ;;
                --style)   STYLE="$2"   ; ANY_SET=1 ; shift 2 ;;
                --persona) PERSONA="$2" ; ANY_SET=1 ; shift 2 ;;
                *) error "Unknown flag: $1" ; exit 1 ;;
            esac
        done

        if [ "$ANY_SET" -eq 0 ]; then
            $PYTHON_CMD "$LIB_DIR/image_gen.py" --show-chronicler
            exit $?
        fi

        ARGS=(--set-chronicler)
        [ -n "$NAME" ]    && ARGS+=(--name "$NAME")
        [ -n "$STYLE" ]   && ARGS+=(--style "$STYLE")
        [ -n "$PERSONA" ] && ARGS+=(--persona "$PERSONA")
        $PYTHON_CMD "$LIB_DIR/image_gen.py" "${ARGS[@]}"
        exit $?
        ;;

    appearance)
        require_active_campaign
        if [ -z "$1" ]; then
            error "Usage: gm-image.sh appearance \"<character name>\""
            exit 1
        fi
        $PYTHON_CMD "$LIB_DIR/image_gen.py" --appearance "$1"
        exit $?
        ;;

    log)
        require_active_campaign
        LOG_FILE="$WORLD_STATE_DIR/images/_gen-log.jsonl"
        if [ ! -f "$LOG_FILE" ]; then
            info "No images generated yet for this campaign."
            exit 0
        fi
        $PYTHON_CMD - "$LOG_FILE" <<'PY'
import json, sys
total = 0.0
with open(sys.argv[1]) as f:
    for line in f:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        c = r.get("est_cost_usd")
        total += c or 0.0
        print(f"{r.get('ts','?'):20}  {('$%.3f'%c) if c is not None else '   ?  ':>7}  "
              f"{r.get('quality','?'):6} {r.get('size','?'):10}  {r.get('file','?')}")
print(f"\nTotal estimated spend: ${total:.2f}")
PY
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: generate, chronicler, appearance, log"
        exit 1
        ;;
esac

exit $?
