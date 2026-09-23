# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Newton's cradle simulator: pendulum balls hanging by strings, dragging one and releasing transfers momentum through the chain. Window is 1280×720. Press **UP** to add a ball, **DOWN** to remove one (capped between 1 and 10 balls).

Spanish identifiers throughout (`radio`, `velocidad`, `angulo`, `colisiona`, `colision_ryp`, `colision_circulos`, `orig_x/orig_y`). Folder name contains an apostrophe: quote the path when running: `python "Newton's Cradle\Newton's Cradle.py"`.

Diverges from the repo skeleton: no `Sprite` base class, no `xper`/`yper` helpers, no `deltaT` (uses fixed-step physics). The `Ball` class manages its own pendulum integration via `angulo` and `velocidad` around its anchor `orig_x, orig_y`.

See [../CLAUDE.md](../CLAUDE.md) for the shared conventions this file does not follow.


## AUDIO: fix and new material (2026-09-22)

**The freeze.** `playClick()` was called from inside `frame()` and the `requestAnimationFrame` is
further down. An audio exception, an interrupted context on mobile throws `InvalidStateError` when
writing any parameter, did not leave the cradle mute: it left it **STILL**, never asking for another
frame again. The call now sits in `try/catch` and `playClick` requires `actx.state === 'running'`, not
merely that the context exists.

**The orphan WAV.** `sounds/woodenballs.wav` is 19.6 MB that nothing loaded: 69 s of a real recording
of wooden balls colliding, 24-bit stereo at 48 kHz, with **39 isolated impacts**. That is more than
enough material for the one game in the repo whose sound IS two wooden spheres colliding. The six
clean hits (silent lead-in, no clipping, whole tail) were extracted to `wood1..6.mp3`, **17.6 KB in
total**:

| | attack centroid | tail to -40 dB |
|---|---|---|
| wood5 | 646 Hz (low, muted) | 59 ms |
| wood1 | 1682 Hz | 72 ms |
| wood2 | 1635 Hz | 177 ms |
| wood6 | 2528 Hz | 55 ms |
| wood3 | 3249 Hz | 61 ms |
| wood4 | 3357 Hz (bright, dry) | 43 ms |

They are not six copies of the same hit: the game can pick by collision speed. **They are not wired up
yet**: the synthesised `playClick` is still what plays.

The 19.6 MB WAV is still in the repo: it is source material and deleting it is Franco's call.
