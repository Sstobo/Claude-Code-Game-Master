---
slug: tts-spool-writer
title: speak_manager write path + gm-speak.sh narrate/say → narration.jsonl
category: enhancement
kind: afk
priority: p1
lane: agent
parentPrd: tts-narration
blockedBy: []
claimedBy: null
claimedAt: null
changedFiles: []
resolution: null
createdAt: 2026-06-07T22:05:00Z
updatedAt: 2026-06-07T22:05:00Z
---

## Parent

TTS narration (prds/tts-narration.md)

## Category

enhancement

## What to build

The write half of the spoken channel: the GM enqueues a beat's prose as ordered,
speaker-tagged segments, persisted to an append-only spool. Foundation for the daemon.

- `lib/speak_manager.py` → `class SpeakManager(EntityManager)` with:
  - `enqueue(segments)` where `segments` is a list of `{speaker, text}` dicts. Appends one
    JSON object per line to `narration.jsonl` = `{seq, speaker, text, ts}`. `seq` is
    monotonic (max existing seq + 1, computed from the file). `ts` from
    `json_ops.get_timestamp()`. Empty/whitespace `text` segments are skipped.
  - Append must be crash-coherent: O_APPEND single-write per line (preferred for a
    growing log) OR read-modify-temp+rename — pick one and document why. No partial lines.
  - Light input guard: cap each segment text (~8 KB), strip C0 control chars except
    `\n`/`\t`. (Heavy sanitization for speech happens in the daemon ticket.)
- `tools/gm-speak.sh` → wrapper mirroring `tools/gm-view.sh`: source `common.sh`.
  - `narrate` — reads a JSON array of segments from **stdin** (multi-line safe), calls
    `enqueue`. Guarded by `require_active_campaign`.
  - `say --speaker <who> "<text>"` — convenience single-segment enqueue (speaker defaults
    to `Narrator`). Guarded by `require_active_campaign`.
  - House `if not args.action: print_help; sys.exit(1)` pattern; `chmod +x`.
  - (The `listen` / `voices` / `stop` subcommands are added by later tickets — usage stub
    or omit.)

Spool path: `world-state/campaigns/<active>/narration.jsonl` (`self.campaign_dir /
"narration.jsonl"`). Already gitignored (`world-state/campaigns/*`).

## Acceptance criteria

- [ ] `gm-speak.sh narrate` with a JSON array on stdin appends one well-formed
      `{seq, speaker, text, ts}` line per segment, order preserved.
- [ ] `seq` is monotonic across calls (survives reload — second call continues numbering).
- [ ] `gm-speak.sh say --speaker "Donut" "hi"` enqueues a single segment; omitting
      `--speaker` defaults to `Narrator`.
- [ ] Empty/whitespace-only segment text is skipped; per-segment text cap enforced; C0
      ctrl chars (except `\n`/`\t`) stripped.
- [ ] `narrate`/`say` fail cleanly via `require_active_campaign` when no campaign is active.
- [ ] pytest covers the round-trip (enqueue → reload → parse lines → seq monotonic, order
      + speaker tags intact, empty skipped, cap enforced).

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-07T22:05:00Z  created → ready  [ship-it]
