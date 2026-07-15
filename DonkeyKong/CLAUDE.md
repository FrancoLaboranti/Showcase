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

## Movement & feel

Mario uses **momentum**, not on/off movement: `mario.vx` accelerates toward `±WALK` (`RUN_ACCEL`, with `TURN_BOOST` on direction change) and, on release, decays by `RUN_DECEL` (glides to a stop). Velocity carries into jumps (`airVx = vx`) and there is light air control (`AIR_ACCEL`); landing resumes momentum. **Falling off a girder loses the round** (`FALL_DEATH = 0.075`): your own jump apex (~0.04) survives, but dropping to a lower girder (~0.11+) kills — the classic-DK rule. (An earlier "daredevil shortcut" that rewarded surviving a 1-girder drop was removed because it contradicts this.)

## Controls

Two-thumb mobile D-pad in `#bar`: left cluster `◄ ►` (walk), right cluster `▲ ▼` (climb), utilities (`✕ ⛶ ⓘ`) centered. Buttons are `.pad button` (the old `#ui` wrapper is gone — `clearInput` and CSS target `.pad`). Jump = tap the canvas / Space. Each D-pad button uses `setPointerCapture` so both thumbs work at once.

## Visual style (modern pass, echoing TankWARS/CrazyTanks)

Per-frame rendering avoids `shadowBlur` (expensive on mobile — TankWARS' lesson): background gradients (`bgGrad`/`pfGrad`) and a `vigGrad` vignette are built once per `resize()`; entities get cheap elliptical contact shadows (`shadowAt`); the HUD sits on a translucent rounded panel (`roundRectPath`). The **baked** level (`bakeLevel`, one-time) is where glow lives — girders use a vertical gradient + glowing top rim + rivets, ladders glow cyan.

## State machine

`gh.screen` is `menu`|`game`; within a game `gh.phase` is `intro`→`play`→(`dying`|`win`)→… and `over`. `die()`/`winLevel()` no-op unless `phase==='play'`, so per-frame entity loops `break` out the moment one fires. `BONUS` decays on a timer and reaching 0 kills (time-out). Hi-score persists in `localStorage` under `dk_hiscore`.

## Replayability systems (layered on top of the base game)

Nine gameplay systems extend the single-board core; all are tuned to preserve the base balance:

- **Seeded boards + Daily mode** — `applyLevelLayout()` re-rolls which `LADDERS` are `broken` (constant per-tier count `[1,1,1,1,1,0]`, so difficulty is unchanged), jitters girder 1–4 slopes slightly, and re-seeds the two hammer spots, all via `mulberry32(gh.seed ^ level)`. `layoutWinnable()` validates a 0→6 non-broken chain and falls back to `restoreOriginalLayout()` if needed. **Level 1 classic = canonical board**; daily + levels 2+ are seeded. The menu has a second "DESAFÍO DIARIO" pill (`gh.mode='daily'`, date seed) whose scores persist to `dk_daily_<date>`, never to `dk_hiscore`.
- **Hazard draft** (`HAZARDS`, `pickHazardChoices`/`chooseHazard`) — from level 2 the intro shows two pills (CALMA vs a spicy modifier); the pick scales the **already-clamped** `lvlSpeed`/`spawnGap`/`descProb`/fireball-cap plus a score multiplier (`gpScore` vs plain `addScore`). The intro does not auto-advance until a pick (8s safety → CALMA).
- **Frenzy** (`updateFrenzy`/`drawFrenzy`, `gh.frenzy*`) — one telegraphed 6 s spike per level; barrel speed is hard-clamped to `BARREL_SPD*1.9`.
- **Wild barrel** (`Barrel(wild)`) — blue, faster, never descends ladders; spawned with a level-gated chance at the `dk.process` throw site.
- **Combo** (`gh.comboN/comboT`) — chained barrel/pie jumps multiply the jump score (capped at +500 pre-hazard).
- **Rivet levels** (every 4th, `isRivetLevel`) vs **Pauline collectibles** (other levels, seeded `ITEM_SPOTS`) — they **alternate** to avoid clutter; both are optional pure-score. Pickup state persists across a respawn within the same level (`gh.pickupLevel/rivetsPopped/itemsTaken`) so death can't re-farm.
- **Pie & conveyor** (`belt`, `Pie`, `beltFor`) — one girder (2 or 3, seeded) drifts Mario toward the clamp-safe end; pies slide along it.
- **Skins** (`SKINS`, `bakeMario`, `gh.total`/`dk_total`) — lifetime-points milestones unlock cosmetic Mario recolors (palette swap only — hitbox/physics untouched); equipped from a menu carousel.

## Registered in the Arcade

Listed in [../Arcade/index.html](../Arcade/index.html) `GAMES` as `'DonkeyKong/DonkeyKongWeb/'`, `portrait`, accent `#e83b2a`, thumbnail `Arcade/thumbnails/DonkeyKong.png`.

See [../CLAUDE.md](../CLAUDE.md) for the shared web-port conventions.
