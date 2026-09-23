# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Tron light-cycle game for 1–4 players (mix of humans + AI). Each player leaves a trail; collision with any trail or wall eliminates the player. Window is 1280×720.

## Controls (per player)

- **Player 1**: `LEFT` / `DOWN`
- **Player 2**: `Q` / `W`
- **Player 3**: `O` / `P`
- **Player 4**: `V` / `B`

Each player has two keys (left-turn / right-turn), not four directions. The `directions` dict maps direction id → `[dx150, dy150, dx2, dy2, scoutDx, scoutDy]`, which is used both for movement and for AI lookahead.

Menu controls: arrows to navigate, `RETURN` to confirm, `ESC` to back out / quit.

AI logic uses `aiturn_cdtime` / `aiturn_incd` to throttle turn decisions and `dire_cdtime` / `dire_incd` to throttle direction commits. See [../TronV2/](../TronV2/) for the revision with longer scout distance arrays and `maxDistanceDir` AI target tracking.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**Light cycles.** One continuous engine per session: two sawtooths detuned by 7 cents plus a third
at half frequency standing for the SWARM of living AIs, all through a resonant lowpass.

**The engine turns into sound a number the game ALREADY computes for the AI**: `clearDist`, how much
free space there is ahead. The less there is, the higher and the more open the filter. **Shaving past
a trail stops being purely visual.** And one swarm layer per living AI: measured, gain 0.012 with 3
cycles on the grid, 0 when one is left.

The engine **drops to 0, it never stops**: a stopped oscillator cannot be started again, and cutting
it dead clicks.

A round is a partial and the set is the real outcome: if the set is over, **only** `setEnd` plays.
Stacking the two turns the ending into a collision of two jingles and neither reads.

### The bug it had

`audioResume()` was **defined and never called**. No gesture hooked it, so the `AudioContext` was
never created and the game was mute no matter what: measured with the harness: zero contexts. And
since `buildEngine()` lives inside `audioResume`, the entire engine
(`buildEngine`/`engineUpdate`/`engineOff`) was dead code: none of the three was ever called. Also
missing were the per-frame ceiling reset, the three round/set call sites, the mute button handler and
`visibilitychange`.

> Pattern shared across the repo: WebAudio synthesis with no files, an `AudioContext` created
> inside `try/catch` on the first gesture, a per-frame voice ceiling **with its reset at the top of
> `loop()`**, a per-voice cooldown, a mute button persisted in `localStorage`, and
> `visibilitychange` so nothing continuous keeps playing with the tab in the background. If audio
> fails, the game keeps running. Verified with a headless harness that wraps the `AudioContext` and
> logs every node and every ramp. **The harness does not listen**: it checks that what was designed
> plays, when it was designed to, with which parameters. Judging it by ear is still pending.


## The fullscreen button sent you back to the menu (2026-09-23)

`resize()` ended in `backToMenu()`, with the comment "Resizing invalidates the track; we go back to
the menu (the old grid is no use)". That is true here and not in TronV2: V2's world is a fixed size
that the camera blits scaled, while **this one's occupancy grid is one cell per viewport pixel**
(`grid = new Uint8Array(W * H)`), so changing size leaves it matching nothing.

Tapping ⛶ changes the viewport, which fires `resize`, which dropped you into the menu mid-round.
TronV2 carries a comment saying that exact bug was fixed there; it never reached V1.

Removing the call is not enough: the grid would be the wrong size and collisions would stop working.
The track **moves house** instead:

- the grid, by walking the OLD one and marking the destination rectangle of every occupied cell.
  The source is walked, not the destination, on purpose: that way no wall is lost when shrinking
  (several old cells land on one new one) or when growing. Walking the destination and sampling the
  source drops walls, and a trail with holes is a trail you can drive through;
- the trail canvas, drawn scaled onto the new one. It has to be copied out first: assigning
  width/height clears a canvas;
- each bike's position, its last stamp and the bright points of its tail.

**Then each bike is dug out of its own trail.** Being generous with the grid thickens it by a pixel
or two, and a bike's head sits on the trail it just laid, so after the migration it woke up buried
in it and died instantly. Measured: the round ended the moment the size changed. It is standing
there, so that is not a wall.

In the menu (and on the first call) `backToMenu()` still runs, exactly as before.

Verified by measuring **synchronously across the event dispatch**, because `resize()` runs
synchronously and anything measured after an `await` cannot tell "the resize killed it" from "it
crashed by itself while we waited", which is what happened in two runs before the probe was fixed:

| | bikes alive | grid cells | menu |
| - | - | - | - |
| resize, no size change | 2 → 2 | 1425 → 1395 (the bikes dug out) | no |
| resize, 834x259 → 600x318 | 2 → 2 | 1395 → 1938 | no |
