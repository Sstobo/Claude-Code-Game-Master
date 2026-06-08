---
slug: tts-controls
title: gm-speak.sh stop (skip) + gm-session.sh tts on/off toggle
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: tts-narration
blockedBy: [tts-speaker-daemon]
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

Player control over the voice: barge-in/skip, and a global on/off toggle that the GM respects.

- **Skip / barge-in:** `gm-speak.sh stop` — interrupts the current utterance and moves on
  (or pauses playback). Implementation: the daemon writes its PID / a control file; `stop`
  kills the in-flight `say` child (the daemon then advances to the next segment). Define
  whether `stop` skips one segment or silences the queue until resumed — pick "skip current,
  keep going" for v1 and document it.
- **Toggle:** `gm-session.sh tts on|off|toggle` — persisted in session/campaign config (mirror
  the action-menu `choices on|off|toggle` pattern exactly). Surface the current TTS state in
  `gm-session.sh context` so the GM knows whether to enqueue.
- When TTS is **off**, the GM skips `gm-speak.sh narrate` calls (cheapest), and/or the daemon
  ignores new segments. Spec the precedence: off = GM does not enqueue; daemon also no-ops on
  segments arriving while off.

## Acceptance criteria

- [ ] `gm-speak.sh stop` interrupts the current utterance; the daemon continues with the next
      segment (no crash, no orphaned `say`).
- [ ] `gm-session.sh tts on|off|toggle` persists state and is idempotent (mirrors `choices`).
- [ ] TTS state appears in `gm-session.sh context` output.
- [ ] With TTS off, newly enqueued segments are not spoken; turning it back on resumes for
      subsequent segments.
- [ ] pytest: toggle persistence + readout in context; "off suppresses playback" via the
      patched `_speak` seam.

## Verification

Lane: agent

## Blocked by

tts-speaker-daemon

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-07T22:05:00Z  created → ready  [ship-it]
