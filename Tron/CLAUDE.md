# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Tron light-cycle game for 1–4 players (mix of humans + AI). Each player leaves a trail; collision with any trail or wall eliminates the player. Window is 1280×720.

## Controls (per player)

- **Player 1** — `LEFT` / `DOWN`
- **Player 2** — `Q` / `W`
- **Player 3** — `O` / `P`
- **Player 4** — `V` / `B`

Each player has two keys (left-turn / right-turn), not four directions. The `directions` dict maps direction id → `[dx150, dy150, dx2, dy2, scoutDx, scoutDy]`, which is used both for movement and for AI lookahead.

Menu controls: arrows to navigate, `RETURN` to confirm, `ESC` to back out / quit.

AI logic uses `aiturn_cdtime` / `aiturn_incd` to throttle turn decisions and `dire_cdtime` / `dire_incd` to throttle direction commits. See [../TronV2/](../TronV2/) for the revision with longer scout distance arrays and `maxDistanceDir` AI target tracking.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**Light cycles.** One continuous engine per session — two sawtooths detuned by 7 cents plus a third
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
never created and the game was mute no matter what — measured with the harness: zero contexts. And
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
