# Marbles

A browser-based marble physics sandbox. Drag, throw, pile up and shake a bag of
procedurally-generated glass marbles, with real recorded marble sound effects.
Built for touch (multi-touch aware) but works with a mouse too.

Physics run on [Matter.js](https://brm.io/matter-js/) (vendored locally as
`matter.min.js`, so no CDN dependency at load); rendering, marble art and audio are
hand-rolled on a plain `<canvas>`. It's just [Marbles/index.html](Marbles/index.html),
`matter.min.js` and the sound samples in [Marbles/sounds/](Marbles/sounds/) — no
build step, works fully offline.

## Features

- **Throw & grab** — drag any marble to fling it; each finger can hold and throw
  its own marble independently.
- **Procedural marbles** — every marble gets a random size, color and pattern
  (striped, sphere-striped, spiral, diamond, pinwheel, dotted, candy, hex or
  plain), baked once into a translucent glass-look sprite with a specular hotspot.
- **Wall modes** — cycle between a closed box, a side tunnel (top/bottom wrap), and
  full wrap-around (no walls).
- **Pin** — nail a held marble in place so others bounce off it.
- **Jump & shake** — make all loose marbles hop, either with the button or by
  physically shaking the device (accelerometer).
- **Real sound** — recorded marble clicks, rolls and bag-rummaging samples, pitched
  by marble size and gated so collisions don't saturate.
- **Debug HUD** — optional overlay with FPS, marble/pinned counts and a top-speed
  bar chart.

## Controls

| Control | Action |
|---------|--------|
| **Drag a marble** | Grab and throw it (release to fling) |
| **↑ button** | Make all loose marbles jump |
| **Shake device** | Same as jump (needs accelerometer access) |
| **Pin button** | Pin / unpin the currently held marble(s) |
| **Wall button** | Cycle wall mode: box → side tunnel → full wrap |
| **+ / − buttons** | Add / remove a marble (hold to repeat) |
| **Reset button** | Regenerate the current set of marbles |
| **ⓘ button** | Toggle the debug HUD |

Up to 100 marbles at once.

## Running

Because the page fetches the `.mp3` samples, open it through a local web server
rather than `file://`:

```powershell
# from the repo root
cd Marbles
python -m http.server 8000
# then open http://localhost:8000 in a browser
```

Any static server works. On a phone, the shake-to-jump accelerometer only fires
over **HTTPS** (or inside an app WebView); the rest works over plain HTTP.

> Matter.js ships in the repo as `matter.min.js`, so there's no network dependency
> at startup and the app runs offline / inside a packaged WebView (e.g. Capacitor).
