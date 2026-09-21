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

- **Split lógica/render.** Cada peleador tiene DOS esqueletos de 14 puntos:
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
| puño (limb = mano) | pelvis → columna → hombro → brazo | `torso`, `chest`, `dx`, `dy`, brazo que pega | cabeza, brazo libre, piernas |
| patada (limb = pie) | pelvis → pierna | `lRu`, `lRl`, `dy`, `dx` | cabeza, `torso`, `chest`, **ambos brazos**, pierna de apoyo |

Las piernas **no** heredan el ángulo del torso ni de `chest`, por eso en una patada todo el tren
superior es libre. `dx` mueve la pelvis, o sea la raíz de TODAS las cadenas: siempre está atado.
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
- **Pie plantado = altura del piso ACTUAL.** Si `f.py` no coincide con la superficie que pisa el
  cuerpo, quedó de otra plataforma y se corrige de una (sin pasito). Con un solo nivel no se
  notaba; con varias alturas el pie se quedaba clavado a la altura vieja y terminaba POR ENCIMA
  de la pelvis. Ojo también: levantarse de un knockdown necesita `replantFeet()` explícito.
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
- **13 DOF** en `Float64Array` (orden en `J`), autorados mirando a la DERECHA; `facing` espeja en FK.
  Convención: cadenas "cuelgan" (0 = abajo, dirDown), torso apunta arriba. Rodillas: flexión = valores
  NEGATIVOS de `lLl/lRl`.

### Columna en dos segmentos (2026-09-21)

El torso era UN hueso rígido pelvis→cuello y eso topaba con todo: el cuerpo no podía encorvarse
(la rodada nunca fue una bolita — la distancia pelvis→cabeza era constante), los hombros no podían
girar independientes de la cadera, y no había con qué contrapesar. Ahora:

- Punto nuevo `P_.chest` (NP 13 → 14) a 42 % del torso; `B.spineLo` + `B.spineUp` = `B.torso`,
  con la suma hecha por RESTA para que sea exacta.
- DOF nuevos (NJ 11 → 13, **agregados al final** para no correr ningún índice existente):
  - `chest` = flexión del segmento superior. Cabeza, hombros y **ambos brazos** cuelgan de él, así
    que rotarlo gira el tren superior entero dejando la cadera quieta.
  - `dx` = desplazamiento lateral de la pelvis (en CH, espacio local). El torso se balancea SOBRE
    los pies plantados en vez de arrastrarlos.
- `J_LINEAR = [J.dy, J.dx]`: son LONGITUDES. En `springs` no se los envuelve con `wrapPi`.

**La propiedad que hizo segura la migración**: con `chest = 0` y `dx = 0` la FK devuelve
exactamente los mismos puntos que la versión de un solo hueso. Verificado con el probe: **0.000 px
en los 11 moves** antes de tocar ninguna animación. Cada pose se migró después, de a una.

**Qué DOF entra en la cadena de golpe** (ver la tabla de la regla de oro más arriba):

| DOF | puño | patada | por qué |
|---|---|---|---|
| `chest` | **atado** | libre | mueve el hombro, y el brazo cuelga del hombro |
| `dx` | **atado** | **atado** | mueve la pelvis, y de ella cuelgan hombro Y cadera |

Por eso los puños llevan los ángulos de brazo **re-resueltos por IK** en la clave de contacto y en
los pines: se elige el `chest` deseado y se recalcula el brazo para que la mano caiga en la MISMA
posición relativa a la pelvis (`probe_retarget.js`, error medido 0.00000 px). La solución es
analítica y fuerza el lado natural del codo —`l = +acos(...)`, que en este rig es siempre positivo—
porque elegir la rama por cercanía **invertía la articulación** (probado: el codo saltaba 12 px al
otro lado). Como el alcance total está fijo, avanzar el hombro obliga a acortar el brazo: por eso
los valores de contacto son modestos (el brazo queda al 96-98 % de extensión) y la rotación grande
vive en el wind-up y el recupero, que son zonas libres.

**Trampa del sampler por canal con `dx`**: definirlo en la carga y recién otra vez en el recupero
lo hace interpolar CRUZANDO la ventana activa (y mueve el golpe 1:1). Tiene que quedar clavado en 0
en la clave de contacto y en los dos pines. Costó 5-8 px de alcance hasta que se cazó.

**Hurtboxes**: `hurtboxes()` sigue usando la cápsula recta pelvis→cuello (no se partió en dos para
no tocar el combate). Con la columna doblada el pecho se sale de esa recta, pero poco: medido
1.1-1.6 px en las poses defensivas. Lo que sí importa es que el cuello se mueve al doblar el
torso, así que **las poses en las que te pueden pegar llevan `chest` acotado** (idle 0 exacto,
stance 0.06, block 0.07, crouch 0.09 → la cabeza se corre ≤ 7.8 px sobre un radio de 29). Las
expresivas van a fondo (ballRoll 0.95, getup 0.34) porque ahí o hay invulnerabilidad o el cuerpo
de verdad está plegado.

**Ragdoll**: `RAG_BONES` suma pelvis→chest y chest→neck, y los hombros cuelgan del chest (igual que
en la FK). El piso necesita el offset de reposo del punto nuevo. El torso ahora se dobla al caer
en vez de quedar como un palo.

**Rodadura del pie, SIN DOF nuevo**: el pie se dibujaba siempre horizontal (apoyar era estampar un
sello). `footRoll()` en `drawStick` deriva el ángulo de la pantorrilla y lo pesa por cuánto está el
pie despegado del piso: plantado = plano, en vuelo o pateando = en punta. Cero grados de libertad,
cero puntos. Se descartaron muñecas y tobillos como DOF reales: con `cam.frac = 0.11` el muñeco
mide ~80 px en pantalla y una mano son 4 px — a esa escala lo único que se lee es la SILUETA.
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

### Nivel generado por secciones + grafo de navegación (2026-09-21)

**El nivel se arma en cada partida** (`buildLevel(seed)` en `startMatch`, y después `bakeBg()` +
`bakeTerrain()` porque los bakes son world-space). `ARENA` es un objeto que se **muta**, no se
reemplaza: todo el resto del juego lo referencia por `ARENA.surfs` / `.exit` / … y no se enteró.

La variedad no sale de tirar plataformas al azar: son **8 secciones autoradas a mano** (escalera,
puente, arco de dos rutas, pirámide, zigzag, balcón, columnas, doble ruta) más la torre de salida,
y lo que varía es cuáles salen, en qué orden, con qué parámetros y si van espejadas. Medido sobre
300 niveles: 284 combinaciones distintas, mediana 20 plataformas.

**`NAV` es un grafo sobre las superficies** y lo usan DOS cosas:
1. La IA, para perseguir entre alturas.
2. El **generador, para validar**: si la salida no es alcanzable desde el piso, si alguna
   plataforma no puede volver al piso, o si alguna es una **isla** (sólo se cae en ella), la
   tirada se descarta y se genera otra. Medido: 0 fallos de cualquier tipo en 300 niveles.

Los enlaces salen de la **física real del salto**, no de constantes:
`alcanceSubiendo(rise)` resuelve el instante en que la parábola vuelve a bajar de `rise` y lo
multiplica por la velocidad de carrera (≈ 390 px para un salto al máximo, ≈ 540 al mismo nivel).
Con el `320` fijo que tenía antes, **281 plataformas en 300 niveles quedaban como islas**.
La tabla de próximo-salto es all-pairs por BFS inversa, calculada una vez por nivel (18 nodos,
324 entradas, 0.20 ms): en runtime la IA hace un lookup O(1).

### Navegación de la IA (`aiNavegar`)

Corre **antes** de DEFEND y devuelve `false` apenas comparten superficie: de ahí en adelante manda
el cerebro de combate de siempre, así que **los arquetipos pelean igual que antes** (medido:
TÉCNICO 19 puños/2 patadas, MATÓN el que más se pega a 0.32·CH).

- **El bug que arregla**: el aggro exigía `|Δy| < 2.2·CH` para engancharse. Con el jugador tres
  plataformas arriba, 0 de 4 enemigos llegaban y **los 4 se quedaban literalmente quietos**. Ahora
  la condición es que EXISTA UNA RUTA en el grafo; el radio horizontal (3.2·CH) no cambió, así que
  cada uno sigue cuidando su zona.
- **Salto PREDICTIVO**: no hay "saltar cuando estoy cerca de un punto mágico". Se resuelve la
  parábola real con la velocidad actual (y con la que ganaría acelerando en el aire) y se salta en
  el frame en que el aterrizaje cae dentro de la plataforma destino. Las versiones con
  anticipación fija por arquetipo fallaban 2 de 6 intentos y el resultado dependía del arquetipo;
  con la predicción son 6/6 en los cuatro, en ~4 s.
- **Bajar**: si el destino está justo abajo y la plataforma es one-way, mantiene ABAJO + salto
  (drop-through); si no, camina hasta pasar el borde y se deja caer.
- **Carril por enemigo** (`br.navLane`), acotado por el solape que banca el destino: sin él los
  nueve apuntaban al mismo punto de despegue, se empujaban con `separateBodies` y no subía
  ninguno. Sin el tope, el carril corría el despegue hasta 83 px y el salto no llegaba nunca.
- **Anti-atasco**: si no cambia de superficie en 2 s, se baja de donde esté y rehace la ruta desde
  el piso. Rompe cualquier ciclo de saltos.
- Costo medido: **0.3 µs/frame para los 9 enemigos** (un frame a 60 fps son 16 700 µs).

> Gotcha de QA: `startMatch()` genera un nivel AL AZAR. Para un test reproducible hay que fijar la
> semilla DESPUÉS de llamarlo, no antes (me pasó: comparaba dos builds sobre niveles distintos).
> Y pararse en la plataforma de la SALIDA completa el nivel y **congela la IA** (`game.state`
> deja de ser `'play'`), así que los escenarios de persecución usan la más alta que no sea ésa.
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
