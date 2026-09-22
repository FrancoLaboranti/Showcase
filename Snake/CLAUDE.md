# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A non-grid Snake: the head smoothly chases the mouse cursor, each body segment chases the segment in front of it. Window is 1280×720, toggleable to fullscreen at runtime (the main loop recreates `windowSurface` with `pygame.FULLSCREEN` when `self.fullScreen` flips).

**LMB held** = sprint (head speed ×1.5). Each `SnakePiece` adjusts its `vel` and `angVel` based on distance to its target, so the body undulates naturally around tight turns. New segments inherit position and angle from the previous-tail segment.

Body coloring alternates: every 4th segment uses a brighter green range (`randColorInRange(10,40,225,255,10,40)`), the rest use a darker green. Per-segment `wave_time`/`wave_time_total` drives a sine-wave breathing animation.

The `manager` global is a single-element list `[Manager()]` — index it as `manager[0]` (see `SnakePiece.process` reading `manager[0].gameOver` and `manager[0].pause`). This is unusual for the repo; don't replace it with a plain object without updating every read site.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**The world's material is WATER**, and water has no dry transients: **no sound in this game may
start with a click**. Every voice carries a 4 to 8 ms attack. A hard `setValueAtTime` on the gain
produces an audible switching click, and a click is precisely what water does not do.

Two families and no more:

- **HYDRAULIC** — body and weight: sines and triangles from 40 to 250 Hz with lowpassed noise for
  the displaced water. Bites, charges, hits, mines, bosses.
- **BIOLUMINESCENT** — everything that glows: pure sines from 500 to 1800 Hz, very short, with a
  harmonic at the fifth. Eating, levelling up, picking a card.

### The master lowpass is an instrument

Everything goes through a lowpass at 2600 Hz: you are underwater, no treble arrives intact. And the
filter moves. Measured: **2600 Hz (normal water) → 1500 (inside the jellyfish shield) → 2600 → 300
(sinking) → 2600 (reset)**. No new sound is needed to say "something changed": the WATER changes.

Other decisions:

- **Eating is the game's most frequent sound**, so it lasts 85 ms and lives at 0.045. The pitch rises
  with the star's rarity: an orange one sounds better than a yellow one without looking at it.
- **The mine has its OWN timbre**, not the bite's: muffled metal. It is the only metallic thing on
  the reef and that is why it is recognisable without seeing it.
- **Hitting a boss gives TWO timbres** depending on whether the armour absorbed it: a dry, matte
  knock if it did not land, a bell if it did. It is the only way to know whether the vulnerable
  window was open without memorising each boss's phase.
- **The lake edge is not a knock, it is pressure**: a continuous hiss while you are outside.
- The end of the shield, the poison and the turbo recharge fire **on an EDGE**, compared against the
  previous frame's value. Without the edge they would be one voice per frame, which is exactly what
  the cooldown cannot cover.

> Pattern shared across the repo: WebAudio synthesis with no files, an `AudioContext` created
> inside `try/catch` on the first gesture, a per-frame voice ceiling **with its reset at the top of
> `loop()`**, a per-voice cooldown, a mute button persisted in `localStorage`, and
> `visibilitychange` so nothing continuous keeps playing with the tab in the background. If audio
> fails, the game keeps running. Verified with a headless harness that wraps the `AudioContext` and
> logs every node and every ramp. **The harness does not listen**: it checks that what was designed
> plays, when it was designed to, with which parameters. Judging it by ear is still pending.
