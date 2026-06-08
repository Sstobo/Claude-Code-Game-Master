---
slug: tts-delivery-polish
title: Beat pauses between speakers + mood → rate/pitch delivery
category: enhancement
kind: afk
priority: p2
lane: manual
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

The performance layer — what turns a screen reader into an audio drama. Layers onto the
daemon's `_speak` without changing its loop.

- **Beat pauses:** when the speaker changes between consecutive segments
  (narrator→dialogue→narrator), insert a short silence using `say`'s inline command
  `[[slnc 350-450]]` (or a real inter-utterance sleep). Tunable constant.
- **Mood → delivery:** read the speaking NPC's mood (from `npcs.json` inner-life —
  `set-inner`/`mood`) and map it to `say` rate/pitch:
  - frightened/panicked → faster, higher
  - dying/weak/somber → slower, quieter
  - angry → faster, harder; calm/neutral → baseline.
  Build a small, documented `mood → {rate, pitch/volume}` table; unknown mood → baseline.
  Apply per-segment when resolving how to speak it.
- Keep it behind the same `_speak` seam / a `_delivery_for(speaker, dir)` helper so tests can
  assert the chosen parameters without playing audio.

## Acceptance criteria

- [ ] A speaker change between consecutive segments inserts the configured beat pause; same
      speaker back-to-back does not.
- [ ] An NPC's tracked mood maps to non-baseline rate/pitch per the table; unknown/absent
      mood → baseline (no crash).
- [ ] Delivery parameters are derived behind a testable seam (asserted without audio).
- [ ] No regression to the daemon's order/dedup/sanitize behavior.
- [ ] pytest: mood→params mapping (a few moods + unknown), and pause-on-speaker-change logic.

## Verification

Lane: manual

Param mapping is machine-verified; the actual *feel* (does the rhythm/mood land) is a human
ear check during play.

## Blocked by

tts-speaker-daemon

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-07T22:05:00Z  created → ready  [ship-it]
