# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Pong with a menu system, configurable win-points (5/10/20/40/practice), and an optional "fire mode" where rallies above a streak threshold ignite the ball and paddles. 1280×720 window. Spanish identifiers (`pelota`, `apretado`, `puntos_victoria`, `crear_pelota`, `crear_texto`, `gamestates = ['menu','juego','pausa']`, `opcion_menu`).

Diverges from the repo skeleton: no `Sprite` base class, no `xper`/`yper` helpers, no `deltaT`. State is a `gamestate` string switched between `'menu'`, `'juego'`, and `'pausa'`. Ball physics use a 5-element list `[x, y, radius, vx, vy]` rather than an object.

`fire_mode`, `j1onfire`, `j2onfire`, `firenet` are top-level globals — gameplay reads/writes them directly rather than through a manager.

See [../CLAUDE.md](../CLAUDE.md) for the shared conventions this file does not follow.
