# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Mouse-driven fireworks particle simulator. Each `Firework` rises and explodes after a random timer; `Explosion` spawns child `Explosion`s recursively (one generation, capped at 100 active explosions / 500 if forced via `Q`).

## Controls

- **LMB** — launch firework at cursor (rate-limited to one per 0.1s)
- **LMB + MMB** — launch 5 fireworks per click
- **RMB** — bypass cooldown (rapid-fire)
- **SPACE** — held while launching → higher launch (more negative `acel`)
- **Q** — detonate all in-flight fireworks immediately
- **W** — detonate one random in-flight firework (0.1s cooldown)
- **F** — toggle FPS / sprite-count overlay
- **P** — toggle pause flag (the flag exists but the main loop does **not** actually skip `process()` — pause is effectively a no-op in V1)
- **ESC** — quit

Window is 800×800. The 13-entry `colors` table holds `(rmin,rmax,gmin,gmax,bmin,bmax)` ranges used by `randColorInRange`. Sprites are z-sorted descending each frame so the cursor (`z=-2`) draws above explosions (`z=-1`) above fireworks (`z=0`).

See [FireworksV2/](../FireworksV2/) for the wider-window revision with a working pause overlay, and [../CLAUDE.md](../CLAUDE.md) for shared conventions.
