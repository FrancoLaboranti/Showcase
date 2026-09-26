---
name: crazytanks-level
description: Tune or extend the PROCEDURAL circuit generator in the CrazyTanks web port (CrazyTanks/CrazyTanksWeb/index.html). Every free race auto-generates a fresh track (varied layouts, optional edge-crossing portals, randomized start direction). Use when the user asks to change how maps are generated, vary their shape/size/difficulty/portals, fix a bad auto-generated layout, or add a hand-authored circuit to the curated pool.
---

# CrazyTanks — circuit generator (auto-generated per race)

Every free race generates a new circuit on starting (`regenAutoTrack()` in `startRace`/`_rebuildRace`).
The tournament does NOT auto-generate (it uses the curated tracks 0–9). Your job here is to **tune the generator** or add
a fixed track to the curated pool.

A single file, no build: `CrazyTanks/CrazyTanksWeb/index.html`.

## How `buildAutoTrack(idx, W, H, theme)` works — the HAMILTONIAN CYCLE model

**THE GOLDEN RULE: the racing line is a HAMILTONIAN loop over a grid (the spanning-tree method): the
cycle walks ALL the cells and comes back.** It is a single loop, **guaranteed simple** (it never crosses itself, by
construction), which **snakes across the whole map** with plenty of curves (S/U/V, hairpins). The corridor is a
NARROW BAND (an offset) → there is room left for more straights and curves. This replaces the oval/ring attempts
that all came out the same and with enormously wide roads.

1. **Rolls**: a grid of *rooms* `a×b` (2–4 × 2–3 → a cycle of `4ab` cells = 16..48), `margin` (inset, 150–300),
   `wall` (the minimum wall between lanes, 120–170). The world (4300–5200 × 2600–3200) and the theme are rolled.
2. **A random spanning tree** (DFS) over the `a×b` grid (`_spanningTree`) → a **Hamiltonian cycle** over the
   `2a×2b` grid of nodes (`_hamiltonian`): each room starts as a 2×2 CW loop, and each edge of the tree
   MERGES two neighbouring loops → a single cycle is left passing through the `4ab` cells. (`ok` = it is 1 cycle of length
   `4ab`.) `_cornersOf` leaves only the corners (the curves).
3. **Width — a rolled STYLE, clipped to what fits, and sometimes VARIABLE per straight**: `fit = (min(cellX,cellY) − wall)/2`
   is the MAXIMUM half-width that leaves `wall` between adjacent lanes. If `fit < 80` → `return false` (it retries).
   A style is rolled (`styles`: technical 72–105 / normal 110–158 ×2 / wide 165–235 ×2, biased towards wider) →
   `half = max(72, min(ri(style), fit, margin−45))`. With **prob 0.5** the width is VARIABLE: each edge of the base
   (each STRAIGHT) rolls its own half-width `hw[i] ∈ [~0.42·fit, min(fit,235)]` → wide and narrow straights are
   combined in the same track. Since EVERY width is ≤ `fit` and the adjacent lanes are ≥ `cellX/Y` apart, **they never
   merge** (verified). The result: wide roads on small grids, narrow ones on large, + intra-track variation.
4. **Offset ±hw** (`_offset` accepts a scalar OR a **per-edge array** = a variable width; a miter-clamp per vertex) →
   outer/inner; **`_isSimple(outer/inner)`** catches spikes on curves and lanes that would merge → if it fails, it retries.
(Verified in Python: 4000/4000, ~1.3 attempts, half median≈147 [≤235], intra-track span median≈83, 8–22 curves.)
5. **PORTAL (wrap), prob 0.28, a rolled AXIS**: the loop is cut with a CLEAN line halfway through a cell (far from
   corners) and wrapped. Axis 0 = a **vertical** cut (`c=margin+(g+0.5)·cellX`) → a HORIZONTAL crossing, wrap X; axis 1 =
   a **horizontal** cut (`c=margin+(g+0.5)·cellY`) → a VERTICAL crossing, wrap Y. The cut may only go through
   STRAIGHT stretches perpendicular to the edge (`|p[1−ax]−q[1−ax]|≈0`), with openings at least `2·wMax+wall` apart. The loop is the
   SAME (simple); it is displaced by `−c` along the axis and rendered with `±W`/`±H` copies (`copies=[k=0,k=1]`, `tile`). By
   construction the crossing is STRAIGHT, aligned at both edges, with no self-crossing. `TRACK_WRAP[idx]=wrap`; the waypoints
   are wrapped (`mod W`/`mod H`) and the seam (a jump > 1200) is skipped by `pointBackAlong` and by the AI. Verified: 300/300
   openings aligned on EACH axis (top/bottom for Y, left/right for X).
6. **Walls**: `_ringWallsMulti(copies, …)` — the corridor is CLIPPED to `[0,W]` before the complement (the wrap's
   copies run outside the world). **Drawing**: `drawCorridorCarve` (the complete wall + CARVE OUT each copy's corridor,
   `destination-out`, + a bevel). The collision and the drawing both come from `smoothSample(outer/inner)` → they coincide.
7. **Waypoints**: `smoothSample(sBase, 70)` (the centreline = the Hamiltonian corner loop, displaced/wrapped if there is a
   portal); the **start** on a straight stretch (low curvature, NEVER on the seam) → a straight exit. The FINISH LINE is
   drawn PERPENDICULAR to the tangent of the racing direction (diagonal on a curve) — `TrackPoint.draw` rotates the chequers.
   Its length is **MEASURED by RAYCAST** (`_raySeg`) perpendicular to EACH wall at the start → `FINISH_ASYM[idx]=[dP,dM]`
   (asymmetric, bounded by the opposite side `+50` to discard grazing rays) `+14` → it covers the WHOLE road even on a
   curve/variable width. The curated tracks have no `FINISH_ASYM` → they use a symmetric `fl[0]`. It is also drawn on the
   **minimap** (white + black dashes, perpendicular at `wp[0]`). `BIG_VERTICAL` is no longer read.

## What to touch according to the request

- **More/fewer curves**: the range of the `a×b` grid (more cells = more curves). Today 2–4 × 2–3.
- **A wider/narrower band**: the `styles` table (the ranges per style) and/or `wall`. The `fit` cap stops lanes
  merging however much width you ask for (it goes up only where it fits).
- **More/less VARIABLE width (straights of different widths)**: the `Math.random() < 0.5` probability and the `[~0.42·fit, min(fit,235)]` range.
- **More/fewer portals / the proportion of axes**: the `Math.random() < 0.28` probability and the axis's `ri(0,1)` in `buildAutoTrack`.
- **For it to fill more/less**: `margin`.
- **A bigger/smaller world** (it allows bigger grids = more curves): `regenAutoTrack`.
- **A bigger/smaller world**: `regenAutoTrack`'s `ri(43,52)*100 / ri(26,32)*100`. The baked background
  has a memory cap (`BG_MAX_PIXELS`, ~38MB): bigger worlds are baked at a lower resolution
  (`bgK<1`) and scaled up when blitting — it does not break, it only softens.
- **Perf**: `bands = H/32` in `_ringWallsMulti` (fewer bands = fewer bodies).

## PORTALS (crossing from edge to edge) — ENABLED (prob 0.28, axis X or Y), by a CLEAN CUT of the loop

The key to the portal always being STRAIGHT (perpendicular to the edge, never in the middle of a curve): an open
corridor is NOT designed; the CLOSED Hamiltonian loop (already validated) is reused and **cut with a clean line +
wrapped**. Since the base is rectilinear, a line `c` halfway through a cell (perpendicular to the rolled axis) crosses
ONLY straight stretches perpendicular to the edge → the crossing is perpendicular by construction, and since the loop is still
the same simple polygon, **it cannot cross itself**. A rolled axis: **X** (a vertical cut → a horizontal
portal, displaced `−c` in x, `±W` copies) or **Y** (a horizontal cut → a vertical portal, displaced `−c` in y,
`±H` copies). `_ringWallsMulti` clips the corridor to `[0,W]`. Aligned openings verified 300/300 per axis.

The engine already supported portals (tank/bomb wrapping in X/Y at `[2795]`/`[1000]`, the AI aiming "unwrapped" at `[848]`,
`pointBackAlong` skipping seams > 1200 at `[598]`) — it was dormant; now `buildAutoTrack` switches it on sometimes.
To raise/lower the frequency, touch `Math.random() < 0.22`. The cut demands ≥2 horizontal crossings at least
`2·half+wall` apart; if it does not find a clean one, the map is left with no portal (it is not forced).

## Adding a FIXED track to the curated pool (optional)

Add an object to `BIG_TRACKS` (`{name, theme, w, h, half, bands, base:[[x,y],…]}`) — the `BIG_TRACKS`
loop wires it up (indices 10–14, they appear in `TRACK_ORDER`). The `base` is the track's centreline
(a non-convex polygon, world coords). Themes: 0 green, 1 desert, 2 snow, 3 techno, 4 lava.

## Verification and checklist

- If you changed the generator → simulate it in Python first (a mirror of `_spanningTree`/`_hamiltonian`/`_cornersOf` +
  `_offset` + `_isSimple` + `smoothSample` + the scanline primitives `_cross/_pairs/_subtract/_union/_complement`):
  run it ≥1000 times and measure the **% valid** (without a fallback), **attempts/valid**, the **distribution of `half`** (that
  there is spread: narrow + wide), the **number of curves** (min ≥ 3) and the **cycle sizes**. For PORTALS: verify that
  the corridor's openings at `x≈0` and `x≈W` are ALIGNED in `y` and with the same count (clipping the corridor
  to `[0,W]` BEFORE the complement — `_complement` returns walls outside `[0,W]`, do not confuse them with edges).
- [ ] Brace/parenthesis balance:
      `python -c "s=open('CrazyTanks/CrazyTanksWeb/index.html',encoding='utf-8').read(); print(s.count('{')-s.count('}'), s.count('(')-s.count(')'), s.count('[')-s.count(']'))"` → `0 0 0`.
- [ ] Server 200 + a hard reload on the phone. Run several races: DIFFERENT maps every time (smooth loops,
      wavy, zigzag, asymmetric), that they fill the map, laps that count, starts on a straight stretch.

## Infield scenery (BIG decor per biome, BAKED)

`drawScenery(track, ww, hh)` draws big, recognisable decor over the INFIELD (the area outside the corridor):
park (trees/bushes/flowers), desert (dunes/pyramids/cacti), snow (snowmen/rocks), techno
(buildings/cables), lava (lakes/rivers/embers). It is called INSIDE `drawCorridorCarve`, on the wall layer
`tc`, **BEFORE** the `destination-out` → the scenery that falls on the road is erased by the carve (a clean road)
and the bevel covers the seam. It is 100% baked (cost/frame = 0). `getScenery`/`sceneryBase` + the helpers
(`drawTree`, `drawPyramid`, `drawBuilding`, `drawLavaPool`, …) live just before the "MOTIFS" section.
- **More/less decor per theme**: `SCENERY_DENSITY=[13,9,9,4.5,6]` (items per screen-equivalent; it scales with the world's area).
- **It varies per map**: `TRACK_DECO_SEED[AUTO_TRACK]` is re-rolled in `regenAutoTrack`; `getDeco`/`getScenery`
  cache by `.seed` (new decor + scenery on each generation, stable across re-bakes/resizes).
- **Contrast**: each palette is tuned against its infield (`THEME_WALL`). If you change `THEME_WALL`/`THEME_FLOOR`,
  check that the scenery still lifts off the background.
- It only applies to the AUTO-GENERATED road (`drawCorridorCarve`); the curated tracks (`drawSmoothCorridor`) do not use it.

## Performance notes (already applied; do not undo)

- Tanks: an offscreen sprite cache per (skin, state) + culling outside the camera.
- **Walls: `_mergeWallRects` merges vertically contiguous strips (edges within TOL=6px) → ~16% fewer
  static bodies in Matter** (the physics with 16 tanks scales with the number of bodies). The joined rect only
  GROWS (it covers every strip) → the road narrows by ≤6px, it never opens a gap. `_ringWalls`/`_ringWallsMulti` apply it.
- Walls/waypoints do NOT go into `sprites` (they live baked); F2 debug through `tp.debugDraw()`.
- The nearest waypoint: an incremental search (a ±7 window around the last one, a full scan as a fallback).
- Minimap: the walls baked once per track (`minimapWallsImg`, the key `mmKey`).
- Background: `BG_MAX_PIXELS` + `bgK` (a resolution cap on the bake for big worlds).
