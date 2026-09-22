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


## El botón ⓘ y el panel de información (2026-09-22)

**Antes, en 18 de los 22 juegos el botón ⓘ mostraba un contador de FPS.** Sólo Loop y StickFight
explicaban cómo se juega. Y `arcade-shell.css` oculta el `#hint` de *todos* los juegos con el
argumento de que "los controles ya están en el botón ⓘ" — que era falso: la única explicación que
el jugador tenía estaba apagada, y lo que veía en su lugar eran cuadros por segundo.

Ahora los 22 tienen un `#infoPanel` con reglas reales, sacadas de los controles del port web (no
del `CLAUDE.md` de la carpeta, que describe sobre todo la versión de Pygame). Los `#hint` fueron la
mejor fuente: son la descripción de controles del propio autor.

**El FPS no se quitó: se mudó.** El `#fpsOverlay` pasa a ser un hijo del panel, así que el handler
que cada juego ya tenía lo sigue prendiendo y apagando — sólo que ahora es una línea adentro de la
tarjeta. No se clona el botón ni se sacan listeners: los dos handlers escuchan el mismo
`pointerdown` y parten del mismo estado, así que quedan sincronizados solos.

Tres cosas del panel que no son decorativas:

- **`touch-action: pan-y` + `overscroll-behavior: contain`.** Varios juegos declaran
  `touch-action: none` en el `body`, y el navegador resuelve el gesto permitido como la
  **intersección** con todos los ancestros: sin esa línea el panel no se desplaza con el dedo por
  más overflow que tenga. Es la misma trampa que Loop ya había pisado.
- **La barra se MIDE, no se asume.** Se usa `innerHeight − bar.top`, no `--bar-height`: varios
  juegos no declaran esa variable, y en Hangman la barra flota **encima del teclado en pantalla**,
  así que con el alto solo el panel le caía justo arriba.
- **Si arriba de la barra no queda lugar usable, el panel se ancla al piso y tapa lo que haya.**
  En Hangman apaisado el teclado y la barra se comen 319 de 380 px. Por eso el panel tiene un **✕
  propio**: cuando se ancla al piso puede quedar por encima del botón que lo abrió, y sin una
  salida adentro el jugador queda atrapado leyendo las instrucciones.

## El acento es una variable, no un color

`arcade-shell.css` define `--shell-accent` y **cada juego la redefine con un color de su propia
paleta**. Es lo que permite que la colección se sienta una sola sin que ningún juego quede con el
celeste de Loop encima: el buscaminas es verde pasto, Simón es dorado, Tron celeste, los fuegos
naranjas.

El cuerpo del botón viene de Loop y son tres capas: superficie de panel, **filo de luz arriba**
(`inset 0 1px 0` — es lo que hace que se lea como pieza física y no como rectángulo pintado) y una
base oscura corta. El estado activo **encoge** (`scale(.9)`): un botón que crece al tocarlo tapa lo
que está al lado justo cuando el dedo ya está encima.

**El área táctil se agranda con un `::after`, no con el cuerpo.** El dibujo mide 32 px porque más
grande tapa juego, pero un pulgar necesita ~44. La expansión lateral es de sólo 2 px a propósito:
con `gap: 8px` dos áreas de ±4 se tocarían y el tap caería en el vecino. En los cinco juegos con
barra propia (CrazyTanks, Pong, Snake, StickFight, TankWARS) los botones están a 38 px de paso con
cuerpos de 30, así que ahí la ampliación es **sólo vertical**.

**Cinco juegos no incluyen el shell y así queda**: tienen la barra hecha a mano por razones
propias (botones flotantes, no una fila). A ésos el CSS del panel les va en línea. Duplicación
deliberada: meterles el shell entero les cambiaría los botones.

## Gotchas

- **A blanket `.png` → `.webp` replace in `index.html` is safe only because the icons live in
  `manifest.json`.** The catalogue's pattern is `.png',` with the quote-comma. Count before
  replacing.
- The grid is `repeat(auto-fill, minmax(150px, 1fr))`, so tile width varies with the viewport —
  never assume a pixel size for the cards.
- `#exitApp` (close the PWA) shows only when installed. In a browser tab `window.close()` is
  blocked by Chrome, so the button would do nothing and is hidden.
