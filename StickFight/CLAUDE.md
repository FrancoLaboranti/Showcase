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

### Proporciones: hombros, cuello y cabeza (2026-09-21b)

El torso se veía *por debajo* de la cabeza. Medido sobre un retrato de 16 poses: el hombro estaba a
**0.23·CH** sobre la pelvis y la base de la cabeza a **0.382·CH** → **0.152·CH de cuello pelado, el
15 % de la altura del personaje**. Encima la camisa se cerraba en PUNTA a la altura del hombro, así
que los brazos parecían salir del cuello.

El hueco se repartió en tres movimientos chicos, porque cada uno tiene su costo:

| | antes | ahora | costo |
|---|---|---|---|
| `B.torso` | 0.30 | **0.31** | sube el hombro ⇒ sube el punto de impacto de los puños |
| `B.neck` | 0.08 | **0.022** | — |
| `B.headR` | 0.10 | **0.108** | mueve la hurtbox de la cabeza |
| `B.shoDrop` | 0.07 | **0.04** | sube el hombro |
| hombro sobre pelvis | 0.23 | **0.27** | |
| cuello pelado | 37 px | **16 px** | |

Tres arreglos más, todos de dibujo:

1. **La camisa termina en una LÍNEA DE HOMBROS** (`wSho = 0.088·CH`), no en pico, con silueta cónica
   (`wChest 0.068`, `wWaist 0.046`), cintura levantada a la cadera y **esquinas redondeadas con
   `arcTo`** — con vértices filosos el hombro de atrás salía en punta cada vez que el torso se
   inclinaba, porque el ancho es perpendicular a la columna.
2. **El cuello se dibuja ANTES de la camisa.** Dibujado después, su cap redondo mordía el escote y
   dejaba un manchón de piel sobre el pecho (se veía en las 16 poses).
3. **La cabeza pivota en el ATLAS**, no en la base del cuello (`fk()`). Antes el DOF `head` giraba
   cuello+cabeza desde abajo con una palanca de 0.13·CH: al mirar hacia abajo (agacharse, encajar un
   golpe) el cuello se veía estirado en diagonal. Ahora el cuello sigue la columna alta y sólo el
   cráneo rota, con palanca `B.headR`. **Con `head = 0` el punto es idéntico** (los dos tramos son
   colineales), así que no hay migración de poses. El atlas es un punto DERIVADO en `drawStick` (no
   se agregó a `P_`: ni `NP` ni el ragdoll cambian).

**Qué le costó al combate** (medido, ver más abajo): los puños caen **8-10 px más arriba** porque el
hombro subió; el **alcance horizontal es idéntico** (≤ 0.79 px en los 11 moves, y ése es el
uppercut, que es vertical). El `lunge` era el único golpe plano y perdía alcance real contra
agachados (0.66 → 0.50 CH), así que **hunde la cadera esos mismos px durante el golpe**
(`MASK_PUNCH_DY`, `dy` autorado en sus 7 claves): puño exacto donde caía, brazo igual de estirado.

#### Lo ÚNICO que el cambio de proporciones le movió al combate

Matriz `probe_conecta.js`, determinista, 1430 celdas, HEAD vs ahora: **21 celdas distintas
(8 ganadas, 13 perdidas) — el 1.5 %**. Un paso de la matriz son 0.055 CH ≈ 13.5 px.

| golpe | blanco | alcance máx (CH) |
|---|---|---|
| jab · cross · airpunch | agachado / bloqueo bajo | −0.055 |
| cross | de pie | **+0.110** |
| hook | de pie | **+0.055**; bloqueo bajo −0.110 |
| uppercut | agachado | mismo alcance, un hueco interno |
| lunge | bloqueo alto / bajo | −0.055 |
| sweep | bloqueo alto −0.055 · bloqueo bajo **+0.055** |
| spinkick | bloqueo bajo | **+0.055** |
| roundhouse · dropkick · airkick | todos | **sin cambios** |

La causa no es el puño sino el **defensor**: su hurtbox de cabeza bajó ~10 px con las proporciones
nuevas. Por eso también se mueven filas de patadas cuyo contacto es idéntico al píxel.
Se evaluó y se DESCARTÓ compensarlo agrandando `CFG.fight.hurtHead` un 8 % (subiría el radio sólo
2.4 px y agrandaría el blanco en todos los demás cruces).

**Los combos no cambiaron** (`probe_combo.js`, 4 cadenas × 16 distancias): mismo número de golpes
conectados y mismo daño total en todas las celdas, salvo que tres cadenas mantienen su cuenta alta
UN paso más lejos. Nada perdido.

### Empalme entre estados (2026-09-21b)

`targetPose` pegaba **saltos de hasta 2.37 rad en UN frame** al cambiar de estado (medido sobre 18
escenarios: `idle→jump` 2.37 en `aRu`, `idle→dash` 2.01, `run→jump` 1.98, `skid→run` 1.95,
`fall→idle` 1.90). El resorte los absorbe, pero un ESCALÓN en el objetivo hace que arranque con
aceleración máxima: eso es lo que se sentía como "empieza de golpe".

`buildPose` cruza ahora el objetivo con `smoothstep` desde la última pose del estado anterior
(`CFG.anim.blendT = 0.075 s`): llega a lo mismo, en el mismo tiempo, pero con derivada nula al
empezar y al terminar. **Nunca durante un ataque** — ahí `targetPose` ES el frame-data, y el probe
confirma 0.000 px de diferencia. Medido después: **máximo 0.46 rad** (−81 %).

Dos cosas más de la misma tanda:

- **`dirN` continuo** en `runCycle`. Valía ±1 y saltaba de −1 a +1 al cruzar `vx = 0`: al cambiar de
  sentido el torso invertía su inclinación de golpe (y con él los brazos, que se autoran en ángulo
  de mundo). Ahora cruza el cero de forma continua.
- **HITSTUN tiene pose propia** (`hurtPose`). No tenía rama en `baseLoco`: caía en `idlePose()` y el
  único registro del golpe era la capa de flinch. Los BRAZOS cuentan ahora el impacto — y los brazos
  **no son hurtbox** (`hurtboxes()` usa cabeza, pelvis→cuello y pelvis→pies), así que no mueve ni un
  píxel de caja de daño. Además HITSTUN entró en `IK_STATES` y en **`SLIDE_STATES`**: antes las
  piernas salían de FK pura y los pies viajaban con el cuerpo mientras te empujaban (medido
  4.83 px/frame, el peor de todos los estados controlables). Va en el arrastre y no en el plantado
  a propósito: clavarlos con el cuerpo yéndose ES el estirón de patas de araña.

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

La variedad no sale de tirar plataformas al azar: son **14 secciones autoradas a mano** más la
torre de salida, y lo que varía es cuáles salen, en qué orden, con qué parámetros y si van
espejadas. Al repertorio original (escalera, puente, arco, pirámide, zigzag, balcón, columnas, doble
ruta) se sumaron seis patrones en 2026-09-21b: **solapadas** (dos losas que se pisan en x: se pasa
por abajo o por arriba), **bifurcacion** (dos ramas que salen del mismo rellano y reconectan),
**saltitos** (cadena de plataformas chicas, saltos encadenados), **islote** (plataforma alta con una
sola entrada), **pozo** (sector compacto: dos paredes de repisas y una tapa) y **voladizo**
(asimétrica: una losa larguísima y un muñón corto arriba).

#### Etapas de dificultad (2026-09-21b)

`game.nivel` crece al llegar a la SALIDA (`siguienteNivel()`, cura 45 %) y la etapa sale de
`etapaDe(nivel)` — **dos niveles por etapa**. La dificultad es ESTRUCTURAL: no toca daño, vida,
velocidad ni el cerebro de nadie.

| etapa | niveles | patrones | `wK` | `gap` | torre |
|---|---|---|---|---|---|
| INICIAL | 1-2 | 5 | 1.14 | 296-372 | 5 |
| INTERMEDIA | 3-4 | 9 | 1.00 | 304-384 | 6 |
| AVANZADA | 5-6 | 13 | 0.90 | 312-396 | 7 |
| EXPERTA | 7+ | 14 | 0.82 | 322-408 | 7 |

`wK` escala el ancho de cada plataforma (piso 0.62·CH): más avanzada = menos superficie donde caer
y por lo tanto huecos efectivos más grandes, **sin mover un solo salto de sitio**. Medido sobre 200
semillas por etapa: ancho mediano **297 → 275 → 252 → 231 px**.

**`secs` NO es una palanca**: el ancho de arena (8000 px) corta antes que el contador. Con `secs = 7`
el generador truncaba en silencio y EXPERTA salía MÁS corta que AVANZADA. Va alto a propósito (8)
para que el nivel llene la arena siempre y el largo no dependa de la etapa.

**El ancho total de una sección se DERIVA** de sus plataformas (`max(dx + w)`), ya no se autora a
mano: autorarlo era la fuente de los solapes raros al espejar.

`buildLevel(seed, nivel)` es reproducible: misma semilla + mismo nivel ⇒ misma geometría
(verificado 32/32, ensuciando el estado entre las dos tiradas). `armarNivel(semilla)` y
`startMatch(semilla)` aceptan semilla opcional — es lo que usa el QA.

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

Sondas nuevas de 2026-09-21b (todas en el scratchpad, se inyectan antes de `</body>`):

- **`probe_conecta.js`** — matriz ¿CONECTA? de 11 golpes × 5 estados del blanco (de pie, agachado,
  bloqueo alto, bloqueo bajo, en el aire) × 26 distancias = 1430 celdas. Es la única prueba que
  mide el ALCANCE EFECTIVO en vez de la geometría. **Ojo con dos trampas que costaron una corrida
  entera**: (a) el blanco hay que clavarlo en x ABSOLUTO — re-anclarlo a `P1.x` lo hace perseguir
  al atacante por el root motion y la distancia miente; (b) `this.T` (reloj de respiración) nace en
  `rnd(0, 9)`, así que sin fijarlo la matriz no es reproducible **ni contra sí misma** (medido:
  9 filas distintas entre dos corridas del mismo build). Con `P1.T` y `E.T` fijos: 0 filas.
- **`probe_continuidad.js`** — mide, no asume: salto de `targetPose` en cada cambio de estado, jerk
  por joint, patinaje de pie plantado POR ESTADO, desbalance pelvis-vs-apoyo, articulación del
  torso. Hay que descartar una ventana de ~6 frames después de cada teleport del propio test
  (`resetFighter` pisa `poseCur` de golpe: sin filtro el jerk y el patinaje no miden nada).
- **`probe_niveles.js`** — reproducibilidad, barrido de 200 semillas × 4 etapas, repertorio de
  patrones por etapa, persecución de la IA por etapa y progresión de partida (8 niveles seguidos).
- **`probe_humo.js`** — 6 minutos de partida real con input pseudo-aleatorio reproducible: NaN,
  estados fuera del enum, hp fuera de rango, peleadores fuera del mundo, pies sobre la pelvis.
- **`probe_huesos.js`** / **`probe_retrato.js`** — retratos grandes con y sin las articulaciones
  marcadas encima. Para juzgar proporciones no alcanza con los números: hay que mirar.
- **`ejes.py`** — descompone el cambio de un golpe en EJES. `compare.py` mide `+ALCANCE` **radial**
  desde la raíz, así que subir la mano 9 px le da +5.5 px aunque el alcance horizontal no cambie.


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
