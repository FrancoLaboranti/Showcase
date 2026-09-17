# LOOP

**Arena arcade roguelite** nacida de cruzar las mecánicas del resto del repo en un solo
juego nuevo (no es un hub ni una recopilación). **Web-only** como DonkeyKong/Pacman/StickFight:
no hay `.py`, todo vive en [LoopWeb/index.html](LoopWeb/index.html) (~4090 líneas).
Registrado en el Arcade como `landscape`, acento `#7df9ff`. **UI enteramente en inglés**
(el juego se llama LOOP); los comentarios del código siguen en español.

Sos una **canica** que arrastra un **hilo de luz** por la **esfera de un reloj**. El hilo
desvía orbes como una paleta de Pong; cruzarlo consigo mismo **cierra un bucle** y detona
todo lo que quedó encerrado. Los enemigos son piezas de ajedrez que telegrafían su carril,
la aguja del reloj marca las oleadas, y cada hora elegís **una sola cosa, alternando**:
una **regla** para la arena o una **carta** (las 5 equipadas forman una mano de póker).

## Pasada MOBILE (2026-09-16) — medir antes de tocar

Franco reportó FPS bajos en teléfono. Lo primero fue un **perfilador**, no una corazonada:
`s_prof.py` envuelve cada función del render y atribuye las operaciones de canvas caras contando
los contadores antes y después de cada llamada. (Los TIEMPOS no sirven en headless — el
virtual-time congela `performance.now()` — pero los CONTEOS son objetivos: 24 clips por frame son
24 clips en cualquier lado.)

El perfil dijo algo que ninguna intuición habría dicho: **`drawEnemy` era el 43,6 % del render**, y
buena parte de eso era el `clip()` del bisel que había metido la pasada de arte. Segundo lugar
inesperado: casi todos los `fill` de `drawEnemy` **no eran la pieza sino su sombra**.

Resultado, misma escena (14 piezas, 8 orbes, hilo de 109, 14 minas):

| | antes | después |
|---|---|---|
| peso total | 459 | **172** (−62 %) |
| `clip` | 16,9 | **4,0** |
| `fill` | 154,8 | **57,0** |
| `stroke` | 147,8 | **66,7** |
| gradientes | 30,0 | **8,2** |

### El principio: lo que se ve igual en todos los frames se dibuja UNA vez

Ninguna de las correcciones baja la calidad — son la misma imagen con menos operaciones.
`bakeSprite(key, half, dibujar)` (en `p03_engine`) es el único lugar donde se hornea.

- **Piezas**: una pieza siempre se ve igual y sólo tiene cuatro estados de color (propio, flash
  blanco, frenesí azul, frenesí titilando). Horneada, un `drawImage` reemplaza cuatro fills, tres
  strokes, un gradiente y un clip. **La sombra de contacto va DENTRO del sprite** (era constante
  para todo lo que no salta). El caballo queda afuera: su sombra depende del salto.
- **Casco del tanque**: no rota, sólo la torreta. Horneado se van los últimos clips del render.
- **Orbes y cabezas de obús**: mismo criterio.
- **Lo que NO se hornea**: lo que rota (moto, aguja) o lo que mira (los ojos del fantasma). Un
  sprite rotado gira su propio brillo, y eso rompe la regla de la luz clave fija.

**`resize()` tiene que vaciar los cachés** (`clearBakes`): todo lo horneado depende de PXR, y si no
crecen sin techo y encima quedan a la escala vieja.

**Un gradiente cacheado guarda COORDENADAS.** Los de la aguja viven en espacio local, así que sólo
dependen del ángulo de la luz contrarrotada: cuantizarlo en 32 pasos (11° de escalón, invisible en
algo que da una vuelta por hora) los saca del frame. Se vacían en el mismo `clearBakes`, y se
declaran **en el mismo archivo** que su limpieza: `typeof` NO protege contra el TDZ de un `const`.

### Otras dos que valen para cualquier canvas

- **Hoisting de `clip`.** `drawSectors` recortaba contra el MISMO círculo una vez por sector (nueve
  por frame), y la telegrafía de las piezas una vez por pieza que apunta (~16 por frame). Los dos
  pasaron a un solo clip afuera del bucle. Efecto lateral bienvenido en la telegrafía: las piezas
  quedan siempre por encima de los carriles.
- **Lotes por alfa.** Las celdas de mina encendidas del todo comparten alfa, así que sus filos se
  acumulan en un path. **OJO CON EL ORDEN**: la primera versión trazaba los filos en lote ANTES de
  los rellenos y el propio relleno se los comía. Van tres pasadas: rellenos, filos en lote, y
  las que se están apagando una por una.
- **`arc` de 1-3 px → `fillRect`.** En aditivo y en movimiento son el mismo pixel, pero `arc` hay
  que teselarlo. Las chispas grandes siguen redondas.

### Escalón táctil

`CFG.perf.sparkMul` (0.62 en táctil) es el ÚNICO lugar donde se baja algo. No toca resolución ni
saca efectos: baja la cantidad de partículas de un efecto aditivo, donde veinte y treinta se ven
casi igual y la diferencia la paga el relleno de píxeles — justo lo que escasea en un móvil.

## Layout VERTICAL: dos bugs que sólo aparecen en teléfono

Toda la sesión se revisó a 1280×720 y 1920×1080. A 500×905 aparecieron dos cosas que en apaisado
no se ven, y ninguna la detecta el QA de invariantes — hay que MIRAR:

- **La línea de racha caía encima de la placa siguiente.** En vertical `panelRects` apila las
  placas con `gap = H*0.016`, pero abajo de cada una se dibuja la racha en `b.y + b.h + S*0.026`.
  El hueco entre placas **no es decorativo**: tiene que dejar lugar a lo que se dibuja ahí.
- **Los naipes del draft usaban el 63 % del ancho.** `cw = min(W*0.19, S*0.25)`: en desktop manda
  el tope `S*0.25` y no se nota, pero en un teléfono (donde `S == W`) mandaba el `0.19` y los
  naipes quedaban chicos, con el texto del efecto ilegible y 37 % del ancho sin usar. Subir el
  factor a `0.26` sólo cambia las pantallas angostas.

**Moraleja de método**: un `min(fracción_de_W, fracción_de_S)` se comporta distinto según cuál de
los dos manda, y en apaisado manda uno y en vertical el otro. Cada vez que aparezca ese patrón hay
que preguntarse cuál gana en cada orientación.

### Trampas al verificar mobile en headless

- **Chrome headless tiene un ancho mínimo de 500 px.** Pedir `--window-size=390,...` da una captura
  de 390 px pero la página reporta `innerWidth = 500`: el layout se calcula para 500 y la captura
  muestra 390, así que todo aparece corrido y cortado. Parece un bug de centrado y no lo es. Usar
  500 o más (500×1000 es proporción de teléfono real).
- **Sacar `body.noTouch` no vuelve táctil al navegador.** `IS_TOUCH` es una constante de JS y sigue
  en falso, así que se dibujan los anillos de recarga del canvas (que en táctil están detrás de
  `if (!IS_TOUCH)`) Y además aparecen los botones DOM: se ve una superposición que **en un teléfono
  real no existe**. Me hizo perseguir un bug inexistente.

## MOVIMIENTO vs SELECCIÓN — el joystick se comía los taps

`#jMove` es un div fijo de **52 % × 84 %** con `z-index: 3` sobre el canvas, y sólo se ocultaba con
`body.inMenu`. Durante `rule`/`card`/`slot` seguía vivo: **tocar la carta de la izquierda creaba un
joystick y la selección nunca llegaba al canvas.**

La solución NO es achicar el joystick (empeora el control, que es lo que se quería arreglar): es
apagar las zonas táctiles cuando la pantalla es de SELECCIÓN (`body.picking`, sincronizada por
`syncTouchUI()` una vez por frame y escrita **sólo cuando cambia**). Mientras elegís no hay nada
que mover, así que el dedo sólo puede significar una cosa.

Detalle que hay que acordarse: si la zona se oculta con el dedo apoyado, el navegador **no manda
`pointerup`** y la palanca queda pegada. Por eso `moveStick.soltar()`.

El escenario `touchsel` lo prueba con `document.elementFromPoint` sobre el centro de cada elemento
seleccionable. **Tiene que sacar `body.noTouch` primero**: en headless `IS_TOUCH` es falso, las
zonas están ocultas de todos modos, y el test pasaría trivialmente sin probar nada.

## La palanca manda VELOCIDAD, no aceleración

```js
const ax = (inP.mx / mag) * accel;   // ax * mag = mx * accel
P.vx += ax * mag * dt;               // y el tope es maxS SIEMPRE
```

Escalaba la ACELERACIÓN: con el stick al 30 % igual terminabas a velocidad máxima, sólo que
tardando más. En un analógico eso es **no tener control fino**. Ahora `mag` es la fracción de
velocidad y la velocidad se acerca al objetivo con `CFG.player.respHl`.

Dos cosas de una: el 30 % es el 30 %, y arrancar, frenar y doblar cuestan lo mismo (antes invertir
el sentido eran 0,88 u/s frenados a 4,6 u/s² = **0,34 s arrastrándose en la dirección equivocada**,
que era exactamente la sensación que Franco describió como "se arrastra").

Medido por el escenario `feel`:

| | antes | después |
|---|---|---|
| arranque al 90 % | 0,172 s | **0,117 s** |
| frenado al 10 % | 0,282 s | **0,133 s** |
| inversión al 80 % | 0,344 s | **0,150 s** |
| palanca al 50 % | 100 % de velocidad | **50 %** |

Queda física: es un acercamiento exponencial, no un teletransporte de velocidad. Lo que se fue es
la inercia residual, no el peso.

## Cómo se edita este archivo de 5500 líneas

**`LoopWeb/index.html` es la fuente de verdad y lo único que hay en el repo**, igual que el resto
de los ports: un archivo autocontenido, sin paso de build. Pero editar a mano un HTML de ~5500
líneas es insostenible, así que durante las sesiones largas se parte en trece archivos
(`p01_head.html`, `p02_core.js`, … `p13_tail.html`) en un directorio temporal, se parchea ahí y se
reensambla con un `cat` en ese orden.

**Esos `parts/` NO están versionados y no sobreviven a la sesión.** Cuando esta guía los menciona,
habla de esa copia de trabajo, no de algo que vayas a encontrar en el repo. Para retomar: volvé a
partir `index.html` por los comentarios de sección, o editá el monolito directo.

Dos cosas que ese flujo enseñó y conviene repetir:

- **Los parches se aplican con un helper que afirma que el ancla existe Y es única** (`sub()` en
  Python), nunca con un reemplazo a ciegas. Un ancla ambigua que pisa la ocurrencia equivocada es
  el error más caro de todos porque no falla: compila y hace otra cosa.
- **Antes de aplicar, correr el parche contra una COPIA de las partes.** Así se cazó que
  `wantPointer(false)` colgado de la cadena de `else if` se tragaba las pantallas de muerte y
  victoria — el juego nunca llegó a tener ese bug.

## De dónde salió cada cosa

| Origen | Qué aportó | Dónde vive |
|---|---|---|
| Pong · Balls · MiniBalls | El hilo **desvía** orbes; solver de impulso elástico | `threadDeflect`, `resolveOrbPair` |
| Tron · Snake | El rastro como **objeto persistente** con presupuesto de largo | `thread[]`, `pushThreadPoint` |
| Newton's Cradle | La carga **se contagia** en cadenas de orbes; péndulos con Verlet | `resolveOrbPair`, `updatePendulums` |
| Ajedrez | Enemigos que se mueven por reglas de pieza, con carril telegrafiado | `ETYPES`, `pickLane` |
| Ta-Te-Ti | Sectores 3×3 que se reclaman encerrándolos; tres en línea = frenesí | `claimSectorsIn`, `checkTateti` |
| Póker | Las 5 cartas equipadas se evalúan como una mano | `evalHand`, `recomputeStats` |
| Buscaminas | Minas ocultas; el hilo **revela** las celdas y sus números | `seedMines`, `revealCell` |
| Simón Dice | Secuencia de sectores que se "toca" **recorriéndolos** | `updateSimon` |
| Pac-Man | Fantasma con objetivo tipo Pinky; frenesí comestible | `updateGhost`, `startFrenzy` |
| Tank Wars | Tanque con obuses **devolvibles** con el hilo; escudo con espera | `updateTank`, `updateShells` |
| Crazy Tanks | `createJoystick` hand-rolled; reglas como objeto de multiplicadores | `createJoystick`, `RULE` |
| Fuegos Artificiales | Muertes que estallan; la regla PIROTECNIA | `killEnemy`, `updateFlares` |
| Reloj | **La aguja ES el temporizador de oleada** y una paleta física | `updateClock` |
| DonkeyKong | Draft de modificadores; seeds derivadas; combos con ventana | `openRuleDraft`, `mulberry32` |
| StickFight | Estructura del archivo, audio con `voice()`, shell del Arcade | todo el esqueleto |

## Arquitectura (lo no-obvio)

- **Espacio mundo, no píxeles.** La arena es un círculo de **radio 1** centrado en (0,0);
  la pantalla se deriva al dibujar con `sx()/sy()/sr()`. A diferencia de `sper/xper` del
  resto del repo, **un resize no toca un solo número de la simulación** — que es lo que
  permite guardar ~200 puntos de hilo sin reescalarlos nunca.
- **El hilo es una SOGA simulada, no una pintura** (`layThread` + `simThread`, 2026-09-14).
  Franco: *"mejoraría MUCHÍSIMO con un movimiento mejor del hilo"*. Cadena Verlet con
  **fricción por edad** (`CFG.rope`): un punto fresco desliza y hace látigo detrás de la
  canica; uno viejo se clava. El último elemento del array es siempre la **cabeza, clavada a
  la canica**; los puntos se siembran a **paso fijo** entre el último apoyado y la cabeza (antes
  un tirón los dejaba 10× más separados). Presupuesto de largo = puntos × paso.
- **Cada punto tiene un ANCLA (`ax, ay`) = dónde fue apoyado, y vuelve ahí al asentarse.**
  Sin ancla la soga acorta las curvas por adentro y la cabeza **nunca vuelve a cruzarla: cero
  bucles** (medido con el bot). Con ancla hace látigo ~0.5 s y después se asienta EXACTO sobre el
  camino real, así la geometría del bucle es la misma que antes (área máx del bot idéntica).
  Ojo: **se siembra desde el ancla del último apoyado, no desde su posición actual**, o las
  anclas trazarían el atajo en vez del camino.
- **Los golpes patean la soga de verdad** (`kickThread`): desplazan los puntos del segmento y
  Verlet lo convierte en velocidad; la onda viaja sola y el ancla la devuelve. Reemplaza al
  viejo "ripple" senoidal sintético. `hitT` quedó sólo para el brillo.
- **Cierre de bucle** = intersección del tramo recorrido este frame contra el hilo viejo
  (`findSelfCross` → `segSegT`), salteando el tramo más nuevo. Sin ese salteo, girar fuerte
  cierra "bucles" de dos píxeles. **El salteo se mide en DISTANCIA (`CFG.thread.skipDist`),
  no en cantidad de puntos**: durante un tirón los puntos quedan 10× más separados, y contarlos
  dejaba ciega justo la línea recta que el tirón acaba de dibujar — que es con la que querés cerrar.
- **La regla de balance central**: `tight = sqrt(0.17 / area)` ⇒ **bucle chico = daño,
  bucle grande = puntos**. Sin eso el juego sería "barré la cancha con un círculo enorme"
  y no habría skill. Si tocás esto, tocás el juego entero.
- **Colisión orbe↔hilo BARRIDA** (`threadDeflect`): se testea el tramo recorrido contra el
  segmento, no la posición puntual. A 2 u/s un orbe avanza 4 radios en un frame lento.
- **Dos familias de enemigo y nada más**: deslizantes (`fam:'s'`, esperan → telegrafían un
  carril → embisten) y libres (`fam:'f'`, tanque y fantasma). El jefe es `fam:'b'`.
  Agregar un enemigo = una fila en `ETYPES`.
- **Armadura del jefe**: `hurtEnemy(..., src)` divide el daño por 3 salvo `src === 'loop'`.
  El clímax obliga a usar el verbo central del juego.
- **UNA regla por vez, no apiladas** (`hourRule`). Antes se acumulaban toda la run y para la
  hora 7 tenías péndulos + minas + espejo + resonancia + pirotecnia a la vez. Franco lo dijo
  textual: *"en cierto punto no entiendo nada"*. El reparto que quedó es la regla de oro del
  juego: **cartas = tu build (se acumulan) · reglas = el clima (cambia)**.
  `nextHour()` limpia péndulos/minas/secuencia y corre sólo el `onStart` de la regla vigente.
- **RACHA DE CORAJE** (`braveMul`): el precio de sacar el apilado fue perder el efecto
  compuesto, y sin él convenía jugar siempre a lo seguro (el bot prudente llegaba a la hora 11
  y el arriesgado moría en la 3). La racha devuelve la recompensa compuesta **sin** devolver el
  caos: cada hora seguida con regla picante sube un multiplicador permanente, y CALMA lo corta.
  El caos es por hora (legible), la recompensa se compone (motivante), y se lee en un número.
- **Roster por hora** (`pickRoster`): no salen todos los tipos desbloqueados a la vez, sino
  1–3 sorteados que son los únicos de esa hora. Con seis comportamientos distintos en pantalla
  no se lee nada. El peón siempre entra, como relleno.
- **El aviso de inicio de hora** (`drawIntro`) dice regla + descripción. Es la pantalla que
  enseña; si la sacás, vuelve la sensación de no entender qué pasa.
- **`RULE` es un objeto de multiplicadores recomputado desde cero** (`applyRules`), nunca
  estado mutable acumulado.
- **`recomputeStats()` se recalcula íntegro** desde `hand[]`: agregar o cambiar una carta no
  puede duplicar un efecto. Preserva la vida **absoluta** y acredita todo aumento del máximo.
- **Dificultad = vida y cadencia, con tope en el daño** (`scaleHp/scaleCd/scaleDmg`).
  Lección de TankWARS: escalar el daño sin tope hace que a la hora 10 te maten de un toque.
- **El perfil del TIRÓN** (`lungeVel`) es el twin-smoothstep de SnakeWeb: área exacta 0.5
  por fase ⇒ el avance neto es analítico, y la embestida nunca cambia de signo ⇒ sin recoil.
  Devuelve **velocidad**: se suma en la integración, nunca `vx +=` (acumularía y sale volando).
- **Subpasos acotados** en el loop (máx 3): estabilizan las cadenas de rebote orbe-orbe.
  Ojo: cualquier lógica con umbral de distancia por frame tiene que medir contra el **último
  punto guardado**, no contra la posición del subpaso anterior.

## Lo que salió del playtest largo (2026-09-14)

Franco jugó y disparó una tanda de cambios que redefinieron varias cosas. Las decisiones y
**el porqué**, que es lo que no hay que volver a romper:

- **Una decisión por hora, ALTERNANDO** (`endHour`): horas impares cambia la REGLA (y dura
  dos horas), pares llega una CARTA. Antes venían las dos pantallas juntas *y* la mano se
  llenaba tan rápido que te pasabas la run descartando. Con 11 transiciones salen 6 reglas y
  5 cartas: **la mano se completa justo al final y no descartás nunca**.
- **Ocho mejoras, dos por palo** (antes dieciséis). Varias eran tan específicas que no daban
  ganas de elegirlas. Con ocho **repetís seguido**, y como los duplicados apilan su efecto,
  sacar dos iguales es a la vez un PAR y el doble del efecto: recién ahí el póker pasa.
- **Nombres reales del póker** (PAIR / TWO PAIR / THREE OF A KIND / STRAIGHT / FLUSH / FULL
  HOUSE / FOUR OF A KIND / STRAIGHT FLUSH).
- **El inventario se ve al elegir**: la mano con los huecos libres, siempre, en el draft.
- **Reclamar sector = rodear el ROMBO** del centro (`claimSectorsIn` + `drawSectorTargets`).
  Antes se muestreaba 5×5 la cobertura contra un umbral: invisible, y se sentía arbitrario
  ("parece inconsistente"). Ahora hay un blanco dibujado y la regla se ve. El rombo late en
  dorado si cerrarlo completa una línea (`wouldCompleteLine`).
- **FRENESÍ rehecho**: ya no huyen. Imán suave hacia la canica (`CFG.frenzy.pull`, a propósito
  MÁS LENTO que el andar de una pieza: las escora, no las mueve), sos **invulnerable**, las
  piezas dejan de amenazar, y al terminar sale una **onda de choque gratis** (`frenzyBurst`).
  La versión anterior convertía el premio en una persecución.
- **Los rombos abren en una VENTANA, no siempre** (`game.sectorsOpen`, abre en la 1ª campanada
  de cada hora). Estando siempre, el ta-te-ti se encadenaba sin descanso. Y el **frenesí sale
  una vez por hora** (`run.frenzyHour`).
- **El 3x3 paga TODAS sus líneas** (`linesDone` + `newLines` + `checkLines`): el tablero no se
  limpia al cerrar una terna, así que ir sumando sectores va cerrando combinaciones nuevas —
  un reclamo bien puesto cierra dos juntas, y con los 9 salen las 8. Recién se resetea cuando
  están los nueve.
- **El hilo ONDULA** (`CFG.rope.waveAmp/waveK/waveSpd`): la onda desplaza el **ancla**, no el
  dibujo, así que pasa por el mismo resorte amortiguado y se mezcla con los golpes y el látigo.
  Tiene media cero alrededor del camino grabado ⇒ **la geometría del bucle no cambia**. Sin
  esto el tramo asentado quedaba absolutamente muerto y el hilo se leía como una línea dibujada.
- **RESONANCE no castiga pisar otros sectores.** En una grilla 3×3, para ir de un sector al
  siguiente casi siempre cruzás uno intermedio: con la regla de "sector equivocado = reinicio"
  la secuencia se caía apenas te movías. La única presión es el reloj. **No la re-agregues.**
- **RESONANCE es un Simón de verdad**: cuatro colores por sector (`SECT_CI`/`SIMON_COL`), una
  nota por color, el resto de la esfera **apagada**, puntos de progreso y aviso de error. Antes
  no se entendía si habías acertado.
- **La cabeza del hilo DIRIGE** (`CFG.thread.headPts` / `headAim`): cerca de la punta la salida
  se mezcla hacia donde te estás moviendo — es un raquetazo, no un rebote. Lejos, física pura.
  La punta se dibuja con halo propio: si no se ve, no sabés con qué parte estás pegando.
- **Las piezas NO se barren al cerrar la hora.** Verlas evaporarse al elegir una carta rompía
  la continuidad. El premio por aguantar es la cuerda (14% de vida) y el bonus.
- **El cartel de hora es una placa compacta** arriba, con cinta del color de la regla. No dice
  qué enemigos vienen (Franco lo pidió: prefiere descubrirlo).
- **`addScore` no hace nada en `over`/`win`.** El fondo sigue vivo, pero ver el número moverse
  solo después de morir arruinaba la lectura del resultado.
- **Fuera** la regla ESTELAS (rastros de enemigos) y la palabra tipo Ahorcado: la primera no le
  pareció buena mecánica, la segunda no tenía ninguna.
- **DAÑO y PUNTOS son dos lenguajes distintos** (`drawFloaters`): el daño es un número pelado
  con una chispa de cuatro puntas al lado (vive en el mundo); los puntos van siempre con "+"
  dentro de una chapa oscura con borde (se lee como UI). Antes eran el mismo número con otro
  color y se confundían constantemente.
- **Tipografía Outfit** (Google Fonts). La anterior era la system-ui, que en Windows cae en
  Segoe UI y se lee cuadrada y genérica — sobre todo en los números del score.
- **Modos con nombre y explicación**: FREE RUN / DAILY RUN como tarjetas con subtítulo. "LIBRE"
  y "DIARIO" sueltos no decían nada.

## Segundo playtest (2026-09-15) — bugs de fondo y afinado

- **EXPLOSIÓN DE DAMAS (el bug más grave que tuvo el juego).** Las damas invocaban peones y
  los peones que llegaban al centro coronaban en damas: reacción en cadena exponencial. Peor,
  `enemyCap()` sólo lo miraba el spawner del reloj, así que coronaciones e invocaciones
  entraban por la puerta de atrás sin tope. Tres candados, **no los saques**:
  `HARD_CAP` aplicado **dentro de `spawnEnemy`** (cubre toda fuente), `MAX_QUEENS = 2`, y la
  dama ya **no** invoca peones. Verificado: 10 horas con el jugador quieto → se estaciona en
  11 enemigos y 2 damas. Antes reventaba.
- **La CELDA es cuadrada; lo RECTANGULAR es sólo dónde va el rombo.** (Corregido más tarde el
  mismo día: primero se acható la celda entera y eso cambió el "#" del reloj, que no era lo
  buscado.) La celda es el tercio de siempre (`SECT_Q`, `sectRect`, `sectorAt`) — es lo que
  dibuja el reloj, lo que se pinta entero y lo que define en qué sector estás. El BLANCO va en
  una grilla achatada (`SECT_DX/SECT_DY`): en el centro geométrico de una celda de esquina el
  rombo caía a radio 0.94, sobre el borde, y **el tablero no se podía completar nunca**.
- **Ciclo del tablero** (versión final): la ventana abre pasada `CFG.clock.sectorsAt` de la
  hora (33%), **una sola vez por hora** (`game.sectorsShown`), y cobrar una línea **limpia el
  tablero entero** y cierra la ventana — los sectores se descargan en el frenesí. Los sectores
  sin cobrar sí persisten entre horas. Las ternas cobradas viven en `linesDone`, que
  `resetSectors()` limpia junto con el tablero.
- **Los rombos se dibujan DESPUÉS de la aguja**: el del centro quedaba tapado justo cuando la
  aguja pasaba por ahí, que es casi siempre.
- **Cerrar acepta el ROCE** (`CFG.thread.closeTol` ≈ radio de la canica). Medido: la ondulación
  costaba un cierre de cada tres exigiendo la intersección exacta de la línea de centro. El
  modelo mental pasa a ser "TOCÁ tu hilo y cierra". (La pista visual `nearClose` que se había
  pensado NO existe en el código: se perdió en un parche fallido y nunca se rehizo.)
- **El hilo se dibuja como CINTA RELLENA, no como línea con grosor.** Con strokes por tramos
  siempre quedaba el escalón entre capas; un polígono relleno tiene silueta continua. El color
  va en rodajas opacas que COMPARTEN sus vértices de borde, así no hay costura. El ancho de cada
  punto es el que tenía la mano al apoyarlo (`thread[i].w`, ver la auditoría más abajo).
- **Fuga de orbes: el hilo TAMBIÉN se mueve.** El test barrido del orbe no alcanza — cuando la
  soga barre por encima de un orbe casi quieto no hay intersección contra la posición actual
  del segmento. Se testea también contra la posición ANTERIOR (`p.px/p.py`) y los cruces en
  diagonal. Y `deflCd` (ventana CIEGA) volvió a ser corto: a 0.15 s eran 0.26 unidades de vuelo
  sin colisión. El "no estar siempre prendido" se resuelve aparte con `o.chargeCd`.
- **Los orbes dejaron de decidir la oleada**: hacían 26 + velocidad y conservaban el 60% de la
  carga, así que un orbe barría grupos enteros y la población siguiente era una lotería. Ahora
  17 + velocidad y conservan 28%. El daño del BUCLE subió para compensar: decide tu habilidad.
- **RESONANCE no castiga pisar otros sectores** (ver abajo).

## Auditoría de QA (2026-09-15) — bugs que el playtest no encontraba

Todo esto estaba vivo y ninguno tiraba un error. **No los re-introduzcas.**

- **La racha de coraje nunca se cortaba.** `chooseRule` comparaba `r.id === 'calma'`, pero el id
  quedó en `'calm'` cuando se tradujo la UI. Tomar CALM subía la racha igual que una regla
  picante — y el propio cartel del draft promete lo contrario, porque ahí sí compara bien.
  Moraleja: **un id de datos que se usa en dos archivos es una dependencia silenciosa**; si
  renombrás uno, buscá el string en TODO el repo.
- **La ventana de rombos se reabría al frame siguiente de cobrar.** `checkLines` hace
  `game.sectorsOpen = false`, pero `updateClock` la reabre en cuanto ve `u >= sectorsAt`, cosa
  que sigue siendo cierta el resto de la hora. El cierre duraba UN frame. Ahora hay
  `game.sectorsShown`: la ventana se abre **una sola vez por hora**.
- **Morir en el mismo frame en que termina la hora te robaba la pantalla de derrota.**
  `stepSim` llamaba `updateClock` ANTES de mirar el estado; con dt grande hay hasta 3 subpasos,
  y si morías en el primero, el segundo cruzaba la hora y `endHour()` abría el draft ENCIMA de
  la derrota: partida zombi con el jugador muerto. Medido 60/60 casos antes, 0/60 después.
  Hacen falta **los dos** chequeos de estado (antes y después de `updateClock`).
- **La pantalla de derrota seguía jugando sola.** En `over`/`win` el loop llama a `updateOrbs`
  para que el fondo respire, pero eso desviaba contra el hilo (`run.deflects++`) y los orbes
  cargados mataban piezas (`run.kills++`, combo, drops). El resumen final mostraba números
  subiendo. Ahora `updateOrbs` mira `game.state === 'play'` antes de tocar nada que sea estado
  de partida; los orbes siguen rebotando contra las paredes y entre sí.
- **El pincel del hilo no existía.** `drawThread` lee `thread[j].w` con un fallback defensivo
  `|| 1`… y `newPt` nunca escribía `w`. El fallback corría SIEMPRE: ancho constante y
  `CFG.thread.speedW` sin efecto. **Cuidado con los `|| valor` defensivos: tapan justamente el
  bug que tendrían que delatar.**
- **La fuente del canvas no era la que se carga.** El `<link>` trae Outfit y el CSS la aplica al
  body, pero TODO el texto del juego se dibuja en canvas con la constante `FONT`, que seguía en
  Segoe UI. Ahora coinciden, y se re-hornea el plato con `document.fonts.ready` (si no, los
  numerales quedan con la fuente de sistema para siempre).
- **El espejo nunca cargaba los orbes.** `mirrorDeflect` arma un orbe fantasma y se olvidaba de
  `chargeCd`; adentro, `if (o.chargeCd <= 0)` con `undefined` da **false**, así que el reflejo
  desviaba pero no encendía nada. `undefined` en una comparación numérica no explota: miente.
- **`spawnOrb` simulaba un orbe dos veces.** `updateOrbs` recorre al revés; cuando una pieza
  muere adentro de ese bucle suelta un orbe, y con la mesa llena `spawnOrb` hacía `splice` de un
  neutro. Sacar un elemento por debajo del índice actual corre el array. Ahora **reemplaza en el
  lugar**.
- **El modo DIARIO no era reproducible**, por dos causas independientes:
  1. la ondulación de la soga usaba `perfT` (reloj de pared desde que cargó la página), así que
     la fase dependía de CUÁNDO empezaste. Ahora usa `ropeT`, que acumula dt de simulación y lo
     reinicia `startRun`;
  2. el polvo de ambiente llamaba a `rnd()` (el rng **sembrado**) desde un temporizador que no
     se reiniciaba entre partidas ⇒ el stream entero se corría. La decoración ahora usa
     `Math.random`. **Regla: lo decorativo nunca toca la semilla.**
  Verificado: 4000 frames bit a bit idénticos, con cambios de hora, drafts, coronaciones y
  muerte incluidos, comparando sumas de verificación de todo el estado.
- **`hitstop` sobrevivía de una partida a la otra** y el primer frame de la nueva quedaba sin
  simular. `startRun` limpia `hitstop`, `trauma`, `flashA` y `zoomPunch`.
- **El frenesí quedaba colgado** al salir al menú o al ganar: `updateFrenzy` sólo corre en
  `play`, así que nunca terminaba y el ×1.5 de `hurtEnemy` quedaba activo. Lo limpian `endRun` y
  `backToMenu`.
- **La quema de sector no se reiniciaba al salir**: `e.sectT` sólo subía, así que una pieza que
  pisaba medio segundo y volvía después ardía al instante. Es un contador de PERMANENCIA.
- **Con el jugador QUIETO la cola del hilo se iba de la arena.** Parado, el hilo se queda en 2
  puntos y `simThread` salía temprano (`if (n < 3) return`), así que ni el ancla ni el recorte
  contra el plato corrían — pero `kickThread` sí seguía empujando la cola en cada rebote. Medido
  en la prueba AFK: radio 1.14 a la hora 2, 1.60 a la hora 3, **2.86 a la hora 4** (la arena
  tiene radio 1), con el hilo dibujado como una recta enorme saliendo de la esfera. **Una salida
  temprana por "caso trivial" es sospechosa si algo de afuera puede seguir escribiendo ese
  estado.** Ahora el caso `n < 3` aplica ancla y recorte igual.
- **El buscaminas era ilegible**: la casilla destapada se pintaba a alpha 0.05 (invisible) y los
  números quedaban DEBAJO de los carriles de telegrafía y de la aguja. Franco, textual: "¿qué
  marca ese número?". Ahora el dibujo va en dos pasadas — `drawMineCells()` con el fondo y
  `drawMineMarks()` **arriba de todo lo vivo**, porque es información, no decorado.

## Sistema visual (art direction, 2026-09-16)

Mesa de casino: fieltro oscuro, metal dorado, naipes de hueso. Antes cada pantalla elegía sus
colores y tamaños a ojo y por eso parecían de juegos distintos. Ahora hay **tokens** en
`p03_engine` y todo se escribe contra ellos:

- **`C`** — paleta. Cinco familias, **una función cada una**: superficies (`void/felt/surf/
  surfHi/line/lineHi`), tinta (`ink/inkDim/inkFaint`), **oro** = valor (puntaje, premios, el
  reloj), **hielo** = vos (canica, hilo, herramientas), **carmesí** = lo que te lastima,
  **violeta** = reglas y resonancia. Si un color hace dos cosas, deja de significar algo.
- **`TS`** — escala tipográfica en fracciones de `min(W,H)`: `display/title/sub/body/cap`.
  No inventar tamaños sueltos.
- **`panel(x,y,w,h,r,accent,glow)`** — el ÚNICO lugar donde se decide cómo se ve una placa:
  gradiente vertical, borde de acento, filo de luz arriba. Lo usan draft, menú, cartel de hora,
  botones y el panel del stack.
- **`txtO()`** — texto contorneado, para lo que vuela sobre la arena. El `txtG` de sombra
  desplazada se lee como un texto pegado encima; el contorno centra la silueta.
- Las mismas variables existen en CSS (`:root`) para que la cáscara DOM no sea otro juego.

**Regla de rendimiento que manda sobre todo: "que parezca caro de producir, pero que sea barato
de renderizar".** Sin `shadowBlur`, sin `filter`, sin partículas nuevas. La profundidad se arma
con gradientes verticales, un filo claro arriba y una base oscura — tres fills y dos líneas.

### Los números de daño dicen QUIÉN, y el tamaño dice CUÁNTO

Eran tres naranjas casi idénticos (`#ff6b81 / #ff9f43 / #ffd23f`) separados por un `kind` que
el jugador no podía deducir, con tamaño fijo. Ahora:

- lo que **hacés vos** → hueso, y vira a **oro** cuanto más fuerte pega;
- lo que **te hacen** → carmesí, más pesado (`kind: 3`, nuevo);
- lo que te **cura** → verde;
- el **tamaño** sale de `dmgRef()` = lo que pega un bucle ceñido a esa altura de la partida, así
  que un 40 impresiona en la hora 1 y es rutina en la 11 — como se siente jugando;
- sólo los golpes grandes se ganan un destello, y usa el sprite cacheado de `bloomPx`. Si
  brillara todo, no brillaría nada.

El puntaje es una **ficha** (chapa con filo dorado), no un globo: es otro lenguaje, no otro color.

### Decisiones de performance de esta pasada

- **La tira de la mano se HORNEA** (`bakeHandStrip`). Es lo único del rediseño que costaba EN
  JUEGO: corre en cada frame del HUD y cada naipe pedía dos `createLinearGradient` — 10 por
  frame para dibujar algo que sólo cambia cuando agarrás una carta. Ahora es **un `drawImage`**,
  invalidado por `handKey()` (contenido + jugada + tamaño) y por el resize. Mismo patrón que
  `bakeDial`.
- **El contador de FPS ya no corre siempre.** Tenía un `requestAnimationFrame` propio vivo desde
  que cargaba la página, se mirara o no el panel de info. Ahora arranca al abrirlo y se corta al
  cerrarlo (`startFps`/`stopFps`).
- **Las animaciones de entrada terminan.** Draft de reglas y de cartas entran escalonadas en
  0.24–0.26 s; pasado ese tiempo el factor vale 1 y no se recalcula nada. La única animación
  permanente es un `Math.sin` por naipe en el draft (flotación de reposo), y sólo mientras el
  draft está abierto.
- **La sombra de los naipes son dos rects desplazados**, no `shadowBlur` — que es de lo más caro
  que hay en canvas mobile.

### La arena (2026-09-16, segunda pasada) — donde de verdad se nota

La primera pasada tocó cartas, paneles, números y pantallas: **todo lo que se mira por segundos**.
El plato, las piezas, las orbes y la aguja — lo que se mira TODO el rato — quedaron como estaban,
y el resultado fue "no sentí mucha diferencia". Lección que vale para cualquier rediseño acá: **el
pase de arte se juzga por lo que ocupa la pantalla durante el juego, no por las pantallas de menú.**

**Una sola luz clave.** `LIGHT` (`p03_engine`) es la dirección de la luz en coordenadas de
PANTALLA, arriba a la izquierda. Todo lo que tiene volumen la respeta: canica, piezas, orbes,
aguja, torreta del tanque. Antes cada cosa elegía la suya (o ninguna) y el conjunto parecía un
collage de stickers. **Si un objeto se dibuja ROTADO, hay que contrarrotar la luz** (moto, aguja,
torreta): si no, el brillo gira con el objeto y se lee como algo que se ilumina solo.

Dos helpers, y no hay un tercer lugar donde se decida esto:

- **`groundShadow(x,y,r,a)`** — dos elipses apiladas, sin gradiente (a 24 piezas en pantalla, un
  `createRadialGradient` por pieza por frame es gasto real y se ve igual). Es el detalle más barato
  del pase y el que más cambia: **sin sombra las piezas flotan; con sombra están apoyadas.**
- **`bevelShape(pathFn, w, liteA, darkA, lx, ly)`** — filo claro arriba / oscuro abajo DENTRO de
  la silueta. El truco es recortar contra la forma y volver a trazarla corrida: lo que sobresale
  se recorta, así que del trazo queda sólo la mitad interior, que es exactamente un borde de luz.
  Da volumen sin un gradiente por objeto y sin una sola sombra de canvas. `pathFn` se llama tres
  veces, así que tiene que poder reconstruir el camino.

**El plato es un objeto, no un círculo.** `bakeDial` se hornea una vez por resize, así que **ahí
adentro el detalle es gratis y conviene gastarlo todo**: bisel de latón con gradiente cónico (el
doble reflejo es lo que lo hace leer como metal), anillo de capítulo, sombra interior del bisel
cayendo sobre el fieltro — ese gradiente solo es el golpe de profundidad de la pasada entera — y
grano de tela por mosaico. Las grillas van **grabadas**: línea oscura + línea clara corrida hacia
la luz. Una línea sola se lee dibujada; dos se leen talladas.

Tres cosas que costaron una iteración cada una y conviene no repetir:

- **El bisel arrancó demasiado claro y ancho** y se comió la escena — parecía un aro de oro
  gigante. Un bisel ENMARCA; si brilla, dejó de ser marco.
- **Los numerales compartían radio con sus propias marcas de hora** y quedaban atravesados. El
  anillo necesita DOS bandas: marcas afuera, números adentro.
- **La caída interior tan marcada achicaba el área jugable.** La profundidad se sugiere, no
  recorta el tablero.

**Cachear un `CanvasPattern` es un bug esperando.** Un pattern nace atado al contexto que lo creó,
y cada resize hornea el plato en un canvas nuevo. Se cachea el **mosaico** y se llama
`createPattern` por horneado.

### Estados (hover) y la trampa de layout

El hover se calcula con la posición del puntero, y la forma obvia de conseguirla
(`getBoundingClientRect` en cada `pointermove`) es **exactamente** lo que el brief pedía evitar:
una lectura que fuerza recálculo de layout, disparada decenas de veces por segundo. El rect se
cachea en `resize()` (`cvLeft/cvTop`) y el handler sólo resta dos números. `hovering(r)` da falso
siempre en táctil. El cursor se escribe **sólo cuando cambia** (`wantPointer`), mismo patrón que
ya usaba el joystick: escribir `style.cursor` cada frame es una escritura al CSSOM por frame para
dejarlo igual.

**`wantPointer(false)` NO puede colgarse de la cadena de `else if` del render.** Como
`typeof wantPointer === 'function'` siempre da verdadero, se tragaba las ramas de `'over'` y
`'win'` y las pantallas de muerte y victoria dejaban de dibujarse. Lo cazó el dry-run del parche
sobre una copia de `parts/`, no el juego.

## EL RELOJERO necesita un COMPÁS, no más números

Las cuatro quejas del playtest — "acercarse es solo posible si tenés escudo", "todo el rato es
igual", "hay tantos enemigos que no entiendo lo que pasa", "re difícil hacerle daño" — eran **la
misma falla**: la pelea no tenía ciclo. Los brazos giraban sin parar, el núcleo lastimaba siempre,
el ataque salía a cara o cruz cada 3 s, y la armadura (`src !== 'loop'` → 30 %) dejaba una sola
forma de hacer daño: justo la que exige meterse donde te pegan. **Sin un momento en que la
respuesta sea "AHORA", lo único que queda es entrar, comer el golpe y salir a esperar el escudo.**

Tres tiempos, en `CFG.boss`:

| estado | qué pasa |
|---|---|
| `idle` | los brazos giran, el núcleo lastima; dura menos en cada fase |
| `wind` (1 s) | los brazos aceleran y un aro rojo se cierra hacia adentro — telegrafía |
| `open` (2.6 s) | los brazos **se frenan y se recogen**, el núcleo se abre en hielo, **no lastima al contacto** y **recibe ×3** |

Medido: 14 transiciones en 30 s, núcleo abierto el 40 % del tiempo, ×3.00 confirmado, y 40 frames
parado encima del núcleo abierto = 0 de daño.

Dos principios que valen para cualquier jefe que se agregue acá:

- **La señal es la ausencia de movimiento.** Los brazos frenándose dicen "ahora" mejor que
  cualquier cartel, y no hay que enseñarla.
- **Los ataques ALTERNAN, no se sortean.** Un patrón se aprende; una moneda, no. `rng() < 0.5`
  entre dos ataques no genera variedad: genera ruido.

La armadura pasó a `CFG.boss.armor = 0.55`. El bucle sigue siendo el rey — no la paga — pero al
30 % todo lo demás eran cosquillas y la pelea era un peaje de vida. Y las invocaciones ahora se
topean contra las piezas **que ya hay vivas** (`CFG.boss.maxAdds`): el jefe llamaba 2-5 cada 3 s
ENCIMA del spawner normal de la hora, y por eso no se entendía nada.

## La aguja ya no batea las orbes

Era una paleta giratoria que las reflejaba y les pasaba su energía angular. En el papel sonaba
bien; en la práctica es una fuerza que cruza el plato entero cada hora, sin telegrafía, mandando
pelotas para cualquier lado justo cuando estás resolviendo otra cosa. El reloj ya manda con las
reglas y con las campanadas. Los brazos del jefe, que son agujas, tampoco.

**Trampa al sacarlo**: `ex`/`ey` (el coseno y el seno de `clock.ang`) estaban declarados DENTRO de
ese bloque, y los sigue necesitando el spawn de piezas — las piezas nacen en la punta de la aguja.
Borrar el bloque entero dejó `ex is not defined` en once escenarios. Lo cazó la regresión, no yo.

### Un test verde que no probaba nada (dos veces seguidas)

Verificar "la orbe no se mueve" dio **dos falsos positivos** antes de servir:

1. el **imán del jugador** también tira de la orbe;
2. `spawnOrb` **randomiza radio y masa**, así que dos corridas comparaban orbes distintas — y 30
   frames de simulación además consumen RNG y spawnean piezas que la chocan.

Lo que sirvió fue llamar `updateClock(dt)` **sola**, con la orbe quieta encima de la aguja, y
exigir velocidad **cero exacto**. Regla: cuando midas que algo dejó de pasar, aislá la función que
tocaste en vez de correr el juego entero y mirar el resultado.

## Playtest 2026-09-16 (tarde)

### La racha se mide contra un umbral ABSOLUTO, no contra las otras dos opciones

El corte era relativo: la opción de multiplicador más bajo de la terna mandaba la racha a cero.
Con {RESONANCE x1.45, HORDE x1.50, THE GALLOWS x1.75} eso castigaba elegir RESONANCE — que tiene
riesgo real — sólo porque las otras dos eran peores. Franco, textual: *"no quiero que me castigue
los puntos por elegir el simon dice"*. Ahora hay `SAFE_RISK = 0.20` y `breaksStreak(r)`: una regla
con riesgo real **nunca** corta la racha, aunque sea la más floja de las tres. El color de la placa
sale del riesgo propio de la regla, no de su puesto en la terna.

La lección general: **un castigo relativo castiga por el contexto, no por la decisión.** El jugador
elige una regla concreta y espera que el precio dependa de esa regla — no de qué le tocó al lado.

### THE GALLOWS: fuera

No gustó ni el minijuego ni cómo se veía, y no comunicaba qué pasaba al completarse (cobraba 34%
de vida máxima y volvía a cero — que haya habido que preguntarlo ya es el veredicto). Se sacó
entero: regla, objeto, contador, alivio, update, dibujo, CFG y los chequeos de QA. **Apagar una
regla dejándole el código es deuda**: la próxima pasada de auditoría la vuelve a encontrar.

### Lo "cortado" no era la animación, era la rasterización

La flotación de los naipes recorría 4 px en 2 s: ~0.06 px por frame. El cuerpo del naipe se movía
suave, pero **el texto se rasteriza a píxel entero**, así que se quedaba clavado quince frames y
saltaba uno de golpe. Suavizar la curva no lo habría arreglado nunca. Lo que lo arregla es más
recorrido y, sobre todo, una **inclinación mínima** (±0.6°): con el canvas rotado el rasterizador
ya no puede alinear el texto a la grilla y el movimiento se vuelve continuo.

Regla para la próxima: **si algo se mueve menos de ~0.3 px por frame y lleva texto, se va a ver a
los saltos por más suave que sea la curva.** O se mueve de verdad, o no se mueve.

### Buscaminas: la paleta clásica, y por qué ahora sí

Los números usaban una rampa fría **a propósito**, porque cuando usaban la del daño un "3" de celda
y un "34" de golpe se leían igual. El clásico mete rojo en el 3, o sea que vuelve a ese territorio.
Se puede porque las dos familias ya se distinguen por algo que **no es el color**: el número de
celda está quieto, anclado en el centro de una casilla encendida y con contorno oscuro (`txtO`); el
de daño flota, sube, se desvanece y nunca lleva contorno. Con eso resuelto, la paleta del Buscaminas
es conocimiento que el jugador ya trae puesto. El 7 y el 8 originales (negro y gris) suben a hueso
y gris claro: sobre fieltro oscuro no existirían.

La casilla destapada se dibuja **hundida** (filo claro del lado de la luz, oscuro del contrario), y
la mina es una esfera metálica con la luz clave de todo lo demás, con el rojo reservado para el aro
que late — un solo elemento rojo dice "peligro" mejor que un cuerpo rojo con aros rojos.

### Riders: el rumbo objetivo y el rumbo real

`e.dir` es el rumbo OBJETIVO (siempre en ángulo recto) y `e.ang` el REAL, que lo alcanza girando a
`CFG.cycle.turnRate`. Antes eran lo mismo y la moto cambiaba de dirección entre dos frames: se leía
como un teletransporte de rumbo. Separarlos hace que curve como el fantasma sin perder el circuito —
los tramos rectos siguen rectos y los giros siguen siendo de 90°, sólo que con radio.

Con el giro suave **ya no alcanza con "dobla al llegar a 0.88"**: mientras gira sigue avanzando, así
que hace falta un tope duro contra el aro (0.93) que además le fuerce el rumbo hacia adentro.

`life` x `spd` es el LARGO de la estela en unidades del plato (que mide 2 de punta a punta). Estaba
en 4.0 x 0.80 = 3.2 unidades: más de una vuelta entera, el plato tapado de naranja. Ahora 1.5 x 0.60
= 0.9 — una pared que se esquiva, no un laberinto.

## Una regla que termina no puede dejar restos

`nextHour` dice explícitamente que limpia el mundo (péndulos, minas, secuencia) — pero **las orbes
estaban afuera de esa lista**. `orbCap()` depende de `RULE.orbRate`, así que una hora de "más
pelotas" llenaba hasta 14 y la hora siguiente se las quedaba TODAS: el tope baja, pero `spawnOrb`
sólo REEMPLAZA cuando está lleno, nunca recorta. Un efecto temporal quedaba permanente por el
resto de la partida. Ahora `nextHour` poda al tope, sacando primero las neutras (misma política
que ya usaba `spawnOrb`).

Lo encontró `frenzy50` con un `ORB-CAP` **intermitente** — dependía de qué regla saliera sorteada.
Un fallo que aparece una de cada varias corridas no es ruido: es un fallo con una precondición que
todavía no identificaste. El mensaje del chequeo no alcanzaba para diagnosticarlo, y agregarle el
contexto (hora, `orbRate`, regla, estado) fue lo que lo volvió legible.

## El bucle no puede devaluarse con la hora

La vida enemiga escala (`scaleHp()`: ×2.6 en la hora 11) y el daño del bucle era **constante**.
Medido: un bucle ceñido valía **0.94 torres en la hora 1 y 0.36 en la hora 11** — el verbo
central del juego se apagaba solo, y Franco lo sintió como "ya no parecía hacer daño". Ahora
`closeLoop` multiplica por `scaleHp()`, así que el poder RELATIVO es constante (1.13 torres en
las dos horas, verificado). **Cualquier cosa que sea la herramienta principal del jugador tiene
que escalar con lo que escala en su contra**; si no, el juego se vuelve imposible solo.

## RESONANCE deja una marca, no puntos invisibles

Pagaba 1600 puntos fijos. Con marcadores de seis o siete cifras eso no se ve: resolvías la
secuencia y no pasaba nada legible. Ahora cada secuencia resuelta suma `run.resonance`, que da
**hilo +8% y bucle +15% permanentes** (se aplican en `recomputeStats`, nunca acumulando sobre el
valor anterior — sigue siendo idempotente) más puntaje que escala con la hora. Una sola cosa que
se apila, no un menú de bonus aleatorios: hacer un segundo sistema de cartas habría competido
con el que ya existe.

## La racha mide RIESGO, no cantidad de reglas

`run.brave++` daba lo mismo GRAVEDAD (x1.40) que DOBLE O NADA (x2.00), y HORA MUERTA (x0.55,
donde no spawnea nadie) construía racha igual que una regla peligrosa. Ahora `ruleRisk(r)`:
rojas (mult >= 1.6) suman 2, picantes normales 1, las que no son riesgo (mult <= 1) suman 0, y
CALMA sigue cortando a cero. El cartel del draft muestra el salto real.

## Las manos de póker tienen que decir QUÉ dan

`HAND_BONUS[i].desc` existía en la tabla desde siempre y **no se dibujaba en ningún lado**:
tenías una pierna de ases y no había forma de saber para qué servía. Ahora el efecto va bajo la
tira del HUD, y tocar la tira (o `H`) abre el **panel del stack**, que congela la simulación y
muestra las cinco cartas grandes con su efecto concreto más la mano y su bonus. El COLOR es el
único cuyo efecto depende del palo, así que tiene su propia tabla (`FLUSH_DESC`) — el texto
viejo decía "The whole suit overflows", que no informa nada.

**Ojo con el orden de render:** el panel es un modal y va ÚLTIMO, después de `drawToasts()`.
Puesto junto a `drawHUD()` quedaba debajo del cartel de inicio de hora, que le tapaba las cartas.

## La economía: REGLA por calendario, CARTA por puntaje

Hasta el 2026-09-15 se alternaba — horas impares regla, pares carta — y la regla duraba dos
horas. Franco lo cambió: **la regla cambia todas las horas** (dos horas seguidas de lo mismo se
volvía rutina) y **la carta se gana con PUNTOS** (`CARD_SCORE = [4000, 12000, 26000, 46000,
75000]`). El objetivo declarado: *"incentivar que el jugador explote la puntuación"* — el score
dejó de ser un marcador y pasó a ser la moneda con la que se compra el build.

Detalles que importan:

- **Ganar una carta NO interrumpe.** `addScore` sólo incrementa `run.cardsWon` y avisa; la carta
  se cobra al cerrar la hora, después de la regla. Abrir un draft en pleno combate sería peor
  que el premio. Lo inmediato es el aviso, no la pantalla.
- **Se encadenan.** Si un solo golpe cruza dos umbrales (o venías con una guardada), salen dos
  pantallas de carta seguidas. El flujo pasa por `afterDraft()`, que es el único lugar que
  decide "¿otra carta o la hora siguiente?" — **no llames `nextHour()` directo desde un draft**.
- **El HUD muestra el progreso** pegado al score (barra fina + cuánto falta, o `CARD READY`).
  Sin eso, "hacer puntos" no se siente conectado con nada; esa barra ES el incentivo.
- Consecuencia para el QA: **cerrar una hora puede encadenar 2+ pantallas**, así que todo helper
  de test que avance drafts tiene que vaciar la cola en un bucle, no avanzar una sola vez.

## MINEFIELD: el hilo es un SONAR, no un marcador

Primera versión: `revealed` era un `Uint8Array` de flags y la celda quedaba destapada **para
siempre**. A la hora de juego el plato entero estaba pintado (Franco: *"no quiero que queden
todas las celdas marcadas"*), y peor: con todo destapado los números te decían dónde estaban las
minas **sin haberte acercado nunca**, que era la otra queja. Las dos salen de la misma causa.

Ahora `revealed` es un `Float32Array` de **segundos restantes** (`CFG.mines.scanT`, con
`CFG.mines.fade` de desvanecido). El hilo refresca las celdas por las que pasa y el resto se
apaga: la información es fresca o no es. Medido: de 50+ celdas acumuladas a **11 encendidas a la
vez**. Las celdas LIMPIAS (0 minas al lado) se pintan mucho más tenues que las que tienen número
— eran la mayoría y las que hacían la mancha.

La excepción deliberada: **una mina sobre la que pasaste queda fichada para siempre** (`m.seen`).
Encontrarla es el premio de haber ido hasta ahí; lo que se apaga es el barrido, no el hallazgo.

### El bug que hacía que los números fueran ruido

La mina se creaba con `mines.push({ c, r, ..., r: CELL * 0.34, ... })` — **dos claves `r`**: la
fila y el radio. En un literal de JS **gana la última**, así que `m.r` valía 0.0755 y la FILA se
perdía en silencio. De ahí:

- `mineCountAt` comparaba `|0.0755 − fila| <= 1`, verdadero sólo para las filas 0 y 1 ⇒ los
  números que veías no eran la cuenta de minas vecinas, eran ruido;
- `revealCell` fichaba con `m.r === r`, y 0.0755 nunca es una fila entera ⇒ **pisar la celda de
  una mina no la revelaba nunca**; las únicas que aparecían eran las que ya habían explotado.

El radio ahora se llama `rad`. **Lección doble:** una clave repetida en un literal no avisa —
ni error, ni warning, ni nada; y el campo pisado era justo el que tenía el nombre más corto y
más fácil de repetir. Si un objeto mezcla coordenadas de grilla con medidas físicas, que los
nombres no puedan chocar.

**Y la lección de QA, que es peor:** el escenario `minefield` verificaba `mineCountAt` contra un
cálculo manual… que leía el mismo `m.r` roto. El oráculo tenía el mismo bug que el código, así
que coincidían y daba verde. **Un oráculo que comparte la fuente de datos con lo que testea no
prueba nada.** El que sí lo agarró fue mirar los valores crudos (`minas en (c,r)` mostró
`8,0.0755` catorce veces).

### Números de tablero vs números de feedback

Los números del buscaminas usaban **exactamente la misma paleta que los de daño**
(`#ffd23f / #ff9f43 / #ff6b81`), el mismo peso 900 y el mismo halo: un "3" de celda y un "34" de
golpe se leían igual. Ahora van en una rampa FRÍA (`MINE_NUM`) que el daño no usa nunca, y más
chicos. Regla general para este juego: **lo que es información del tablero no puede compartir
lenguaje visual con lo que es feedback de un golpe.**

## RESONANCE: por qué el castigo mide QUEDARSE y no tiempo

La primera versión ("sector equivocado = reinicio inmediato") estaba rota: en una grilla 3×3, ir
de un sector al siguiente casi siempre cruza uno intermedio. La segunda ("no castigar nada")
sacaba todo el riesgo. La tercera —la que está— distingue **transitar** de **plantarse**:

    const spf = clamp(hyp(P.vx, P.vy) / (CFG.player.maxSpd * P.spdMul), 0, 1);
    simon.wrongT += dt * (1 - 0.85 * spf);

Un umbral de tiempo pelado NO alcanza, y está medido: cruzar la celda del centro **en diagonal**
son 0.94 u ≈ 1.07 s a máxima velocidad (más el arranque), así que cualquier valor que castigara
plantarse castigaba también el viaje normal. Pesando por velocidad, a fondo casi no acumula y
quieto acumula entero. El umbral vive en `CFG.simon.wrongT` (panel `T`) y el sector equivocado se
tiñe de rojo mientras corre: el aviso se ve, no hay que explicarlo.

## El cartel de hora NO es un estado

Era `game.state = 'intro'` y congelaba la simulación 2.1 s después de cada draft. Franco:
"no lo hagas pausar despues de elegir lo que sea". Ahora es `game.banner`, un contador que sólo
dibuja un overlay; se juega desde el primer frame de la hora. Si volvés a necesitar una pantalla
que congele, **no la metas como estado de `game.state`**: el estado decide si corre la
simulación, y mezclar "qué se dibuja" con "qué se simula" es lo que trajo este problema.

## QA: qa.py (humo) y qa2.py (invariantes)

- `qa.py` es el de siempre: corre escenarios, saca capturas y caza errores de JS.
- `qa2.py` es el **auditor**: además de correr, inspecciona el estado interno con `chk()` — NaN,
  Infinity, HP negativo, posiciones fuera del plato, caps violados, arrays que crecen,
  contadores que retroceden. `chkEvery = 1` lo corre en cada frame.
- Truco para leer estado: las `const` de nivel superior NO quedan en `window`, pero
  `window.eval(expr)` es eval **indirecto** ⇒ corre en el scope global y sí ve el entorno léxico.
  `G('sparks.length')` llega a cualquier cosa sin tocar el juego.
- **Para comparar dos corridas hay que igualar TRES cosas**: la semilla (`mode='daily'`), el
  `lastT` del juego (bombear unos frames antes de `startRun`) y el **valor absoluto** del reloj
  del driver (`t = 100000` en las dos). Restar dos floats grandes y cercanos no da exactamente
  `STEP`: con `t ≈ 1e5` ms el error es ~1e-11 s, y el sistema lo amplifica en ~500 frames.
- **El detector de fugas POR FRAME sobre-reporta y no hay que creerle.** El escenario `leak`
  (qa.py) y `tunnel` (qa2.py) muestrean una vez por frame el tramo del orbe contra la posición
  **final** del hilo — pero el hilo se movió durante los 3 subpasos, así que un barrido legítimo
  cuenta como "cruce". A 50 ms llega a decir 100% de fugas. Los que valen son `tunnel2` (hilo
  asentado, un disparo por vez, 5 velocidades × 2 dt) y `tunnel3` (hilo EN MOVIMIENTO, cuenta por
  posición final del orbe): **0 de 50 y 0 de 56**. Si vas a medir colisiones, medí por
  consecuencia (¿rebotó? ¿dónde terminó?), no por muestreo geométrico.
- **Un bot que se queda quieto se muere**, y una vez muerto `stepSim` sale al toque: todo lo que
  midas después es basura. Si el escenario necesita quietud, hacelo inmortal
  (`B.P.hp = B.P.hpMax; B.P.ifr = 9`) y, si hace falta, congelá la hora (`CFG.clock.hourT = 1e6`).
- **Lo mismo con los drafts**: si la hora termina, la simulación se congela hasta que elijas.
  Todo escenario largo necesita su `advance()`.

## Los carteles de draft (lección de legibilidad)

Los dos drafts se ven **distintos a propósito**, porque son cosas distintas:

- **Cartas** = naipes de verdad. Cara de papel crema sobre la arena oscura, rango en las dos
  esquinas, palo de marca de agua, y una **cinta con el nombre de la familia en PALABRAS**
  (HILO / VIDA / CODICIA / ORBES). El color del palo solo no alcanzaba para entender qué hacía.
- **Reglas** = placas de pizarra grabadas con un sello de lacre con el multiplicador.

La tabla `EFF` (en `p09`/sección de cartas) devuelve el **efecto concreto en números** de cada
carta según el rango que sacó ("Hilo +42% más largo"). Antes había una barra de fuerza abstracta
y la primera reacción de Franco fue *"no entiendo si es por nivel o qué"*. La regla que quedó:
**una carta tiene que decir lo que hace, no insinuarlo**. Si agregás un upgrade, agregá su
entrada en `EFF` o la carta queda muda.

Las alturas de las esquinas del naipe están **calculadas, no al ojo**: con `textBaseline
'middle'` un glifo ocupa ~±0.37·F, y por eso el rango va a 0.07 y el palo a 0.175 del alto.
La cinta de familia va por encima de la esquina invertida, que antes se la comía.

## Render

- La esfera se **hornea una vez por resize** a `dialCv` (60 marcas + 81 celdas + numerales +
  el "#" del ta-te-ti): un `drawImage` por frame en vez de ~300 llamadas de path.
- **Nada de `shadowBlur` en entidades**: el glow es `bloomPx()`, un sprite de gradiente
  radial cacheado por color cuantizado (`_glowCache`) dibujado con composite `lighter`.
  Es la lección de TankWARS/DonkeyKong y lo que mantiene los FPS en mobile.
- El hilo se dibuja en **7 tramos** con color interpolado cola→cabeza más **una sola**
  pasada de halo. Un gradiente de canvas no puede seguir un path y 200 strokes serían carísimos.
- Las piezas son **vectoriales** (`piecePath`), no glifos Unicode de ajedrez: en varios
  Android faltan y se ven como cuadraditos.
- **Radio de dibujo 1.14× el de colisión** (patrón `drawRadius` de TankWARS): se leen mejor
  sin tocar el balance.
- El trío de **context-loss** es obligatorio (iframes del Arcade sobre el mismo renderer):
  si agregás un bake nuevo, invalidalo en el handler de `contextrestored`.

## Controles

- **Táctil**: palanca dinámica en la mitad izquierda (nace donde apoyás el dedo),
  **TIRÓN** y **PULSO** abajo a la derecha. `#aimSafe` es el colchón muerto entre zona y
  botones (sandwich de z-index 3 < 4 < 5, gotcha heredado de StickFight).
- **Teclado**: WASD/flechas · `ESPACIO`/`SHIFT` tirón · `E` pulso · `P` pausa ·
  `ENTER` confirmar · `1`/`2`/`3` elegir en los drafts · `T` panel de tuning.

## QA headless (sin node)

Chrome headless con `--virtual-time-budget` **no dispara rAF de forma sostenida**: la sim
queda congelada aunque los timers corran. El loop está preparado para bombearse a mano:

- `window.LOOP.loop(t)` es llamable directo y `scheduleRaf()` tiene dedupe.
- Handle de debug: `window.LOOP = { CFG, P, game, run, RULE, hand, enemies, orbs, thread,
  inP, moveStick, keys, simon, frenzy, hourRule, resetThread, ... , freeze, slow }`.
- **El driver tiene que escribir `moveStick`, no `inP`**: `pollInputs()` reescribe `inP`
  desde la palanca y el teclado en cada frame.
- **El reloj del driver se llama `t`.** Un escenario que declare `var t` lo pisa: el bombeo se
  rompe y el bucle del test sale tras una iteración con un contador absurdo. Ya pasó.
- **Las corridas libres NO son deterministas.** Para comparar dos configuraciones hay que
  forzar `B.game.mode = 'daily'` (rng sembrado); si no, la diferencia que ves es ruido.
- `LOOP.freeze = true` congela la sim y sigue dibujando → screenshot del instante exacto.
- Harness con cazador de errores: `qa.py` de las sesiones 2026-09-12/14
  (menu · play · wave6 · intro · rule · card · slot · simon · frenzy · reglas · boss · over ·
  win · poker · tateti · dash · rope · leak · closes · afk). `reglas` recorre TODAS las reglas
  de a una; `afk` prueba el jugador quieto durante horas (la explosión de damas); `leak` cuenta
  orbes que atraviesan el hilo sin rebotar; `closes` mide cierres variando las perillas.

Ver [../CLAUDE.md](../CLAUDE.md) para las convenciones compartidas de los ports web.
