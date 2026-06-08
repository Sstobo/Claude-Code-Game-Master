---
slug: tts-voice-registry
title: Voice resolution — narrator config + per-NPC tts_voice + auto-assign + gm-speak.sh voices
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

The radio-drama core: map a speaker name → a concrete macOS `say` voice, consistently and
defensively. Pure resolution logic (no audio) so it's fully unit-testable; the daemon ticket
consumes it.

- In `lib/speak_manager.py` (module-level fns; the daemon read path resolves the campaign dir
  directly via `CampaignManager`, NOT `EntityManager`):
  - `installed_voices()` → parse `say -v '?'` into `[{name, locale}]`. Empty list if `say`
    is absent (degrade, never crash).
  - `narrator_voice(campaign_dir)` → read from campaign config (`tts.json` or
    `campaign-overview.json` `tts.narrator`), defaulting to a sensible installed voice
    (first installed en-* voice, else system default).
  - `resolve_voice(speaker, campaign_dir)`:
    - `Narrator` (or empty/unknown) → narrator voice.
    - NPC name → that npc's `tts_voice` from `npcs.json` if set and still installed.
    - **Auto-assign-and-remember:** if the NPC has no `tts_voice` (or it's no longer
      installed), pick one **deterministically** from the installed pool (stable hash of the
      name → index, excluding the narrator voice when possible) and **persist** it back to
      `npcs.json` so the character sounds the same next time.
    - Fallback chain when the pool is empty/unknown: assigned → narrator → system default.
- `gm-speak.sh voices` subcommand → list installed voices (and which are currently assigned
  to the narrator / NPCs). NO `require_active_campaign` for the bare list; assignment readout
  needs a campaign.

## Acceptance criteria

- [ ] `installed_voices()` parses `say -v '?'` to name/locale; returns `[]` (no crash) if
      `say` is unavailable.
- [ ] `resolve_voice("Narrator", dir)` returns the configured/default narrator voice.
- [ ] An NPC with a set, installed `tts_voice` resolves to exactly that voice.
- [ ] An NPC with no `tts_voice` auto-assigns deterministically (same name → same voice on
      repeat) AND the choice is persisted to `npcs.json`.
- [ ] An NPC whose stored `tts_voice` is no longer installed falls back (re-assign or
      narrator), never returns an uninstalled voice.
- [ ] `gm-speak.sh voices` lists installed voices; readout works with `say` present.
- [ ] pytest (stub `installed_voices`/`say` so no audio): narrator default, explicit win,
      deterministic auto-assign + persistence, missing-voice fallback, empty-pool fallback.

## Verification

Lane: agent

## Blocked by

None.

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-07T22:05:00Z  created → ready  [ship-it]
