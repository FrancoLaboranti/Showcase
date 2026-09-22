# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Top-down 4-tank racing game with menu, tournament mode, 10 tracks, 3 race lengths (10/20/40 laps), 4 AI difficulties, and a ramming/bomb combat layer. ~1087 lines — read with `offset`/`limit` rather than in one shot.

## Controls

- **Player 1** — Arrows + `SPACE` (shoot)
- **Player 2** — `WASD` + `LCTRL` (shoot, two-player mode only)
- **Menus** — Arrows to navigate, `RETURN` to confirm, `ESC` to back out / quit
- **In-race debug** — `F1` toggles tank hitboxes, `F2` toggles trackpoint markers

## Architecture notes

- Sprite classes: `Tank`, `Bomb`, `Wall`, `TrackPoint`, `MainHandler` (menus + state), `AuxiliaryHandler` (in-race state — countdown, pause, tournament scoring). Parallel lists `tanks`, `bombs`, `walls`, `trackpoints` mirror subsets of `sprites`.
- **Track data is huge inline literals.** Wall rectangles live in `Wall.__init__`'s `maps` tuple; centerline waypoints live in `TrackPoint.__init__`'s `maps` list, populated by per-track loops (`PARK`, `HALLWAYS`, `MESSY`, `PORTAL`, `ZIGZAG`, `SMILEY`, `TWAINPORTALS`, `SNAIL`, `COMBINED`, `BOXES`). Per-track `(nWalls, nTrackpoints)` counts are also hard-coded in `MainHandler.process` and `AuxiliaryHandler.process` — edit both when adding/removing geometry.
- **Resolution-dependent physics.** `Tank.process` scales velocity/angular velocity differently based on `SCREEN_X` thresholds (`>=1400`, `>=1000`, `>=500`). Don't simplify without testing across window sizes.
- **AI lap-following.** `Tank.process` finds the nearest trackpoint, then aims at the point 8 ahead (`(closest.id+8) % len(trackpoints)`). Lap counting uses `lap_checkpoint` (0→1 near start, 1→2 near end, →0 crossing finish).

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**Steel plate and track links over a floor that changes.** These are not cars: they are metal boxes
driven by chain, and that calls for TWO continuous layers, not one. A car has a single voice; a tank
has the engine and has what the engine drags.

### The track changes material with the biome

`THEME_HANDLING` gives each biome a different lateral grip (0.01 on snow, 0.40 on desert), and that
number ALREADY exists and already decides how the tank handles. The track uses it to change
material. Measured:

| biome | grip | track gain | filter |
|---|---|---|---|
| desert | 0.40 | 0.032 | 1920 Hz — hard, grainy |
| snow | 0.01 | 0.010 | 520 Hz — dull, muffled |

**You hear the floor before you see it slide.**

The engine runs 34 to 80 Hz with speed; the diesel pulse comes out of the beating between two
near-identical sawtooths. Nitro is a **third tap of the SAME noise buffer** as the track, not a new
source: a `BufferSource` is single-use, but its outputs can branch as many times as needed.

The three continuous layers are **one single graph per session**: they are modulated, not recreated.
They are rewritten at 20 Hz — writing six `AudioParam`s per frame adds nothing audible.

Discrete: the shot is a **mortar COUGH, not a laser** (this thing lobs bombs out of a short barrel),
the impact is the plate first and the hull cavity after, and the countdown fires on an EDGE — `seg`
is recomputed every frame and without the edge it would be a continuous buzz.

Only the PLAYER's laps play: seven tanks crossing the line would be seven meaningless chimes.

> Pattern shared across the repo: WebAudio synthesis with no files, an `AudioContext` created
> inside `try/catch` on the first gesture, a per-frame voice ceiling **with its reset at the top of
> `loop()`**, a per-voice cooldown, a mute button persisted in `localStorage`, and
> `visibilitychange` so nothing continuous keeps playing with the tab in the background. If audio
> fails, the game keeps running. Verified with a headless harness that wraps the `AudioContext` and
> logs every node and every ramp. **The harness does not listen**: it checks that what was designed
> plays, when it was designed to, with which parameters. Judging it by ear is still pending.
