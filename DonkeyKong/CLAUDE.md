# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Donkey Kong — a web-only homage to the 1981 arcade game. **There is no `.py` original**; unlike most folders here, this project exists *only* as the web port in [DonkeyKongWeb/index.html](DonkeyKongWeb/index.html) (single self-contained HTML + CSS + JS, Canvas 2D, no build step).

## UI lineage

The mobile shell is copied from the **Tron v1** port ([../Tron/TronWeb/index.html](../Tron/TronWeb/index.html)), not Tron V2: same `#bar` of circular buttons, `#hint`, `arcade-shell.css`/`.js` wiring, the JS error overlay, the FPS overlay toggled by `#btnInfo`, and the dt-clamping loop guard. The visual *style* is its own (arcade pixel-art, `Press Start 2P` font, pink girders / cyan ladders). Orientation is **portrait** (`data-orient="portrait"`), so the bar holds 4 D-pad buttons (◄ ▲ ▼ ►); **jump = tap the canvas** (or Space).

## Layout & resolution model

Everything is expressed in **fractions of the playfield** (`PF`), the web analog of the Python `xper`/`yper` helpers — see `ppx(f)`/`ppy(f)`. `PF` is a portrait rect (`ASPECT ≈ 0.58`) centered in the canvas, so desktop gets arcade-cabinet side bands. Because all entity positions are PF-fractions, **`resize()` does not reset the game** (it only re-bakes the static level into `levelCv`); the run continues in place.

## Level data

`GIRDERS` (index 0 = floor, 6 = Pauline's platform) are sloped beams `{x0,x1,yL,yR}`; barrels roll toward the lower end (`rollDir`) and fall off the open edge. `LADDERS` are `{x,lo,hi,broken}` connecting girder `lo`↔`hi`; **broken ladders block Mario but barrels/fireballs still descend them.** Before changing ladder layout, re-verify the board stays winnable: there must be a chain of non-broken ladders 0→1→2→3→4→5→6 whose `x` lies inside both connected girders' `[x0,x1]`.

## Sprites & audio

All art is pixel-art string maps baked to offscreen canvases via `makeSprite(rows, palette)` and drawn with `imageSmoothingEnabled=false` (hard pixels). Barrel rolling frames are generated procedurally (`barrelMap(phase)`). Sound is synthesized inline with WebAudio (`sfx.*` / `note()`) — no audio files; the context is unlocked on first pointer/keys gesture (`ac()`).

## State machine

`gh.screen` is `menu`|`game`; within a game `gh.phase` is `intro`→`play`→(`dying`|`win`)→… and `over`. `die()`/`winLevel()` no-op unless `phase==='play'`, so per-frame entity loops `break` out the moment one fires. `BONUS` decays on a timer and reaching 0 kills (time-out). Hi-score persists in `localStorage` under `dk_hiscore`.

## Registered in the Arcade

Listed in [../Arcade/index.html](../Arcade/index.html) `GAMES` as `'DonkeyKong/DonkeyKongWeb/'`, `portrait`, accent `#e83b2a`, thumbnail `Arcade/thumbnails/DonkeyKong.png`.

See [../CLAUDE.md](../CLAUDE.md) for the shared web-port conventions.
