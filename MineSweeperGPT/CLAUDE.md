# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Classic Minesweeper. 13×13 grid, 40 mines, 40-pixel tiles → 520×520 window. **LMB** reveals, **RMB** flags/unflags, **R** resets, **ESC** quits. Mines are placed *after* the first click (the clicked tile and its 8 neighbors form a guaranteed safe zone — see `GameManager.place_mines`).

Two divergences from textbook Minesweeper worth knowing:

- **Mine clusters.** Each placement attempt has a 20% chance of expanding into a 3–5 tile contiguous cluster via `generate_mine_cluster`'s BFS-style frontier walk, instead of placing a single mine.
- **No timer / counter / smiley.** UI is just the grid and a centered Game Over / You Win banner.

Departs slightly from the repo-wide convention: uses `screen` instead of `windowSurface`, fixed-timestep `clock.tick(60)`, no `xper`/`yper` helpers, event-driven mouse handling via `MOUSEBUTTONDOWN` rather than polled `mouse.get_pressed()`. The `GameManager` is named `manager` (singular) — `Tile.draw` reads `manager.game_over` directly as a module global.

See [../CLAUDE.md](../CLAUDE.md) for shared conventions (most of which this file ignores).


## AUDIO — correccion (2026-09-22)

`audioOn()` creaba el `AudioContext` **sin `try/catch`** y es la primera sentencia de los cinco
handlers de `pointerdown` del juego. Sin esa guarda, un contexto que no se puede crear no dejaba el
juego mudo: dejaba el tablero **sin responder a un solo toque**.

Pendiente: `sndBoom` suma 0.95 de amplitud de pico directo al destino (no hay `masterGain`), unas
8 veces por encima de la mezcla del propio juego.
