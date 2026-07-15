# CLAUDE.md

Guidance for working with the **Pac-Man** project.

## What this is

A **web-only** Pac-Man. There is **no `Pacman.py`** — unlike most folders in this repo, this game was authored directly as the web port. The only file is [PacmanWeb/index.html](PacmanWeb/index.html) (single self-contained HTML + CSS + JS, Canvas 2D, no build step, no libraries).

It reuses the **Tron V1 web UI shell** ([../Tron/TronWeb/index.html](../Tron/TronWeb/index.html)): a **bottom control bar** (`#bar`, translucent black + top border) holding circular buttons, with the canvas occupying the area *above* the bar (`resize()` sizes it to `W × (innerHeight − barH)`). It has its own Pac-Man visual identity: neon-blue baked maze with glow, `Press Start 2P` arcade font, classic four-ghost AI, WebAudio synth sound.

## Running

Open [PacmanWeb/index.html](PacmanWeb/index.html) in a browser, or launch it from the Arcade shell (registered in [../Arcade/index.html](../Arcade/index.html) `GAMES` as `Pacman/PacmanWeb/`, portrait, accent `#ffe300`). Thumbnail is `Arcade/thumbnails/Pacman.png`.

## Architecture notes (differs from the shared Pygame skeleton)

- **No `Sprite`/main-loop skeleton.** This is a state-machine game, not the repo's sprite-list pattern. `gh.state` ∈ `menu | ready | play | dying | flash | gameover | initials` drives both update and draw. `gh` also holds the meta state for the replayability systems below (`mode`, `skin`, `menuSel`, `bonusRound`/`bonusT`/`bonusFruits`, `deathsThisLevel`/`perfectStreak`, `levelTime`, `initials`/`initialSlot`/`pendingScore`).
- **Grid-edge movement.** Actors don't move in free pixels — they travel along grid edges: each actor holds `from`/`to` tiles and `t` ∈ 0→1. **All turn / AI decisions happen exactly at tile centers** (`t` wraps to 1), which is what makes "I overshot the junction" bugs impossible. `posA(actor)` converts edge-state to a fractional tile position; the ghost house states (`house`/`leaving`/`entering`) bypass the grid and use direct `sx`/`sy` instead.
- **Mazes are 28×31 ASCII grids in `MAZES[]`** (`MAP` = classic 244 pellets, `MAZE2` = honeycomb 292 pellets). `#` wall, `.` dot, `o` energizer, `-` house door, space = open/empty. `maze` is the active grid; `open()`/`bakeMaze()`/`resetLevel()` all read it. `mazeForLevel(L)` rotates every 4 levels. **Invariant for any new maze: rows 9–19 (the ghost house + tunnel + the col-6/col-21 vertical spines) MUST stay identical to `MAP`** — the house geometry, door (13–14 @ row 12), tunnel (`TUNNEL_ROW = 14`), and all spawns are hardcoded against it. Only the top (rows 1–8) and bottom (rows 20–29) quadrants may differ. Tunnel uses virtual columns `-1`/`28` that wrap on arrival. **Always validate a new maze with a flood-fill from the Pac start (13/14, 23)** before shipping (0 unreachable pellets); every row must be exactly 28 chars.
- **Maze rendering is baked once** in `bakeMaze()` into an offscreen canvas: per exposed wall-cell edge it strokes an inset contour line, extending the ends based on neighbor walls (straight / convex / concave) so corners close cleanly. `mazeFlashCv` is the white variant used for the level-clear flash. Pellets are baked separately into `pelletCv` and **erased per-tile** with `eatPelletAt()` as they're eaten (no per-frame pellet redraw).
- **Ghost AI is the original four-personality model.** Scatter/chase timeline in `gh.modeIdx`/`modeT` (per-level `modes` table); targets in `ghostTarget()`: Blinky (id 0) = Pac tile, Pinky (1) = 4 ahead, Inky (2) = vector reflected through Blinky, Clyde (3) = chase-when-far-else-corner. `elroy()` speeds Blinky up as dots run low. Frightened ghosts pick randomly; eaten ghosts become `eyes` and route back to the house door at (13,11).
- **Audio is fully synthesized** (`WebAudio`, no asset files): `tone()` builds every effect; a continuous `siren` oscillator + LFO changes character (`norm`/`fright`/`eyes`) via `updateSiren()`. `localStorage` keys: `pacmanMuted`, `pacmanScores` (top-5 table), `pacmanAch` (achievement ids), `pacmanSkin` (chosen skin), `pacmanHigh` (legacy single value, still written for migration).
- **Input is adaptive** like the other ports: pointer **swipe** (re-anchors on each fire so you can chain swipes without lifting) + arrows/WASD. `pac.desired` is the buffered next direction; it's only committed at a tile center (or instantly on a reverse).

## Replayability systems (all additive — none changes the base difficulty curve)

These were layered on top of the classic game without touching `lvlSpec(L)` (the base balance). The only difficulty hook is `spec()`, which returns `lvlSpec(gh.level)` adjusted *per mode*; everything that needs per-level numbers calls `spec()`, not `lvlSpec()` directly.

- **Modes (`gh.mode`, `MODE_NAMES`/`MODE_TAG`):** Clásico (base), Difícil (`spec()` bumps ghost speed +0.06 and cuts `fright` ×0.7), Maratón (starts at level 6), Diario (seeded). Chosen on the menu's selectable rows; the HUD shows the tag.
- **Daily seed:** all randomness goes through `ri()` → `rng`. `startGame()` sets `rng = mulberry32(todaySeed())` in Diario mode (reproducible run per calendar day), else `Math.random`.
- **Rotating mazes:** see `MAZES`/`mazeForLevel` above.
- **Skins (`SKINS`, `applySkin`):** pure color (`PAC_COL`/`WALL_COL`/`WALL_GLOW`/`DOT_COL` are `let`, reassigned by `applySkin`). Unlocked by all-time top score (`skinUnlocked`). Re-bake (`bakeMazeLayers`) picks up the new wall colors.
- **Top-5 score table + initials entry:** `scores[]` (`qualifies`/`insertScore`). On game over, `endGame()` routes to the `initials` state (3-slot ▲/▼ picker + keyboard A–Z) when the score qualifies, then `finalizeInitials()` saves and shows `drawGameOver()`'s table.
- **Achievements + toasts:** `ACH` ids, `unlockAch()` (idempotent, persists, pushes a `toast()`). Checked at existing event sites (`addScore`, `checkCollisions`, `eatAt` fruit, level-up).
- **Moving fruit:** the fruit is an edge-movement actor (`spawnFruit`/`updFruit`/`fruitDecide`/`fruitPos`) that enters from a tunnel mouth and wanders; spawns at 70/170 dots eaten. (Bonus rounds use static `gh.bonusFruits` instead.)
- **Bonus rounds (`isBonus`, every 5th level):** no ghosts, a `gh.bonusT` countdown, fruits scattered on random open tiles (`pickFruitSpots`); ends on timer. Handled by `updBonus()`.
- **Mastery + speed bonuses (`clearLevel`):** clearing all dots awards a speed bonus (faster = more, never negative) and, if `gh.deathsThisLevel === 0`, an escalating perfect-level bonus (`gh.perfectStreak`). Eating all 4 ghosts on one energizer (`gh.combo` reaches 4 in `checkCollisions`) gives a flat +2000.

## Conventions kept from the repo

- **Spanish UI strings, English identifiers** (`¡LISTO!`, `PUNTOS`, `RECORD`, `NIVEL`).
- **Resolution independence:** all geometry is in tile units; `resize()` recomputes tile size `ts` + maze origin `ox`/`oy` and re-bakes the maze/pellets. No hardcoded pixel layout.
- **Arcade shell wiring** follows Tron V1 — a thin bottom `#bar` (`--bar-height: 66px`) in centered order `✕ salir · ⟳ · 🔊 · ⛶ · ⓘ`, `data-orient="portrait"`, FPS overlay toggled by `ⓘ`. **There are no on-screen movement buttons** (Tron's `◄ ►` turn pair is gone): movement is keyboard (arrows/WASD) on desktop and **swipe on the canvas** on mobile. The bar holds only utility buttons; the **sound toggle** (`#btnSound`) and **reset** (`#btnReset`) are what this game adds over the base Tron set (`✕ ⛶ ⓘ`).
