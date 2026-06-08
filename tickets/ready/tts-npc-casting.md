---
slug: tts-npc-casting
title: npc-builder casts a fitting tts_voice at NPC creation + npcs.json schema
category: enhancement
kind: afk
priority: p2
lane: agent
parentPrd: tts-narration
blockedBy: [tts-voice-registry]
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

Character baked in from birth: instead of the daemon's deterministic auto-assign, let the
`npc-builder` agent (which already invents personality) cast a *fitting* macOS voice when it
creates/enriches an NPC (gruff brute, silky vizier, reedy goblin).

- `npcs.json` schema: document the optional `tts_voice` field (a macOS `say` voice name) on the
  NPC record. Update `docs/schema-reference.md`.
- `npc-builder` agent instructions: when creating/enriching an NPC, choose a `tts_voice` that
  fits the NPC's personality/voice from the **installed** pool (use `gm-speak.sh voices`), and
  persist it via the existing NPC write path (`gm-npc.sh`). If no good fit / `say` unavailable,
  leave it unset — the daemon's auto-assign (tts-voice-registry) is the safety net.
- This is additive: nothing breaks if `tts_voice` is absent.

## Acceptance criteria

- [ ] `docs/schema-reference.md` documents the optional `tts_voice` field on the NPC record.
- [ ] `npc-builder` instructions direct it to cast a fitting installed voice and persist it via
      `gm-npc.sh`, with an explicit "leave unset if no fit / say unavailable" fallback.
- [ ] A persisted `tts_voice` is honored by `resolve_voice` (already true from tts-voice-registry)
      — add/confirm a test that an npc-builder-style assignment round-trips and resolves.
- [ ] Absent `tts_voice` still works (daemon auto-assigns) — no regression.

## Verification

Lane: agent

Agent-instruction wording is a doc/judgement check; the schema + resolution round-trip is
machine-verified.

## Blocked by

tts-voice-registry

---

## QA Reports

<!-- newest first -->

## History

- 2026-06-07T22:05:00Z  created → ready  [ship-it]
