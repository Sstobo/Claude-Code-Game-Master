---
slug: tts-agent-integration
title: CLAUDE.md spoken-channel note + launch/setup docs (voice download hint)
category: enhancement
kind: afk
priority: p2
lane: manual
parentPrd: tts-narration
blockedBy: [tts-speaker-daemon, tts-controls]
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

Teach the GM to author the spoken channel, and document how a player launches + sets it up.
Keep GM discipline minimal — like the canvas note.

- One optional block in lean `CLAUDE.md` near the Output Format canvas note:
  > **Optional spoken narration.** If the player is listening (`bash tools/gm-speak.sh listen`
  > in a second pane), author the beat's prose as tagged segments:
  > `printf '%s' '[{"speaker":"Narrator","text":"..."},{"speaker":"<NPC>","text":"..."}]' |
  > bash tools/gm-speak.sh narrate`. Tag dialogue with the NPC's name (gets their voice),
  > description with `Narrator`. NEVER enqueue dice/HUD/menus/box art — prose only.
  > Respect the `tts` toggle (scene context reports it); skip enqueuing when off. Optional —
  > if no one's listening, ignore it.
- Document launch + setup where players find it (README "Live Canvas" sibling section + `/help`):
  second terminal → `gm-speak.sh listen`; `gm-speak.sh voices` to see installed voices; a
  one-time hint to download 3-4 good voices (System Settings → Accessibility → Spoken Content →
  System Voice → Manage Voices) so the multi-voice casting has a real pool.
- Note the supersession: enemy/NPC voices are now spoken, building on the existing voice system.

## Acceptance criteria

- [ ] `CLAUDE.md` gains a concise spoken-channel note (segments via stdin, speaker tags,
      "prose only, never mechanics", respect the toggle) consistent with lean-core tone — no bloat.
- [ ] README + `/help` document launching `gm-speak.sh listen` in a second terminal and the
      `gm-speak.sh voices` discovery command.
- [ ] A one-time setup hint explains downloading additional macOS voices (path stated) so
      multi-voice casting works.
- [ ] All documented commands match the shipped wrapper (narrate/say/listen/voices/stop).

## Verification

Lane: manual

Doc/wording review — human confirms the note fits lean-core tone and the launch/setup steps are
accurate.

## Blocked by

tts-speaker-daemon, tts-controls

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-07T22:05:00Z  created → ready  [ship-it]
