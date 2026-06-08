"""image_gen.py — GM scene illustration via OpenAI gpt-image-2.

The GM calls this at high-impact beats (new location, boss reveal, big loot) to
show the player a real image. The image is saved into the active campaign's
``images/`` folder and the path is handed back so the caller can show the player
a clickable link. Every generation is logged with an estimated cost so spend is
auditable.

Display path: we DON'T try to render pixels in the terminal. We save a PNG and
return its path; the VS Code terminal linkifies the path so the player clicks to
open it.

No third-party SDK — the request is a single JSON POST, done with stdlib urllib
so the project gains no new dependency.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import base64
import urllib.error
import urllib.request
from pathlib import Path

from campaign_manager import CampaignManager


def resolve_campaign_dir(world_state_dir: str = "world-state"):
    """Return the active campaign dir as a Path, or None if none is active."""
    return CampaignManager(world_state_dir).get_active_campaign_dir()


CHRONICLER_FILE = "chronicler.json"


def _chronicler_path(campaign_dir) -> Path:
    return Path(campaign_dir) / CHRONICLER_FILE


def load_chronicler(campaign_dir=None):
    """Return this campaign's chronicler dict {name, style, persona}, or None."""
    campaign_dir = campaign_dir or resolve_campaign_dir()
    if campaign_dir is None:
        return None
    p = _chronicler_path(campaign_dir)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_chronicler(*, name=None, style=None, persona=None, campaign_dir=None) -> dict:
    """Merge-update the campaign's chronicler. Only provided fields change."""
    campaign_dir = campaign_dir or resolve_campaign_dir()
    if campaign_dir is None:
        raise ImageGenError("No active campaign. Run /new-game or /import first.")
    data = load_chronicler(campaign_dir) or {}
    if name is not None:
        data["name"] = name
    if style is not None:
        data["style"] = style
    if persona is not None:
        data["persona"] = persona
    _chronicler_path(campaign_dir).write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


API_URL = "https://api.openai.com/v1/images/generations"
DEFAULT_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")
DEFAULT_QUALITY = os.environ.get("OPENAI_IMAGE_QUALITY", "medium")
DEFAULT_SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1536x1024")  # cinematic landscape
REQUEST_TIMEOUT = 180  # gpt-image-2 can take up to ~2 min on complex prompts

# Published gpt-image-2 per-image USD pricing (docs). Used only to LOG estimated
# spend — not billed here. Unknown size/quality combos report None (logged as ?).
_COST = {
    "low":    {"1024x1024": 0.006, "1536x1024": 0.005, "1024x1536": 0.005},
    "medium": {"1024x1024": 0.053, "1536x1024": 0.041, "1024x1536": 0.041},
    "high":   {"1024x1024": 0.211, "1536x1024": 0.165, "1024x1536": 0.165},
}


def estimate_cost(quality: str, size: str):
    """Return the published per-image USD cost, or None if not in the table."""
    return _COST.get(quality, {}).get(size)


def _slug(title: str) -> str:
    """A filesystem-safe, short slug from a scene title."""
    s = re.sub(r"[^a-z0-9]+", "-", (title or "scene").lower()).strip("-")
    return (s or "scene")[:48]


def _next_path(images_dir: Path, title: str) -> Path:
    """Sequenced filename: NNNN-slug.png, continuing the highest existing index."""
    images_dir.mkdir(parents=True, exist_ok=True)
    highest = 0
    for p in images_dir.glob("[0-9][0-9][0-9][0-9]-*.png"):
        try:
            highest = max(highest, int(p.name[:4]))
        except ValueError:
            continue
    return images_dir / f"{highest + 1:04d}-{_slug(title)}.png"


def _log_generation(images_dir: Path, record: dict) -> None:
    """Append one JSON line to the per-campaign generation/spend log."""
    try:
        with (images_dir / "_gen-log.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass  # logging must never break a successful generation


class ImageGenError(Exception):
    """Raised for user-correctable failures (missing key, moderation, bad request)."""


def generate_image(prompt: str, *, title: str = "", quality: str = DEFAULT_QUALITY,
                   size: str = DEFAULT_SIZE, model: str = DEFAULT_MODEL) -> dict:
    """Generate one image and save it under the active campaign's images/ dir.

    Returns {path, rel_path, cost, model, quality, size, title}. Raises
    ImageGenError for actionable problems (no campaign, no key, moderation).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ImageGenError(
            "OPENAI_API_KEY not set. Add it to .env (OPENAI_API_KEY=sk-...) to enable images."
        )

    campaign_dir = resolve_campaign_dir()
    if campaign_dir is None:
        raise ImageGenError("No active campaign. Run /new-game or /import first.")

    if not prompt or not prompt.strip():
        raise ImageGenError("Empty prompt — describe the scene to illustrate.")

    # Lock the campaign's art-style signature into every prompt so the gallery
    # reads like one artbook even if the caller forgets to restate the style.
    chronicler = load_chronicler(campaign_dir)
    final_prompt = prompt
    style = (chronicler or {}).get("style", "").strip()
    if style and style.lower() not in prompt.lower():
        final_prompt = f"{prompt.rstrip()}\n\nConsistent art style (campaign signature): {style}."

    payload = json.dumps({
        "model": model,
        "prompt": final_prompt,
        "size": size,
        "quality": quality,
        "n": 1,
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ImageGenError(_format_http_error(e)) from e
    except urllib.error.URLError as e:
        raise ImageGenError(f"Network error reaching OpenAI: {e.reason}") from e

    try:
        b64 = body["data"][0]["b64_json"]
        image_bytes = base64.b64decode(b64)
    except (KeyError, IndexError, ValueError) as e:
        raise ImageGenError("Unexpected response from image API (no image data).") from e

    images_dir = Path(campaign_dir) / "images"
    out_path = _next_path(images_dir, title)
    out_path.write_bytes(image_bytes)

    cost = estimate_cost(quality, size)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "file": out_path.name,
        "title": title,
        "model": model,
        "quality": quality,
        "size": size,
        "est_cost_usd": cost,
        "chronicler": (chronicler or {}).get("name"),
        "prompt": final_prompt[:500],
    }
    _log_generation(images_dir, record)

    return {
        "path": str(out_path),
        "rel_path": os.path.relpath(out_path, Path.cwd()),
        "cost": cost,
        "model": model,
        "quality": quality,
        "size": size,
        "title": title,
    }


def _format_http_error(e: "urllib.error.HTTPError") -> str:
    """Turn an OpenAI HTTP error into an actionable one-line message."""
    try:
        err = json.loads(e.read().decode("utf-8")).get("error", {})
    except Exception:
        err = {}
    code = err.get("code")
    msg = err.get("message", "")
    if code == "moderation_blocked":
        stage = (err.get("moderation_details") or {}).get("moderation_stage", "input")
        return f"Image blocked by content moderation ({stage}). Revise the prompt and retry."
    if e.code == 401:
        return "OpenAI rejected the API key (401). Check OPENAI_API_KEY in .env."
    if e.code == 429:
        return "OpenAI rate limit / quota hit (429). Wait and retry, or check billing."
    return f"OpenAI error {e.code}: {msg or 'request failed'}"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate a scene image with gpt-image-2")
    parser.add_argument("--prompt", help="Scene description (or read from stdin if omitted)")
    parser.add_argument("--title", default="", help="Scene title (used in filename + canvas)")
    parser.add_argument("--quality", default=DEFAULT_QUALITY, choices=["low", "medium", "high", "auto"])
    parser.add_argument("--size", default=DEFAULT_SIZE, help="e.g. 1536x1024, 1024x1024, auto")
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON")
    parser.add_argument("--show-chronicler", action="store_true",
                        help="Print the campaign's chronicler (name/style/persona) and exit")
    parser.add_argument("--set-chronicler", action="store_true",
                        help="Save/merge the campaign's chronicler from the fields below, then exit")
    parser.add_argument("--name", help="Chronicler name (with --set-chronicler)")
    parser.add_argument("--style", help="Locked art-style signature (with --set-chronicler)")
    parser.add_argument("--persona", help="Chronicler persona/voice (with --set-chronicler)")
    args = parser.parse_args()

    if args.show_chronicler:
        chronicler = load_chronicler()
        if args.json:
            print(json.dumps(chronicler or {}))
        elif not chronicler:
            print("No chronicler set for this campaign yet.")
        else:
            print(f"Chronicler: {chronicler.get('name', '(unnamed)')}")
            if chronicler.get("persona"):
                print(f"  persona: {chronicler['persona']}")
            if chronicler.get("style"):
                print(f"  style:   {chronicler['style']}")
        return

    if args.set_chronicler:
        if args.name is None and args.style is None and args.persona is None:
            print("[ERROR] --set-chronicler needs at least one of --name/--style/--persona",
                  file=sys.stderr)
            sys.exit(1)
        try:
            data = save_chronicler(name=args.name, style=args.style, persona=args.persona)
        except ImageGenError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(data) if args.json else f"Chronicler saved: {data.get('name', '(unnamed)')}")
        return

    prompt = args.prompt if args.prompt is not None else sys.stdin.read()

    try:
        result = generate_image(prompt, title=args.title, quality=args.quality, size=args.size)
    except ImageGenError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result))
    else:
        print(result["path"])


if __name__ == "__main__":
    main()
