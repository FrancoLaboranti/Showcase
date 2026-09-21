# StickFight

**Sandbox platformer-brawler** de stickmans articulados con estética Fancy Pants (papel beige +
sombras de hojas, terreno azul-piedra a tinta con rayones, personajes de tinta con pantalón naranja).
Recorrés un nivel con plataformas flotantes bajando enemigos a piñas hasta llegar a la SALIDA;
si te bajan, respawneás al inicio (los enemigos ya bajados quedan bajados). **Web-only** (como
DonkeyKong/Pacman): no hay `.py`, todo vive en [StickFightWeb/index.html](StickFightWeb/index.html).
Registrado en el Arcade (`landscape`).

> Ojo: nació como fighter 1v1 estilo MK (2026-07-22) y Franco lo pivoteó a sandbox (2026-07-23).
> La cámara sigue SOLO al jugador (`CFG.cam.frac` = alto del muñeco / pantalla ≈ 0.16, escala FPA);
> los enemigos son N instancias de `Fighter` con un cerebro (`newBrain()`) y radio de aggro c/histéresis.

## Arquitectura (lo no-obvio)

- **Split lógica/render.** Cada peleador tiene DOS esqueletos de 13 puntos:
  - `logicPts` = FK de `targetPose` (los keytracks nominales de los golpes) → **hitboxes**. Determinista:
    los resortes jamás alteran el frame-data.
  - `renderPts` = FK de `poseCur` (resortes críticamente amortiguados por articulación) + IK de piernas +
    mezcla de ragdoll → **dibujo y hurtboxes** (esquivar moviéndose esquiva de verdad).
- **Pose en 3 capas** (`buildPose`): (a) locomoción base computada del movimiento (lean por
  aceleración + lean por velocidad, poses de aire por vy — ley Fancy Pants: la animación se CALCULA,
  no se reproduce); (b) keytrack del ataque, overwrite enmascarado con peso; (c) aditivas (flinch,
  squash de aterrizaje, respiración).

### REGLA DE ORO para tocar animación de golpes

El alcance de un golpe lo define SÓLO la cadena de FK que llega al limb. Mirando `fk()`:

| golpe | cadena | joints ATADOS | joints LIBRES |
|---|---|---|---|
| puño (limb = mano) | pelvis → torso → hombro → brazo | `torso`, brazo que pega, `dy` | cabeza, brazo libre, piernas |
| patada (limb = pie) | pelvis → pierna | `lRu`, `lRl`, `dy` | cabeza, torso, **ambos brazos**, pierna de apoyo |

Las piernas **no** heredan el ángulo del torso, por eso en una patada todo el tren superior es libre.
Para lo atado hay tres recursos, todos verificados con el probe headless:

1. Claves de **anticipación** con `at <= startup − 0.033` (2 frames de colchón a 60 Hz): caen fuera de
   la ventana activa *y* fuera de la cápsula barrida del primer frame activo (que mira la pose del
   frame ANTERIOR — por eso el colchón, si no el barrido se alarga y el golpe alcanza más lejos).
2. Claves **PIN** en mitad y fin de la activa con los valores exactos de la curva vieja (los escupe
   `probe_moves.js`); a partir del pin, el recovery es territorio libre.
3. Aditivas con `safeAddW()`, que vale **exactamente 0** en toda la ventana activa (y 2 frames antes).
   Así van el hundido/empuje de `atkDrive`, la anticipación de despegue y el ciclo de aterrizaje.

Ojo con un cuarto camino silencioso: la **capa base** se filtra a los joints que la máscara no cubre.
`MASK_PUNCH` no incluye `dy`, así que cualquier cosa que la base le ponga a la pelvis mueve el hombro
y con él el alcance — por eso `baseLoco` usa `idlePose(tp, quiet)` durante un golpe (sin rebote de
guardia ni ruido, `dy` exactamente el de `POSES.idle`, como fue siempre).

### Por qué los golpes se sentían cortos (2026-09-21) — medir el RECORRIDO, no el alcance

Un golpe se lee como grande por lo que RECORRE el miembro, no por dónde termina. Medido con el
probe: el brazo mide 76 px y en el wind-up viejo la mano quedaba a **46 px del hombro, o sea el
63 % ya extendido**; la pierna mide 95 px y el pie del chamber quedaba a 65-78 px (rodilla casi
recta). Con esos números el jab sólo podía recorrer el 37 % que le quedaba: por eso parecía un
movimiento de muñeca, aunque la extensión final estuviera al máximo.

La causa de fondo no estaba en los keytracks sino en las **poses de espera**: `idle`/`stance`/
`block` tenían las manos estiradas hacia adelante en vez de al mentón. Todo golpe nace de ahí.

Arreglo: manos al mentón (25-36 px) y chambers de verdad (pie a ~30 px). Resultado medido:

| | recorrido | más recogido |
|---|---|---|
| jab | 77 → 124 px | 46 → 30 px |
| cross | 110 → 145 px | 39 → 20 px |
| roundhouse | 354 → 408 px | 65 → 28 px |
| spinkick | 373 → 442 px | 72 → 29 px |

**Lo que hace que esto NO sea un cambio de alcance**: el punto de contacto y el frame-data no se
tocan. Plegar más el wind-up alarga la cápsula barrida del primer frame activo *hacia el cuerpo*
(7-21 px), nunca hacia afuera — y esa zona ya estaba cubierta por el radio (`hitR` + hurt ≈ 46 px)
de la cápsula del frame de contacto, así que no habilita ningún golpe nuevo. El probe mide las dos
direcciones por separado: **`+ALCANCE` (crecimiento hacia afuera) ≤ +0.13 px en los 11 moves**.

Dos claves que NO se pueden tocar aunque estén antes del startup, porque su segmento entra en la
ventana activa: la de `0.07` del uppercut (gobierna 0.10-0.13, y la activa arranca en 0.10) y la
de `0.06` del sweep. En el sweep el chamber se movió a una clave nueva en `0.045` y la de `0.06`
volvió a sus valores originales; en el uppercut simplemente se dejó el brazo como estaba.

### Peso y footwork (dónde vive la transferencia de peso)

La pelvis no se puede mover durante un golpe sin mover el alcance, así que el peso se cuenta con los
PIES, que no están en ninguna cadena de hitbox:

- `atkWeight()` da la curva −1 (cargado atrás) → +1 (descargado adelante) → 0.
- `m.fw = {rear, front, heel}` la aplica como offset TEMPORAL sobre el objetivo del pie (nunca sobre
  `f.px`, así el plantado no se entera y no hay deriva). En una patada sólo existe la pierna de
  apoyo: ahí ese offset *es* la compensación de equilibrio.
- **Shuffle de root motion**: mientras el envelope del golpe empuja el cuerpo, los pies barren con él
  (`dampHL(f.px, stanceX, 0.055, dt)`). Sin esto el torso viajaba y los pies se quedaban: combo tras
  combo el muñeco terminaba cayéndose de punta. Medido con la métrica `desbalance` (pelvis adelante
  del punto medio de los pies): 0.30·CH antes → 0.17·CH ahora.
- `m.drive = {sink, rise, twB, twF}` es lo que la pelvis y el torso SÍ pueden hacer fuera de la activa.

### Locomoción procedural

- `runCycle()` calcula el ciclo entero de la fase de marcha: brazos contralaterales, antebrazo con
  retraso (`elbLag` = overlapping action), balanceo de torso al doble de frecuencia, cabeza que se
  nivela sola. **`CFG.run.armC/armA` están en ángulo de MUNDO**: los brazos son hijos del torso, así
  que se les descuenta la inclinación (`- tor`). Autorarlos relativos era justo lo que daba el
  corredor "llevando una bandeja" — cuanto más se inclinaba, más se le iban los brazos adelante.
- Rama **slide** de `feetIK` (`SLIDE_STATES` = derrape y dash): los pies NO se plantan, arrastran con
  el cuerpo en base ancha. Plantarlos mientras el cuerpo se va a 0.34·S es exactamente lo que daba el
  estirón de patas de araña.
- `idlePose()` mezcla idle ↔ `POSES.stance` según la cercanía del rival y le suma rebote de guardia.
  La diferencia entre `idle` y `stance` está casi toda en los BRAZOS **a propósito**: las hurtboxes
  salen de `renderPts`, así que bajar cabeza o pelvis en la guardia sería regalar/robar blanco.
- `airPose()` consulta `groundAt()` cuando `vy > 0` y mezcla hacia `POSES.airLand` al acercarse el
  piso: sin esa anticipación el salto se lee como una estatua volando.
- **Ciclo de marcha procedural** (`strideParams` + rama `gait` de `feetIK`, tuneable en `CFG.gait`):
  cada pierna alterna APOYO (el pie queda CLAVADO en el mundo — la fase avanza por distancia con
  ciclo = `2·half/duty`, así la derivada del pie en apoyo es exactamente 0 → cero patinaje) y VUELO
  (arco `sin(π·u)` con rodilla adelante vía IK). Zancada/duty/altura escalan con la velocidad.
  Antes había un sistema de "replantado por estiramiento" que parecía patas de araña — no volver a eso.
  `feetIK` corre TAMBIÉN con dt=0 (freeze de hitstop): si no, las piernas saltan a la pose FK cruda.
- **La tabla de semividas de resortes es el dial de "sueltitud"** (`CFG.spr`): el limb que golpea baja
  a `hStrike=0.02 s` durante los frames activos (converge al frame-data justo cuando pega); cabeza y
  mano libre van 1.4× más lentas (follow-through gratis).
- **Amortiguación por canal** (`CFG.spr.z*`, `springToZ`): 1 = crítico (llega y se queda); < 1 = la
  articulación se PASA del objetivo y vuelve. Sobrepaso = `exp(−zπ/√(1−z²))` de la distancia
  recorrida (0.62 ≈ 7 %, 0.55 ≈ 12 %). Sólo lo usan cabeza, mano libre y el limb en recovery; con
  z = 1 la función cae en el camino rápido de siempre (sin trigonometría).
- **El sampler de keytracks interpola POR CANAL** (`sampleMove`): para cada joint busca la clave
  anterior y la siguiente *que lo definen*. Antes elegía una "clave siguiente" global, así que meter
  una clave para la cabeza le partía el segmento a la pierna — o sea le cambiaba la trayectoria, o
  sea el hitbox. Con canales independientes se autora el tren superior de una patada sin rozar el
  arco del pie. Con los datos viejos da idéntico (todas las claves definían todos sus joints atados).
- **11 DOF** en `Float64Array` (orden en `J`), autorados mirando a la DERECHA; `facing` espeja en FK.
  Convención: cadenas "cuelgan" (0 = abajo, dirDown), torso apunta arriba. Rodillas: flexión = valores
  NEGATIVOS de `lLl/lRl`.
- **Gotcha de `ik2(bendDir)`**: con el y-abajo del canvas, rotar +θ es HORARIO visual → para que la
  rodilla apunte hacia adelante hay que pasar `-facing` (las piernas de `feetIK` ya lo hacen).
  Pasar `facing` da piernas de pájaro — ya pasó y Franco lo notó al toque.
- **`ik2Blend` mezcla el OBJETIVO, jamás los puntos resueltos.** El promedio de dos poses válidas no
  es una pose válida: interpolar codo y mano entre la solución FK y la IK estira los huesos (medido
  89 % de error en el brazo al soltar el borde en la trepada). Mezclando el objetivo, la cadena se
  resuelve una sola vez y los largos quedan exactos por construcción.
- **Root motion de golpes/dash**: `lungeVel()` devuelve VELOCIDAD instantánea — se suma en la
  integración (`x += (vx + rootVx)·dt`), **nunca** `vx +=` (acumularía y sale volando; ya pasó).
- **Ragdoll verlet** (13 partículas, constraints con rest tomado al activar) sólo en KNOCKDOWN/KO;
  el piso proyecta con offset de reposo POR PARTE (cabeza sobre su radio) — sin eso el cuerpo queda chato.
- **Hitstop por entidad**: `hitstopT` congela el `simDt` del par; el knockback queda `pendKb` y se
  aplica al DESCONGELAR.
- **Aturdimiento con degradación + recuperaciones pedidas** (`CFG.fight.stun*`/`kd*`/`airTechT`):
  antes cada golpe RESETEABA el stun al 100 %, así que un combo de 4 dejaba al jugador 2.39 s sin
  poder hacer nada (medido). Ahora:
  1. `stunDecay`/`stunFloor`: cada golpe seguido de la misma cadena aturde menos (análogo de
     `jugScale` para el daño). `hitChain`/`hitChainT` viven en el DEFENSOR.
  2. **Techeo aéreo** (`airTechT`): en LANZADO, salto/puño/patada devuelve el control. El
     knockback y el daño no se tocan; lo que se acorta es el rato sin poder reaccionar.
  3. **Ukemi al aterrizar**: si venís pidiendo algo al tocar el piso, caés RODANDO (0.38 s) en vez
     de knockdown + levantada (~0.6 s). Vale el botón sostenido o el del buffer: machacar funciona.
  4. **Levantada rápida** (`kdQuickT`) y **techo duro** (`kdMax`) por si el ragdoll no frena.
  La IA sostiene dirección en LANZADO/KNOCKDOWN, así que cobra el ukemi y la levantada rápida: el
  recorte no es sólo para el jugador. El techeo aéreo sí es del que apriete un botón.
  Medido: combo de 4 recibido pasa de **2.39 s → 2.15 s** pasivo, y **0.95 s** si te recuperás.
- **IA con percepción honesta**: lee snapshots de hace `reactionMs` (nunca el estado actual);
  arquetipos como filas de datos (`ARCHS`); la dificultad SÓLO escala reacción/bloqueo/drop de combos.
- `separateBodies`: clinch mínimo 0.24·CH — más corto que lo usual porque el uppercut llega apenas
  0.17·CH adelante; si lo agrandás, el uppercut del combo P,P,P deja de conectar.
- **Estilo**: paleta en `PAPER/ROCK/INK` (p07). El fondo son DOS bakes world-space horneados una vez:
  `bgCanvas` (sombras de hojas, parallax 0.45) y `terrainCanvas` (roca+tinta+rayones+puerta SALIDA,
  parallax 1). Nada aditivo en efectos: sobre papel claro el composite 'lighter' se lava a blanco.
- El tope de velocidad NO es drag-vs-accel: se acelera sólo por debajo de `maxRun` (con drag suave
  encima para la embalada del dash). Con drag débil el equilibrio quedaba 65% arriba del tope.

## QA headless (sin node)

Chrome headless + `--virtual-time-budget` NO dispara rAF de forma sostenida: **la sim queda congelada
aunque los timers corran**. El loop está preparado para bombearse a mano:

- `loop(t)` es global y `scheduleRaf()` tiene dedupe → un driver inyectado puede llamar
  `loop(qaNow += 16.7)` desde un `setInterval` sin duplicar la cadena rAF.
- Handle de debug: `window.SF = {P1, P2, CFG, game, cam, MOVES, POSES, ST, simT}`; `SF.simT` es el
  reloj de simulación acumulado — agendá acciones de test por `simT`, no por tiempo real.
- `dbgFreeze = true` congela la sim (sigue dibujando) → screenshot exacto del instante deseado.
- Patrón completo (cazador de errores + driver por escenario + status dump): el harness `qa.py` de la
  sesión 2026-07-22/23; escenarios útiles: menu/fight/run/skid/jump/jab/combo/kick/ko/hang/boxes.
- **`--virtual-time-budget` ni hace falta**: `loop(t)` se puede bombear SINCRÓNICAMENTE en un `for`,
  lo que hace los escenarios deterministas y rápidos. El driver tiene que manejar `keys` (teclado),
  **no** `inP1`: `pollInputs()` reescribe `inP1` entero en cada frame.
- Tres harnesses de la sesión de animación (2026-09-20), en el scratchpad:
  1. **probe de moves**: reconstruye la capa (b) de `buildPose` y muestrea la trayectoria del limb
     cada 1 ms → compara frame-data exacto, desvío dentro de la activa, **Hausdorff unilateral de
     la cápsula barrida** y, la métrica que de verdad manda, **`+ALCANCE`**: cuánto más lejos de
     la raíz llega el barrido nuevo. Positivo = el golpe llega más lejos (eso sí sería cambiar el
     alcance); ≤0 = sólo creció hacia el cuerpo, que es inofensivo. Corre a 60 y 30 Hz.
     También mide el **recorrido** del miembro y cuánto se pliega en el wind-up, que es el número
     que hay que mirar cuando un golpe "se siente corto".
  2. **harness de simulación**: ~30 escenarios guionados con validador por frame (finitud, largos de
     hueso, pie sobre pelvis, pie lejos del cuerpo, patinaje en apoyo, jerk, desbalance pelvis/pies,
     alcance real punta a punta). Corre a 16.7 / 33.3 / 50 ms.
  3. **tiras de fotogramas**: reasigna el `ctx` global y llama a `drawStick()` para pintar N poses en
     una grilla, y saca UNA screenshot. Es la única forma práctica de *ver* una animación acá.
- Ojo al comparar corridas: `Fighter` arranca con `this.T = rnd(0, 9)` (fase de respiración), así que
  escenarios donde un golpe conecta justo en el límite dan ±8 px de diferencia **entre corridas del
  mismo build**. Antes de culpar a un cambio, corré el mismo build dos veces.
- Teclas de debug en vivo: `T` panel de tuning (sliders sobre `CFG`), `H` hit/hurtboxes, `G` cámara
  lenta, `Y` dump de pose a consola; triple-tap en la versión del menú abre el panel en mobile.

## Gotchas

- Todo el DOM del juego está declarado ANTES del script principal (gotcha TankWARSWeb); el script de
  cola (info/FPS/mute) va después de `arcade-shell.js`.
- El trío de context-loss invalida `bgCanvas`, `skyGrad` y `_glowCache` — si agregás un bake nuevo,
  sumalo ahí (los sprites de chispas guardan la ref en la partícula: se regeneran vía cache Map).
- Los tiempos de los keytracks (`poses[].at`) son ABSOLUTOS dentro del move y el sampler arranca
  desde `atkPose0` (la pose real al iniciar el golpe) — una pose parcial sin una clave "sostiene" el
  último valor definido.
