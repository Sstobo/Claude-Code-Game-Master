---
slug: tts-speaker-daemon
title: gm-speak.sh listen — tail spool, dedup, resolve voice, say sequentially
category: enhancement
kind: afk
priority: p1
lane: manual
parentPrd: tts-narration
blockedBy: [tts-spool-writer, tts-voice-registry]
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

The live speaker: a long-running, user-launched process (second daemon after
`gm-view.sh watch`) that reads new spool segments and speaks them. Mirror `run_watch`'s
lifecycle shape.

- `run_listen(poll=0.2)` in `speak_manager.py`:
  - Poll `narration.jsonl` for lines past the **last-spoken seq** (high-water mark
    persisted to a small state file, e.g. `tts-state.json`, so a restart/crash resumes
    without re-speaking). Resolve the campaign dir each tick (handle none → idle/wait).
  - For each new segment, in order: `resolve_voice(speaker, dir)` → speak via a single
    seam `_speak(voice, text)` that shells out to `say -v <voice>`. **Sequential** (block
    until each utterance finishes) so voices never overlap; advance the high-water mark
    after each.
  - **Sentence-chunk** long segments (split on sentence boundaries) so audio starts fast
    and each sentence is an interruptible unit.
  - **Sanitize for speech** before `say`: strip markdown emphasis (`* _ #` `` ` ``), strip
    emoji, collapse whitespace, drop residual control chars. (Channel should be clean prose;
    this is defensive.)
  - Trap SIGINT/SIGTERM: kill any in-flight `say` child, exit quietly. `try/finally`.
- `listen` subcommand in `main()` + `tools/gm-speak.sh listen` → `exec $PYTHON_CMD ... listen`
  (exec so signals reach Python). **No `require_active_campaign`** — starts before a campaign
  exists, idles on the placeholder, picks up when one activates.

Keep `_speak` and `installed_voices` behind seams that tests patch — CI must never play audio.

## Acceptance criteria

- [ ] `gm-speak.sh listen` runs continuously and speaks each NEW spool segment exactly once,
      in seq order, each in its resolved voice.
- [ ] High-water mark persists: stopping and re-running `listen` does NOT re-speak old
      segments.
- [ ] Long segments are sentence-chunked; markdown/emoji/control chars are stripped before
      the `say` seam (asserted on the sanitized string, audio mocked).
- [ ] Ctrl+C / SIGTERM kills any in-flight utterance and exits cleanly (no orphaned `say`).
- [ ] Started with no active campaign → idles without error; activating a campaign begins
      playback without restart.
- [ ] pytest drives the loop with a patched `_speak`: asserts spoken order, dedup across a
      simulated restart, and sanitize/chunk behavior. (Live audio quality is manual.)

## Verification

Lane: manual

Interactive/audio: human runs `gm-speak.sh listen` in a second pane while playing — confirms
segments are spoken in order, voices are distinct, no overlap, Ctrl+C is clean, and ONLY prose
is read (no dice/menus/HUD leak). The signature/dedup/sanitize core is machine-verified.

## Blocked by

tts-spool-writer, tts-voice-registry

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-07T22:05:00Z  created → ready  [ship-it]
