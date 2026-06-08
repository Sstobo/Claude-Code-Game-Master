---
slug: tts-narration
title: TTS narration — spoken, multi-voice audio drama for the prose (not the mechanics)
status: active
version: 1
supersedes: null
createdAt: 2026-06-07T22:00:00Z
updatedAt: 2026-06-07T22:00:00Z
---

## Problem Statement

The game is text. A player who wants to *listen* — eyes off the screen, or just for
immersion — has no good option. Naive text-to-speech on the assistant message is
unlistenable: it reads HP bars, `🎲 Attack: 17+5=22`, the `1. 2. 3.` action menu,
ASCII scene/combat/loot boxes, status labels, and tool output as if they were prose.
The mechanical layer drowns the story.

## Solution

A spoken channel the **GM authors directly** — the same architecture as the canvas.
Because the GM is writing both the narration and the mechanics, it already knows which
sentences are story; it tags the prose into a dedicated stream rather than us trying to
reverse-engineer it out of rendered markdown.

- The GM enqueues each beat's prose as ordered **segments**, tagged by speaker
  (`Narrator` or an NPC name), via `gm-speak.sh`.
- A user-launched **speaker daemon** (`gm-speak.sh listen`, run in a second pane like
  `gm-view.sh watch`) tails the spool and speaks each new segment with macOS `say`,
  sequentially, in a **distinct voice per speaker** — a radio drama, not a screen reader.
- Free, offline, zero new deps (macOS `say`). Voices are cast once per NPC and
  remembered, so each character sounds consistent forever.

## User Stories

1. As a player, I want the narration and dialogue read aloud — but NOT the dice, HUD,
   menus, or ASCII art — so I can play with my eyes off the screen and stay immersed.
2. As a player, I want each NPC to have a consistent, fitting voice, so the world feels
   like a cast of characters instead of one monotone reader.
3. As a player, I want to skip a long read or toggle voice off entirely, so the audio
   never traps me.
4. As the GM (agent), I want to push spoken prose with one tagged call per beat, so the
   separation is definitive and costs me almost no extra effort.

## Implementation Decisions

### Engine & philosophy
- **macOS `say`** (platform is darwin). Free, offline, instant, zero new Python deps —
  matches the canvas's "stdlib only, no watchdog" stance. ElevenLabs/OpenAI are an
  explicit non-goal for v1 (see Out of Scope), but the voice-resolution seam is built so
  a premium backend could slot in later.

### Capture (GM-authored spoken channel)
- **New:** `lib/speak_manager.py` and `tools/gm-speak.sh` (wrapper mirroring
  `gm-view.sh`).
- `gm-speak.sh narrate` reads a JSON array of segments from **stdin** (multi-line safe,
  same reason the canvas reads the scene body from stdin):
  `[{"speaker":"Narrator","text":"..."},{"speaker":"Princess Donut","text":"..."}]`.
  A `gm-speak.sh say --speaker <who> "<text>"` convenience exists for single lines.
- Appended to a **spool**: `world-state/campaigns/<active>/narration.jsonl`, one JSON
  object per line: `{seq, speaker, text, ts}`. `seq` is monotonic. Append is atomic
  (write-temp+rename of the whole file, or O_APPEND single-write line — chosen for
  crash-coherence). Already gitignored under `world-state/campaigns/*`.
- Writes are guarded by `require_active_campaign` (use `EntityManager` for the write
  path); the daemon's read path resolves the dir directly via `CampaignManager` (never
  `EntityManager`, which raises with no campaign) — exactly the canvas split.

### Playback (speaker daemon)
- `gm-speak.sh listen` → `speak_manager.py listen`, a long-running user-launched process
  (second daemon in the repo after `gm-view.sh watch`; reuse its lifecycle shape).
- Loop: poll the spool (~0.2s) for new lines past the **last-spoken seq** (high-water
  mark persisted so a restart/crash resumes without re-reading — the watcher dedup idea).
- For each new segment: resolve voice → run `say -v <voice> [pace/pauses] <text>`,
  **sequentially** (so voices never overlap), then advance the high-water mark.
- **Sentence-chunk** long segments so audio starts fast and each sentence is a skippable
  unit.
- **Sanitize** before speaking (defensive — the channel should already be clean prose):
  strip markdown emphasis (`*_#`), strip emoji, collapse whitespace. Never speak control
  chars.
- Clean exit: alt-screen not needed (no full-screen draw), but trap SIGINT/SIGTERM to
  kill any in-flight `say` child and exit quietly.

### Voice registry (the radio-drama core)
- **Narrator voice:** stored in campaign config (`campaign-overview.json` or a small
  `tts.json`), defaulting to a sensible installed voice; ideally seeded at `/new-game`
  voice time to match the world's NARRATIVE VOICE (noir vs heroic gets a different reader).
- **Per-NPC voice:** an optional `tts_voice` field on the npc record (`npcs.json`).
- **Auto-assign-and-remember:** if a tagged speaker has no `tts_voice`, the daemon picks
  one deterministically from the *installed* voice pool and persists it back — so a
  character's voice is stable across sessions with zero manual casting.
- **Availability is per-machine.** Installed voices vary (Premium voices need a manual
  download). So: `gm-speak.sh voices` lists what's actually installed; resolution falls
  back (assigned voice missing → narrator voice → system default); a one-time setup hint
  points the player to download 3-4 good voices.

### Delivery polish (what makes it perform, not just read)
- **Beat pauses:** insert a short silence (`[[slnc 350-450]]`) between speaker changes
  (narrator→dialogue→narrator) for audio-drama rhythm.
- **Mood → delivery:** map the NPC mood you already track to `say` rate/pitch (frightened
  = faster/higher, dying = slower/quieter). Reuses the existing inner-life system. Can be
  a v1 flag or deferred if it risks scope — included as a small, high-leverage touch.

### Controls
- `gm-speak.sh stop` — kill the current utterance / skip ahead (barge-in).
- `gm-session.sh tts on|off|toggle` — persisted like the action-menu toggle; surfaced in
  scene context so the GM knows whether to enqueue. When off, the GM skips `narrate`
  calls (or the daemon ignores) — no wasted work.

### Agent integration
- One optional block in lean `CLAUDE.md` (near the canvas note in Output Format): when a
  listener is running, author the beat's prose via `gm-speak.sh narrate` with segments
  tagged by speaker; never enqueue dice/menus/HUD; persist-before-narrate still holds.
- `npc-builder` casts a fitting `tts_voice` at NPC creation (gruff brute, silky vizier).
- Launch + setup docs (README "Live Canvas" sibling, `/help`).

## Testing Decisions

- **agent lane (pytest, DCC fixture):**
  - writer round-trip — `narrate` appends well-formed `{seq, speaker, text, ts}` lines,
    seq is monotonic, multi-segment order preserved, atomic (no temp left).
  - voice resolution — assigned `tts_voice` wins; unassigned auto-assigns deterministically
    and persists; missing-voice falls back to narrator/default; `voices` lists installed.
  - daemon dedup — high-water mark advances; a re-`listen` does not re-speak old lines
    (drive `say` through a mockable seam, e.g. a `_speak(voice, text)` function patched in
    tests so no audio actually plays in CI).
  - sanitize — markdown/emoji/control chars stripped before the `say` seam.
  - toggle — off suppresses enqueue/playback.
- **manual lane (human ear):** the actual audio — voice quality, that NPCs sound distinct
  and fitting, beat-pause rhythm, mood delivery, skip/stop responsiveness, and that the
  spoken stream contains *only* prose (no dice/menus/HUD leaked). Cannot be asserted in code.
- Prior art: the canvas tickets (`speak_manager` mirrors `view_manager`'s write/read split,
  daemon mirrors `run_watch`, wrapper mirrors `gm-view.sh`, tests mirror `test_view_manager`).

## Out of Scope

- Non-macOS engines and cloud TTS (ElevenLabs / OpenAI / local neural) — the resolution
  seam allows them later, but v1 is `say` only.
- Speech-to-text / voice *input* from the player (this is output only).
- Background music / ambience / sound beds (a natural future feature, not this).
- Reading mechanical text aloud in any form (dice, HUD, menus) — explicitly never.
- Auto-launching the daemon via a hook or settings.json — user-launched process, like the
  canvas.

## Further Notes

- No new Python deps (stdlib + macOS `say` only). No `.claude/settings.json` change.
- Reuse, do not reinvent: `tools/common.sh`, `EntityManager`, `JsonOperations`,
  `CampaignManager`, the canvas daemon lifecycle, the NPC inner-life/voice system.
- The spool is append-only and gitignored; it can be truncated/rotated on session end if
  it grows (minor housekeeping, not v1-critical).
- Cross-feature synergy (optional, later): the canvas could surface "▸ now speaking: <name>"
  while a segment plays.
