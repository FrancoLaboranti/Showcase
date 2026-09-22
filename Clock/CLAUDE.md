# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Analog clock face rendered from `datetime.now()`. Click anywhere to toggle the second hand between **ticking** (`segundero == 0`, snaps per second) and **smooth** (`segundero == 1`, interpolated via `microsecond`). The smooth-second math packs microseconds into seconds as `(ca_ms + ca_s*999999) / (60*999999)` — that 999999 magic number is the multiplier, not a typo.

Window is 650×650. Spanish identifiers (`radio`, `centro_x/y`, `fuente`, `crear_texto`, `segundero`, `pressed`). No `ESC`-to-quit — only the window-close button exits.

This file shadows the stdlib `time` module by reassigning `time = datetime.datetime.now()` inside the loop. The `import time` at the top is currently unused; don't add `time.sleep(...)` without renaming the local first.

See [../CLAUDE.md](../CLAUDE.md) for shared conventions across the repo.


## AUDIO (2026-09-22)

**Fosforo sobre vidrio negro, no madera ni laton.** Este reloj es un instrumento de laboratorio —
anillos con `shadowBlur`, degrade de cara de vidrio, digitos Orbitron, siete paletas neon —, asi
que la familia timbrica es cuarzo y vidrio: transitorios secos y altisimos sobre silencio absoluto.
Sin drone, sin ambiente, sin musica. Lo unico tonal son campanitas inarmonicas.

El tictac es el corazon y por eso es lo mas dificil de dosificar: suena una vez por segundo
durante toda la sesion, asi que vive al fondo de la mezcla. Un tictac que se nota es un tictac que
en diez minutos es insoportable.

| voz | que es |
|---|---|
| `tic(par)` | el escape. Alterna dos alturas, como un escape real |
| `whir` | el barrido del segundero continuo |
| `minuto` / `hora` | campanitas de vidrio, inarmonicas |
| `modo` / `color` / `auto` | la interfaz, apenas audible |

Techo de 10 voces por frame: el reloj no tiene fisica, su pico real es la campanada de la hora.

> Patron comun a todo el repo: sintesis WebAudio sin archivos, `AudioContext` creado con
> `try/catch` en el primer gesto, techo de voces por frame **con su reseteo al tope del `loop()`**,
> cooldown por voz, boton de mute con persistencia en `localStorage`, y `visibilitychange` para que
> nada continuo siga sonando con la pestana al fondo. Si el audio falla, el juego sigue andando.
> Verificado con un arnes headless que envuelve el `AudioContext` y anota cada nodo y cada rampa.
> **El arnes no escucha**: comprueba que suene lo que se diseno, cuando se diseno y con que
> parametros. La evaluacion auditiva queda pendiente.
