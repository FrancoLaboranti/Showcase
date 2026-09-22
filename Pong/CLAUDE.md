# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Pong with a menu system, configurable win-points (5/10/20/40/practice), and an optional "fire mode" where rallies above a streak threshold ignite the ball and paddles. 1280×720 window. Spanish identifiers (`pelota`, `apretado`, `puntos_victoria`, `crear_pelota`, `crear_texto`, `gamestates = ['menu','juego','pausa']`, `opcion_menu`).

Diverges from the repo skeleton: no `Sprite` base class, no `xper`/`yper` helpers, no `deltaT`. State is a `gamestate` string switched between `'menu'`, `'juego'`, and `'pausa'`. Ball physics use a 5-element list `[x, y, radius, vx, vy]` rather than an object.

`fire_mode`, `j1onfire`, `j2onfire`, `firenet` are top-level globals — gameplay reads/writes them directly rather than through a manager.

See [../CLAUDE.md](../CLAUDE.md) for the shared conventions this file does not follow.


## AUDIO (2026-09-22)

**Charged light and glass.** The background is a near-black radial gradient with a blue grid,
everything is drawn with `shadowBlur` and the particles run in `lighter`: there is not one matte
surface on screen. So no impact is a knock — it is a DISCHARGE, a glassy transient with a TUNED
resonant tail.

**The rally ladder.** The pitch of the return rises with `rallyHits`: measured, 293 Hz on step 0 and
1186 Hz on step 8. You hear a long rally tighten. Ball speed scales the gain separately (0.048 slow
vs 0.075 fast), so pitch = how long they have been at it, gain = how hard it is coming.

**The court on fire changes the timbre, not the volume**: the same hit goes from `triangle` to
`sawtooth`. Same gesture, different consequence.

### The bug it had

`sndThisFrame++` was in three places and **`sndThisFrame = 0` in none**. It is exactly the trap the
pattern documents: the counter only goes up, `ac()` cuts off at 10, and the game goes mute FOREVER
after ten sounds without throwing a single error. Measured with the harness before the fix: the
counter ended at 13 and subsequent hits did not play.

> Pattern shared across the repo: WebAudio synthesis with no files, an `AudioContext` created
> inside `try/catch` on the first gesture, a per-frame voice ceiling **with its reset at the top of
> `loop()`**, a per-voice cooldown, a mute button persisted in `localStorage`, and
> `visibilitychange` so nothing continuous keeps playing with the tab in the background. If audio
> fails, the game keeps running. Verified with a headless harness that wraps the `AudioContext` and
> logs every node and every ramp. **The harness does not listen**: it checks that what was designed
> plays, when it was designed to, with which parameters. Judging it by ear is still pending.
