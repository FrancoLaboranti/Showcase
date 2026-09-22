# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Revision of [../Tron/Tron.py](../Tron/Tron.py). Same 4-player concept, same 1280×720 window, same per-player two-key control scheme (P1 `LEFT`/`DOWN`, P2 `Q`/`W`, P3 `O`/`P`, P4 `V`/`B`).

Functional differences from V1:

- **`directions` arrays are 8 elements** (`[dx150, dy150, dx2, dy2, dx4, dy4, dx100, dy100]`) instead of 6 — multiple scout distances for more thorough AI lookahead.
- **Player colors are injected** as a constructor parameter (`Player(i, colors, ...)`) instead of being hardcoded inside the class.
- **AI uses `maxDistanceDir`** to pick the direction with the most clear space ahead, replacing V1's `dire_cdtime` random-interval direction commits.
- Uses `pygame.freetype` (V1 does not).

V1 still exists alongside this — don't delete it. Keep both files behaviorally distinct rather than back-porting changes between them.

See [../Tron/CLAUDE.md](../Tron/CLAUDE.md) for control details and [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**No hay materia, hay programas.** No hay masa, ni roce, ni impacto, ni gravedad: es una grilla de
ocupacion de bytes donde cuatro programas de colores fijos avanzan a velocidad constante y solo
pueden girar 90 grados. Vocabulario puramente electronico: `square` y `sawtooth`, alturas
cuantizadas, envolventes rectas, cero jitter en las voces del jugador — el giro es determinista, no
un choque.

**Cada programa tiene una ALTURA fija, igual que tiene un color fijo.** Medido: el de-rez de la IA
1 suena a 277 Hz, el de la 2 a 330, el de la 3 a 392. Se sabe cual cayo sin mirar el minimapa.

**El ruido blanco aparece en UN solo lugar de todo el juego: el de-rez**, porque desintegrarse es
lo unico de aca que se rompe. Por eso se destaca tanto — no compite con nada de su familia.

**El giro no lleva voz propia**: el motor continuo SALTA de nota al escalon de la nueva direccion
(0 / +2 / +4 / +5 semitonos). Lo unico que se agrega es un click de rele muy al fondo, para que el
gesto tenga un borde. El motor se abre ademas con la proximidad a una pared, usando el mismo
escaneo hacia adelante que el juego ya hace.

En el menu, el VALOR suena a su altura (se oye que subio) y el RENGLON es sordo y fijo: dos clases
distintas de gesto no pueden sonar igual.

> Patron comun a todo el repo: sintesis WebAudio sin archivos, `AudioContext` creado con
> `try/catch` en el primer gesto, techo de voces por frame **con su reseteo al tope del `loop()`**,
> cooldown por voz, boton de mute con persistencia en `localStorage`, y `visibilitychange` para que
> nada continuo siga sonando con la pestana al fondo. Si el audio falla, el juego sigue andando.
> Verificado con un arnes headless que envuelve el `AudioContext` y anota cada nodo y cada rampa.
> **El arnes no escucha**: comprueba que suene lo que se diseno, cuando se diseno y con que
> parametros. La evaluacion auditiva queda pendiente.
