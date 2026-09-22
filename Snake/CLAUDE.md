# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A non-grid Snake: the head smoothly chases the mouse cursor, each body segment chases the segment in front of it. Window is 1280×720, toggleable to fullscreen at runtime (the main loop recreates `windowSurface` with `pygame.FULLSCREEN` when `self.fullScreen` flips).

**LMB held** = sprint (head speed ×1.5). Each `SnakePiece` adjusts its `vel` and `angVel` based on distance to its target, so the body undulates naturally around tight turns. New segments inherit position and angle from the previous-tail segment.

Body coloring alternates: every 4th segment uses a brighter green range (`randColorInRange(10,40,225,255,10,40)`), the rest use a darker green. Per-segment `wave_time`/`wave_time_total` drives a sine-wave breathing animation.

The `manager` global is a single-element list `[Manager()]` — index it as `manager[0]` (see `SnakePiece.process` reading `manager[0].gameOver` and `manager[0].pause`). This is unusual for the repo; don't replace it with a plain object without updating every read site.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**El material del mundo es AGUA**, y el agua no tiene transitorios secos: **ningun sonido de este
juego puede empezar con un click**. Todas las voces llevan un ataque de 4 a 8 ms. Un
`setValueAtTime` de golpe sobre la ganancia produce un click de conmutacion audible, y un click es
justamente lo que el agua no hace.

Dos familias y ninguna mas:

- **HIDRAULICA** — cuerpo y peso: senos y triangulos de 40 a 250 Hz con ruido pasa-bajo para el
  desplazamiento de agua. Mordidas, embestidas, golpes, minas, jefes.
- **BIOLUMINISCENTE** — todo lo que brilla: senos puros de 500 a 1800 Hz, muy cortos, con un
  armonico a la quinta. Comer, subir de nivel, elegir carta.

### El lowpass del master es un instrumento

Todo pasa por un lowpass a 2600 Hz: estas abajo del agua, no llega ningun agudo entero. Y el filtro
se mueve. Medido: **2600 Hz (agua normal) → 1500 (dentro del escudo de medusa) → 2600 → 300
(hundiendote) → 2600 (reinicio)**. No hace falta ningun sonido nuevo para decir "algo cambio":
cambia el AGUA.

Otras decisiones:

- **Comer es el sonido mas frecuente del juego**, asi que dura 85 ms y vive en 0.045. La altura
  sube con la rareza de la estrella: una naranja se oye mejor que una amarilla sin mirarla.
- **La mina tiene timbre PROPIO**, no el de la mordida: metal ahogado. Es lo unico metalico del
  arrecife y por eso se reconoce sin verlo.
- **Pegarle a un jefe da DOS timbres** segun si la armadura absorbio: golpe seco y mate si no
  entro, campanazo si entro. Es la unica forma de saber si la ventana vulnerable estaba abierta sin
  memorizar la fase de cada jefe.
- **El borde del lago no es un golpe, es presion**: siseo continuo mientras estas afuera.
- El fin del escudo, el veneno y la recarga del turbo se disparan **por FLANCO**, comparando contra
  el valor del frame anterior. Sin el flanco serian una voz por frame, que es justo lo que el
  cooldown no alcanza a tapar.

> Patron comun a todo el repo: sintesis WebAudio sin archivos, `AudioContext` creado con
> `try/catch` en el primer gesto, techo de voces por frame **con su reseteo al tope del `loop()`**,
> cooldown por voz, boton de mute con persistencia en `localStorage`, y `visibilitychange` para que
> nada continuo siga sonando con la pestana al fondo. Si el audio falla, el juego sigue andando.
> Verificado con un arnes headless que envuelve el `AudioContext` y anota cada nodo y cada rampa.
> **El arnes no escucha**: comprueba que suene lo que se diseno, cuando se diseno y con que
> parametros. La evaluacion auditiva queda pendiente.
