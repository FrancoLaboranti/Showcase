---
name: crazytanks-level
description: Tune or extend the PROCEDURAL circuit generator in the CrazyTanks web port (CrazyTanks/CrazyTanksWeb/index.html). Every free race auto-generates a fresh track (varied layouts, optional edge-crossing portals, randomized start direction). Use when the user asks to change how maps are generated, vary their shape/size/difficulty/portals, fix a bad auto-generated layout, or add a hand-authored circuit to the curated pool.
---

# CrazyTanks — generador de circuitos (autogenerado por carrera)

Cada carrera libre genera un circuito nuevo al arrancar (`regenAutoTrack()` en `startRace`/`_rebuildRace`).
El torneo NO se autogenera (usa las pistas curadas 0–9). Tu trabajo acá es **ajustar el generador** o sumar
una pista fija a la pool curada.

Archivo único, sin build: `CrazyTanks/CrazyTanksWeb/index.html`.

## Cómo funciona `buildAutoTrack(idx, W, H, theme)` — modelo CICLO HAMILTONIANO

**REGLA DE ORO: la línea de carrera es un loop HAMILTONIANO sobre una grilla (método del spanning-tree): el
ciclo recorre TODAS las celdas y vuelve.** Es un único loop, **garantizado simple** (jamás se cruza, por
construcción), que **serpentea por todo el mapa** con muchas curvas (S/U/V, horquillas). El corredor es una
BANDA ANGOSTA (offset) → queda lugar para más rectas y curvas. Esto reemplaza a los intentos de óvalo/anillo
que salían todos iguales y con calles anchísimas.

1. **Sorteos**: grilla de *rooms* `a×b` (2–4 × 2–3 → ciclo de `4ab` celdas = 16..48), `margin` (inset, 150–300),
   `wall` (pared mínima entre carriles, 120–170). Mundo (4300–5200 × 2600–3200) y tema sorteados.
2. **Spanning tree** aleatorio (DFS) sobre la grilla `a×b` (`_spanningTree`) → **ciclo hamiltoniano** sobre la
   grilla de nodos `2a×2b` (`_hamiltonian`): cada room arranca como un loop CW de 2×2, y cada arista del árbol
   FUSIONA dos loops vecinos → queda un solo ciclo que pasa por las `4ab` celdas. (`ok` = es 1 ciclo de largo
   `4ab`.) `_cornersOf` deja sólo las esquinas (las curvas).
3. **Ancho — ESTILO sorteado, recortado a lo que entra, y a veces VARIABLE por recta**: `fit = (min(cellX,cellY) − wall)/2`
   es el medio-ancho MÁXIMO que deja `wall` entre carriles contiguos. Si `fit < 80` → `return false` (reintenta).
   Se sortea un estilo (`styles`: técnico 72–105 / normal 110–158 ×2 / ancho 165–235 ×2, sesgado a más ancho) →
   `half = max(72, min(ri(estilo), fit, margin−45))`. Con **prob 0.5** el ancho es VARIABLE: cada arista de la base
   (cada RECTA) sortea su propio medio-ancho `hw[i] ∈ [~0.42·fit, min(fit,235)]` → se combinan rectas anchas y
   angostas en la misma pista. Como TODO ancho ≤ `fit` y los carriles contiguos están a ≥ `cellX/Y`, **nunca se
   fusionan** (verificado). Resultado: calles anchas en grillas chicas, angostas en grandes, + variación intra-pista.
4. **Offset ±hw** (`_offset` acepta escalar O **array por-arista** = ancho variable; miter-clamp por vértice) →
   outer/inner; **`_isSimple(outer/inner)`** caza picos en curvas y carriles que se fusionarían → si falla, reintenta.
   (Verificado en Python: 4000/4000, ~1.3 intentos, half med≈147 [≤235], span intra-pista med≈83, 8–22 curvas.)
5. **PORTAL (wrap), prob 0.28, EJE sorteado**: se corta el loop con una línea LIMPIA en mitad de celda (lejos de
   esquinas) y se envuelve. Eje 0 = corte **vertical** (`c=margin+(g+0.5)·cellX`) → cruce HORIZONTAL, wrap X; eje 1 =
   corte **horizontal** (`c=margin+(g+0.5)·cellY`) → cruce VERTICAL, wrap Y. El corte sólo puede atravesar tramos
   RECTOS perpendiculares al borde (`|p[1−ax]−q[1−ax]|≈0`), con aberturas separadas ≥ `2·wMax+wall`. El loop es el
   MISMO (simple); se desplaza `−c` en el eje y se renderiza con copias `±W`/`±H` (`copies=[k=0,k=1]`, `tile`). Por
   construcción el cruce es RECTO, alineado en ambos bordes, sin auto-cruce. `TRACK_WRAP[idx]=wrap`; waypoints se
   envuelven (`mod W`/`mod H`) y la costura (salto > 1200) la saltan `pointBackAlong` y la IA. Verificado: 300/300
   aberturas alineadas en CADA eje (top/bottom para Y, left/right para X).
6. **Paredes**: `_ringWallsMulti(copies, …)` — el corredor se RECORTA a `[0,W]` antes del complemento (las copias
   del wrap salen del mundo). **Dibujo**: `drawCorridorCarve` (pared completa + CALA el corredor de cada copia,
   `destination-out`, + bevel). Colisión y dibujo salen de `smoothSample(outer/inner)` → coinciden.
7. **Waypoints**: `smoothSample(sBase, 70)` (el centro = el corner-loop hamiltoniano, desplazado/envuelto si hay
   portal); **largada** en un tramo recto (baja curvatura, NUNCA sobre la costura) → salida derecha. La META se
   dibuja PERPENDICULAR a la tangente del sentido de carrera (diagonal en curva) — `TrackPoint.draw` rota el damero.
   Su largo se **MIDE por RAYCAST** (`_raySeg`) perpendicular a CADA pared en la largada → `FINISH_ASYM[idx]=[dP,dM]`
   (asimétrico, acotado al lado opuesto `+50` para descartar rayos rasantes) `+14` → cubre TODA la calle aún en
   curva/ancho variable. Las pistas curadas no tienen `FINISH_ASYM` → usan `fl[0]` simétrico. También se dibuja en
   el **minimapa** (blanco + guiones negros, perpendicular en `wp[0]`). `BIG_VERTICAL` ya no se lee.

## Qué tocar según el pedido

- **Más/menos curvas**: rango de la grilla `a×b` (más celdas = más curvas). Hoy 2–4 × 2–3.
- **Banda más ancha/angosta**: la tabla `styles` (rangos por estilo) y/o `wall`. El `fit`-cap impide que se fusionen
  carriles aunque pidas más ancho (sube solo donde entra).
- **Más/menos ancho VARIABLE (rectas de distinto ancho)**: la prob `Math.random() < 0.5` y el rango `[~0.42·fit, min(fit,235)]`.
- **Más/menos portales / proporción de ejes**: la prob `Math.random() < 0.28` y el `ri(0,1)` del eje en `buildAutoTrack`.
- **Que llene más/menos**: `margin`.
- **Mundo más grande/chico** (permite grillas más grandes = más curvas): `regenAutoTrack`.
- **Mundo más grande/chico**: los `ri(43,52)*100 / ri(26,32)*100` de `regenAutoTrack`. El fondo horneado
  tiene un tope de memoria (`BG_MAX_PIXELS`, ~38MB): mundos más grandes se hornean a menor resolución
  (`bgK<1`) y se escalan al blitear — no rompe, sólo suaviza.
- **Perf**: `bands = H/32` en `_ringWallsMulti` (menos bandas = menos cuerpos).

## PORTALES (cruce de borde a borde) — ACTIVADOS (prob 0.28, eje X o Y), por CORTE LIMPIO del loop

La clave para que el portal sea siempre RECTO (perpendicular al borde, jamás en mitad de curva): NO se diseña
un corredor abierto; se reusa el loop hamiltoniano CERRADO (ya validado) y se lo **corta con una línea limpia +
se envuelve**. Como la base es rectilínea, una línea `c` en mitad de celda (perpendicular al eje sorteado) cruza
SÓLO tramos rectos perpendiculares al borde → el cruce es perpendicular por construcción, y como el loop sigue
siendo el mismo polígono simple, **no puede auto-cruzarse**. Eje sorteado: **X** (corte vertical → portal
horizontal, desplaza `−c` en x, copias `±W`) o **Y** (corte horizontal → portal vertical, desplaza `−c` en y,
copias `±H`). `_ringWallsMulti` recorta el corredor a `[0,W]`. Aberturas alineadas verificado 300/300 por eje.

El motor ya bancaba portales (wrap de tanques/bombas en X/Y a `[2795]`/`[1000]`, IA apunta "desenrollado" a `[848]`,
`pointBackAlong` salta costuras > 1200 a `[598]`) — estaba dormido; ahora `buildAutoTrack` lo prende a veces.
Para subir/bajar la frecuencia, tocá `Math.random() < 0.22`. El corte exige ≥2 cruces horizontales separados
≥ `2·half+wall`; si no encuentra uno limpio, el mapa queda sin portal (no se fuerza).

## Sumar una pista FIJA a la pool curada (opcional)

Agregá un objeto a `BIG_TRACKS` (`{name, theme, w, h, half, bands, base:[[x,y],…]}`) — el loop de
`BIG_TRACKS` la cablea (índices 10–14, aparecen en `TRACK_ORDER`). La `base` es el centro de la pista
(polígono no convexo, coords del mundo). Temas: 0 verde, 1 desierto, 2 nieve, 3 tecno, 4 lava.

## Verificación y checklist

- Cambiaste el generador → simulalo en Python primero (espejo de `_spanningTree`/`_hamiltonian`/`_cornersOf` +
  `_offset` + `_isSimple` + `smoothSample` + las primitivas de scanline `_cross/_pairs/_subtract/_union/_complement`):
  correr ≥1000 veces y medir **% válidos** (sin fallback), **intentos/válido**, **distribución de `half`** (que
  haya spread: angostas + anchas), **nº de curvas** (mín ≥ 3) y **tamaños de ciclo**. Para PORTALES: verificar que
  las aberturas del corredor en `x≈0` y `x≈W` están ALINEADAS en `y` y con el mismo conteo (recortando el corredor
  a `[0,W]` ANTES del complemento — `_complement` devuelve paredes fuera de `[0,W]`, no las confundas con bordes).
- [ ] Balance de llaves/paréntesis:
      `python -c "s=open('CrazyTanks/CrazyTanksWeb/index.html',encoding='utf-8').read(); print(s.count('{')-s.count('}'), s.count('(')-s.count(')'), s.count('[')-s.count(']'))"` → `0 0 0`.
- [ ] Server 200 + hard-reload en el celu. Correr varias carreras: mapas DISTINTOS cada vez (loops lisos,
      ondulados, zigzag, asimétricos), que llenen el mapa, vueltas que cuentan, largadas sobre tramo recto.

## Escenografía del infield (deco GRANDE por bioma, HORNEADA)

`drawScenery(track, ww, hh)` dibuja deco grande y reconocible sobre el INFIELD (la zona fuera del corredor):
parque (árboles/arbustos/flores), desierto (dunas/pirámides/cactus), nieve (muñecos/piedras), tecno
(edificios/cables), lava (lagos/ríos/brasas). Se llama DENTRO de `drawCorridorCarve`, sobre la capa de pared
`tc`, **ANTES** del `destination-out` → la escenografía que cae sobre la calle la borra el carve (calle limpia)
y el bevel tapa la costura. Es 100% horneado (costo/frame = 0). `getScenery`/`sceneryBase` + helpers
(`drawTree`, `drawPyramid`, `drawBuilding`, `drawLavaPool`, …) viven justo antes de la sección "MOTIVOS".
- **Más/menos deco por tema**: `SCENERY_DENSITY=[13,9,9,4.5,6]` (items por pantalla-equivalente; se escala por área del mundo).
- **Varía por mapa**: `TRACK_DECO_SEED[AUTO_TRACK]` se re-sortea en `regenAutoTrack`; `getDeco`/`getScenery`
  cachean por `.seed` (deco + escenografía nuevas cada generación, estables entre re-horneados/resize).
- **Contraste**: cada paleta está tuneada contra su infield (`THEME_WALL`). Si cambiás `THEME_WALL`/`THEME_FLOOR`,
  revisá que la escenografía siga despegándose del fondo.
- Sólo aplica al camino AUTOGENERADO (`drawCorridorCarve`); las pistas curadas (`drawSmoothCorridor`) no la usan.

## Notas de perf (ya aplicadas; no deshacer)

- Tanques: sprite-cache offscreen por (skin, estado) + culling fuera de cámara.
- **Paredes: `_mergeWallRects` fusiona tiras verticalmente contiguas (aristas dentro de TOL=6px) → ~16% menos
  cuerpos estáticos en Matter** (la físca con 16 tanques escala con la cantidad de cuerpos). El rect unido sólo
  CRECE (cubre cada tira) → la calle se angosta ≤6px, nunca abre hueco. Lo aplican `_ringWalls`/`_ringWallsMulti`.
- Paredes/waypoints NO van a `sprites` (viven horneados); debug F2 via `tp.debugDraw()`.
- Waypoint más cercano: búsqueda incremental (ventana ±7 alrededor del último, full-scan de fallback).
- Minimapa: paredes horneadas una vez por pista (`minimapWallsImg`, clave `mmKey`).
- Fondo: `BG_MAX_PIXELS` + `bgK` (cap de resolución del horneado para mundos grandes).
