# CLAUDE.md

Guidance for working with the **Pac-Man** project.

## What this is

A **web-only** Pac-Man. There is **no `Pacman.py`** — unlike most folders in this repo, this game was authored directly as the web port. The only file is [PacmanWeb/index.html](PacmanWeb/index.html) (single self-contained HTML + CSS + JS, Canvas 2D, no build step, no libraries).

It reuses the **Tron V1 web UI shell** ([../Tron/TronWeb/index.html](../Tron/TronWeb/index.html)): a **bottom control bar** (`#bar`, translucent black + top border) holding circular buttons, with the canvas occupying the area *above* the bar (`resize()` sizes it to `W × (innerHeight − barH)`). It has its own Pac-Man visual identity: neon-blue baked maze with glow, `Press Start 2P` arcade font, classic four-ghost AI, WebAudio synth sound.

## Running

Open [PacmanWeb/index.html](PacmanWeb/index.html) in a browser, or launch it from the Arcade shell (registered in [../Arcade/index.html](../Arcade/index.html) `GAMES` as `Pacman/PacmanWeb/`, portrait, accent `#ffe300`). Thumbnail is `Arcade/thumbnails/Pacman.png`.

## Architecture notes (differs from the shared Pygame skeleton)

- **No `Sprite`/main-loop skeleton.** This is a state-machine game, not the repo's sprite-list pattern. `gh.state` ∈ `menu | ready | play | dying | flash | gameover` drives both update and draw.
- **Grid-edge movement.** Actors don't move in free pixels — they travel along grid edges: each actor holds `from`/`to` tiles and `t` ∈ 0→1. **All turn / AI decisions happen exactly at tile centers** (`t` wraps to 1), which is what makes "I overshot the junction" bugs impossible. `posA(actor)` converts edge-state to a fractional tile position; the ghost house states (`house`/`leaving`/`entering`) bypass the grid and use direct `sx`/`sy` instead.
- **The maze is the classic 28×31 ASCII `MAP`.** `#` wall, `.` dot, `o` energizer, `-` house door, space = open/empty. Validated: 244 pellets (240 + 4), fully connected, tunnel on row `TUNNEL_ROW = 14`. The tunnel uses virtual columns `-1` / `28` that wrap on arrival. If you edit `MAP`, keep every row exactly 28 chars and re-check connectivity from the Pac start (13/14, 23).
- **Maze rendering is baked once** in `bakeMaze()` into an offscreen canvas: per exposed wall-cell edge it strokes an inset contour line, extending the ends based on neighbor walls (straight / convex / concave) so corners close cleanly. `mazeFlashCv` is the white variant used for the level-clear flash. Pellets are baked separately into `pelletCv` and **erased per-tile** with `eatPelletAt()` as they're eaten (no per-frame pellet redraw).
- **Ghost AI is the original four-personality model.** Scatter/chase timeline in `gh.modeIdx`/`modeT` (per-level `modes` table); targets in `ghostTarget()`: Blinky (id 0) = Pac tile, Pinky (1) = 4 ahead, Inky (2) = vector reflected through Blinky, Clyde (3) = chase-when-far-else-corner. `elroy()` speeds Blinky up as dots run low. Frightened ghosts pick randomly; eaten ghosts become `eyes` and route back to the house door at (13,11).
- **Audio is fully synthesized** (`WebAudio`, no asset files): `tone()` builds every effect; a continuous `siren` oscillator + LFO changes character (`norm`/`fright`/`eyes`) via `updateSiren()`. Muted state persists in `localStorage` (`pacmanMuted`); high score in `pacmanHigh`.
- **Input is adaptive** like the other ports: pointer **swipe** (re-anchors on each fire so you can chain swipes without lifting) + arrows/WASD. `pac.desired` is the buffered next direction; it's only committed at a tile center (or instantly on a reverse).

## Conventions kept from the repo

- **Spanish UI strings, English identifiers** (`¡LISTO!`, `PUNTOS`, `RECORD`, `NIVEL`).
- **Resolution independence:** all geometry is in tile units; `resize()` recomputes tile size `ts` + maze origin `ox`/`oy` and re-bakes the maze/pellets. No hardcoded pixel layout.
- **Arcade shell wiring** follows Tron V1 — a thin bottom `#bar` (`--bar-height: 66px`) in centered order `✕ salir · ⟳ · 🔊 · ⛶ · ⓘ`, `data-orient="portrait"`, FPS overlay toggled by `ⓘ`. **There are no on-screen movement buttons** (Tron's `◄ ►` turn pair is gone): movement is keyboard (arrows/WASD) on desktop and **swipe on the canvas** on mobile. The bar holds only utility buttons; the **sound toggle** (`#btnSound`) and **reset** (`#btnReset`) are what this game adds over the base Tron set (`✕ ⛶ ⓘ`).
