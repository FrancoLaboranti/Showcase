# CLAUDE.md — Arcade

Guidance for Claude Code when working on `Arcade/`. See [../CLAUDE.md](../CLAUDE.md) for the
conventions shared by the whole repo.

## What this folder is

`Arcade/` is **not a game**. It is the installable PWA launcher that hosts every web port, and
since the root [`index.html`](../index.html) became a redirect to `Arcade/`, it is also **the
landing page of the whole repo** — the first thing anyone sees.

| file | job |
|---|---|
| `index.html` | the whole launcher: grid, catalogue, player, PWA wiring. ~36 KB, no build step |
| `arcade-shell.js` | included **by each game**, not by the launcher. Exit / fullscreen / orientation + the bridge back to the launcher |
| `arcade-shell.css` | the styles those shared buttons need |
| `sw.js` | minimal service worker — exists so the app is *installable* |
| `manifest.json`, `icon*.png`, `icon.svg` | PWA metadata and icons |
| `thumbnails/*.webp` | one 900×900 card image per game |

## The catalogue

Games live in the `GAMES` array in `index.html`:

```js
['Loop.webp', 'Loop', 'Loop/LoopWeb/', 'landscape', '#7df9ff'],
//  thumb      name    path (from repo root)  orientation  hue (historical, ignored)
```

To add a game: drop `<Name>.webp` in `thumbnails/` and add one row. The 5th field is dead — the
card colour comes from a single global `--accent` that cycles for every tile at once.

The path is **relative to the repo root**, not to `Arcade/`, because the launcher escapes its own
folder to reach the games.

## The player: one iframe, no navigation

Tapping a card does **not** navigate. `launch()` builds an `<iframe>` inside `#player` and leaves
the page where it is, so the Fullscreen permission obtained on that tap survives the whole
session. Three things in there are load-bearing:

- **`?t=' + Date.now()`** on the iframe `src` is deliberate here: a game must never be served
  stale after a deploy. This is the one place in the repo where a cache buster belongs, because
  it busts an HTML document, not an asset. **Do not copy the pattern onto images** — see
  [Assets](#assets).
- **`frame.src = 'about:blank'` before `remove()`** when closing. Every game shares one renderer
  process, and iOS caps canvas memory **per tab**; without forcing the document out, the heavy
  games stop loading after a few launches. This is the fix for a bug that already happened.
- **`#frame.landscape` is rotated 90° by CSS** when the device is in portrait
  (`translateX(100vw) rotate(90deg)`), so a landscape game is played by turning the phone without
  the device ever rotating — zero orientation flashes. The game inside sees a landscape viewport
  and touches map themselves through the transform.

That rotation has a consequence worth knowing before debugging touch: **inside the iframe, the
browser's own gestures live in a rotated coordinate system.** Native touch scrolling of an
element inside a game can classify the gesture on the wrong axis. Loop's info panel hit exactly
this and ended up scrolling by hand with pointer events.

## The bridge

Each game includes the shared shell:

```html
<script src="../../Arcade/arcade-shell.js" data-orient="landscape"></script>
```

`data-orient` is `landscape` | `portrait` | `any` and decides whether the game asks for an
orientation lock. The shell expects `#btnExit`, `#btnFs` and optionally `#btnInfo` to exist in
the game's HTML, and it talks to the launcher with three messages:

- `arcade:exit` — game → launcher, close the player
- `arcade:fullscreen` — game → launcher, toggle real fullscreen (the launcher owns it, not the iframe)
- `arcade:fs-state` — launcher → game, so the ⛶ icon reflects reality

When embedded the shell hides ⛶ (toggling fullscreen from inside an iframe is meaningless) and
lets the parent do the work. Standalone, the game does it itself. 18 of the ports include the
shell; the rest predate it.

## The service worker

`sw.js` is deliberately almost empty. It exists because Chrome requires a `fetch` handler for the
app to be installable. Navigations are **network-first with `cache: 'no-store'`** so a deploy is
visible immediately; everything else falls through to the browser's normal cache. It caches
nothing on purpose.

Its scope is `/Arcade/` only — **the games live outside it** and are refreshed by the iframe
cache buster instead.

## Assets

- **Thumbnails are 900×900 WebP**, and screenshots must be saved that way. They used to be PNG:
  8.86 MB for 22 cards, against 0.73 MB at the *same* resolution in WebP. The weight never came
  from the dimensions but from storing photographs losslessly. Quality ~82 measures 34–40 dB PSNR
  against the original, and a card is displayed at 150–250 px.
- The `<img>` tags carry `loading="lazy"` and `decoding="async"`. All 22 used to be requested at
  once.
- 900 is kept (rather than 450) because a 250 px tile on a dpr-3 phone genuinely uses ~750 px.
- The PWA icons in `manifest.json` are still PNG and should stay that way: install prompts are
  fussier about formats than `<img>` is.


## The ⓘ button and the info panel (2026-09-22)

**Before this, in 18 of the 22 games the ⓘ button showed a frame counter.** Only Loop and StickFight
explained how to play. And `arcade-shell.css` hides the `#hint` of *every* game on the grounds that
"the controls are already in the ⓘ button" — which was false: the only explanation the player had
was switched off, and what they saw in its place was frames per second.

Now all 22 have an `#infoPanel` with real rules, taken from the web port's controls (not from the
folder's `CLAUDE.md`, which mostly describes the Pygame version). The `#hint`s were the best source:
they are the author's own description of the controls.

**The FPS was not removed: it moved.** `#fpsOverlay` becomes a child of the panel, so the handler
each game already had keeps switching it on and off — only now it is a line inside the card. The
button is not cloned and no listeners are removed: both handlers listen to the same `pointerdown`
and start from the same state, so they stay in sync by themselves.

Three things about the panel that are not decorative:

- **`touch-action: pan-y` + `overscroll-behavior: contain`.** Several games declare
  `touch-action: none` on the `body`, and the browser resolves the allowed gesture as the
  **intersection** with every ancestor: without that line the panel does not scroll under the finger
  however much overflow it has. It is the same trap Loop had already stepped on.
- **The bar is MEASURED, not assumed.** It uses `innerHeight − bar.top`, not `--bar-height`: several
  games do not declare that variable, and in Hangman the bar floats **above the on-screen keyboard**,
  so going by height alone the panel landed right on top of it.
- **If no usable room is left above the bar, the panel anchors to the floor and covers whatever is
  there.** In Hangman in landscape the keyboard and the bar eat 319 of 380 px. When it anchors to
  the floor it can end up over the button that opened it, so in that case it is positioned to leave
  the button clear — the ⓘ is the only way to close it and it must stay reachable.

**There is no ✕ inside the panel.** The ⓘ button is the only toggle, in all 22: a second control that
does the same thing as the first is one more thing to find, and it made the panel's own chrome differ
from game to game. `Escape` also closes it on desktop.

## The accent is a variable, not a colour

`arcade-shell.css` defines `--shell-accent` and **each game redefines it with a colour from its own
palette**. That is what lets the collection feel like one thing without leaving every game wearing
Loop's cyan: Minesweeper is grass green, Simon is gold, Tron cyan, the fireworks orange.

The button body comes from Loop and is three layers: a panel surface, a **light edge on top**
(`inset 0 1px 0` — that is what makes it read as a physical piece and not a painted rectangle) and a
short dark base. The active state **shrinks** (`scale(.9)`): a button that grows when touched covers
what is next to it exactly when the finger is already on top.

**The touch area is enlarged with an `::after`, not with the body.** The drawing is 32 px because
bigger covers game, but a thumb needs ~44. The sideways expansion is only 2 px on purpose: with
`gap: 8px` two areas of ±4 would touch and the tap would land on the neighbour. In the five games
with their own bar (CrazyTanks, Pong, Snake, StickFight, TankWARS) the buttons sit at a 38 px pitch
with 30 px bodies, so there the enlargement is **vertical only**.

**Five games do not include the shell and that is fine**: they have a hand-made bar for reasons of
their own (floating buttons, not a row). Those get the panel CSS inline. Deliberate duplication:
giving them the whole shell would change their buttons.

## Gotchas

- **A blanket `.png` → `.webp` replace in `index.html` is safe only because the icons live in
  `manifest.json`.** The catalogue's pattern is `.png',` with the quote-comma. Count before
  replacing.
- The grid is `repeat(auto-fill, minmax(150px, 1fr))`, so tile width varies with the viewport —
  never assume a pixel size for the cards.
- `#exitApp` (close the PWA) shows only when installed. In a browser tab `window.close()` is
  blocked by Chrome, so the button would do nothing and is hidden.
