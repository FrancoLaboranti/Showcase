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

## La barrida de la flecha ahora construye tambien la PUNTA (2026-09-22)

Franco: *"la punta de la flecha aparece completa desde el principio"*. Era cierto, y estaba puesto
a proposito — el comentario del codigo lo defendia con un argumento que tambien era cierto:

> en un carril largo la cabeza mide un 8% del largo, asi que atarla al avance del cuerpo la
> dejaria casi apagada durante el 92% del aviso, justo cuando lo unico que importa es HACIA DONDE.

Las dos cosas no se resuelven eligiendo una. Se resuelven **separando forma de relleno**:

- **La FORMA esta entera desde el frame 0**, como un fantasma a alpha 0.055 — cuerpo y punta. La
  direccion se lee siempre, que era el motivo del diseno viejo.
- **El RELLENO es UN solo recorte que avanza** sobre la silueta completa. No hay dos rellenos ni
  dos alfas: el mismo corte revela el cuerpo y despues la punta, de corrido. Una sola animacion.
- **El FILO del frente es la misma silueta** recortada a una franja angosta, no un rectangulo: asi
  adentro de la cabeza se angosta solo hasta el vertice. Antes era una barra de alto fijo que no
  sabia que forma tenia la flecha.

Medido con capturas a `u` congelado (`dbgFreeze` + dos `loop(t)` con el MISMO `t`, que da dt = 0 y
dibuja sin avanzar): a 0.12 y 0.70 la punta es solo contorno; a 0.97 esta construida entera. A
`u = 1` la flecha ya no esta, porque la pieza ejecuta el movimiento — eso es el juego, no un bug.

### El acabado

Cuerpo 16% mas grueso (`r*1.12` -> `r*1.30`) y cabeza proporcionalmente mas larga.

**Las esquinas se redondean estirando el contorno**, no con curvas: se rellena Y se contornea la
MISMA ruta con `lineJoin`/`lineCap` redondos y un trazo de `pad*2`. Eso redondea todos los
vertices de una — la punta y los dos hombros donde el cuerpo se ensancha, que es la union que se
veia dura.

**Por eso la silueta se construye hasta `L - pad` y no hasta `L`.** El trazo redondo sobresale
`pad`, asi que el BORDE EXTERNO sigue cayendo exacto en el destino. Sin esa correccion la flecha
apuntaria un poco mas alla de la casilla a la que la pieza va — un error de un par de pixeles que
en un juego donde la telegrafia ES la mecanica se paga caro.

No se toco la logica de movimiento ni las reglas de telegrafia: `u`, `e.dur`, `e.tx/ty` y el carril
del caballo quedaron igual. Los 8 escenarios de `qa.py` pasan sin cambios.

## AUDIO: el techo de voces tenia una inversion de prioridad (2026-09-21)

**Te morias en silencio.** No es una forma de hablar: esta trazado frame a frame.

`ac()` cortaba en `sndThisFrame < CFG.perf.sndPerFrame` (5) y el presupuesto se lo llevaba el que
llegaba primero. En un frame de cierre de bucle el orden de ejecucion es

    hurtEnemy (hit, 1 nodo) -> killEnemy (kill, 2) -> detonateMine (pulse, 2) = 5

y a partir de ahi se caen, **en este orden**: `claim`, `tateti`, `frenzy`, `hand` y `tight`. O sea
el cierre de bucle entero, que es el acto central del juego. Sin minas tambien pasa:
hit(1) + kill(2) + claim(2) = 5 y se pierden `tateti`, `frenzy` y `tight`. Y el comentario de
`closeLoop` dice textual *"Que el bucle fue cenido ya lo dicen el fantasma dorado y EL SONIDO"* —
en ese frame el sonido no estaba.

Peor: `killPlayer` llama `sfx.lose()` DESPUES de `sfx.hurt()` (2 nodos). Con tres voces rutinarias
previas en el mismo frame — `wall` + `deflect` + `clack`, perfectamente alcanzables con 14 orbes
vivos — el presupuesto llega a 5 y **la muerte del jugador no suena**. Y `endRun` ademas llama
`droneOff()`, asi que la habitacion tambien se calla: silencio absoluto justo en el unico momento
que no puede pasar desapercibido.

### El arreglo no es subir el techo

Subirlo seria devolver el problema que el techo resuelve. El techo existe para defenderse de las
voces **rutinarias** — el rebote contra el aro, el clack, el tictac, el silbido —, que se disparan
muchas veces en el mismo frame y son las unicas que pueden ametrallar. Las voces **narrativas**
(moriste, ganaste, cerraste el bucle, entro el frenesi) ocurren como mucho una vez por frame por
construccion y son justamente lo que hay que oir.

Asi que hay **dos presupuestos**, no uno:

```js
function ac(prio) {
  if (!(AC && AC.state === 'running')) return false;
  return prio ? sndPrioThisFrame < CFG.perf.sndPrioPerFrame : sndThisFrame < CFG.perf.sndPerFrame;
}
```

`voice(name, cdMs, fn, prio)` levanta una bandera mientras corre el cuerpo (`enPrio`, restaurada en
un `finally` para que no quede pegada si el cuerpo tira), y `note()`/`noiseHit()` llaman a `bump()`,
que carga el disparo al carril que corresponde. Ni `note()` ni `noiseHit()` saben nada de esto.

**`prio` no significa "mas fuerte" ni "antes".** Significa que no comparte presupuesto con el ruido
de fondo. La reserva tiene su propio techo (`sndPrioPerFrame: 4`), asi que no es un agujero: se
verifico que con `sndPrioThisFrame = 99` una voz narrativa tampoco suena.

**`CFG.perf.sndPerFrame` esta expuesto en el panel de afinado (tecla T) y ahora significa otra
cosa**: el techo de las rutinarias, no de todo. Esta documentado en el comentario de `CFG.perf`.

Son narrativas: `loop`, `tight`, `claim`, `tateti`, `hand`, `hurt`, `chime`, `hour`, `promote`,
`boss`, `bossWind`, `frenzy`, `win`, `lose`, `mine`, `barrel`, `simon`, `simonGo` y la muerte de
dama. Todo lo demas sigue compitiendo por el techo de siempre.

### Cinco sonidos que estaban mal asociados

El patron es el mismo en los cinco: una voz compartida entre dos eventos que el juego YA distingue
visualmente.

| evento | usaba | problema |
|---|---|---|
| mina detonada | `pulse` | **el pulso es lo que la detona**, en el mismo frame: el cooldown de 200 ms se comia la mina SIEMPRE. El codigo se tomo el trabajo de que el fogonazo "diga MINA" y el oido no se enteraba |
| barril que nace | `wall` | el aviso de un peligro de 21 de dano sonaba igual que el rebote del orbe contra el aro, **el ruido de fondo mas frecuente del juego**, y compartia su cooldown de 40 ms |
| salto del caballo | `shot` | `shot` es el obus del tanque y el abanico del jefe, o sea la senal de *esquiva esto*. El caballo no dispara: SALTA |
| aviso del jefe (`wind`) | `ui` | el segundo de lectura del climax sonaba al click de 30 ms de los botones de menu |
| muerte de enemigo | `kill` unico | el juego distingue peon/torre/dama con chispas, anillo y sacudon distintos — y las tres sonaban igual |

`kill(val)` ahora tiene tres escalones que salen de `e.T.score`, que es el dato que el juego ya
tenia una linea antes y no usaba. Mas grave, mas largo y con mas cuerpo cuanto mas vale la pieza:
**432 / 340 / 234 Hz** medidos, con volumenes 0.06 / 0.075 / 0.095. El cooldown es **por escalon**
(`'kill' + k`): con un solo nombre, un peon muerto 20 ms antes se comia a la dama.

### Lo demas

- **La pestana al fondo no apagaba el colchon.** Es el unico nodo continuo del juego: dos
  osciladores arrancados una vez y nunca detenidos. Con la pestana oculta el rAF se frena,
  `updateAmbience` deja de correr y el zumbido de 55 Hz sigue sonando indefinidamente — en
  escritorio el navegador no suspende el audio de una pestana de fondo, asi que no se arreglaba
  solo. Ahora `visibilitychange` llama `droneOff()` + `AC.suspend()`, y a la vuelta `audioResume()`
  (en movil el contexto se auto-suspende y el juego quedaba mudo hasta el primer toque).
- **`simonFlash` y `updateSimon` llamaban `note()` directo**, salteando `voice()` y por lo tanto la
  guarda de estado del contexto — justo la leccion de la seccion de las guardas mas abajo. Ademas
  gastaban presupuesto de frame sin poder ser frenados por el. Ahora son `sfx.simon(f)` y
  `sfx.simonGo()`.
- **`noiseHit` no clampeaba el volumen** antes de la rampa exponencial y `note()` si, a medio
  archivo de distancia. Hoy ningun llamador puede pasar 0 (el mas bajo es `wall` con 0.005), asi
  que era una mina latente y no un sintoma — pero el proximo `noiseHit` escalado por intensidad la
  pisaba, y falla en silencio.
- **`sndThisFrame = 0` estaba DESPUES de los returns tempranos de `loop()`.** Con el contexto de
  canvas perdido el frame se va por el return, pero los handlers de DOM siguen disparando sonidos
  (`onCanvasTap` toca `ui`/`hour`/`card`) y el contador se clavaba por encima del techo. Se
  auto-curaba al restaurarse el contexto, por eso era menor — pero resetear arriba de todo no
  cuesta nada y el par `contextlost`/`contextrestored` ya existe, o sea que el estado es real.

### Como se verifico

Con un arnes headless que envuelve el `AudioContext` y anota cada nodo, cada rampa y cada
start/stop, corriendo un escenario que provoca los eventos de a uno. La prueba decisiva fuerza
`sndThisFrame = 99` y comprueba que **las rutinarias se caen (0 voces) y `lose()` suena igual**
(2 osciladores a 330 y 247 Hz, que son sus dos notas). Vive fuera del repo, en el scratchpad, junto
a `qa.py`/`qa2.py`.

**Ninguno de los 68 escenarios de la suite mide audio** — miden comportamiento y recursos. Estos
cambios no los tocan: no se movio una sola mecanica, ni un numero de balance, ni una condicion de
victoria. Lo unico que cambio de semantica es que `sndPerFrame` ahora cuenta solo las rutinarias.

**Esto no se escucho.** El arnes verifica que suene lo que se diseno, cuando se diseno y con los
parametros que se disenaron; no tiene placa de sonido. La evaluacion auditiva es de Franco.

## BARRILES: lo que DonkeyKong aportaba de mecánica (2026-09-18)

DonkeyKong venía dando sólo estructura — el draft, las semillas, la ventana de combo — y ni una
mecánica. La regla `barrels` (×1.55) es la primera que entra de verdad: barriles que llegan desde
afuera del reloj, cruzan en línea recta y **le pegan a todo**, al jugador y a las piezas.

Eso último es lo que los hace de Donkey Kong y no un proyectil más: **un barril no es del enemigo
ni tuyo, es del escenario.** Pararte del lado correcto de uno que viene convierte un peligro en
una herramienta, que es exactamente el juego que propone DK.

- **No apuntan al centro** (`a + PI + rnd(-0.55, 0.55)`). Si todos pasaran por el eje el patrón
  sería siempre el mismo y se esquivarían de memoria en dos horas.
- El daño AL JUGADOR es fijo (21, el de la dama, por `scaleDmg` como cualquier pieza). El daño A
  LAS PIEZAS va por **`scaleHp()`**: fijo, pasada la hora 8 el barril dejaría de matar nada y
  media regla se apagaría sola. Quinta vez que aparece el mismo error en este proyecto (bucle,
  pulso, orbe, curación del frenesí, barril), así que queda como regla de la casa: **lo que tiene
  que seguir importando cuando la vida enemiga crece, escala con ella.**
- Enfriamiento corto al golpear: sin él un barril arrasa una fila en un frame; con él la ARA.
- **El jefe, excluido.**
- Rotar el sprite horneado acá es lo CORRECTO, al revés que en la moto o la aguja: un barril que
  rueda tiene que girar su propio brillo, porque está girando de verdad.

### Un test que midió un mundo congelado

La primera versión del escenario puso la prueba que MATA al jugador en segundo lugar. El jugador
murió, `stepSim` dejó de correr con el estado en `'over'`, y las dos pruebas siguientes midieron
una simulación detenida — reportando "el barril no le pega a las piezas" cuando en realidad no
pasaba nada en absoluto. **En un escenario con varias pruebas, la que puede terminar la partida va
última**; si no, todo lo que venga después mide un mundo que ya no simula.

## UI 2026-09-18 — ranuras fijas, reserva de espacio y feedback asimétrico

### El HUD no puede recolocarse solo

La tira de la mano vivía en `pad + S * (run.combo >= 2 ? 0.178 : 0.118)`: cada vez que se cortaba
el combo, **saltaba hacia arriba**. Ahora hay tres ranuras con Y fijo (`Y_SCORE`, `Y_MULT`,
`Y_HAND`) y el hueco del multiplicador existe esté visible o no. Medido: 112.3 px en los dos
estados, y vuelve exacto.

Regla: **si un elemento del HUD aparece y desaparece, lo de abajo no puede depender de él.** Un
ternario en la coordenada Y es la forma más fácil de escribir un reflow sin darse cuenta.

### El espacio se reserva de AFUERA hacia adentro

La lista de jugadas al costado de la mano quedó pegada al margen dos veces seguidas, porque la
calculaba al revés: las cartas tomaban su tamaño y la lista se acomodaba con lo que sobrara. Con
la mano centrada, el hueco de la izquierda mide `(W - total) / 2` — o sea que lo fija el tamaño de
las cartas, y la lista no tiene voz.

La cuenta correcta va de afuera hacia adentro: `margen + lista + separación` es lo que la mano NO
puede ocupar **de cada lado** (de cada lado, porque va centrada), y el ancho de carta sale de lo
que queda. Así la lista siempre tiene su aire y la mano nunca se mueve.

### El marco del naipe cruzaba los números

El rango de esquina estaba en `bh*0.078` con cuerpo `0.185·bw`: su borde superior caía a
`0.022·bw` del borde del naipe, y la regla interior estaba a `0.058·bw`. Se cruzaban por
construcción. Resuelto por layout y sin agrandar el naipe: el marco salió a `0.046` y el contenido
entró a `bh*0.125` (que es exactamente `(0.046 + holgura + 0.5·cs) / bh`), más los anchos máximos
del nombre y del efecto, que llegaban a tocar la segunda regla.

### En frenesí, TODO lo tuyo se los come

El contacto directo hacía `hurtEnemy(e, 999)` pero el orbe y el pulso seguían con su daño normal:
dos reglas distintas para el mismo estado. Ahora los tres matan de un toque durante el frenesí —
**el jefe explícitamente afuera**, porque el frenesí no puede saltearse la pelea. Medido: orbe
120/141 → muerto, pulso 138/141 → muerto, jefe 2600 → 1776.

### El número del TIGHT se va; el multiplicador se queda

Antes de sacarlo había que mirar qué hacía: `tight` **multiplica el daño del bucle** hasta ×3.3,
no es decorativo. Lo que no aportaba era el NÚMERO — un "x2.4" al lado de un "148" agrega una
incógnita en vez de información, y el daño ya está a la vista. Que el bucle fue ceñido lo dicen el
fantasma dorado y el sonido. El test lo verifica inspeccionando la fuente de `closeLoop`: el
multiplicador tiene que estar, el cartel no.

(Primer intento del test: cerrar bucles con el bot y mirar los carteles. Dio verde con **cero
bucles cerrados** — un test que casi nunca dispara la rama que dice cuidar no prueba nada.)

### Feedback asimétrico a propósito

`healPlayer(n, callado)`. El goteo del frenesí son treinta y pico de ticks de 1 HP, y treinta y
pico de "+1" verdes saltando encima de la canica tapan justo lo que hay que mirar. El daño
RECIBIDO sigue sacando su número: **el golpe hay que registrarlo, la curación se lee sola en la
barra.**

### El joystick es el plato en miniatura

Más chico (0.155 → 0.125 del lado corto) con la zona muerta bajada de 0.10 a 0.075 para no perder
control fino — el radio ES la resolución de la palanca, así que achicarla se paga y hay que
compensarlo. Visualmente: fieltro oscuro, aro de latón, filo de luz arriba, y el pomo es **la
canica** con el mismo degradado y el mismo brillo especular. Lo que arrastrás se parece a lo que
estás arrastrando.

Dos detalles que importan:
- Se mueve con **`transform`**, no con `left`/`top`: left/top fuerza recálculo de layout en cada
  movimiento del dedo.
- El pomo viaja hasta `BASE_R - KNOB_R`, o sea que queda **siempre dentro del aro**, mientras el
  input sigue midiéndose sobre `BASE_R` completo. Es un remapeo lineal de lo que se ve: no se
  pierde ni un paso de precisión y deja de parecer que el pomo se escapa.

## Pasada de ASIGNACIONES (2026-09-17, noche)

Hasta acá siempre había medido operaciones de canvas. Nunca **asignaciones** — y en un móvil el
recolector se paga en tirones, o sea que la basura constante es justo lo que produce los picos
hacia abajo. Seis fuentes, y **tres las había metido yo optimizando**:

| dónde | qué hacía | ahora |
|---|---|---|
| `autoDpr` | `Array.from(40).sort()` **en cada frame** | typed array reusado, evalúa cada `dprEvery` |
| cachés de sprite | armaba la clave concatenando strings por pieza/orbe/obús **por frame** | el sprite se recuerda en la entidad y se compara un NÚMERO |
| chispas | un string `rgba(...)` por chispa por frame (~50) | `globalAlpha` + color cacheado por valor |
| drafts | `hand.concat()` + `evalHand` (con `map`+`sort`) por carta **por frame** | se calcula al ABRIR |
| viñeta de vida baja | gradiente nuevo + dos strings por frame | gradiente cacheado + `globalAlpha` |
| cierre del jefe | `enemies.some(e => …)` = un closure por frame | bucle plano |

**Lección de método, la más cara de la sesión: un perfilador que no mide algo no dice que sea
barato — dice que no lo mide.** Pasó dos veces seguidas: primero con la construcción de paths (el
hilo era el 34 % del render y no aparecía), ahora con las asignaciones. Y las dos veces la mitad
de lo que encontré lo había introducido yo en la pasada anterior "optimizando". Cada optimización
hay que medirla con la vara que corresponde a lo que toca.

### Cachear por VALOR, no por identidad

El caché de strings de color arrancó con un `WeakMap` sobre el array de color. No servía: casi
todos los llamados a `spawnSparks` pasan un literal nuevo (`[120,170,230]`), así que la referencia
nunca se repite. La clave es el color empaquetado en un entero — buscar con un número no asigna
nada, que es todo el punto del ejercicio.

### Lo que NO se encontró

Nada significativo en física, animaciones ni "elementos fuera de pantalla": el juego tiene UNA
arena y todo lo que existe está a la vista, así que no hay culling que hacer. Post-processing son
sólo las dos viñetas. Vale registrarlo para no volver a buscar ahí.

## La curación del frenesí va de a 1 HP

Mismo total (`healFrac` = 1/3 de la barra) y mismo tiempo; cambia el GRANO. Medido: con 100 de
vida máxima son 33 ticks de exactamente 1 HP repartidos en 6.30 s de los 6.5; con 220, **74 ticks**
— más ticks, no ticks más gordos, que es lo que hace que la fracción sea la unidad correcta.
El `while` que los entrega tiene tope de 4 por frame para que un frame largo no dispare una ráfaga.

## El mismo layout no sirve para las dos orientaciones

La tabla de jugadas del panel del mazo va a la IZQUIERDA en apaisado (donde sobra ancho): no se
come alto y los naipes crecen. En VERTICAL va abajo, porque ahí lo escaso es el ancho y una
columna lateral les robaba más de lo que les liberaba — medido, dejaba las cartas **19 % más
chicas** que antes. Es el mismo patrón que ya había aparecido con `panelRects`: cuando una medida
sale de `min(fracción_de_W, fracción_de_S)`, en cada orientación manda una distinta.

## Resolución de mobile: base fija, adaptativo sólo como red

`CFG.perf.dprMobile = 1.4` es con lo que ARRANCA un táctil y lo que mantiene: una resolución
estable se siente mejor que uná que se mueve sola a mitad de partida. `dprCeil` es además el
TECHO del afinador, así que lo adaptativo sólo puede bajar, nunca subir por encima de la base.
Verificado para devicePixelRatio 1 / 1.5 / 2 / 2.625 / 3 / 4: todos los de 1.5 o más quedan
exactos en 1.40, y el de 1x se queda en 1.00 porque no se puede renderizar por encima de lo
nativo (`dprMin` acota cuánto puede BAJAR el afinador, no la resolución nativa — mi primer
chequeo confundía las dos cosas y marcaba un falso positivo).

## Playtest 2026-09-17 (tarde)

### El joystick se comía la tira de la mano — y sólo en APAISADO

`elementFromPoint` sobre el centro de la tira devolvía `jMove`. La zona mide 52 % × 84 %, y con
`H` chico —que es lo que pasa en apaisado, que es **como está registrado Loop en el Arcade**— ese
84 % trepa hasta el HUD. En vertical no pasa. Regla: cuando una zona táctil se define en
PORCENTAJE de pantalla, hay que probarla en las dos orientaciones; el mismo número tapa cosas
distintas según cuál sea el lado corto.

La solución no es achicar la zona (empeora el control, que es lo que se quería arreglar): el
joystick **pregunta** si el punto pertenece a algo tocable del HUD (`hudTap`) y le cede el toque.
Vive en `p04_input` y no adentro del joystick, para que cualquier zona futura consulte lo mismo.

**Ojo al verificarlo**: el arreglo actúa a nivel de EVENTO, así que `elementFromPoint` **sigue**
devolviendo `jMove` y no prueba nada. Hay que despachar un `pointerdown` de verdad y mirar la
conducta. Y `moveStick.active` tampoco sirve como señal — el joystick lo prende recién al salir
de la zona muerta. La señal honesta es mandar un `pointermove` y ver si la palanca respondió.

### El Simón ya no castiga

Franco: *"que la penalización venga dada orgánicamente de perder el beneficio extra"*. Se fue todo:
no hay sector rojo, no hay perder por quedarse parado, no hay vencimiento. La secuencia espera
hasta que la completes o hasta que el cambio de hora se lleve la regla. Volvió la **pista** del
sector que toca (arriba sigue sin mostrarse nada).

El principio: **un castigo explícito encima de perder el premio es cobrar dos veces por la misma
decisión.** Si el minijuego es opcional, no completarlo ya es la consecuencia.

### El panel del mazo LISTA las manos

Mostraba sólo la mano actual, en un tamaño ilegible en mobile. Pero la pregunta del jugador no es
"qué tengo" —eso lo ve en las cartas— sino **"qué me conviene armar"**. Ahora lista las ocho con
su efecto y marca la actual: deja de ser un cartel de estado y pasa a ser un motivo.

### El frenesí cura

*"Es mucha la presión de no recibir daño."* El frenesí ya es la recompensa del ta-te-ti y ya te
hace intocable: sumarle curación lo vuelve LA ventana de recuperarse sin inventar un sistema
nuevo, y le da una segunda razón para ir a cerrar la línea.

`CFG.frenzy.healFrac` va como **fracción de la barra**, no como HP/s. Con un número fijo, a más
vida máxima (cartas de VIGOR) la curación se volvería insignificante — el mismo error que ya
tuvieron el bucle, el pulso y la orbe: daño fijo contra vida que escala. Se cobra en tandas de
~1/9 de barra porque `healPlayer` saca un número flotante por llamada y a 60 fps serían sesenta
numeritos por segundo.

### Resolución adaptativa en vez de bajar la calidad a mano

`autoDpr` mide la MEDIANA del frame (no el promedio: un solo frame largo no puede mover la
decisión) y ajusta `dprScale`. Histéresis 17.5 ms / 13.5 ms para que no bombee, y enfriamiento de
2.5 s porque cada cambio llama a `resize()` y eso re-hornea todo — **si el remedio produce el
síntoma, no es remedio**. En un equipo que llega a 60 no baja nunca.

Trampa aritmética que casi se me pasa: el piso `dprMin / base` puede quedar **por encima de 1** en
un equipo con `devicePixelRatio` 1, y entonces "bajar" terminaría SUBIENDO la escala. Va acotado
con `Math.min(1, ...)`.

### Un invariante no puede depender del ORDEN

`ORB-SPD: v=3.08 contra un tope de 1.75` volvió después de darlo por arreglado. El primer intento
puso el clamp después de los pares orbe-orbe, pero el problema nunca fue ese lugar puntual: hay
**cinco** cosas que empujan orbes (pares, péndulos, bengalas, el tirón del frenesí, las
campanadas) y varias corren DESPUÉS de `updateOrbs` — `frenzyBurst` las empuja con +1.4.

`clampOrbSpeeds()` es ahora la última palabra de `stepSim`, cuando ya empujó todo el mundo.

**Un invariante que depende de en qué orden corran las cosas, o de cuántas veces por frame corran,
no es un invariante.** Se aplica una vez, al final.

### Y borrar por rango se lleva vecinos

Sacar el cartel de hora borrando de `function drawIntro` hasta `function onCanvasTap` se llevó
puesta `drawEndScreen`, que vivía en el medio. Lo cazó la regresión (`drawEndScreen is not
defined`), no yo. Cuando se borra un bloque por rango, hay que mirar qué hay adentro del rango.

## El costo que no dependía de nada (2026-09-17)

Franco, después de la pasada anterior: *"está un poco lento todavía y eso que al principio sin
mucho en pantalla"*. **Esa frase es el diagnóstico**: si cuesta igual con la arena vacía, lo caro
no es por objeto — es POR FRAME FIJO, y todo lo optimizado antes escalaba con la cantidad de
objetos. Cuando alguien reporta lentitud, la primera pregunta útil es *¿con qué escala?*

### El perfilador tenía un agujero

Contaba `fill`, `stroke`, `clip`, gradientes y `drawImage` — pero **no la construcción de paths**.
`moveTo`/`lineTo`/`quadraticCurveTo` son trabajo de CPU por vértice y no aparecían por ningún
lado. Al agregarlos:

    34.2%  drawThread   412 comandos de path por frame

El hilo tiene hasta 195 puntos y se recorre tres veces (una pasada de resplandor con cuadráticas
más la cinta rellena, que va de ida y de vuelta). **Estaba siempre ahí**, con o sin enemigos. Es
decir: el mayor gasto del render nunca había aparecido en el perfil, y era justo el que explicaba
el síntoma. Un perfilador que no mide algo no dice que sea barato — dice que no lo mide.

### Las dos correcciones

**1. Decimado adaptativo del dibujo.** Los puntos están a `CFG.thread.spacing` (0.010 u), que en
pantalla es `spacing * PXR`: ~4.8 px en un monitor y ~2.3 px en un teléfono. Mandar un vértice
cada 2 px es tirar resolución que ningún ojo ve. El paso se calcula para que los vértices queden a
~5.5 px, así que da 1 en desktop (no cambia nada) y 2 en pantallas chicas — el recorte cae solo
donde hace falta. **La simulación sigue con todos los puntos**: esto es sólo cuántos vértices se
mandan a dibujar. 412 → 214 comandos, y en una curva cerrada no se ve facetado.

Detalle que importa: la tangente se toma contra los vecinos **dibujados** (`i ± step`), no contra
los originales. Si no, la normal no corresponde al polígono que de verdad se traza y la cinta se
abre en las curvas.

**2. La simulación corría DOS VECES por frame.** `steps = min(3, max(1, ceil(simDt / (1/70))))`:
con `1/70`, un frame de 60 fps da `ceil(1.167) = 2` **siempre**. O sea que la soga entera — medidas
713 resoluciones de restricción + 237 integraciones por frame con la arena vacía — se resolvía dos
veces en el caso normal. Con `1/50` el frame de 60 fps entra en un subpaso y el segundo aparece
recién por debajo de 50 fps. El trabajo por SEGUNDO en un equipo lento no cambia; lo que se va es
el doble gasto cuando todo va bien.

Verificado antes de darlo por bueno, porque los subpasos existen para algo: **tunneling 0/50** con
hilo quieto (5 velocidades × 2 timesteps) y **0/56** con hilo en movimiento, 14/14 rebotando.

### Bajar el costo destapó un bug que el costo tapaba

Al pasar a un subpaso, `frenzy50` marcó **ORB-SPD: v=3.08 con el tope en 1.75**. No lo rompió el
cambio: lo *reveló*. El clamp de velocidad vive DENTRO del bucle por orbe de `updateOrbs`, y
`resolveOrbPair` corre **después** de ese bucle — así que el impulso de un choque encadenado se
iba sin tope hasta el frame siguiente. Con dos subpasos, el segundo lo clampeaba dentro del mismo
frame y el agujero nunca se veía.

O sea: **el tope estaba tapado por el costo, no cerrado.** Un tope que depende de cuántas veces
por frame corra la física no es un tope. Se arregla aplicándolo también después de resolver los
pares, no volviendo a los dos subpasos.

Tercera vez en este proyecto que aparece la misma forma: algo defensivo (un `|| 1`, un subpaso de
más, un `chk` que comparte el error con el código que audita) **oculta** el problema en vez de
delatarlo. Cuando una optimización rompe un test, vale la pena preguntarse si lo rompió o si lo
destapó.

### Y de paso

- Cinco `new Array(n)` por frame en `drawThread` (~1000 números) pasaron a `Float32Array` que viven
  entre frames. A 60 fps eso era basura constante para el recolector, y en un móvil el recolector
  se paga en tirones.
- Los filos de las celdas de mina pasaron de polilíneas trazadas a `fillRect`: una línea de un
  píxel y un rectángulo de un píxel se ven igual, pero `fillRect` no construye path (eran ~125
  comandos por frame, ahora cero).

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
| DonkeyKong | Draft de modificadores; seeds derivadas; combos con ventana; **BARRILES** | `openRuleDraft`, `mulberry32`, `updateBarrels` |
| StickFight | Estructura del archivo, audio con `voice()`, shell del Arcade | todo el esqueleto |

## Qué del repo entró de verdad, y qué quedó afuera

La tabla de arriba dice de dónde salió cada cosa, pero varias entradas están **de nombre más que
de sustancia**. Esto es el mapa honesto, para no volver a creer que algo está cubierto:

| Origen | Estado real |
|---|---|
| **Ahorcado** | **Afuera del todo.** THE GALLOWS fue un intento y se eliminó (ver su sección). El pool quedó sin nada de Hangman. |
| **Snake** | Aportó la FORMA del rastro, no su REGLA. En Snake cruzarte **te mata** y comer **te agranda**; acá cruzarte es la RECOMPENSA y el largo es un presupuesto que se compra con cartas. Las dos ideas que definen a Snake están invertidas o ausentes. |
| **Tron** | Medio adentro. LIGHT CYCLES dio el lado enemigo (una moto cuya estela quema), pero **tu propio hilo no es una pared**: roza por 3.5 con enfriamiento, no mata. En Tron el punto es que TU línea es letal. |
| **Fireworks** | Sólo estallido al morir y la regla PIROTECNIA. El ciclo que lo define — lanzar, arco, reventar en patrón — no está. |
| **Ajedrez** | La coronación sí; la decisión de tablero no. Las piezas son amenazas telegrafiadas, no un rival moviendo. |
| **DonkeyKong** | Era sólo estructura hasta que entró BARRILES (2026-09-18). |
| **StickFight** | Esqueleto del archivo, `voice()`, shell del Arcade. **Cero mecánica.** |

### Tres mecánicas cableadas que NADIE puede obtener

`P.thorns` (devolver daño al recibirlo), `P.loopHeal` (curarte al cerrar un bucle) y `P.lifesteal`
existen, se resetean en `recomputeStats` y **se chequean en el juego** — pero ninguna carta ni
regla las sube nunca de 0. Son código que corre para algo que no puede pasar.

No es urgente arreglarlo, pero conviene saberlo por dos motivos: son ranuras listas si hace falta
tapar alguna de las ausencias de arriba, y son exactamente el tipo de cosa que un lector futuro
va a suponer que funciona. (Misma familia que el `thread[j].w || 1` que hacía del pincel código
muerto, o que `chargeCd` faltando en el espejo.)

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

**Agujero encontrado el 2026-09-18: `ALL` no era la lista de escenarios, era una lista a mano.**
`SCENARIOS` tenia 47 definidos y `ALL` nombraba 35. Los DOCE que faltaban eran justo los mas
nuevos - `boss`, `barriles`, `hudfijo`, `fkill`, `feedback`, `dprbase`, `heal`, `handtouch`,
`touchsel`, `feel`, y los dos de hoy - o sea que `python qa2.py` a secas jamas los corria y solo
se ejecutaban nombrandolos a mano el dia que se escribieron. Ya estan todos en `ALL`. **Cuando se
agrega un escenario hay que agregarlo a `ALL` en el mismo movimiento**, o nace muerto: pasa una
vez y despues no vuelve a correr nunca.

Agregados el 2026-09-18: **`peon`** (el peon come en diagonal y avanza derecho; elige celdas A MANO
y no al azar, porque lo que se prueba es una regla determinista - con posiciones sorteadas pasaria
por casualidad la mitad de las veces) y **`obus`** (24 obuses cruzando un hilo de 112 puntos desde
todos los angulos: ninguno puede cambiar de bando, y uno tiene que llegar igual al jugador con el
hilo en el medio).

## Playtest 2026-09-18 - el peon decide, y el hilo deja de ser un paraguas

### El hilo ya no para los obuses

`updateShells` reflejaba el obus que cruzara el hilo y le cambiaba de bando: en el papel era la
fusion Pong + Tank Wars, y era la idea que mas me gustaba de todo el modulo. En la mano no
funcionaba, y la razon es puramente geometrica: el hilo mide casi un plato de largo y va
ARRASTRANDO detras tuyo, asi que tapa un arco enorme en todo momento. El obus rebotaba SIEMPRE.
Franco lo dijo en una linea: "imposible que te hagan algo asi". Un tanque que no puede pegarte no
es un enemigo - es un dispensador de proyectiles propios.

Ahora el obus ATRAVIESA el hilo y lo unico que se hace con el es esquivarlo. El ORBE sigue
rebotando, y esa asimetria es la regla, no una inconsistencia: **el orbe es de la mesa y lo podes
hacer tuyo; el obus es de quien lo disparo.**

Se fueron con el rebote: `run.reflects`, el logro `devolver` ('10 shells returned'), el campo
`deflCd` del obus y el `px/py` que solo usaba el barrido. Los logros son solo toasts (no hay
pantalla que los liste), asi que sacar una clave de `ACH` no rompe nada.

### El peon: avanza derecho, come en diagonal

Era la unica pieza del tablero sin decision - apuntaba al centro y caminaba. Y es justo la pieza
de ajedrez con la regla mas particular de todas, y la mas facil de leer desde afuera.

`pawnLane(e, c, r, pc, pr)` (en `p08_enemies.js`, arriba de `pickLane`) decide UNA vez, al elegir
carril, antes de telegrafiar:

- `adelante` = hacia el centro del plato, reducido al eje dominante. Ahi es donde el peon corona.
- Las dos diagonales de captura salen de `adelante` mismo: la perpendicular de un eje es su par
  invertido (`p = [f[1], f[0]]`), asi que con `f=(1,0)` dan `(1,1)` y `(1,-1)`.
- Si el jugador esta PARADO en una de esas dos casillas, va por ahi. Captura de ajedrez: una
  casilla, en diagonal, y solo si hay algo que comer. Si no, avanza.

Se evalua una sola vez a proposito. Entre la decision y el golpe hay medio segundo de telegrafia
(`aim: 0.50`), y ese medio segundo es la salida del jugador. Un peon que recalculara te
PERSEGUIRIA, y perseguir no es lo que hace un peon: un peon te castiga por haberte quedado parado
en el lugar equivocado. Y es determinista, no sorteado - si sorteara, la regla dejaria de ser una
regla y el jugador no podria hacer nada con ella salvo tener suerte.

`e.pawnBite` marca la captura y `drawTelegraphs` pinta ese carril en CARMESI en vez del blanco
hueso del peon. Sin eso la regla existiria solo en el codigo: el jugador veria un peon moverse
raro y no sabria que fue por donde estaba parado.

### El naipe estaba corrido, y el motivo era la rotacion

La cinta del palo se le montaba al palo de la esquina de abajo. Mirando los numeros sueltos no
cerraba: la cinta iba de `bh*0.700` a `0.792` y el RANGO de esa esquina esta en `0.875`. Lo que
faltaba ver es que esa esquina se dibuja con `rotate(PI)`, asi que su palo, que en coordenadas
locales va `+0.097` POR DEBAJO del rango, en pantalla cae `0.097` POR ENCIMA: `bh*0.778`, justo
adentro de la cinta.

**Leccion general: en un bloque rotado 180 grados, todo desplazamiento local invierte su signo en
pantalla.** Cualquier calculo de colision de layout tiene que hacerse en coordenadas de pantalla,
no en las del bloque.

La franja util del naipe va de `0.257` (pie de la esquina de arriba) a `0.743` (techo de la de
abajo, que es su PALO y no su rango). El bloque de contenido estaba centrado en `0.585`. Subio
`0.085` ENTERO, sin tocar los espacios internos - lo que estaba bien adentro sigue igual - y la
cinta ademas se angosto de `0.66` a `0.58` de ancho, porque sus tapas redondas llegaban a
`0.83*bw` y el palo de la esquina vive en `0.820`. Que dos cosas no se toquen por tres pixeles no
es que no se toquen.

### El Relojero, con mas vida

De 2600 a 4400. La pelea estaba ARREGLADA (la ventana del nucleo abierto, la armadura de 0.30 a
0.55, el tope de invocaciones) y con eso se paso de largo: de peaje imposible a tramite. Lo que
sobraba era DURACION, no dificultad - el compas leer/esquivar/castigar esta donde tiene que estar,
solo que se acababa antes de que llegaras a jugarlo dos veces. Por eso se movio la vida y NADA
MAS: tocar `armor` o `openDmg` volveria a mover el sentimiento de la pelea.

### Nada de tipografia decorativa en texto que se dibuja

Paso dos veces seguidas. Primero el punto del medio (`·`): "eliminalos de todo el juego, no los
quiero ver". Se reemplazo por comas y por RAYA LARGA donde encabezaba... y a la vuelta siguiente
Franco pidio sacar tambien la raya larga: "no quiero que diga 'Promoted - Queen', ese caracter no
lo uses en nada".

**La leccion no es cambiar 129 caracteres, es la regla:** un separador que no es ni una palabra ni
un signo comun obliga al lector a interpretarlo, y a este tamano sobre fieltro oscuro se lee como
un guion roto. Cambiar un signo raro por otro signo raro no arregla nada — por eso fallo la
primera vez.

Los textos que se DIBUJAN se reescriben como FRASES, no se les cambia el separador:
`'PROMOTED TO QUEEN'` no necesita ninguno, y en el panel de info cada raya paso a ser un punto y
una oracion nueva. Donde de verdad hacia falta separar dos cosas va coma o dos puntos. El nombre
de "sin jugada" en `HAND_BONUS[0]` era `—` y ahora es `'NONE'`: una palabra dice lo mismo y
ademas se lee.

En los COMENTARIOS, guion simple. Ojo con uno: `0.74·r` era una MULTIPLICACION, no un separador, y
un reemplazo a ciegas lo habria convertido en `0.74-r`. Va asterisco.

**Chequeo, no memoria:** despues de tocar esto hay que contar los caracteres en el `index.html`
construido (`—`, `–`, `·`, el escape `—` y `&mdash;`). Todos en cero.

### El boton de INFO se escribe contra el CODIGO, no contra la memoria

Seguia diciendo que las cartas llegan alternando con las reglas. Eso dejo de ser cierto hace
rato: **la REGLA es por calendario (todas las horas) y la CARTA es por PUNTAJE** (`CARD_SCORE`,
`nextCardAt`, `cardsDue`), y el draft se abre en el momento en que cruzas el umbral, en plena
hora. Tambien decia que al jefe "solo los bucles le hacen dano completo", cuando hoy la armadura
es 0.55 y la ventana del nucleo abierto multiplica por 3.

**Regla de la casa: el panel de info es documentacion de usuario y envejece igual que cualquier
otra. Cada vez que cambie una mecanica hay que abrirlo.** Lo que dice hoy, verificado contra el
codigo: rueda de reglas por hora, cartas por puntaje con reemplazo cuando la mano esta llena,
frenesi una vez por hora que cura un tercio de la barra, y que el hilo NO para los obuses.

## El barril tiene que ser un BARRIL, no una esfera con rayitas

Franco: "no se distinguen bien por su tamano y parecen otro tipo de orbe mas que un barril". El
problema no era el tamano. Estaba dibujado como una ESFERA que rotaba sobre si misma, y una esfera
con dos rayitas es una orbe con dos rayitas.

Un barril que rueda por el piso, **visto desde arriba**, es otra cosa:

- Su **eje es perpendicular al viaje**. Rueda hacia adelante, asi que el cilindro esta acostado
  cruzado: la silueta es mas larga a lo ancho que a lo largo del movimiento, y esa proporcion sola
  ya dice hacia donde va. No hace falta ninguna flecha.
- Es **mas gordo en el medio de su largo**. Esa panza es lo que separa un barril de una lata.
- **NO GIRA EN EL PLANO DE LA PANTALLA.** Esto era el error de fondo. El eje de rotacion de un
  barril que rueda hacia vos es horizontal, o sea perpendicular a la camara: en pantalla la
  silueta no se mueve nada. Rotar el sprite en el plano es una moneda bailando, no un barril.
- Entonces se ve que rueda por las **duelas**: las tablas corren a lo largo del eje y giran con la
  superficie, asi que en pantalla barren de un borde al otro. Los **aros** de metal estan en
  planos perpendiculares al eje y se quedan quietos. **Duelas que barren + aros quietos = rueda.**
  Es el truco de la rueda de carreta en animacion vieja.

`spin` (un angulo de pantalla) paso a ser `roll` (la fase de la SUPERFICIE). Y **se fue el
horneado**: existia porque el sprite rotaba, pero ahora la silueta es fija y lo que cambia son las
duelas, asi que un bake se regeneraria entero en cada frame — seria mas caro, no mas barato. Son
tres barriles como mucho y solo con la regla puesta. La luz SI se contra-rota (como la moto, la
aguja y la torreta): el barril no gira en el plano, entonces su brillo se queda donde esta la luz
de la escena.

`CFG.barrel.r` (0.048 -> 0.058) es el radio de COLISION y queda a proposito entre los dos semiejes
del dibujo (0.075 a lo ancho, 0.048 en el sentido del viaje). Con una silueta alargada un circulo
es siempre un compromiso; que caiga del lado generoso para el jugador es la decision.

## EL LUCHADOR (StickFight) — el primer enemigo que se acerca y se compromete

StickFight no habia aportado **ni una** mecanica. Lo que tenia para dar es lo que faltaba: en la
arena habia cuatro maneras de que algo te amenazara — carril telegrafiado (piezas), persecucion
(fantasma), proyectil (tanque, barriles) y estela (moto) — y **ninguna entra a distancia de un
brazo y se queda ahi**.

Camina hasta vos, planta los pies y tira una tanda de tres: jab, jab, envion. **Mientras pega no
se mueve**, y esa es toda la contrajugada. El envion llega casi al doble que un jab (0.200 contra
0.115), asi que retroceder un poquito no alcanza: o salis de verdad, o comes el ultimo.

Tres cosas que encontro la QA y que valen mas que el enemigo:

1. **Se plantaba aunque estuviera de espaldas.** Durante la preparacion gira LENTO a proposito
   (para que se lo pueda juquear por un costado), asi que no alcanzaba a corregir medio giro y
   tiraba la tanda al aire. Pasa de verdad en partida: un bucle o un pulso lo empujan. El arreglo
   no es un caso especial sino una condicion — si no esta encarado sigue CAMINANDO, que es el
   estado donde gira rapido, y se acomoda solo.
2. **El puno flotante hacia que abrazarlo fuera la defensa perfecta.** Como disco en la punta del
   brazo, el envion golpeaba un ANILLO (entre 0.140 y 0.260) y no tocaba nada adentro de 0.140.
   Cuanto mas cerca, menos te pegaba el golpe mas grande — exactamente al reves. **El arreglo no
   es mover numeros: es que la prueba de impacto describa lo que se ve.** Un brazo que se estira
   barre desde el cuerpo hasta la punta, asi que el impacto va contra el SEGMENTO cuerpo->puno.
   El escenario paso de 2 golpes de 3 a pegado, a 3 de 3, sin tocar un solo alcance.
3. **Una figura de palo pone mucha menos tinta que una silueta llena del mismo radio**, asi que al
   mismo `r` que una pieza se lee bastante mas chica. Se dibuja a 1.3 veces el radio de colision
   (el radio de colision NO se toca: lo que hay que corregir es cuanto OCUPA en pantalla). Y las
   proporciones importan mas que el tamano: con la cabeza compitiendo con el tronco, todo el medio
   queda hecho un nudo y solo se entiende la pose que estira el brazo.

La marcha es procedural, no una tabla de cuadros: el pie describe una elipse — avanza levantado,
vuelve apoyado — y la rodilla sale de doblar hacia adelante segun cuanto se acorto la pierna. El
ciclo avanza con lo que AVANZA el muneco, no con el reloj: si lo frenan, cojea mas lento en vez de
patinar. **Un ciclo de marcha se lee por la SEPARACION de los pies, no por el balanceo del
cuerpo.** Tinta clara sobre el fieltro, que es el look de StickFight dado vuelta (alla era tinta
sobre papel).

El telegrafo no es un carril sino un ARCO de alcance que se llena mientras el brazo se recoge, y
desaparece cuando el puno sale: para cuando se ve el puno ya no hay nada que decidir. Mismo idioma
que el carril de una pieza — la forma dice donde, el llenado dice cuando.

## La vida del jefe se MIDE, no se estima

Dos intentos a ojo fallaron seguidos: 2600 y 4400, los dos "muy facil". A la tercera se hizo el
escenario `bossdps`, que barre orbitas alrededor del jefe y mide cuanto dano por segundo se le
puede meter de verdad. Resultado a la hora 12:

    mejor orbita (radio 0.20, apenas por afuera del jefe)     74 /s
    lo mismo con mano de dano (x1.7)                         163 /s
    + acertando la ventana del nucleo abierto (techo)        273 /s

Con 4400 eso es una pelea de **dieciseis segundos**. No es que el jefe fuera facil: es que no
llegaba a pasar. Se paso a **12000** — 44s al techo, ~60s a un jugador bueno pero no perfecto.

**Por que la intuicion se queda tan corta acá:** el nucleo abierto multiplica por 3 y esta abierto
el 40% del compas, y encima a la hora 12 el jugador llega con mano armada. Dos multiplicadores
encimados sobre una base que ya escala con la hora. Cualquier numero elegido a ojo va a errar por
un factor, no por un margen.

**La primera version de `bossdps` media mal, y el error es la pelea entera.** Modelaba al jugador
experto como el que gira PEGADO al jefe y rapido: dio 4/s con 38 bucles cerrados, contra 64/s con
solo 15 bucles del que gira lejos y lento. El que cerraba MAS bucles hacia MENOS dano. La razon es
geometrica: **un bucle lastima lo que queda ADENTRO**, y girar pegado cierra bucles chiquitos al
lado tuyo que no contienen al jefe. El jefe mide 0.15 de radio; la tecnica es girar por afuera de
eso. La version corregida barre radios en vez de adivinar cual es el optimo — cuando no sabes cual
es la tecnica buena, no la supongas, barrela.

**Lo que NO se toco, a pedido de Franco:** la ventana del nucleo abierto y que las agujas no
bateen las orbes. Son lo que hizo que la pelea se sintiera una pelea. Un jefe que se defiende
menos tiene que aguantar mas; eso no es un parche, es la consecuencia.

## qa2.py: el archivo temporal lleva el PID

`QA_HTML` era un nombre fijo (`_qa2.html`). Dos corridas de QA a la vez se pisan: una escribe su
escenario, la otra lo sobreescribe, y el Chrome de la primera termina corriendo el escenario de la
segunda. **Paso de verdad** — en un informe aparecio `### ruleclean` con las notas de `bossdps`.

Lo grave no es la colision sino que es INVISIBLE: no falla, MIENTE. Un escenario reporta BAD(0)
sobre codigo que nunca ejecuto. Ahora `QA_HTML` incluye `os.getpid()`.

## Dos bugs de playtest, y los dos tests que casi mienten

### El fantasma orbitaba en vez de pegar

Franco: "los fantasmas se quedan dando vueltas alrededor mio en vez de ir a pegarme". Medido ANTES
de tocar nada, y la forma del resultado es el diagnostico entero:

    jugador QUIETO              distancia minima 0.000   8 toques    ok
    gira a 0.30 (mas LENTO)     distancia minima 0.120   0 toques    <-- el bug
    gira a 0.44 (a la par)      distancia minima 0.009   4 toques    ok
    huye a 0.86 (mas rapido)    distancia minima 0.139   0 toques    correcto

**Fallaba solo contra un jugador mas lento que el.** Eso descarta la velocidad - le sobra - y
senala la punteria. Eran dos cosas multiplicandose:

1. **El adelanto era una DISTANCIA FIJA (0.34), no un tiempo.** Apuntaba siempre a 0.34 por
   delante del jugador, incluso teniendolo a 0.05. A esa distancia un punto 0.34 adelante queda
   casi PERPENDICULAR a su avance: pasaba de largo, volvia, pasaba de largo otra vez. **La orbita
   no era un error de calculo: era la solucion correcta al problema equivocado.** Ahora el
   adelanto es `t = distancia / velocidad propia` — "donde vas a estar cuando yo llegue" — y de
   cerca tiende a cero, o sea que termina apuntando AL jugador, que es lo unico que cierra una
   persecucion.
   Y explica por que el caso facil de probar a mano andaba: el error angular depende de cuanto
   avanza el jugador en el tiempo de vuelo, y contra uno que va a la par del fantasma el 0.34 fijo
   resultaba ser casi el valor correcto de casualidad.
2. **El radio de giro era mas grande que el contacto.** A 0.44 u/s con 2.6 rad/s el radio minimo
   es 0.169 y el contacto ocurre a 0.069: **mas del doble**. Aun apuntando bien, cualquier error
   cerca se volvia una orbita estable sin salida geometrica. Ahora gira mas rapido cuanto mas
   cerca esta, que ademas es lo que se espera de un fantasma: flota, no tiene inercia.

Se conserva que un jugador a fondo pueda escaparse, y el escenario lo vigila.

### La pieza telegrafiada volvia de un salto a su posicion vieja

`pickLane` guarda `sxp/syp` (el origen de la embestida) cuando la pieza DECIDE, o sea antes del
medio segundo de telegrafia. Si durante ese rato la empujas - un bucle, el pulso, una embestida,
un barril - la pieza se mueve, pero al arrancar el embate el carril interpola desde `sxp/syp` y la
TELETRANSPORTA de vuelta.

Se re-ancla el origen al arrancar: sale de donde realmente esta. **El destino no se toca, y es a
proposito:** `drawTelegraphs` dibuja el carril desde la posicion ACTUAL hasta el destino fijo, asi
que lo que el jugador vio prometido fue "voy a terminar ahi". Mover el destino romperia esa
promesa; mover el origen la cumple. `dur` se recalcula despues de re-anclar, o una pieza empujada
hacia su destino llegaria antes y se quedaria esperando.

### Los dos tests casi mienten, por motivos distintos

**El de la pieza dio verde contra el codigo con el bug puesto.** Media "el primer frame con
`st === 'move'`", pero el cambio de estado y el primer paso del carril NO pasan en la misma
llamada: son ramas de un `else if`, asi que el frame en que `st` pasa a `'move'` es justo el que
todavia no movio nada. Se mide el MAXIMO salto de un frame durante toda la embestida.

**Y despues dio un falso positivo con el caballo.** La cota salia de `T.spd`, pero el caballo
salta con duracion FIJA (0.34s) sin importar cuan largo sea el salto, asi que se mueve mas rapido
que su velocidad nominal y no es una teletransportacion. La cota se saca ahora del CARRIL REAL
(`largo / dur`), con 3.4 de margen porque las curvas de suavizado tienen pendiente maxima 3.

**El del fantasma medía la huida girando en circulo**, y girando el jugador VUELVE a cruzarse con
el fantasma: eso no prueba que se pueda escapar, prueba que se puede chocar. Ahora huye en linea
recta y se verifica que la distancia CREZCA.

**Metodo que hay que repetir:** cuando un test nuevo da verde, correrlo contra una copia del
codigo con el bug puesto a mano. Si no falla ahi, no prueba nada. Se hizo asi con `empuje` y por
eso se encontro que la primera version no servia.

## DIRECCION ARTISTICA (2026-09-18)

> **LOOP deberia sentirse como un reloj de bolsillo abierto que alguien uso como mesa de juego
> durante cien anos.**

Esa frase resuelve sola casi todas las preguntas de diseno visual: explica por que hay naipes y
piezas de ajedrez sobre la misma superficie (alguien jugo ahi), por que el laton tiene patina (es
viejo), por que hay UNA sola luz (hay una lampara sobre la mesa) y por que el tiempo importa (el
objeto es un reloj). **Cada cosa nueva se evalua preguntando si pertenece a eso.**

**Materiales - cinco, y cada cosa pertenece a uno solo.** Fieltro (la arena) - Laton (bisel, aguja,
marcos, el casquillo de la canica) - Hueso/marfil (naipes) - Cristal y luz (orbes, escudo, frenesi)
- **Joya (la canica, y SOLO la canica)**. Si algo nuevo no cae en uno de los cinco, no pertenece.

**Iluminacion:** una lampara, arriba a la izquierda, fija (`LIGHT`, no se toca). Emiten luz solo
tres cosas: la canica, el hilo y lo cargado. Todo lo demas la refleja.

**Color:** el sistema semantico manda sobre la decoracion. Oro = valor. Hielo = vos. Carmesi = te
lastima. Violeta = reglas. Verde = te cura. **Cualquier elemento que use uno de esos cinco esta
haciendo esa afirmacion, le guste o no.** Dos colisiones encontradas, una corregida: la cola del
hilo usaba el violeta de las REGLAS (corregido en el Grupo 2); los enemigos usan oro para la dama,
violeta para el alfil, carmesi para la torre y celeste para el caballo (**sin corregir**: pasarlos
a hueso es la propuesta N2 y necesita decision, porque arriesga la legibilidad por color a
distancia, que es una decision documentada).

**Movimiento:** pesado, inercia corta, nada aparece de golpe. Lo unico que se mueve linealmente es
la aguja, porque es un mecanismo.

**Sonido:** Do mayor pentatonica (`PENTA` siempre lo fue) con el silencio como instrumento.

**Jerarquia de feedback - cuatro niveles y el presupuesto se respeta.** Rutinario: sonido y chispa.
Bueno: + anillo. Excelente: + hitstop y sacudon. Excepcional: + cambio de iluminacion de toda la
arena. **Cerrar un bucle cenido con tres piezas adentro deberia ser el unico evento habitual que
llegue al nivel cuatro.**

**UI:** informacion convertida en objeto, o nada. La hora vive en el anillo de capitulo.

**No es:** neon, sci-fi, arcade generico, Las Vegas, glow excesivo. **Es:** viejo, fino, tactil,
mecanico, misterioso, premium, ligeramente gastado, contenido.

## GRUPO 1 - el reloj suena, barre y cuenta

### El tictac no es un metronomo: es la aguja cruzando las marcas

El plato tiene 60 marcas horneadas y la hora dura 38 s, asi que el tictac sale cada 0.63 s **solo**.
No hay tempo que elegir: **el tempo ya estaba dibujado en el plato**. Esa es la diferencia entre
poner musica encima del juego y hacer sonar el objeto.

Dos tonos alternados como un escape real (La2 y Mi3, tonica y quinta) mas un chasquido de ruido muy
corto, que es lo que de verdad se oye de un escape; el tono solo lo ubica en la tonalidad.

**En el ultimo quinto se SUBDIVIDE a 120**, o sea la misma aguja marcando medias marcas. Un reloj
que cambia de velocidad deja de ser un reloj; uno que marca mas fino sigue siendolo, y avisa que se
acaba la hora sin un solo elemento de UI.

El colchon (`droneSet`) es La1 fijo con su quinta y **no cambia de altura nunca** - cambiar de
altura seria cambiar de tonalidad, y ahi ya es musica. Lo que cambia es cuanto se oye: aparece en la
hora 4 y sube hasta la 12. Las tres primeras horas el juego suena como siempre.

`audioHush(dur, piso)` agacha TODO. Se usa dos veces por partida: 0.75 s antes de que despierte el
Relojero (su rugido esta REPROGRAMADO para entrar cuando el volumen vuelve - un golpe grande
necesita vacio delante o no se oye grande) y un chupon de 0.2 s al entrar en frenesi.

**Bug que esto destapo:** `audioHush` programa rampas sobre `masterGain`, que es el mismo nodo del
boton de mute. **Poner `.value` mientras hay rampas programadas no hace nada.** Sin cancelar las
rampas primero, el mute habria dejado de funcionar despues del primer silencio - o sea, despues de
pelear con el jefe por primera vez. Intermitente y dificilisimo de atar a su causa.

### La aguja hace las transiciones, y NO es un estado

Lo nuevo ya esta dibujado abajo; encima queda una cuna oscura cubriendo el angulo que la aguja no
barrio todavia, con una linea de laton en el filo. Seis transiciones, entre 0.26 s y 0.52 s.

**`sweep` es un contador de render, no un `game.state`.** Esta documentado por que (el cartel de
hora fue un estado, congelo la simulacion y hubo que sacarlo): no bloquea input ni frena la
simulacion. Medido: el jugador se movio 0.244 unidades DURANTE la transicion, y `startRun` la
dispara con el juego ya en `play`. Por eso volver a jugar puede sentirse inmediato.

Avanza con el dt REAL, no con `simDt`: durante un draft la simulacion esta congelada y un barrido
atado a `simDt` se quedaria trabado a la mitad para siempre.

### El anillo de capitulo es la aguja de HORA

Doce numerales, doce horas. La varilla que ya existe da una vuelta por hora (es el minutero) y las
horas vividas se **encienden** en el anillo. No es un indicador nuevo: es la aguja que faltaba.

**Se tiraron dos versiones antes de esta, y el motivo vale mas que el resultado.** La primera era
una banda fina de laton entre las marcas y el bisel: en escritorio apenas se adivinaba y en telefono
apaisado **no existia**. El problema no era el color ni el alfa: a 335 px de alto el radio del plato
son ~150 px, asi que una banda de 0.014 del radio mide **DOS PIXELES**. Ninguna cantidad de brillo
arregla dos pixeles.

**LO QUE SOBREVIVE AL TAMANO ES LA SILUETA Y LO QUE YA ESTA DIMENSIONADO PARA LEERSE.** Los
numerales ya lo estaban. Se hornea un SEGUNDO lienzo (`dialLitCv`) con los mismos numerales en laton
vivo y se pega recortado contra una cuna: un clip y un drawImage.

La segunda version tenia numerales Y banda, y la banda sobraba por dos razones: era un segundo aro
de laton adentro del bisel, y sobre todo **era redundante con la aguja**, que ya marca el avance
dentro de la hora. Quedaron dos indicadores sin superposicion: los numerales cuentan (discreto), la
aguja marca la posicion (continuo).

El contraste se arregla **bajando el apagado, no subiendo el encendido**: las horas que todavia no
viviste estan dormidas, y la esfera se llena de luz durante la run.

## GRUPO 2 - el hilo es un cordon, la canica es la joya

### El hilo

- **La cola usaba el violeta de las REGLAS.** Ahora va de acero frio a hielo. Un color del sistema
  semantico es una afirmacion.
- **No se apoyaba en nada.** Una sola pasada oscura corrida en el eje de la luz da la sombra Y el
  borde de contacto: dos cosas con un stroke.
- **El ultimo tercio lleva un NUCLEO caliente**, asi el cordon se lee redondo donde lo estas usando
  y plano donde quedo apoyado.
- **Tension:** `thread[i].w` guarda la velocidad de la mano al APOYAR cada punto (el pasado). La
  tension es el presente y sale gratis de la velocidad del jugador.
- **Anticipacion de cierre, gratis.** `findSelfCross` YA calculaba la distancia de la cabeza a cada
  segmento viejo para decidir el roce. Se le pide de arrastre el minimo y su indice: cero
  iteraciones nuevas, cero cambios de decision. Con eso, el tramo que vas a encerrar se enciende.

**La cabeza se estaba yendo a BLANCO** y hubo que templarla: el nucleo aditivo se sumaba sobre un
cuerpo que ya estaba en (196,247,255). Dos brillos sumados dan blanco, y **blanco es el material que
convierte un cordon en un laser**. Brillante no es blanco.

### La canica es la joya del mecanismo

El codigo decia con todas las letras "mismo material, misma luz" que las orbes. La intencion era
coherencia; la consecuencia era que el protagonista fuera una orbe un poco mas grande - en la
captura de juego habia que BUSCARLO.

Ahora es un **zafiro octogonal montado en un casquillo de laton**: el unico objeto movil del plato
que lleva el material del reloj, lo que dice solo que el jugador es parte de la maquina. Y resuelve
el anclaje del hilo, porque de un casquillo sale algo.

**Es un OCTAGONO y no un circulo con facetas pintadas**, por la misma razon que la banda de
progreso: en apaisado mide ~4.5 px de radio y a ese tamano las facetas no existen. Contra orbes que
son circulos, un octagono se lee aunque mida cinco pixeles.

El halo bajo de 3.4 radios al 55% a 2.15 al 30%: **una joya no irradia**, un zafiro real es oscuro y
lo que tiene son destellos duros.

### El coste: pagar la materia con resolucion que no se usaba

`drawThread` salto de 214 a **308** comandos de path (+44%) contra un techo autoimpuesto de 15%. Dos
correcciones:

1. Las pasadas nuevas van DECIMADAS (sombra en paso 3, nucleo en paso 2). **Una sombra no necesita
   la resolucion del objeto que la proyecta.** 308 -> 255.
2. Seguia afuera, asi que se pago con algo que sobraba: **el resplandor son cuatro trazos anchos
   aditivos al 2-9% de alfa y se estaba trazando vertice por vertice.** Un halo difuso a esa
   opacidad no puede mostrar facetado. Paso 2. 255 -> **224, +4.7%**.

**La resolucion se gasta en la SILUETA, que es lo unico donde se nota.**

OJO al medir: el peso total del escenario de `s_prof.py` varia entre 271 y 344 segun cuantas piezas
salgan sorteadas. El numero comparable es `drawThread` con largo de hilo fijo, no el total.

### Dos bugs del grupo

- **`gw` ya existia en `bakeDial`.** Colision de nombre con el gradiente de desgaste: `SyntaxError`
  y pantalla negra. Lo cazo la QA en el primer intento.
- **El resaltado de cierre quedaba pegado.** `findSelfCross` solo corre si el jugador se movio; con
  el jugador perfectamente quieto, `nearIdx` conservaba el valor del ultimo frame en que si se movio
  y el tramo dorado quedaba encendido para siempre. **Tercera vez que aparece la misma familia en
  este proyecto** (el `hitstop` que sobrevivia entre partidas, el frenesi colgado al salir al menu):
  un valor de arrastre que solo se ESCRIBE cuando pasa algo y nunca se BORRA cuando deja de pasar.

### Patina, contenida

Todo dentro de `bakeDial`, coste cero por frame: bandas angulares irregulares sobre el bisel (un aro
de metal viejo tiene el brillo manchado), cuatro rayas finas de contacto, y **el fieltro gastado por
donde barre la aguja** - lo unico que pasa siempre por el mismo lugar, hora tras hora. Semilla FIJA
propia, nunca `rnd`: lo decorativo no toca la semilla del juego (ya rompio el modo diario una vez).

## PANTALLA NEGRA (2026-09-19) - dos causas mias, una confirmada y una descartada

Franco: "se me trabo jugando en un momento, quedo la pantalla negra".

**Congelado Y negro tiene DOS firmas posibles en este juego y conviene distinguirlas:**

1. `ctxLost`. El bucle hace `if (ctxLost) { lastT = now; return; }` y deja de dibujar. Si el
   navegador tira el contexto por memoria y no lo restaura, queda negro para siempre.
2. **Una excepcion ANTES del render.** `loop()` llama a `scheduleRaf()` en su PRIMERA linea, asi
   que el proximo frame ya esta pedido cuando algo tira. El juego sigue "vivo" tirando la misma
   excepcion en cada frame, y el lienzo se queda congelado en lo ultimo que alcanzo a dibujar.
   **Esta es la mas enganosa**, porque el juego no esta muerto: esta corriendo y fallando.

### Causa descartada: el bake del tamano equivocado

`dialLitCv` (los numerales encendidos del Grupo 1) era **un lienzo del tamano completo del plato**,
igual que `dialCv`, para dibujar DOCE NUMEROS. En escritorio ~1600x1600x4 = 10 MB: se duplico la
asignacion mas grande del juego para usar el 1% de sus pixeles.

**La leccion vale aunque no fuera la causa: un bake tiene que ser del tamano de lo que DIBUJA, no
del sistema de coordenadas en el que vive.** Copiar la geometria del bake de al lado es lo comodo
(misma escala, mismas coordenadas, se pega con los mismos numeros) y por eso cuesta verlo.

Ahora son doce sprites chicos via `bakeSprite`: ~130 KB contra 10 MB, viven en `_bakes` (asi que
`clearBakes()` los invalida solo, un bake menos que acordarse de poner en el handler de
context-restored), se dibujan SOLO los encendidos, y se fue el `clip`.

**Se descarto como causa del reporte** porque en el telefono de Franco ese lienzo mide menos de
1 MB: duplicarlo no alcanza para tirar un contexto.

### Causa probable: guardas de estado del audio que faltaban

`droneSet` chequea `AC.state !== 'running'` antes de tocar el grafo. **Sus dos hermanos no.**
Escribir cualquier parametro de un nodo de un AudioContext CERRADO tira `InvalidStateError`, y en
movil el contexto se suspende o se interrumpe **solo**: una llamada, cambiar de app, la pagina al
fondo. No es un estado hipotetico.

Y encaja con el sintoma exacto: `updateAmbience` llama a `droneOff()` **cada medio segundo**
mientras no estas jugando, y corre en `loop()` ANTES del render. Firma numero 2 de arriba.

`acOk()` es ahora el UNICO lugar donde se decide si se puede tocar el grafo de audio.

**Regla general que sale de esto: si una funcion toca el grafo de audio, la pregunta no es "hay
contexto" sino "el contexto esta CORRIENDO".** Y todo lo que corra antes del render puede llevarse
puesto el frame entero.

### El invariante que faltaba: `memoria`

La suite tenia 53 escenarios y **ninguno podia cazar esto**, porque todos miden COMPORTAMIENTO y
el problema era de RECURSOS: nada se rompia, se acababa la memoria de lienzos.

`SCENARIOS['memoria']` envuelve `document.createElement`, cuenta cada lienzo que el juego crea y
suma su area despues de forzar un rehorneado y jugar un rato. Falla si el total pasa de 64 MB o si
aparecen mas de dos lienzos de mas de 1 megapixel (**uno grande es el plato y esta bien; dos
significa que alguien volvio a copiar su geometria para dibujar cuatro cosas**).

Medido hoy: **47 lienzos, 3.5 MB en total, el mas grande 1.5 MB, cero de mas de 1 MP.**

Importa especialmente porque todos los juegos del Arcade viven en iframes del mismo renderer y
comparten el techo de lienzos - ya paso una vez y esta en la memoria del proyecto.

## GRUPO 3 - dos gramaticas para el cierre, dos materiales para las grillas

### El bucle chico y el grande eran la misma animacion pintada de otro color

(Correccion de una nota del Grupo 2: el fantasma de los bucles no cenidos NO usaba el violeta de
las reglas, usaba (125,249,255), que es el hielo. El color ya estaba bien.)

**CENIDO = COMPRESION.** El poligono se CONTRAE hacia su centro en 0.22 s con filo duro. El
anillo tambien se contrae (a `addRing` se le pasan los radios al reves). Las chispas nacen EN EL
PERIMETRO y van HACIA ADENTRO: **el sentido de las particulas es la mitad de la lectura** - es lo
que convierte "exploto algo" en "algo se cerro sobre algo". No deja marca: un golpe no deja
huella.

**GRANDE = EXPANSION.** El poligono no se mueve: se enciende ENTERO de una y se apaga en
desvanecido, con el anillo expandiendose, y deja una **huella sobre el fieltro** que se va en
2.6 s. Dura 0.55 s.

(Hubo una version en que el contorno se trazaba punto por punto, en el mismo orden en que lo
dibujo el jugador. La idea era linda - la mesa re-trazando el recorrido - pero Franco pidio
cambiarla y tenia razon en algo de fondo: **el trazado progresivo pone el acento en el PROCESO, y
lo que el jugador acaba de hacer ya termino.** Encender todo de golpe pone el acento en el
RESULTADO, que es lo que corresponde a un premio. Ademas salio mas barato: reusa el mismo path del
relleno en vez de construir un segundo recorrido.)

Las marcas van DECIMADAS (`markPts`, con `ceil` y no `floor` - con floor el tope no se respeta) y
con tope de 2: sin eso, cada marca es un poligono de cientos de puntos pagandose en cada frame y
el plato se llena de graffiti.

### Hitstop: la jerarquia estaba al reves

Cerrar un bucle - el verbo central del juego - no tenia ninguno, mientras que recibir un golpe,
embestir y el envion del luchador si. Ahora: bucle vacio = nada; con algo adentro = un toque;
cenido = claro; cenido con dos o mas muertes = el techo (medido: 0.069 s, exactamente
`CFG.juice.hitstop * 1.25`). **Un bucle vacio no congela nada: si todo congela, nada pesa.**

### Dos grillas, dos materiales

La 9x9 tenia la linea clara AZULADA, lo que la emparentaba con el hielo - el color del jugador - y
la hacia competir. Gris neutro y mas tenue: es estructura de fondo, no informacion.

El "#" del ta-te-ti estaba en cian, o sea en la familia de la LUZ. **El "#" no es luz: es una
pieza del mecanismo.** Pasa a laton, se hornea DORMIDO, y lo enciende una capa que solo se dibuja
mientras `game.sectorsOpen` - cero coste el resto de la hora, y comparte el clip de `drawSectors`
para no agregar un segundo recorte contra el mismo circulo.

El relleno de un sector RECLAMADO se queda en hielo a proposito: **el laton es la estructura del
mecanismo, el hielo sos vos.** Las lineas son de la maquina; las marcas que dejas encima son
tuyas.

### El bug: el temporizador estaba en el lugar equivocado

Al morir, el fantasma y las marcas se CONGELABAN en pantalla, porque sus temporizadores vivian
adentro de `updatePlayer`, que arranca con `if (!P.alive) return;`.

Quinta aparicion de la familia "estado que se queda pegado" en este proyecto, pero el diagnostico
es distinto de las otras cuatro: **el bug no fue olvidarse de limpiar, fue poner el temporizador
en el lugar equivocado.** Un fantasma de bucle y una marca son EFECTOS: viven y mueren como las
chispas y los anillos, y tienen que avanzar donde avanzan ellos. Se mudaron a `updateEffects`.

### Coste: el mismo error que ya se habia corregido una vez

`drawChapterRing` habia quedado en **21.6 de peso, el SEGUNDO dibujo mas caro del juego**, para un
contador de horas: nueve strokes (marcas de hora encendidas) mas nueve blits (numerales)... en el
mismo angulo, diciendo lo mismo. Es identico al error que se corrigio en el Grupo 1 al sacar la
banda de progreso. Se fueron las marcas: **21.6 -> 4.5**, y el anillo se lee igual.

## `bossdps` era un instrumento RUIDOSO presentado como preciso

**Correccion importante sobre lo que se reporto el 2026-09-18.** Cuando se eligio la vida del jefe
(12000), este escenario midio 163/s con mano armada y de ahi salio el "44 s al techo". Medido
despues, sobre builds distintos y sobre el mismo: 130, 163, 200, 200, 226, 229. **El instrumento
oscila casi al doble.**

La causa es estructural: la medicion cuenta el dano hecho en una ventana de 9 segundos en la que
se cierran CUATRO O CINCO bucles. Un bucle mas o menos mueve el resultado un 20-25%. **Medir algo
que ocurre cinco veces adentro de la ventana de medicion no puede dar un numero estable.**

Y el error de metodo es peor que el numero: se saco una conclusion de UNA sola corrida, que es
exactamente lo que el escenario decia estar corrigiendo cuando reemplazo "elegir la vida a ojo"
por "medirla". Medir mal con confianza es peor que estimar sabiendo que se estima.

Lo que el escenario **si** mide bien, porque fue consistente en todas las corridas (74, 79, 82,
84, 92 /s):
  - que la mejor orbita es la de radio ~0.20, apenas por afuera del jefe;
  - que girar PEGADO cierra bucles que no lo contienen (el hallazgo geometrico original);
  - y sirve como ALARMA: si el jefe se cae en menos de 22 s, algo se rompio.

Lo que **no** puede resolver es el numero absoluto de segundos de pelea. La vida del jefe quedo en
12000 y la pelea dura, para un jugador fuerte, **entre ~30 y ~55 s segun la corrida**. Afinar eso
mejor pide jugarlo, no medirlo con esta herramienta.

Ahora reporta la MEDIANA de tres muestras con su dispersion, y el umbral de la asercion paso de
35 s a 22 s: dejo de pretender ser un termometro y es lo que puede ser, una alarma.

## CORRECCIONES 2026-09-19 (lote aparte del Grupo 4)

### El carril viaja con la pieza

Franco: "si una onda de choque desplaza una pieza y despues se ejecuta su movimiento previsto, la
pieza termina recorriendo tambien la distancia adicional desde su nueva posicion hasta el destino
original".

**El arreglo anterior era medio arreglo.** Se habia re-anclado el ORIGEN al arrancar la embestida
(`sxp = e.x`) dejando el destino fijo, con el argumento de que el carril dibujado promete un
destino. Eso quita la teletransportacion pero deja lo otro: el carril se ESTIRA y la pieza recorre
de mas.

Lo correcto es que **el movimiento entero se traslade**: misma direccion, MISMA DISTANCIA, otro
punto de partida. Un empujon te corre a vos y a tu intencion con vos.

Y hay UN SOLO lugar donde hacerlo. Las seis fuentes de desplazamiento - pulso del jugador,
campanada del reloj, rafaga del frenesi, embestida del dash, orbe cargada y barril - pasan todas
por `e.knock()`, que acumula en `kx/ky`, y eso se convierte en posicion en un unico bloque de
`updateEnemies`. Trasladando `sxp/syp/tx/ty` ahi quedan cubiertas todas, **incluidas las que se
agreguen despues**. Se saco el re-anclaje: con el carril viajando seria un segundo mecanismo
haciendo el mismo trabajo, que es como nacen los bugs que nadie entiende.

Efecto lateral que no se habia mirado: durante `move` el lerp del carril PISA la posicion en cada
frame, asi que un empujon en plena embestida se tiraba a la basura y pegarle a algo que embiste no
hacia nada. Medido: el destino se corre 0.217 en vez de 0.

El destino trasladado se acota a radio 0.93. Por eso las distancias medidas dan levemente NEGATIVAS
(-0.016 a -0.044): una pieza empujada contra el borde no puede lanzar su embestida fuera de la
arena. **La asercion del test es asimetrica a proposito**: recorrer de mas es el bug; recorrer de
menos solo puede venir del recorte.

### Un solo control de dash y pulso

Habia dos implementaciones para lo mismo: anillo dibujado en canvas (escritorio) y boton DOM
relleno (tactil), que ademas decian el enfriamiento de forma distinta - arco que se llena contra
opacidad. **La unica forma de que no vuelvan a divergir es que haya una sola implementacion, no
dos que se parezcan.** El anillo se dibuja siempre; el boton DOM queda como zona tactil
invisible (`color: transparent`, no `visibility: hidden`, porque tiene que seguir recibiendo
toques).

`btnRects` se cachea en `resize()`: `getBoundingClientRect` fuerza recalculo de layout y pedirlo
por frame es el error que este proyecto ya cometio con el hover (de ahi `cvLeft/cvTop`). Si no se
pudo leer, el dibujo cae a las posiciones de escritorio - **el control tiene que verse SIEMPRE,
aunque sea en el lugar equivocado.**

Dos detalles que solo aparecieron mirando la captura al tamano real:

- `cacheBtnRects` preguntaba `IS_TOUCH`, y **la pregunta correcta es si los botones estan
  MAQUETADOS**, no que dispositivo creemos que es. Ademas en headless `IS_TOUCH` es falso y no se
  puede forzar: con la condicion vieja era imposible fotografiar lo que ve un telefono, y **un
  cambio visual que no se puede mirar no se puede verificar**.
- La etiqueta de DASH quedaba CORTADA en apaisado: caia a 332 px de un lienzo de 335. Regla que
  no necesita saber la plataforma: si abajo no entra, va arriba.

### El cache de los botones se armaba cuando los botones estaban OCULTOS

Franco, probando el build subido: "estan uno al lado del otro. no estan apilados".

`cacheBtnRects()` se llamaba UNICAMENTE desde `resize()`, y `resize()` corre al cargar la
pagina... **cuando el juego esta en el MENU**, donde `#actBtns` tiene `display: none`. El rect de
un elemento oculto viene en ceros, la guarda de tamano cero deja `btnRects = null`, y el dibujo
cae al plan B: las posiciones de escritorio, que son **lado a lado**. Y no se recalculaba nunca
mas, porque `resize()` solo corre si cambia el tamano de la ventana.

O sea que entrar a jugar desde el menu sin girar el telefono - lo que hace todo el mundo - era
exactamente el unico camino que NO pasaba por el bueno.

**Y la verificacion lo tapo.** La captura y el escenario sacaban `noTouch` y llamaban `resize()`
a mano, o sea que median justo el caso que en el juego real no ocurre. **Un test que prepara el
terreno para que el codigo funcione no prueba el codigo: prueba la preparacion.** Ahora el
escenario entra desde el menu y no toca `resize()`, y verificado al reves: contra un build con el
arreglo revertido, falla ("rects cacheados=NO").

El arreglo: `ensureBtnRects()` rearma el cache cuando cambia la VISIBILIDAD, leida de las clases
del `body` - que es lo que el CSS usa para ocultarlos, o sea la fuente de verdad. Leer clases no
fuerza layout; el `getBoundingClientRect` de adentro si, pero corre unas pocas veces por partida.

Ademas, de la misma tanda: los anillos quedaron **chicos** porque se dibujaban al 84% del boton y
**un contorno se lee mas chico que un relleno del mismo diametro**; el boton venia dimensionado de
cuando era un circuito relleno con el texto adentro, y ahora el texto vive afuera. Dash 84 -> 100,
pulso 60 -> 76, anillo a 0.46 del ancho.
Y la regla "si la etiqueta no entra abajo, va arriba" estaba pensada para un boton solo: en una
COLUMNA, arriba de un boton hay otro boton, y la de DASH caia sobre el anillo de PULSE. Se le hace
lugar abajo (38 px) en vez de voltearla, y el margen es ahora una asercion del escenario.

### El caballo, con silueta de caballo

Era un poligono de ocho puntos rectos y se leia como una esquirla. Ahora es una cabeza de perfil
mirando a la derecha con el lenguaje de las piezas de ajedrez web: hocico largo, dos orejas con su
valle, nuca curva, quijada, base ancha. Manda la SILUETA porque a 20 px es lo unico que sobrevive
- la misma leccion que la banda del anillo y la canica. Como la pieza **se hornea**, las curvas son
gratis.

### El aviso de cierre, revertido

Se fueron el resaltado ambar, el registro de `nearD2`/`nearIdx` dentro de `findSelfCross` y las dos
limpiezas que existian unicamente para el. `findSelfCross` volvio exactamente a lo que era: ni una
asignacion de mas en un bucle que recorre cientos de segmentos por frame. **El resto del hilo del
Grupo 2 se queda**: materialidad, sombra de apoyo, nucleo de la cabeza, tension, paleta.

### El test midio mal TRES veces en este lote

Vale anotarlo junto porque las tres tienen la misma forma - **el instrumento mide una ruta que el
juego ya no usa, o una magnitud que no es la que dice medir** - y las tres reportaron bugs del
juego que no existian:

1. Empujaba con `e.x += dx` a mano. Eso no es el camino real (el juego empuja via `e.knock`) y,
   con el carril viajando, es justo lo UNICO que no lo mueve.
2. Contaba **el empujon mismo** como si fuera un salto del carril. La cota legitima de un frame
   es el paso del carril MAS el empujon vigente, no solo el primero.
3. Usaba el largo de carril capturado al principio, pero en dos segundos una pieza rapida termina
   su embestida y **elige un carril nuevo**: el valor quedaba obsoleto.

**Regla: cuando un test empieza a fallar despues de un arreglo, la primera pregunta es si el test
sigue midiendo lo que el juego hace ahora.**

## Un silencio sin nada del otro lado es solo un bajon de volumen

Franco, probando: "cuando activo el frenesi es como que baja el volumen un par de segundos".

Era el `audioHush(0.20, 0.10)` de `startFrenzy`, y lo que oyo es exactamente lo que pasaba. **Pero
el problema no era la duracion: era que del otro lado no habia nada.**

Antes del jefe el silencio funciona porque despues entra el rugido - el vacio existe PARA que el
golpe suene grande, y por eso la voz del jefe esta reprogramada para entrar cuando el volumen
vuelve. En el frenesi el silencio no precedia a nada, asi que no se lee como "paso algo" sino como
"bajo el volumen".

**Regla: el silencio es un instrumento de CONTRASTE. Sin algo del otro lado no dice nada.**

Se saco el del frenesi. Lo que se queda es que el tictac se corta durante todo el frenesi: eso no
es un bajon de volumen, es que el reloj se fue de la habitacion, y dura los 6.5 s enteros en vez
de un instante. Se vuelve a evaluar en el Grupo 4, cuando el frenesi tenga sonido propio.

## GRUPO 4 - el frenesi deja de ser un buff y pasa a ser un EVENTO DE ARENA

El frenesi ya duraba 6.5 s, ya paraba a las piezas, ya te daba puntos - pero todo eso pasaba
adentro de las reglas. La arena no se enteraba. Era un buff con temporizador, no un momento.

### Lo que cambio de estado, y lo que NO

Nada de lo que DECIDE algo se toco: ni la frecuencia, ni la duracion, ni el iman, ni el puntaje,
ni el dano. Lo que cambio es que ahora **se nota desde afuera del personaje**:

- **el pano se tine** y el bisel se enciende, o sea que el frenesi le pasa al RELOJ, no a vos;
- **el bisel ES el temporizador**: la luz recorre el aro y cuando se termina, se termino. No hay
  barra nueva - la barra es el objeto que ya estaba;
- **el hilo se vuelve oro**, que es el color del valor, porque en frenesi cada bucle vale mas;
- **el drone sube una octava** en vez de agacharse. Una octava es la MISMA nota: el sonido se
  pone urgente sin que el juego cambie de tonalidad, que es lo que hubiera pasado con otra nota.

`frenzyT` entra en 0.22 s y sale en 0.55 s: entra de golpe porque es un susto, sale despacio
porque es un bajon. Se limpia en `startRun` y en `backToMenu` - un estado visual que sobrevive a
una partida es un bug esperando.

### Los que no son piezas tambien viven en la arena

Franco: "los tanques y las flechas tipo TRON no cambian de color como parte del Frenzy".

`drawEnemy` **ya calculaba** el color asustado y se lo pasaba a las piezas horneadas, pero a
`drawCycle` y `drawTank` los llamaba sin el, y cada uno leia `e.T.col` por su cuenta. Todo el
plato se volvia azul menos esos dos. No hizo falta un color nuevo: hubo que **hacerles llegar el
que el juego ya tenia**.

Y despues faltaba la mitad: `drawCycleTrails` tenia su propio `[255,150,60]` hardcodeado, asi que
la moto se ponia azul y dejaba una estela naranja atras. **En TRON la estela ES el enemigo** - es
mas superficie que el cuerpo. Un rastro caliente cruzando un plato que se enfrio se leia como que
ese enemigo no se habia enterado del frenesi.

**Leccion: cuando un objeto se dibuja en mas de un lugar, tintarlo en uno solo lo deja partido a
la mitad.** Buscar TODOS los sitios que eligen su color antes de dar el cambio por hecho.

### El fantasma y el luchador no iban mas rapido: iban DOS VECES

Franco: "se mueven directamente hacia el jugador y mueren al alcanzarlo, se siente demasiado
brusco".

Esta escrito que en frenesi las piezas dejan de amenazar y lo unico que las mueve es el iman, que
a proposito es mas lento que su andar - "no los mueve por su cuenta, los escora hacia vos". Pero
el fantasma y el luchador **seguian persiguiendo por las suyas Y ademas recibian el iman**: dos
fuerzas sumadas hacia el mismo punto. Por eso llegaban encima de golpe.

Se les bajo la persecucion propia de x0.8 a x0.22 dentro del frenesi. El iman pasa a mandar,
igual que con las piezas: siguen acercandose, pero **escorados**, que es la palabra que el diseno
del iman ya usaba. Fuera del frenesi no cambia nada.

**Leccion: antes de bajarle la velocidad a algo que se siente brusco, fijarse cuantas cosas lo
estan empujando.** El sintoma "va muy rapido" y el sintoma "recibe dos empujes" se sienten igual y
se arreglan distinto.

### La jerarquia: matar un peon no puede verse como matar una dama

Cualquier muerte disparaba 38 chispas, un anillo de cinco radios y sacudon de pantalla: el nivel
"excelente" para el evento mas rutinario del juego. Y durante el frenesi, donde caen cinco o seis
por segundo, la pantalla se volvia ilegible justo en el momento que deberia ser el mas claro.

El escalon no se invento: **`e.T.score` ya codifica cuanto vale cada pieza.** Tres niveles, con el
dato que el juego ya tenia:

| | | |
|---|---|---|
| rutina (< 200) | peon | sonido + 9 chispas. Sin anillo, sin sacudon |
| buena (< 800) | torre, alfil, caballo, fantasma, tanque, moto, luchador | + anillo chico + sacudon minimo |
| grande (>= 800) | dama, jefe | + anillo grande + sacudon + punch |

### Ganar no puede ser la pantalla de perder en verde

Es el climax de doce horas y un jefe de 12000 de vida, y era el mismo layout con otro titulo.
Ahora la victoria **cuenta el puntaje hacia arriba** (el numero se gana, no se informa),
**despliega la mano en naipes de verdad** (te ganaste ese build: se muestra, no se nombra en una
fila de tabla) y **apaga menos la arena**, porque el plato quedo con las doce horas encendidas y
eso es parte del premio. La derrota se queda sobria, que esta bien: no todo final merece la misma
celebracion.

## El indicador de "preparate" del Simon tenia la FORMA equivocada (2026-09-19)

Franco: *"el aro cuando se esta por arrancar la secuencia no se dibuja por encima completamente
del sector, una parte esta debajo"*.

Tenia razon y pasaba en las tres clases de celda:

| celda | que se veia |
|---|---|
| centro | el aro nacia con radio 0.35 contra un medio-lado de 0.333: se salia del cuadrado por los cuatro lados desde el primer frame |
| borde | ademas se pasaba del plato y lo cortaba el recorte |
| esquina | se centraba en el centro GEOMETRICO del cuadrado, que esta a 0.943 del eje - practicamente sobre el canto -, asi que casi todo el aro caia fuera y quedaba un pedazo de arco suelto |

**Ese ultimo es un error que este proyecto ya habia cometido y corregido una vez**: los rombos de
sector no van en el centro geometrico de la celda por exactamente esta razon, y para eso existen
`SECT_DX`/`SECT_DY`. El aro del Simon nunca recibio ese arreglo. Cuando una constante de
geometria se arregla en un lugar, hay que buscar quien mas la calcula por su cuenta.

Pero mover el centro no alcanzaba, porque el problema de fondo era otro: **un circulo no entra en
un cuadrado que ademas esta mordido por un circulo mas grande.** Cualquier radio que se vea bien
en el centro se sale en las esquinas, y cualquiera que entre en las esquinas es invisible en el
centro. No habia numero que arreglara esto.

Asi que el indicador dejo de ser un aro y paso a ser **un marco cuadrado que se cierra sobre la
celda**: la misma silueta que la cosa que senala. Nace 1.42x y aterriza EXACTO sobre el
rectangulo que `paint` ya dibuja, asi que el final del gesto es el indicador fundiendose con su
blanco. Y como va bajo el mismo recorte del plato, en las celdas de borde queda cortado EN EL
MISMO LUGAR que la celda: coinciden en vez de contradecirse.

El arco que ademas barria el tiempo se fue: el encogimiento YA es la cuenta regresiva. Eran dos
codificaciones de `u3` en el mismo objeto - la misma redundancia que ya se saco dos veces (la
banda de progreso, el tick de hora encendido).

**Regla: un indicador que senala una cosa deberia tener la forma de esa cosa.** Mientras el
indicador y su blanco tengan geometrias distintas, cualquier recorte, cualquier borde y cualquier
cambio de tamano los va a separar.

Escenario nuevo `aro`: envuelve `strokeRect` del prototipo del contexto y comprueba, en las nueve
celdas, que el indicador sea concentrico con su celda al empezar y aterrice exacto al terminar.
**Contra el codigo viejo falla 9 de 9** - no habia un solo rectangulo concentrico, porque dibujaba
un `arc`.

## El luchador aprende una segunda tanda: PATADAS (2026-09-19)

Franco: *"esta bueno el stickman pero podria tener un combo mas, por ejemplo que haga con
patadas"*.

Tiraba siempre lo mismo - jab, jab, envion - y una tanda sola te la aprendes en dos encuentros.
Ahora hay dos y elige cual antes de plantarse:

| tanda | golpes | alcance | dano total | duracion |
|---|---|---|---|---|
| PUNOS | jab, jab, envion | 0.115 / 0.115 / 0.200 | 2.30 | 1.26 s |
| PATADAS | baja, giro | 0.165 / 0.235 | 2.30 | 1.24 s |

**No es una tanda mas fuerte: es la MISMA amenaza repartida distinto.** Los totales son iguales a
proposito. Lo que cambia es la forma: menos golpes, mas lentos, que llegan mucho mas lejos. Cada
patada sola es mas facil de esquivar - tarda mas en salir y el arco de aviso nace mas grande -
pero retroceder ya no alcanza, que era justo el hueco que dejaban los punos.

**Como elige, y por que se puede leer.** Decide al plantarse, mirando la distancia: fuera del
alcance del jab patea, y encima patea igual una de cada tres. Alejarte no te saca del problema,
te cambia el problema. Y se lee sin memorizar nada porque **el arco de aviso que ya existia se
dibuja con el alcance del golpe que viene**: cuando va a patear, nace mas grande. La informacion
ya estaba en pantalla; ahora dice dos cosas en vez de una. Por eso la tanda se elige al
PLANTARSE y no al pegar: si se eligiera al pegar, el aviso estaria mintiendo durante toda la
preparacion.

En el dibujo la patada sale de la PIERNA, con la misma cuenta con la que se dibujaba el puno
(posicion de mundo, no del muneco, asi que lo que ves es lo que golpea), y la rodilla sale sola
de la formula que ya estaba - con la pierna recogida dobla mucho, estirada queda recta. El torso
se inclina hacia atras mientras la pierna sale: **ese contrapeso es lo que hace que una patada
pese en vez de parecer una pierna que se estira.** La baja va al ras y la de giro va alta.

El escenario `luchador` paso de 5 puntos a 7. El nuevo punto 7 es **el invariante del diseno
escrito como test**: si el dano total o la duracion de las dos tandas se separan mas de un 15%,
o si la patada deja de llegar mas lejos que el puno, salta. El punto 3 (el del envion) ahora
FUERZA la tanda de punos: desde que hay dos, dejarlo elegir haria que ese punto midiera a veces
otra cosa sin avisar.

## "No se hereda" no quiere decir "no afecta" (2026-09-19)

Franco: *"la barra de informacion en el celu no se desplaza"*.

El panel ya tenia `overflow-y: auto`, `touch-action: pan-y` y `overscroll-behavior: contain`, y
al lado un comentario mio que decia: *"`html, body` llevan `touch-action: none`... la propiedad no
se hereda, asi que esto ya deberia poder desplazarse"*.

**La frase es cierta y la conclusion es falsa.** `touch-action` no se HEREDA, pero el navegador no
la resuelve por herencia: cuando el dedo baja, calcula el gesto permitido como la INTERSECCION del
`touch-action` del elemento tocado con el de TODOS sus ancestros. Con `none` en el `body`, la
interseccion es vacia para cualquier descendiente, diga lo que diga.

Y era peor que un panel que no andaba: **el `none` del `body` era lo unico que protegia al
lienzo.** Como `touch-action` no se hereda, el `<canvas>` nunca tuvo el suyo - estaba viviendo de
la prohibicion global. Sacar el `none` del `body` a secas habria arreglado el panel y roto el
juego: arrastrar el dedo sobre el plato habria empezado a mover la pagina. (El escenario nuevo lo
muestra: contra el CSS viejo, el lienzo reporta `touch-action: auto`.)

El arreglo pone cada prohibicion donde corresponde: `html, body` pasan a `manipulation` (mata el
zoom por doble toque, deja pasar el desplazamiento), el `<canvas>` recibe su propio `none`, y
`overscroll-behavior: none` evita que llegar al final de algo arrastre la pagina de atras - que
importa el doble aca, porque el juego vive en un iframe del Arcade.

**Reglas:**
1. `touch-action`, `pointer-events` y `overflow` los resuelve el navegador mirando la CADENA de
   ancestros, no el elemento solo. "No se hereda" y "no afecta" son cosas distintas.
2. **Un comentario que explica por que algo deberia andar, al lado de algo que no anda, es una
   hipotesis escrita como si fuera un hecho.** Si hay que justificar que algo funciona, hay que
   probarlo, no comentarlo.

Escenario nuevo `scroll`, que corre en 800x380 - telefono acostado, que es como juega Franco -:
comprueba que el panel DESBORDE (si no, no habria nada que probar), que ningun ancestro declare
`touch-action: none`, que el lienzo SI lo declare, y que el panel sea un contenedor desplazable de
verdad. Contra el CSS viejo falla los dos primeros. `qa2.py` gano un mapa `SIZES` para que un
escenario pueda pedir su propia ventana.

## Ninguna pieza se mueve fuera de su regla, ni para salir de una esquina (2026-09-19)

Franco: *"vi a las torres moviendose en diagonal"*.

`pickLane` elegia entre las direcciones de la familia pero **no comprobaba que el primer paso
cayera en el tablero** - eso lo hacia unicamente el caballo. Cuando ninguna direccion servia, mas
abajo entraba un plan B:

```js
e.dx = -Math.sign(e.x) || 1; e.dy = -Math.sign(e.y) || 1;   // ambos a la vez = DIAGONAL
```

Para cualquier pieza. Una torre acorralada contra el borde rebotaba en diagonal.

Ahora se filtran las direcciones por "el primer paso cae en el tablero", y el plan B elige, entre
**las direcciones de la pieza**, la que mas apunta al centro; el paso se ACORTA hasta entrar en el
plato en vez de recortar x e y por separado, porque recortar los ejes tuerce la direccion.

**Regla: un caso de escape no es permiso para romper la regla que define al objeto.** El plan B
existia para sacar a una pieza de una esquina, y al hacerlo la convertia en otra pieza.

Escenario nuevo `legal`: 384 elecciones en los ocho bordes y esquinas, mas 96 con la pieza
empujada FUERA de la grilla, comprobando contra el conjunto legal de cada familia. Contra el
codigo viejo: **48/384 ilegales, con "torre en (-0.86,-0.86) eligio (1,1)"** - el bug de Franco,
reproducido literalmente.

## La torre, con perfil de torre

La silueta vieja era un cono invertido: 0.86 de ancho arriba y 0.60 abajo. Se afinaba hacia el
piso, o sea que estaba parada en punta, que es lo contrario de lo que transmite una torre. Franco
la pidio "mas derechita" y paso el dibujo de referencia.

El perfil nuevo es el clasico: **almenas, cuello, fuste casi recto con una cintura apenas
insinuada, y una base ancha que la planta.** Las cuatro almenas salen de una tabla `M` en vez de
veinte `lineTo` a mano, asi que mover una no obliga a recalcular las otras. La pieza se hornea:
las curvas no cuestan nada en tiempo de partida.

## El peon corona por LLEGAR, no por terminar un movimiento

Franco: *"estoy viendo peones que son desplazados al centro y no promocionan; deberian hacerlo
siempre que lleguen al centro sea cual fuere el motivo"*.

La coronacion se miraba dentro del `if (u >= 1)` de la embestida, o sea **solo al terminar su
propio movimiento**. Un peon empujado al centro por un pulso, una campanada o un barril se
quedaba ahi sin coronar, y su siguiente movimiento lo sacaba.

Ahora se mira todos los frames, en `updateEnemies`, **justo despues de que el empuje se volvio
posicion** - para que el frame en que lo empujaron ya cuente.

**Regla: si una condicion es sobre UN LUGAR, se evalua por estar ahi, no por como se llego.**
Atarla al final de un movimiento la convierte en "premio por moverse bien", que es otra cosa.

Lo que sigue sin coronar es un peon que ATRAVIESA el centro a toda velocidad en un solo frame
(un empujon enorme lo mueve 0.6 por frame y la ventana mide 0.27). Eso es correcto: paso por
arriba, no llego. Si alguna vez hace falta, el arreglo es un chequeo barrido contra el segmento
del frame, no agrandar la ventana.

Escenario nuevo `corona`, con tres puntos: empujado **por el pulso de verdad** (el camino que
reporto Franco - el jugador afuera, la onda lo manda al centro), puesto en el centro a mano, y
uno lejos que NO debe coronar. Contra el codigo viejo el peon termina en r=0.081 - o sea, en el
centro - y no corona.

## Modo TEST

Franco pidio "un modo test que tenga vida infinita". Es un MODO y no una dificultad: no cambia
numeros, **saca la muerte**. Por eso vive en `MODES` y no en `DIFFS`, y por eso no guarda record -
un record sin muerte no es un record.

Lo importante es lo que NO hace: **no esconde los golpes.** El impacto se ve, se oye, te sacude,
te empuja y se sigue contando en `run.damage`. Lo unico que no pasa es que baje la vida. Un modo
de prueba que tapa los golpes no sirve para probar nada.

Tres candados, porque hay tres caminos a la muerte: `hurtPlayer`, `hurtPlayerRaw` (el patibulo,
que se saltea la invulnerabilidad) y `killPlayer` (por si aparece un cuarto).

`menuRects` paso a centrar `MODES.length` tarjetas en vez de tener el `(i - 0.5)` de dos cableado:
con la cuenta vieja, agregar un modo descentraba la fila entera.

Escenario nuevo `modotest`: un golpe de 9999, un `hurtPlayerRaw(9999)`, 600 frames quieto en el
medio de la arena a la hora 9 con ocho enemigos, y `saveBest`. Comprueba las dos mitades - que no
muera Y que el golpe siga contandose y dejando chispas.

## La lista de manos, pegada a las cartas

Franco: *"que esten un poco mas pegados a la primera carta de la izquierda, al menos unos 50px"*.

Las filas se dibujaban **alineadas a la izquierda** dentro de una columna de ancho fijo, asi que
cada nombre terminaba donde se le daba la gana y **el hueco hasta la primera carta lo decidia el
largo del texto**: "PAIR" quedaba a media pantalla de la mano y "STRAIGHT FLUSH" casi tocandola.
No era un margen mal elegido - era que no habia margen, habia sobra de texto.

Alineadas a la DERECHA, todas terminan a la misma distancia de la carta. Y la separacion baja de
`S*0.05` a `S*0.018`. En vertical la lista va debajo y centrada, asi que ahi sigue a la izquierda.

La barra de resalte de la mano activa tuvo que aprender a medir: con las filas a la derecha seguia
midiendo la columna entera y quedaba media barra vacia a la izquierda. Se agrego `medirFit`, que
corre **el mismo bucle de achique** que `txtFit` y devuelve el ancho. Corre el mismo bucle a
proposito: si el ancho se calculara aparte, los dos numeros se separarian en cuanto alguien tocara
uno, y el resultado seria una caja que no calza con su texto y nadie sabria por que.

## El panel de info, segunda vuelta: se desplaza A MANO

El arreglo de CSS de la vuelta anterior era correcto y necesario - el `touch-action: none` del
`body` vaciaba la interseccion para todo lo de adentro, y el lienzo estaba viviendo de esa
prohibicion sin tener la suya -, pero Franco probo y **seguia sin desplazarse**.

El sospechoso es donde vive el juego: el Arcade lo mete en un iframe y, en telefono vertical, lo
**rota 90 grados por CSS** para que se juegue apaisado sin girar el aparato. El desplazamiento
tactil dentro de un contenedor rotado depende de como cada navegador clasifica la direccion del
gesto, y `pan-y` se refiere al eje LOCAL del elemento.

No valia la pena seguir adivinando cual capa se lo comia: **el desplazamiento se hace a mano**,
con eventos de puntero - lo que ya usa todo el juego - y `clientY` del documento del iframe, que
viene por la misma transformacion que todo lo demas. Con inercia, porque un panel de texto que
frena en seco donde levantaste el dedo se siente roto en un telefono.

El CSS se queda: es correcto, arregla el lienzo desprotegido, y si el gesto nativo llega alguna
vez los dos caminos hacen lo mismo.

**Regla: cuando un arreglo "correcto segun la especificacion" no arregla el sintoma en el aparato
real, el siguiente paso no es una segunda teoria - es sacar la dependencia.**

El escenario `scroll` gano un punto que despacha eventos de puntero de verdad y comprueba que el
panel se haya movido, en los dos sentidos. Los puntos de CSS se quedan: cubren la otra mitad.

## El luchador solo pateaba, y por que (2026-09-19)

**Medido antes de tocar nada**, con 40 encuentros en condiciones de juego: **0 tandas de punos, 40
de patadas.** El repertorio nunca se perdio - los tres punos seguian ahi con su alcance, su dano y
su tiempo -, lo que fallaba era ELEGIR.

```js
e.cmb = (d > PUNOS[0].reach || rnd(0, 1) < 0.32) ? 1 : 0;
```

La distancia al plantarse, medida, va de **0.1293 a 0.1369**. El alcance del jab es 0.115. O sea
que `d > 0.115` es siempre verdadero, el `||` corta antes de llegar al azar, y sale patada
siempre.

**La causa de fondo no es el umbral: es que `d` no puede informar nada en ese punto.** El luchador
se planta JUSTO cuando entra en `CFG.fighter.enter`, asi que la distancia en ese instante siempre
vale casi lo mismo - la ventana mide un paso de caminata, 0.008. Yo razone "si esta fuera del
alcance del jab, patea", describiendo una situacion que la propia regla de plantarse vuelve
imposible.

**Regla: una variable que el propio codigo acaba de fijar no sirve para ramificar.** Antes de
poner un umbral, preguntarse si el numero puede variar en ese punto.

Un matiz que aparecio en los tests y que vale registrar: en una pelea SOSTENIDA - el luchador ya
pegado al jugador, sin volver a acercarse - `d` si podia bajar de 0.115 y entonces salian punos.
O sea que no era "nunca punos" en abstracto: era **nunca punos en la aproximacion**, que es la
inmensa mayoria de lo que se ve. Las dos mediciones son correctas y miden cosas distintas.

**Arreglo:** ALTERNA. Despues de una tanda hay 75% de que salga la otra. A la larga da 50/50, y
ademas se LEE: "acaba de patear" pasa a ser informacion util. Y la tanda ARRANCA sorteada en vez
de en 0 - con `cmb: 0` fijo la primera tanda de cada luchador salia 75% patadas (medido: 30 de
40), y como la mayoria no vive para tirar muchas, el jugador seguia viendo una mezcla torcida.

## Las animaciones del luchador

Franco: *"se ven toscas y poco pulidas... golpes que parecen simples desplazamientos rigidos de
las extremidades o poses que cambian bruscamente"*. Los saltos eran reales y eran seis.

1. **La maquina de estados saltaba y el cuerpo tambien.** `cam` (cuanto separa los pies) pasaba
   de 1 a 0.18 en UN frame al plantarse, y la carga del envion se apagaba de golpe al empezar a
   pegar. Ahora hay dos valores suavizados en el enemigo - `e.guard` (0 caminando, 1 plantado) y
   `e.crouch` - y todo lo que antes miraba `e.fs` para decidir una pose lee esos numeros. La
   transicion dura ~0.11 s en vez de un frame.
2. **El golpe era una recta.** `lerp(-0.42, 1, t)` con `t` lineal: velocidad constante, que es
   exactamente "una extremidad que se desplaza". Ahora la anticipacion se recoge rapido y SE
   QUEDA cargada -el rato quieto arriba es lo que hace legible el golpe-, la salida va con quinta
   potencia (la mitad del recorrido en el primer 13% del tiempo) y la recuperacion vuelve mas
   lento de lo que fue. Que la vuelta no sea simetrica con la ida es la mitad de por que un golpe
   parece pesar.
3. **El muneco se espejaba en un frame al darse vuelta.** `face` se recalculaba cada frame desde
   `cos(ang)`. Primero le puse histeresis, y el test de continuidad demostro que no alcanzaba: el
   volteo seguia siendo instantaneo, 6.4 px de salto en un muneco de 15.7. Ahora `face` es un
   NUMERO CONTINUO: al girar pasa por cero en ~0.07 s, la figura se angosta y sale del otro lado,
   que es como gira un recorte de papel.
4. **No habia cuerpo detras del golpe.** Ahora el hombro entra con el puno y sale con la patada
   (contrapeso), la cadera empuja hacia el golpe, y el pie de apoyo se desliza adelante en los
   grandes: plantarse y EMPUJAR.
5. **El codo no se estiraba nunca**: tenia un desvio fijo, asi que un puno a fondo seguia doblado.
   Ahora usa la misma cuenta que la rodilla - cuanto mas corto quedo el miembro, mas dobla -, y el
   brazo se endereza al llegar. Es lo que mata la sensacion de palito articulado.
6. **No habia seguimiento.** Durante la salida se traza un rastro tenue de la extremidad unos
   cuadros atras. Son dos lineas y es la diferencia entre un golpe y una pose: sin rastro, a 60
   fps el puno simplemente APARECE afuera.

Y el nudo brillante de la punta entraba de golpe en `ext > 0.45`; ahora entra por alfa desde 0.15.

**Nada de mecanica cambio**: ni dano, ni alcance, ni duracion, ni cadencia, ni cuando se planta,
ni el descanso, ni el frenesi.

### El escenario `lucha2`, y como se mide una animacion

Tres partes. Las dos primeras son directas: **que salgan las dos tandas** (con chequeo de que
ALTERNE, porque las proporciones podrian dar bien con rachas largas) y **que los cinco golpes
ejecuten** - tres punos y dos patadas, cada indice tiene que haber hecho dano al menos una vez.

La tercera es la interesante: se envuelve `drawFighter` y se capturan **los puntos que emite**,
frame a frame. Es lo que llega al lienzo, no una formula copiada del juego.

Tres cosas me obligaron a corregir el test antes de que midiera algo:

- **El rastro corre los indices.** Se dibuja antes del esqueleto y solo durante la salida del
  golpe, asi que los primeros puntos a veces son suyos. Denuncio un salto de 37 px en un muneco
  de 15: no era el muneco, era el test comparando la punta del rastro contra una cadera. Se
  cuenta desde el FINAL: el esqueleto emite 14 puntos fijos, o sea que los ultimos 28 numeros son
  siempre la misma estructura.
- **Caminar no es saltar.** El luchador andando mueve el torso ~3 px por frame. Se le DESCUENTA
  LA TRASLACION y se mide la pose pura.
- **El umbral hay que medirlo, no elegirlo.** El pico del build bueno es 2.6 px sobre 15.7 (0.166)
  y ese pico es la entrada del cuerpo en el puno, o sea la animacion haciendo lo suyo. Se fijo en
  0.22, con 33% de margen. **Contra el build anterior el mismo test da 11.44 px y falla**, que es
  el espejado instantaneo.

**Regla que ya habia aparecido y ahora tiene tercera prueba: cuando un test cambia de color, la
primera pregunta es si el test sigue midiendo lo que el juego hace ahora.**

### Un NaN que me metio el propio parche

El parche inserto `guard: 0, crouch: 0, face: 1,` con un comentario `//` al final de la linea...
y el ancla caia en MEDIO de una linea del fuente, que seguia con `gait: 0, ang: 0, bob: ...`. El
comentario se comio el resto: `ang` quedo sin definir y la posicion del luchador se volvio NaN en
el primer frame.

**Regla: si el ancla de un reemplazo cae en medio de una linea, el reemplazo no puede terminar en
un comentario de linea.** Va arriba, en su propia linea.

## El colchon del frenesi sonaba a telefono vibrando

Franco: *"el sonido en el frenzy que parece como una vibracion de un celular sacalo a la mierda"*.

Mio, de la tanda anterior. El colchon son dos senos - 55 y 82.41 Hz - y en el frenesi yo los subia
una octava: **110 y 164.8 Hz**, a volumen forzado. Un parlante de telefono no reproduce esas notas,
las convierte en golpeteo, y ademas dos senos graves tan juntos baten entre si y producen
modulacion de amplitud. Golpeteo mas modulacion es, literalmente, la descripcion fisica de un
telefono vibrando.

**Regla: en un parlante chico, una nota grave no se oye grave - se oye como un defecto.** Todo lo
que este por debajo de ~200 Hz hay que darlo por perdido o por sucio.

Se saco entero, junto con el parametro `oct` de `droneSet` y `CFG.frenzy.drone`, que no usaba
nadie mas. **Probe dos cosas con el colchon del frenesi y las dos estuvieron mal**: agacharlo (se
oyo como un bajon de volumen) y subirlo (zumbido). Lo que marca el frenesi por audio es que el
TICTAC SE CORTA los 6.5 s enteros - el reloj se fue de la habitacion -, y eso no es un cambio de
volumen, es una ausencia.

## Las puntas de las flechas

Franco: *"las puntas no terminan de verse prolijas... terminaciones toscas"*. La causa era de
construccion, no de tamano. El carril era un cuadrilatero ahusado **con su propio contorno
cerrado**, y la punta un TRIANGULO APARTE encima:

- el carril terminaba en un corte recto contorneado - una tapa dura justo donde deberia haber una
  punta;
- el triangulo arrancaba en `L - 0.45·w1` con medio ancho `1.05·w1` contra un carril de ancho
  `w1`: apenas mas ancho, asi que se leia como un bulto y no como una punta;
- y al ser dos figuras con alfas distintas, la costura quedaba a la vista.

Ahora la flecha es **UNA sola silueta cerrada** - cuerpo ahusado, hombros, vertice y vuelta -, el
contorno la recorre entera y la cabeza mide casi el doble del ancho del cuerpo. Uniones
redondeadas, que a este tamano se ve mas fino que un pico.

Un intento intermedio que descarte: atar el encendido de la cabeza a que el relleno del cuerpo
LLEGARA hasta ella. Sonaba mas fino y estaba mal: en un carril largo la cabeza mide un 8% del
largo, asi que se quedaba apagada durante el 92% del aviso - justo cuando lo unico que importa es
hacia donde. **La cabeza dice la DIRECCION: tiene que verse desde el primer frame.** Ahora se
enciende con el progreso general.

No cambia ni el ancho, ni el largo, ni el color, ni la alfa del cuerpo.

## El dorado de los sectores: rompia la ley de color del juego

Franco: *"las lineas que dividen los sectores se vuelven doradas y no entiendo que representa"*.

**Que lo causaba.** `drawSectorHash` dibuja el "#" del ta-te-ti encendido, y corre unicamente
mientras `game.sectorsOpen` - la VENTANA DE RECLAMO, que se abre pasado un tercio de cada hora y
se cierra al cobrar una linea o al terminar la hora. El resto del tiempo el "#" esta horneado en
el plato, apagado. O sea que el dorado SI significaba algo: "se puede reclamar sectores ahora".

**Por que igual no se entendia.** El juego tiene una ley de color propia - **oro = valor** - y
esto la rompia: el "#" se ponia dorado siempre que la ventana estaba abierta, valiera algo o no,
mientras que los rombos de la MISMA mecanica la respetan (hielo si son un blanco normal, oro si
completan una linea). Dos objetos de la misma mecanica hablando idiomas distintos.

**El dorado no era ambiguo por ser tenue: era ambiguo por mentir.** Un color con significado
asignado que se usa fuera de su significado envenena al resto - si el oro a veces no quiere decir
valor, deja de querer decir valor nunca.

**Arreglo:** el "#" habla el idioma de los rombos. HIELO mientras la ventana esta abierta, ORO
solo cuando algun sector libre completaria una linea. La informacion no se pierde - la ventana se
sigue anunciando, y encima con el color correcto -, y el dorado pasa a ser un aviso con contenido:
hay una linea a un paso.

## EL CRASH DE MOVIL: el juego dibujaba dentro de un sprite (2026-09-20)

Franco: la palanca andaba, el menu de arriba a la derecha respondia al toque pero no hacia nada,
y el boton de info andaba y se podia desplazar.

**Los sintomas eran el diagnostico.** Todo lo que siguio funcionando es DOM puro: la palanca, el
panel de info y su arrastre a mano. Todo lo que "respondia pero no hacia nada" es DOM que cambia
ESTADO DEL JUEGO y necesita que alguien vuelva a dibujar: pausa cambia `game.paused` y no se ve,
reset vuelve al menu y no se ve. O sea, el lienzo dejo de actualizarse y el resto siguio vivo.
No era un problema de controles.

### La causa

Dos lugares PISABAN la variable global `ctx` para dibujar en un lienzo auxiliar y la devolvian al
final - `bakeSprite` y `bakeHandStrip`:

```js
const prev = ctx;
ctx = cv.getContext('2d');       // sin comprobar
ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
dibujar(S / 2, S / 2);           // si esto tira, no hay vuelta
ctx = prev;                      // nunca se ejecuta
```

Si algo fallaba en el medio, **`ctx` se quedaba apuntando al lienzo auxiliar - o a `null` - para
siempre**. A partir de ese frame el juego seguia corriendo, simulando y respondiendo, y dibujaba
todo dentro de un sprite de 40 px que nadie mira.

Dos maneras concretas de fallar, las dos propias del telefono:

1. **`getContext('2d')` devuelve `null`.** iOS tiene techo de memoria de lienzos POR PESTANA y en
   el Arcade todos los juegos viven en iframes de la misma pestana - esto ya le paso a este repo
   con Pong. Reproducido en el test: el build viejo tira
   `Cannot read properties of null (reading 'setTransform')` en `bakeSprite`.
2. **`dibujar()` tira.** Y como `_bakes.set(...)` pasa DESPUES, el sprite no se cachea: se
   reintenta el frame siguiente, y el siguiente, para siempre.

Estos bakes no corren solo al cargar: `bakeSprite` corre cuando aparece un tamano o tipo de pieza
nuevo y `bakeHandStrip` cada vez que cambia la mano. O sea, en mitad de una partida.

### El arreglo

`try/finally` en los dos, mas comprobacion del contexto, mas `blit` tolerando un sprite nulo, mas
las mismas guardas en los otros tres lugares que crean lienzos auxiliares (`bakeDial`, el sprite
de resplandor, la textura de fieltro).

**Regla: un intercambio de variable global sin camino de vuelta es una bomba, no importa que la
tire.** Si una funcion pisa estado global para trabajar, la restitucion va en `finally`, siempre.

### Y que la proxima deje rastro

Aparte de la causa hay un problema de DISENO que es el que convirtio un error en una partida
muerta: **cualquier excepcion dentro de `loop()` congelaba el lienzo para siempre y en silencio.**
`scheduleRaf()` es la primera linea de `loop`, asi que el frame siguiente ya esta pedido cuando la
excepcion sale: el bucle seguia vivo tirando el mismo error eternamente.

Eso no es un sintoma: es la razon por la que Franco no pudo decirme que paso. Ahora un frame que
tira cuesta un frame, y la primera vez aparece un cartel en el DOM - lo unico que sigue vivo
cuando el lienzo muere - con el mensaje del error.

Escenario nuevo `ctxswap`. Contra el build anterior da tres fallas, incluida
**"el juego quedo dibujando fuera de la pantalla"**: el crash de Franco, reproducido sin telefono.

## Flush decia dos cosas distintas, y una era ilegible

El HUD llamaba a `handDesc()` -efecto concreto segun el palo- y el inventario leia
`HAND_BONUS[i].desc` -texto generico-. **No discrepaban por un error de transcripcion: leian
fuentes distintas**, y una de las dos no sabia que el color depende del palo. Se unifico en
`bonusDesc(i)`, que llaman las dos.

Y el tamano: **medido, el efecto se dibujaba a `cw * 0.25` con `cw = S * 0.037`, o sea
`S * 0.00925`. En el telefono acostado de Franco son 3.3 pixeles.** El piso del sistema
tipografico del propio juego es `TS.cap = S * 0.0125`. No era letra chica: estaba por debajo de lo
que el diseno admite.

El arreglo tuvo dos pasos y el primero fue insuficiente. Subir el tamano base no alcanzaba porque
**el tope real era el ANCHO**: el texto iba centrado sobre una tira pegada al borde izquierdo, asi
que solo podia crecer hasta chocar contra el canto de la pantalla. Alineandolo a la izquierda con
la tira puede estirarse hacia la derecha, que es donde no hay nada, hasta el borde del plato. De
3.3 px paso a ~9.
**Cuando un texto no entra, preguntarse si el problema es el tamano o el lugar.**

## Los peones no coronan en frenesi

Efecto colateral del arreglo de ayer, y tenia que aparecer: desde que la coronacion se mira todos
los frames, el IMAN del frenesi -que arrastra las piezas hacia el jugador- empezo a meter peones
en el centro y cada uno que pasaba coronaba. La regla de la casa ya estaba escrita: **en frenesi
no pasa NADA amenazante**, y coronar es la amenaza que crece sola.

## Dos tests que no median lo que decian

Los dos aparecieron en la suite completa y **ninguno era una regresion del juego.**

### `rngdet` comparaba la corrida de CALENTAMIENTO contra una asentada

Bisecado: pasa en los cuatro commits anteriores y falla en `be01d88`. Parecia una regresion
clarisima. Se instrumento la divergencia frame a frame: las dos corridas se separan en el
**frame 1**. La pregunta decisiva fue correr TRES veces:

    1a vs 2a: primer frame distinto = 1
    2a vs 3a: primer frame distinto = -1   (identicas en 700 frames)

**La simulacion sembrada es determinista; lo raro es la PRIMERA corrida de la pagina** - arranca
con el primer frame despues de cargar, con su dt y sus lienzos recien horneados. Y lo decisivo:
esto pasa IGUAL en los builds de anteayer, incluidos los que el test daba por buenos. El test
venia comparando calentamiento contra asentada y pasaba de casualidad; los cambios de ayer hicieron
que el juego consumiera azar en un patron algo distinto por pieza y esa diferencia de un frame
dejo de lavarse.

Se arreglo el TEST: descarta la corrida de calentamiento. Y quedo escrito lo que el modo diario
garantiza de verdad: **la misma arena, las mismas reglas y las mismas cartas** - todo lo que
decide la semilla -, no el mismo resultado, que depende del jugador y del ritmo de frames.

### `barriles` dejaba orbes sueltos en la prueba del jefe

Fallo una vez en la suite y no se reprodujo en 19 corridas aisladas. El escenario corre en modo
LIBRE y deja **siete orbes rebotando** mientras comprueba que el barril no le pegue al jefe, que
esta clavado en el centro. Un orbe cargado le hace dano a cualquier pieza, y 4 de dano es
exactamente lo que hace uno.

El test decia "el barril no le pega al jefe" y medía "nada le pega al jefe". Se le sacan los
orbes. **Un test que a veces falla por algo que no esta probando es peor que no tenerlo: ensena a
ignorar el rojo.**

## Detalles de la misma tanda

- **El numero de vida** pasa de `txtG` (sombra en diagonal) a `txtO` (contorno negro). Sobre una
  barra que va de verde a amarillo a rojo, una sombra desplazada no separa el texto del fondo, lo
  emborrona. `txtO` ya existia y esta documentado como "para lo que tiene que leerse encima de
  cualquier cosa": no hubo que inventar nada.
- **El barrido al morir** se saco. Queda solo en la VICTORIA, donde hace de telon antes de la
  ceremonia de puntaje. Verificado: `sweep.dur` queda en 0 al morir y en 0.52 al ganar.
- Se unificaron los dos bucles de achique de texto (`txtFit` y `medirFit`) en `fitPx`.

### Un error mio que casi entra

Escribi `S * 0.02` dentro de `drawHandStrip`, donde **`S` no esta en alcance** - vive en
`drawHUD`. Lo cazo la revision antes de construir. El margen se expresa ahora en unidades de la
propia tira, que es lo unico que esa funcion conoce.

## LAS MANOS DE POKER: una sola tabla, un color explicito y la escalera real (2026-09-20)

### El problema de fondo: el efecto y su texto eran dos cosas

Habia una cadena de `if` que aplicaba los premios y, aparte, una tabla de strings que los
describia. Dos listas que tenian que decir lo mismo y **nada obligaba a que lo hicieran**. Ya
habia cobrado dos victimas: el COLOR decia una cosa en el HUD y otra en el inventario (arreglado a
mano el dia anterior, o sea parcheando el sintoma), y la ESCALERA DE COLOR decia *"Everything
doubled"*, que no es lo que hace - suma cinco cosas fijas, no duplica nada.

Ahora cada mano es **una entrada con su efecto en datos**:

```js
{ name: 'FULL HOUSE', eff: { dmg: 0.35, greed: 0.35 } }
```

`applyHandBonus` lo aplica y `bonusSegs` lo escribe. **El texto se genera del mismo objeto que
produce el efecto, asi que no puede mentir.** Tocar un numero cambia sola la descripcion en el HUD
y en el inventario a la vez.

**Regla: cuando un texto describe un comportamiento, generarlo DEL comportamiento.** Mientras
sean dos declaraciones separadas, la unica pregunta es cuando divergen, no si.

### El color deja de ser un misterio

El COLOR daba un efecto distinto segun el palo. Franco pregunto dos veces que hacia - la segunda
ya con el texto arreglado -, o sea que **el problema no era la redaccion sino el diseno**: una
mano cuyo premio hay que ir a buscar a otro lado no se puede evaluar mientras jugas.

Ahora: **Damage, Score y Thread +20%.** Tres numeros, una linea, sin ir a buscar nada.

Y hay una razon para que sea ANCHO y no profundo: en este juego **el palo lo decide la carta, no
el azar** (`su: up.su`, y hay dos mejoras por palo). Un color son cinco cartas de las mismas dos
mejoras: un build angosto por construccion. Premiarlo con mas de lo mismo lo hacia mas angosto
todavia; darle un poco de las tres monedas principales lo ABRE.

### La escalera real

`evalHand` devolvia 8 para cualquier escalera de color. Ahora distingue el 10-J-Q-K-A del mismo
palo y devuelve 9. Su premio es **exactamente el doble de la escalera de color** - una relacion
que se entiende de una y no hay que memorizar.

Cuidado con la RUEDA: A-2-3-4-5 es escalera y puede ser color, pero **no** es real. Tiene el As,
que es justo lo que haria pasar un chequeo perezoso del tipo "termina en As"; por eso se mira el
arranque (`rs[0] === 10 && rs[4] === 14`) y hay un caso de test para eso.

**Probabilidad, dicha a Franco para que decida:** es practicamente inalcanzable. Los rangos salen
de `rndi(2,14)` uniforme, asi que cinco rangos que formen 10-J-Q-K-A son 120 de 371293 (0.032%), y
encima los cinco tienen que ser del mismo palo. Esta implementada y es correcta; hacerla visible
exigiria tocar como se sortean los rangos, o sea balance.

### La jerarquia

Sumando los porcentajes como medida cruda de cuanto da cada mano:

    PAR 0.12 - DOBLE PAR 0.30 - TRIO 0.25 - ESCALERA 0.43 - COLOR 0.60
    FULL 0.70 - POKER 0.70+60 vida - ESCALERA DE COLOR 2.85+80 - REAL 5.70+160

Monotona salvo el escalon trio/doble par, que ya estaba asi y no se toco: el doble par reparte
entre dos monedas y el trio concentra en dano, que es lo que los distingue.
**Solo cambiaron dos entradas de la tabla, y las dos porque Franco las pidio.**

### La lista, alineada con las cartas

El paso de la lista se calculaba de la TIPOGRAFIA (`(fsN + fsD) * 1.30`) y la altura salia del
paso: la lista medía lo que medía, y que coincidiera con las cartas era casualidad. No coincidia,
asi que las dos columnas no compartian ningun borde y la vista no las asociaba.

Ahora **la lista ocupa exactamente el alto de los naipes** y la tipografia sale de ahi.

Y una correccion sobre mi propia primera version: repartir el alto en **partes iguales** hacia que
las dos jugadas largas -escalera de color y real, con cinco efectos cada una- mandaran sobre el
tamano de letra de las nueve. Medido en 1080p: la lista caia de 20.5 px a 11.8, o sea que
"alinearla" habia empeorado justo lo que habia que mejorar. Se reparte **a prorrata**: cada fila
pesa lo que necesita (2.18 unidades con un renglon de efecto, 3.05 con dos) y las siete cortas
devuelven el espacio que no usan.

**Regla: alinear un bloque con otro no puede costar la legibilidad del bloque. Si la cuenta
obliga a elegir, la cuenta esta mal planteada.**

Ademas: el ancho de la columna bajo de `S*0.30` a `S*0.26` porque la columna y los naipes se
disputan el ancho y **los naipes le devuelven ALTO a la lista** (su alto ES el de la lista).
Medido en 1080p: con 0.30 el naipe queda en 200 px y la lista en 295 de alto; con 0.26, 216 y 317.
El texto mas largo sigue entrando sin achicarse.

Y el realce de la fila activa abraza el BLOQUE entero: con dos renglones de efecto, una barra de
una linea dejaba media fila afuera de su propio resalte.

### Los tests

- `manos` recorre las NUEVE jugadas con una mano real de cada una y mide el stat **con y sin** el
  bono para comprobar que el efecto aplicado es exactamente el de la tabla. Ese punto es el que
  garantiza que el texto no pueda mentir.
- `manopanel2` mide la GEOMETRIA de lo que se dibuja - envuelve `drawCard` y `txtFit` durante el
  panel - y exige que ningun naipe se salga y que la columna no pise el primer naipe. Corrido en
  1600x900, 900x420 y 520x900.
- Los casos de `evalHand` se actualizaron: 10-J-Q-K-A del mismo palo ya no es 8 sino 9, y se
  agrego la rueda de color (que tiene que seguir siendo 8).

**Gotcha del harness, para no volver a perder tiempo:** `--headless=new` fuerza un ancho minimo de
ventana de 500 px. Pedir 420 da una captura de 420 px de ancho pero la pagina se dispone para 500,
asi que la imagen parece recortada y no lo esta. Un telefono vertical de 390 no se puede
reproducir con este harness; el reparto en vertical es proporcional al ancho (los naipes ocupan
siempre el 86%), asi que lo que entra a 500 entra a 390.

## Lo que sigue en hold (2026-09-18)

Franco descarto las propuestas para **CrazyTanks** (la aguja como rival en una carrera; los
portales del borde) y **Hangman** (la cuenta regresiva dibujada e irreversible). Quedan sin
representacion mecanica y **no hay que implementar nada para esos dos hasta que el lo pida**. El
analisis de por que Hangman no encaja sigue valiendo: su mecanica ES un cuestionario, y un
cuestionario en un juego de reflejos siempre se va a sentir como lo que se sintio.

Ver [../CLAUDE.md](../CLAUDE.md) para las convenciones compartidas de los ports web.
