# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

A collection of standalone Pygame projects — small games, simulations, and visual toys. Each project lives in its own top-level folder containing a single `.py` file with the same name as the folder (e.g. [Snake/Snake.py](Snake/Snake.py)). No shared modules, no package, no build system. Folders are independent and self-contained.

Most projects also have a **web port** alongside the Python file, in a `<Folder>/<Folder>Web/` subfolder (e.g. [Pong/PongWeb/index.html](Pong/PongWeb/index.html)). See [Web ports](#web-ports) below — they are a separate, self-contained reimplementation, not generated from the `.py`.

## Running a project

Every project is launched the same way — there is no entry point script or harness:

```powershell
python <Folder>\<Folder>.py
```

The folder named `Newton's Cradle` contains an apostrophe — quote the path when running it.

## Dependencies

The only external dependency is `pygame`. Several files also use `pygame.freetype` (a submodule of pygame itself, not a separate package). [SimonSays/SimonSays.py](SimonSays/SimonSays.py) additionally uses `pygame.mixer`. There is no `requirements.txt`; install with `pip install pygame`.

## Shared architecture across projects

Most files follow the same hand-rolled pattern — there is no shared base module, so the boilerplate is duplicated in each file. When editing one project, expect to see this structure:

- **`Sprite` base class** with no-op `process()` and `draw()` methods. Every game-object class subclasses `Sprite` and is appended to module-level lists (typically `sprites`, plus type-specific lists like `tanks`, `bombs`, `fireworks`, `explosions`, `trackpoints`).
- **Main loop** (`while True:`) computes a clamped `deltaT` from `time.time()`, polls `pygame.key.get_pressed()` and `pygame.mouse.get_pos/pressed()`, fills the surface, then calls `sprite.process()` followed by `sprite.draw()` on every sprite in order. Movement is delta-time-scaled, not frame-locked.
- **Resolution helpers** `xper(p)`, `yper(p)`, `sper(p)` return percentages of `screenX`, `screenY`, or their average. All positions, radii, and speeds are expressed as fractions of screen size so the games scale across resolutions. When adding new geometry, use these helpers rather than raw pixels.
- **Color helpers** `randColorInRange(...)`, `modifyColor(color, offset)`, `modifyColorPerc(color, factor)` are duplicated across files with identical signatures.
- **Geometry helpers** `getAngle`, `getDist`, and an angle-wrapping variant `getAngle2` / `getAngleForAngVel` (continuous angular velocity across the ±π discontinuity) are also duplicated.
- **Quit** is `ESC` everywhere; the main loop also handles `pygame.QUIT`.

When a project diverges from this skeleton, note it in that folder's CLAUDE.md rather than in this top-level file.

## Web ports

Many folders carry a `<Folder>Web/` subfolder with a browser version of the game — a single self-contained `index.html` (HTML + CSS + JS, Canvas 2D). No build step, no framework: open the file in a browser. [Balls/BallsWeb/index.html](Balls/BallsWeb/index.html) is the **reference port** that established the format. Most ports are dependency-free hand-rolled JS, but a couple vendor libraries locally: Balls and [CrazyTanks/CrazyTanksWeb/index.html](CrazyTanks/CrazyTanksWeb/index.html) use `matter.min.js` (rigid-body physics), and CrazyTanks also uses `nipplejs.min.js` (touch joysticks). These are faithful reimplementations of the Pygame originals, **not** transpiled from the `.py` — edit the two independently.

Shared format across all ports (mirror it when adding or editing one):

- **Mobile-first layout.** The canvas (`#c`) fills the area *above* a fixed bottom `#bar` of circular buttons (settings / actions, SVG or short-text icons), with a `#btnInfo` toggle in the bottom-right corner that draws an info overlay, and a `#hint` line up top that fades after 5 s. The CSS block (`--bar-height`, safe-area insets, `:active`/`.on` button states) is near-identical between ports — copy it.
- **Resolution independence.** `resize()` sizes the canvas to `W × (innerHeight − barHeight)` scaled by `devicePixelRatio` (capped at 2), and all geometry is expressed as fractions of `W`, `H`, or `min(W,H)` — the web analog of the Python `xper`/`yper`/`sper` helpers. Don't hardcode the original 1280×720.
- **Loop.** `requestAnimationFrame` with `dt = min(cap, (now − lastT)/1000)` in seconds, replacing the Pygame `while True:` + `deltaT`. Movement is dt-scaled.
- **Adaptive input.** Pointer events cover mouse + touch from one path; keyboard is layered on for desktop. Multi-touch is tracked in a `pointers` Map. A `tappable(el, fn)` helper fires on `pointerdown` (not `click`) so bar buttons still respond while another finger is held on the canvas.
- **Spanish UI, English identifiers** — same convention as the newer Python files.

## Conventions worth knowing before editing

- **Globals over parameters.** Sprites read `deltaT`, `keys`, `mouseX/mouseY`, `mouseLeft/mouseRight`, `screenX/screenY`, `windowSurface`, etc. directly from module scope. Adding a parameter to a sprite method usually means threading it through many call sites — match the existing global-access pattern instead.
- **Inline data tables.** Levels, tracks, color palettes, and start positions are large nested tuples literally embedded in `__init__` or `process` (see [CrazyTanks/CrazyTanks.py](CrazyTanks/CrazyTanks.py) — `maps`, `startpos`, `colors`, `controls`, `finishlines`). Edits to map geometry happen in those literals, not in external data files.
- **Mixed Spanish/English identifiers.** Older files ([Clock/Clock.py](Clock/Clock.py), [Pong/Pong.py](Pong/Pong.py), [Newton's Cradle/Newton's Cradle.py](Newton's%20Cradle/Newton's%20Cradle.py), [SimonSays/SimonSays.py](SimonSays/SimonSays.py)) use Spanish names (`radio`, `centro_x`, `fuente`, `crear_texto`, `pelota`, `apretado`). Newer files use English. Don't rename across that boundary without reason.
- **Embedded binary blobs.** [SimonSays/SimonSays.py](SimonSays/SimonSays.py) is ~660 KB because raw PCM audio buffers are pasted as bytes literals into `pygame.mixer.Sound(buffer=...)` calls. Do not attempt to read that file in full — use `Grep` or read with explicit `offset`/`limit` to find code sections.
- **No tests, no lint config, no CI.** This is a personal sandbox of independent prototypes — don't add tooling unless explicitly asked.
