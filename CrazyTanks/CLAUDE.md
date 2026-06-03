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
