---
name: crazytanks-level
description: Generate a new large, camera-scrolled race track for the CrazyTanks web port (CrazyTanks/CrazyTanksWeb/index.html). Use when the user asks to create/add/generate a level, track, map or "pista" for CrazyTanks, or wants a bigger track with the follow-camera. Designs the track by hand (walls + waypoints + finish line + start positions), wires it into all the data tables, and verifies counts.
---

# CrazyTanks — generador de niveles (pistas grandes con cámara)

Diseñás **a mano** una pista nueva, grande, que usa la cámara que sigue al jugador, y la cableás en
`CrazyTanks/CrazyTanksWeb/index.html` (archivo único, sin build). Después el usuario la prueba.

## Modelo de mundo + cámara (ya está en el motor)

- Cada pista vive en un **mundo de `W×H` unidades lógicas**. Default = pantalla `1280×720` (sin cámara).
- Una pista declara su mundo en **`WORLDS[track] = [W, H]`**. Si `W>1280` o `H>720` se activa la **cámara**:
  la ventana visible siempre es de `1280×720` unidades del mundo (mismo zoom de siempre) y **scrollea
  siguiendo al tanque del jugador**, clampeada a los bordes del mundo.
- **Tamaño recomendado:** entre `2000×1200` y `2560×1440`. **Tope `~3200×1800`** (el fondo se hornea a
  resolución de dispositivo; mundos enormes = mucha RAM). Mantené el **aspecto ~16:9**.
- **Coordenadas:** origen arriba-izquierda, `x→derecha`, `y→abajo`, en **unidades del mundo**.
  ⚠️ Los `xper(p)`/`yper(p)` valen `p*1280`/`p*720` (relativos a PANTALLA, no al mundo). Para pistas grandes
  usá **números crudos del mundo** o `W*frac`/`H*frac`. No uses `xper/yper` salvo para tamaños chicos fijos.

## Qué hay que agregar (todo indexado por `N = TRACK_NAMES.length` ANTES de agregar)

Editá en `index.html`, en orden:

1. **`TRACK_NAMES`** — `push('Nombre De La Pista')`. (`TRACK_COUNT` se recalcula solo → aparece en el selector
   de **carrera libre**; el torneo sigue usando sólo las pistas 0..9.)

2. **`WORLDS`** (objeto, cerca de los globals de cámara) — `WORLDS[N] = [W, H];`.

3. **`WALL_MAPS`** — agregar un elemento (array de rects `[x, y, w, h]` en coords del mundo):
   - **4 paredes de borde** que encierran TODO el mundo (grosor ≥ 16): izquierda `[0,0,16,H]`, arriba
     `[0,0,W,16]`, derecha `[W-16,0,16,H]`, abajo `[0,H-16,W,16]`. El tanque NO debe poder salir.
   - Paredes interiores que forman un **circuito cerrado** (un loop por el que se corre). **Grosor mínimo
     ~20** en cualquier pared (el tanque avanza ~12px/frame; paredes más finas se pueden atravesar).
   - El bioma/tema es `Math.floor(N/2)` → 0 verde, 1 desierto, 2 nieve, 3 tecno, 4 lava (se repite). El color
     de piso/pared y los motivos salen solos del tema.

4. **`TRACKPOINT_MAPS`** (dentro de `buildTrackpointMaps()`): el array `m` arranca con 10 sub-arrays; agregá
   `m.push([])` (o `m[N] = []`) y poblá los **waypoints `[x, y]` del centro de la pista, EN ORDEN de carrera**
   alrededor del loop. Espaciado parejo (~cada 40–90 unidades). La IA apunta al waypoint **8 adelante**, así
   que necesitás suficientes puntos y bien ordenados. **`waypoint[0]` = la línea de meta/largada.**

5. **`FINISHLINES[N]`** — geometría del damero de meta (se dibuja en `waypoint[0]`). Copiá la forma de una
   pista existente del mismo tipo de orientación y adaptá:
   - **Meta VERTICAL** (la raya corre en `y`): formato `[halfLen, bandW, ...]` → `fl[0]`=media-altura de la raya,
     `fl[1]`=ancho de banda. Si la usás, **agregá `N` a la lista de orientación vertical** en `TrackPoint.draw`
     (el array `[0,1,4,5,7,8,9]`).
   - **Meta HORIZONTAL** (la raya corre en `x`): NO agregues `N` a esa lista. `fl[0]`=media-longitud, `fl[1]`=alto.
   - En la duda, replicá el `FINISHLINES` y la orientación de la pista existente cuya largada se parece más a la tuya.

6. **`startposFor` → tabla `SP[N]`** — **4** posiciones de largada `[x, y, ang]` (una por tanque), justo
   **detrás de `waypoint[0]`**, mirando hacia la dirección de carrera (hacia `waypoint[1]`). `ang`: `0`=derecha,
   `Math.PI/2`=abajo, `Math.PI`=izquierda, `-Math.PI/2`=arriba (o un ángulo arbitrario). Separadas ~50 unidades,
   sin pisar paredes ni encimarse.

7. **`MAP_COUNTS[N]` = `[nWalls, nTrackpoints]`** — DEBEN coincidir EXACTO con el largo de los arrays de los
   pasos 3 y 4. (El juego instancia esa cantidad de `Wall`/`TrackPoint`.)

## Reglas de diseño (para que sea jugable)

- **Loop cerrado y bien ordenado**: los waypoints van en el sentido de carrera; el tanque que da la vuelta
  pasa cerca de cada uno. Sin esto, el conteo de vueltas y la IA se rompen.
- **Conteo de vueltas**: `lap_progress = waypointId / nTrackpoints`. Cruzar de ~95%→0% suma una vuelta. Por eso
  el loop debe ser continuo y `waypoint[0]` la meta.
- **Ancho de pista** cómodo: dejá pasillos de al menos ~6× el radio del tanque (el tanque ≈ 23px de lado).
- **Largada despejada**: las 4 posiciones de salida deben estar sobre la pista, detrás de la meta, sin paredes.
- **Encerrá el mundo** con las 4 paredes de borde (la cámara clampea, pero las paredes evitan que el tanque
  se vaya a zonas vacías).

## Checklist antes de terminar

- [ ] `MAP_COUNTS[N]` == `[WALL_MAPS[N].length, TRACKPOINT_MAPS[N].length]` (contá a mano).
- [ ] `WORLDS[N]`, `TRACK_NAMES[N]`, `FINISHLINES[N]`, `SP[N]` agregados (todos índice `N`).
- [ ] Si la meta es vertical, `N` está en la lista de orientación de `TrackPoint.draw`.
- [ ] 4 paredes de borde encierran el mundo; paredes interiores con grosor ≥ 20.
- [ ] Waypoints en orden de carrera, loop cerrado, `waypoint[0]` en la meta.
- [ ] Balance de llaves/paréntesis OK:
      `python -c "s=open('CrazyTanks/CrazyTanksWeb/index.html',encoding='utf-8').read(); print(s.count('{')-s.count('}'), s.count('(')-s.count(')'), s.count('[')-s.count(']'))"`
      (debe imprimir `0 0 0`).

## Probar

1. Asegurá el server (desde la raíz del repo): `python -m http.server 8080 --bind 0.0.0.0`.
2. Decile al usuario: **hard-reload**, entrar a **New Race**, en la opción **Map** elegir la pista nueva
   (es la última del listado), y correr.
3. Verificá con el usuario: la cámara sigue al tanque y scrollea; el HUD (ranking/cuenta) queda fijo;
   el conteo de vueltas avanza; no se atraviesan paredes; las largadas están bien orientadas.
4. Ajustá según feedback (tamaño del mundo, ancho de pista, posición de la meta).

## Notas

- Es **carrera libre solamente** (no entra al torneo, que usa las 10 pistas originales 0–9).
- El motor de cámara/mundo ya está implementado (`WORLDS`, `updateCamera`, blit de región, HUD con
  `translate(camX,camY)`). Vos sólo agregás DATOS de la pista; no toques el pipeline de render salvo el
  array de orientación vertical de la meta y, si hiciera falta, el tope de tamaño de mundo.
