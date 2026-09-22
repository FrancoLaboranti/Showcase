# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Pong with a menu system, configurable win-points (5/10/20/40/practice), and an optional "fire mode" where rallies above a streak threshold ignite the ball and paddles. 1280×720 window. Spanish identifiers (`pelota`, `apretado`, `puntos_victoria`, `crear_pelota`, `crear_texto`, `gamestates = ['menu','juego','pausa']`, `opcion_menu`).

Diverges from the repo skeleton: no `Sprite` base class, no `xper`/`yper` helpers, no `deltaT`. State is a `gamestate` string switched between `'menu'`, `'juego'`, and `'pausa'`. Ball physics use a 5-element list `[x, y, radius, vx, vy]` rather than an object.

`fire_mode`, `j1onfire`, `j2onfire`, `firenet` are top-level globals — gameplay reads/writes them directly rather than through a manager.

See [../CLAUDE.md](../CLAUDE.md) for the shared conventions this file does not follow.


## AUDIO (2026-09-22)

**Luz cargada y vidrio.** El fondo es un degrade radial casi negro con grilla azul, todo se dibuja
con `shadowBlur` y las particulas van en `lighter`: no hay una sola superficie mate en pantalla.
Por eso ningun impacto es un golpe — es una DESCARGA, un transitorio vidrioso con cola resonante
AFINADA.

**La escalera del peloteo.** La altura de la devolucion sube con `rallyHits`: medido, 293 Hz en el
peldano 0 y 1186 Hz en el 8. Un rally largo se oye tensarse. La velocidad de la pelota escala el
volumen aparte (0.048 lento vs 0.075 rapido), asi que altura = cuanto llevan, volumen = que tan
fuerte viene.

**La cancha en llamas cambia el timbre, no el volumen**: el mismo golpe pasa de `triangle` a
`sawtooth`. Mismo gesto, otra consecuencia.

### El bug que tenia

`sndThisFrame++` estaba en tres lugares y **`sndThisFrame = 0` en ninguno**. Es exactamente la
trampa que documenta el patron: el contador solo sube, `ac()` corta en 10, y el juego se queda mudo
PARA SIEMPRE a los diez sonidos sin tirar un solo error. Medido con el arnes antes del arreglo: el
contador termino en 13 y los golpes posteriores no sonaron.

> Patron comun a todo el repo: sintesis WebAudio sin archivos, `AudioContext` creado con
> `try/catch` en el primer gesto, techo de voces por frame **con su reseteo al tope del `loop()`**,
> cooldown por voz, boton de mute con persistencia en `localStorage`, y `visibilitychange` para que
> nada continuo siga sonando con la pestana al fondo. Si el audio falla, el juego sigue andando.
> Verificado con un arnes headless que envuelve el `AudioContext` y anota cada nodo y cada rampa.
> **El arnes no escucha**: comprueba que suene lo que se diseno, cuando se diseno y con que
> parametros. La evaluacion auditiva queda pendiente.
