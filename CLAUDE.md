# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read the folder's own CLAUDE.md first

**Every game folder has one, and it is the source of truth for that game.** This file only holds
what is true across the repo. The per-folder files are long on purpose — [Loop/CLAUDE.md](Loop/CLAUDE.md)
is ~2500 lines — and they carry the measurements, the bugs already made and the reasons behind
decisions that look arbitrary from outside. Reading one before editing its game is not optional.

## Repository layout

A collection of standalone games, simulations and visual toys, one per top-level folder. No shared
modules, no package, no build system. Folders are independent and self-contained.

Each folder holds up to three things:

- `<Folder>/<Folder>.py` — the original Pygame prototype. **19 of 23 folders have one.**
- `<Folder>/<Folder>Web/index.html` — the browser port. **All 23 have one.**
- `<Folder>/CLAUDE.md` — that game's notes.

**The browser port is now the main artifact.** Four games were born on the web and have no Python
at all: [Loop](Loop/LoopWeb/index.html), [StickFight](StickFight/StickFightWeb/index.html),
[DonkeyKong](DonkeyKong/DonkeyKongWeb/index.html) and [Pacman](Pacman/PacmanWeb/index.html). Where
both exist they are **independent reimplementations, not transpiled** — edit the two separately.

Two folders are not games:

- [Arcade/](Arcade/CLAUDE.md) — the installable PWA launcher that hosts every port. It has its own
  CLAUDE.md; read it before touching it.
- The root [index.html](index.html) is a 733-byte **redirect to `Arcade/`**. It is not leftover: it
  is the entry point GitHub Pages serves, so `…/Showcase/` has somewhere to land.

## Running

```powershell
python <Folder>\<Folder>.py           # the Python original
python -m http.server 8000            # the web ports; they fetch assets, so not file://
```

The folder `Newton's Cradle` contains an apostrophe — quote the path.

## Dependencies

`pygame` for the Python side (plus `pygame.freetype`, a submodule, and `pygame.mixer` in
[SimonSays](SimonSays/SimonSays.py)). [Balls/Balls.py](Balls/Balls.py) also needs **`pymunk`**: it
was migrated to a real physics engine and the legacy hand-rolled version lives in `Balls/handrolled/`.
There is no `requirements.txt`.

On the web side there is **one** vendored library: `matter.min.js` (rigid-body physics), loaded by
Balls, MiniBalls, CrazyTanks and TankWARS. Everything else is dependency-free hand-rolled JS.

> `nipplejs.min.js` still sits in three folders but **no port loads it any more**. Every mention in
> the code is a comment explaining why it was replaced: in `dynamic`/`semi` mode it lost the
> `pointerup` and the stick stayed stuck. The hand-rolled `createJoystick` with `setPointerCapture`
> is the pattern to copy (CrazyTanks, TankWARS, Loop, StickFight; Snake has its own inline version).

## Shared architecture — Python side

There is no base module, so the boilerplate is duplicated in each file:

- **`Sprite` base class** with no-op `process()` and `draw()`. Every game object subclasses it and
  is appended to module-level lists (`sprites`, plus type-specific ones like `tanks`, `bombs`).
- **Main loop** (`while True:`) computes a clamped `deltaT` from `time.time()`, polls
  `pygame.key.get_pressed()` and the mouse, fills the surface, then calls `process()` and `draw()`
  on every sprite in order. Movement is delta-time-scaled.
- **Resolution helpers** `xper(p)`, `yper(p)`, `sper(p)` return percentages of `screenX`, `screenY`
  or their average. Use them instead of raw pixels.
- **Color helpers** `randColorInRange`, `modifyColor`, `modifyColorPerc` — duplicated with
  identical signatures.
- **Geometry helpers** `getAngle`, `getDist`, and the angle-wrapping `getAngle2` /
  `getAngleForAngVel` for continuous angular velocity across the ±π discontinuity.
- **Quit** is `ESC` everywhere, plus `pygame.QUIT`.

## Shared architecture — web ports

A single self-contained `index.html` (HTML + CSS + JS, Canvas 2D). No build step.
[Balls/BallsWeb](Balls/BallsWeb/index.html) established the format.

- **Mobile-first layout.** The canvas (`#c`) fills the area *above* a fixed bottom `#bar` of
  circular buttons, with a `#btnInfo` toggle and a `#hint` line that fades after 5 s. The CSS block
  (`--bar-height`, safe-area insets, `:active`/`.on` states) is near-identical between ports — copy it.
- **Resolution independence.** `resize()` sizes the canvas to the viewport scaled by
  `devicePixelRatio` (capped), and all geometry is a fraction of `W`, `H` or `min(W,H)` — the web
  analog of `xper`/`yper`/`sper`. Never hardcode 1280×720.
- **Loop.** `requestAnimationFrame` with `dt = min(cap, (now − lastT)/1000)` in seconds.
- **Adaptive input.** Pointer events cover mouse and touch from one path; keyboard is layered on for
  desktop. Multi-touch goes in a `pointers` Map. `tappable(el, fn)` fires on `pointerdown`, not
  `click`, so bar buttons still respond while another finger holds the canvas.
- **Context loss is mandatory.** Every game lives in an iframe of the *same* renderer, and iOS caps
  canvas memory **per tab**, so the browser throws away the context of whatever is in the
  background. Without the `contextlost` / `contextrestored` pair plus a re-bake, that is a permanent
  black screen. Implemented in Loop, Pong and StickFight; **the rest still owe it.**
- **English UI and English comments**; the identifiers are left as they were (several folders mix
  Spanish and English names — see the conventions below).

## Assets

- **Screenshots and photographs go in WebP, never PNG.** PNG is lossless, which is the wrong trade
  for a photo: the arcade thumbnails were 8.86 MB as PNG and 0.73 MB as WebP *at the same
  resolution*, and Snake's lake background was a 13 MB PNG where 0.4 MB of WebP is
  indistinguishable. Quality ~82 measures 34–40 dB PSNR.
- **Ship an image at the size it is used.** Snake downloaded 4000×3000 and immediately downscaled it
  to 2048.
- **Never put `Date.now()` in the `src` of an asset.** A cache buster is a tool for iterating, and
  leaving one in means the browser can never cache the file. Snake re-downloaded 13 MB *every game*
  for months because of one. The single legitimate use in this repo is the Arcade busting the
  iframe's HTML document, which must never be stale.

## Audio

**Every one of the 22 web ports has sound, and all of it is synthesised in the browser.** Only two
games ship audio files: Balls/MiniBalls (real marble recordings) and Fireworks/FireworksV2 (launch,
sparks, explosion, background). Newton's Cradle has six 3 KB clips of real wooden-ball impacts cut
from a recording that was already in the repo. Everything else is Web Audio and weighs nothing.

There is **no shared audio module** — the folders stay independent. What is shared is an idiom,
and departing from it has cost real bugs:

- `AudioContext` is created inside `try/catch`, on the first gesture. In four games it was not, and
  because that call is the first statement of a `pointerdown` handler, a throw took the whole
  handler with it: the game lost **input**, not just sound.
- A per-frame voice cap, **reset at the top of `loop()`**. Pong incremented the counter and never
  reset it, so the game went permanently mute after ten sounds, with no error.
- Anything that can fire from a physics loop gets a cooldown; anything continuous (engines, drones,
  sirens) is one graph per session and is switched off on `visibilitychange`, because
  `requestAnimationFrame` stops in a background tab and the audio graph does not.
- Audio called from inside the frame goes in `try/catch` when the `requestAnimationFrame` re-arm is
  below it — otherwise one audio exception freezes the game forever rather than muting it.

Each game's own CLAUDE.md has its sonic identity and its vocabulary. They are deliberately
different: a clock, a tank, a marble and a playing card do not share a timbre.

## Conventions worth knowing before editing

- **Globals over parameters.** Sprites read `deltaT`, `keys`, `mouseX/mouseY`, `screenX/screenY`,
  `windowSurface` directly from module scope. Adding a parameter usually means threading it through
  many call sites — match the existing pattern instead.
- **Inline data tables.** Levels, tracks, palettes and start positions are large nested tuples
  embedded in `__init__` or `process` (see [CrazyTanks](CrazyTanks/CrazyTanks.py) — `maps`,
  `startpos`, `colors`, `controls`, `finishlines`). Map edits happen in those literals.
- **Mixed Spanish/English identifiers.** Older files ([Clock](Clock/Clock.py), [Pong](Pong/Pong.py),
  [Newton's Cradle](Newton's%20Cradle/Newton's%20Cradle.py), [SimonSays](SimonSays/SimonSays.py))
  use Spanish names (`radio`, `centro_x`, `fuente`, `pelota`). Newer files use English. Don't rename
  across that boundary without reason.
- **Embedded binary blobs.** [SimonSays.py](SimonSays/SimonSays.py) is ~660 KB because raw PCM audio
  is pasted as bytes literals into `pygame.mixer.Sound(buffer=...)`. Don't read it in full — use
  `Grep` or an explicit `offset`/`limit`.
- **No lint config, no CI.** The one exception to "no tooling" is Loop, which has a headless QA
  harness of 68 scenarios driven by Chrome + Python (see [Loop/CLAUDE.md](Loop/CLAUDE.md)). Don't add
  tooling elsewhere unless asked.

## The mirror

This repo is mirrored by hand into a second GitHub repo, `repos/Showcase`, which is what GitHub
Pages publishes. **Both have to be pushed**, and a sync has to propagate *deletions*, not only
copies — `cp` alone leaves orphans behind. Verify with `diff -rq <src> <dst> -x .git`.
