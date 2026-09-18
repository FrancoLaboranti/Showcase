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

## Lo que sigue en hold (2026-09-18)

Franco descarto las propuestas para **CrazyTanks** (la aguja como rival en una carrera; los
portales del borde) y **Hangman** (la cuenta regresiva dibujada e irreversible). Quedan sin
representacion mecanica y **no hay que implementar nada para esos dos hasta que el lo pida**. El
analisis de por que Hangman no encaja sigue valiendo: su mecanica ES un cuestionario, y un
cuestionario en un juego de reflejos siempre se va a sentir como lo que se sintio.

Ver [../CLAUDE.md](../CLAUDE.md) para las convenciones compartidas de los ports web.
