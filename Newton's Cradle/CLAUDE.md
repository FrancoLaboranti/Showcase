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

**Where the wood comes from.** The six clips were cut from `sounds/woodenballs.wav`: 69 s of a real
recording of wooden balls colliding, 24-bit stereo at 48 kHz, with **39 isolated impacts**. That is
more than enough material for the one game in the repo whose sound IS two wooden spheres colliding.
The six clean hits (silent lead-in, no clipping, whole tail) became `wood1..6.mp3`, **17.6 KB in
total**.

**The master was REMOVED from the working tree** on 2026-09-23: 19.6 MB that nothing loaded, served
by GitHub Pages and mirrored into Showcase, for a game whose whole sound weighs 18 KB. It is not
lost, it lives in git history and comes back byte-for-byte with

```powershell
git show c07a976:"Newton's Cradle/NewtonsCradleWeb/sounds/woodenballs.wav" > woodenballs.wav
# c07a976 es el ULTIMO commit que contiene el blob. No sirve cualquier commit que `git log
# --follow` liste: --follow sigue renombres y devuelve commits donde el archivo NO esta.
```

which is the command to run before cutting more impacts. Deleting it does NOT shrink a clone: the
blob stays in history. What it fixes is what is served and what is mirrored.

The six, measured **on the shipped mp3s** and in brightness order, which is the order
`WOOD_FILES` uses. Measure the files, not the raw cuts: encoding rolls the top off and the two
sets of numbers do not agree.

| | centroid | tail to -40 dB | onsets |
|---|---|---|---|
| wood5 | 562 Hz (low, muted) | 59 ms | 1 |
| wood2 | 1027 Hz | 97 ms | 1 |
| wood1 | 1044 Hz | 72 ms | 1 |
| wood6 | 1893 Hz | 55 ms | 1 |
| wood3 | 2289 Hz | 61 ms | 1 |
| wood4 | 2947 Hz (bright, dry) | 43 ms | 1 |

They are not six copies of the same hit: the game picks by collision speed, and `playClick` maps
the intensity onto that ladder.

**wood2 was re-cut on 2026-09-23.** The first one had TWO hits, onsets at 5 ms and 134 ms, which
Franco heard as a double knock. What let it through: the extractor rejected a second impact only if
it went over 35 % of the first one's peak, and a wooden ball's return bounce lands just under that.
The count that matters is ONSETS in the finished cut, not energy in a window, so the replacement was
picked by counting them. The five that stayed sit at 41.24, 13.16, 15.86, 22.69 and 57.14 s of the
master; the new wood2 comes from 24.84 s, far enough from all of them to be a different impact.

The 19.6 MB WAV is still in the repo: it is source material and deleting it is Franco's call.
