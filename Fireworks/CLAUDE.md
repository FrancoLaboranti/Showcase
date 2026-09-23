# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Mouse-driven fireworks particle simulator. Each `Firework` rises and explodes after a random timer; `Explosion` spawns child `Explosion`s recursively (one generation, capped at 100 active explosions / 500 if forced via `Q`).

## Controls

- **LMB**: launch firework at cursor (rate-limited to one per 0.1s)
- **LMB + MMB**: launch 5 fireworks per click
- **RMB**: bypass cooldown (rapid-fire)
- **SPACE**: held while launching → higher launch (more negative `acel`)
- **Q**: detonate all in-flight fireworks immediately
- **W**: detonate one random in-flight firework (0.1s cooldown)
- **F**: toggle FPS / sprite-count overlay
- **P**, toggle pause flag (the flag exists but the main loop does **not** actually skip `process()`, pause is effectively a no-op in V1)
- **ESC**: quit

Window is 800×800. The 13-entry `colors` table holds `(rmin,rmax,gmin,gmax,bmin,bmax)` ranges used by `randColorInRange`. Sprites are z-sorted descending each frame so the cursor (`z=-2`) draws above explosions (`z=-1`) above fireworks (`z=0`).

See [FireworksV2/](../FireworksV2/) for the wider-window revision with a working pause overlay, and [../CLAUDE.md](../CLAUDE.md) for shared conventions.


## AUDIO: fixes (2026-09-22)

1. `audioResume()` created the `AudioContext` **without `try/catch`**. If the constructor threw, the
   exception took out the handler that called it and the game was left **unplayable**: no rockets
   launched and no button responded.
2. **There was no `visibilitychange`.** `background.mp3` is a `BufferSource` with `loop = true`, the
   game's only continuous node, and it kept playing with the tab hidden or the phone in another
   app, exactly when the player no longer has the mute button at hand.

The four samples (launch, sparks, explosion, background) stay: they are real recordings and they
sound better than any oscillator.
