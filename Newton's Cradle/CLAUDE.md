# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Newton's cradle simulator — pendulum balls hanging by strings, dragging one and releasing transfers momentum through the chain. Window is 1280×720. Press **UP** to add a ball, **DOWN** to remove one (capped between 1 and 10 balls).

Spanish identifiers throughout (`radio`, `velocidad`, `angulo`, `colisiona`, `colision_ryp`, `colision_circulos`, `orig_x/orig_y`). Folder name contains an apostrophe — quote the path when running: `python "Newton's Cradle\Newton's Cradle.py"`.

Diverges from the repo skeleton: no `Sprite` base class, no `xper`/`yper` helpers, no `deltaT` (uses fixed-step physics). The `Ball` class manages its own pendulum integration via `angulo` and `velocidad` around its anchor `orig_x, orig_y`.

See [../CLAUDE.md](../CLAUDE.md) for the shared conventions this file does not follow.


## AUDIO — correccion y material nuevo (2026-09-22)

**El congelado.** `playClick()` se llamaba desde dentro de `frame()` y el `requestAnimationFrame`
esta mas abajo. Una excepcion del audio — un contexto interrumpido en movil tira `InvalidStateError`
al escribir cualquier parametro — no dejaba el pendulo mudo: lo dejaba **QUIETO**, sin volver a
pedir un cuadro nunca mas. Ahora la llamada va en `try/catch` y `playClick` exige
`actx.state === 'running'`, no solo que el contexto exista.

**El WAV huerfano.** `sounds/woodenballs.wav` son 19,6 MB que no cargaba nadie: 69 s de grabacion
real de bolas de madera chocando, estereo de 24 bits a 48 kHz, con **39 impactos aislados**. Es
material de sobra para el unico juego del repo cuyo sonido ES el choque de dos esferas de madera.
Se extrajeron los seis golpes limpios (entrada silenciosa, sin recorte, cola entera) a
`wood1..6.mp3`, **17,6 KB en total**:

| | centroide del ataque | cola a -40 dB |
|---|---|---|
| wood5 | 646 Hz (grave, apagado) | 59 ms |
| wood1 | 1682 Hz | 72 ms |
| wood2 | 1635 Hz | 177 ms |
| wood6 | 2528 Hz | 55 ms |
| wood3 | 3249 Hz | 61 ms |
| wood4 | 3357 Hz (brillante, seco) | 43 ms |

No son seis copias del mismo golpe: el juego puede elegir segun la velocidad del choque. **Todavia
no estan cableados** — el `playClick` sintetizado sigue siendo el que suena.

El WAV de 19,6 MB sigue en el repo: es material fuente y borrarlo es decision de Franco.
