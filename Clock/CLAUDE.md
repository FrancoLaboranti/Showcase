# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Analog clock face rendered from `datetime.now()`. Click anywhere to toggle the second hand between **ticking** (`segundero == 0`, snaps per second) and **smooth** (`segundero == 1`, interpolated via `microsecond`). The smooth-second math packs microseconds into seconds as `(ca_ms + ca_s*999999) / (60*999999)` — that 999999 magic number is the multiplier, not a typo.

Window is 650×650. Spanish identifiers (`radio`, `centro_x/y`, `fuente`, `crear_texto`, `segundero`, `pressed`). No `ESC`-to-quit — only the window-close button exits.

This file shadows the stdlib `time` module by reassigning `time = datetime.datetime.now()` inside the loop. The `import time` at the top is currently unused; don't add `time.sleep(...)` without renaming the local first.

See [../CLAUDE.md](../CLAUDE.md) for shared conventions across the repo.


## AUDIO (2026-09-22)

**Phosphor on black glass, not wood or brass.** This clock is a laboratory instrument — rings with
`shadowBlur`, a glass-face gradient, Orbitron digits, seven neon palettes — so the timbral family is
quartz and glass: dry, very high transients over absolute silence. No drone, no ambience, no music.
The only tonal material is inharmonic chimes.

The tick is the heart of it and that is exactly why it is the hardest to dose: it plays once a
second for the whole session, so it lives at the bottom of the mix. A tick you notice is a tick that
is unbearable ten minutes later.

| voice | what it is |
|---|---|
| `tic(par)` | the escapement. Alternates two pitches, like a real escapement |
| `whir` | the sweep of the continuous second hand |
| `minuto` / `hora` | glass chimes, inharmonic |
| `modo` / `color` / `auto` | the interface, barely audible |

Ceiling of 10 voices per frame: the clock has no physics, its real peak is the hour chime.

> Pattern shared across the repo: WebAudio synthesis with no files, an `AudioContext` created
> inside `try/catch` on the first gesture, a per-frame voice ceiling **with its reset at the top of
> `loop()`**, a per-voice cooldown, a mute button persisted in `localStorage`, and
> `visibilitychange` so nothing continuous keeps playing with the tab in the background. If audio
> fails, the game keeps running. Verified with a headless harness that wraps the `AudioContext` and
> logs every node and every ramp. **The harness does not listen**: it checks that what was designed
> plays, when it was designed to, with which parameters. Judging it by ear is still pending.
