# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Tic-tac-toe with a menu (2 players / vs CPU as X / vs CPU as O) and a persistent X/O/draw scoreboard. 1280×720 window. Mixed Spanish UI / English identifiers — comments and menu labels in Spanish (`'GANA LA CPU'`, `'EMPATE'`, `'ELEGÍ MODO'`), code is English.

Follows the shared repo skeleton (`Sprite`, `deltaT`, `xper/yper/sper`, `createText`, `manager[0]`/`board[0]` as single-element lists). Two sprites only: `Manager` (menu/HUD/input) and `Board` (cells + CPU move + drawing).

The board is a `list[9]` of ints (`0` empty, `1` X, `2` O), indexed row-major (`row*3 + col`). `WIN_LINES` is the 8-tuple of triplets used by `checkWinner` — it returns `(winner, line)`, `(0, None)` for a draw, or `None` if the game continues. Don't reorder the cells list without updating `WIN_LINES` and `cellCenter` together.

State machine in `Manager.state`: `'menu'` → `'play'` → `'over'`. `ESC` from `'play'`/`'over'` returns to `'menu'`; `ESC` from `'menu'` quits. After each round `startingTurn` toggles so X and O alternate who opens. `R` on the game-over screen wipes the scoreboard.

CPU uses full negamax + alpha-beta (`bestMove` → `negamax`) with `rootMark` carried through to score `+1`/`-1`/`0` from that side's perspective. 3×3 is trivial so there's no depth cap or transposition table — don't add one unless the board size changes. `Board.cpuThinkCD` (0.35 s) is a cosmetic delay so the CPU doesn't slap a mark down instantly; the search itself is sub-ms.

Place/win animations use `easeOutBack` (overshoot pop on placement) and `easeOutCubic` (winning-line draw-in). Both are local helpers, not in the shared skeleton.

`Alt+Enter` toggles fullscreen (recreates `windowSurface` with `pygame.FULLSCREEN`); `F` toggles FPS overlay. The Alt+Enter rebind pattern is repeated verbatim in other games — match it if you add similar shortcuts.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop conventions.


## AUDIO (2026-09-22)

**Vidrio sobre laca.** El tablero es una losa laqueada con sombra proyectada y las marcas son
vidrio encendido con halo. Cada marca es una piedra que se apoya sobre una superficie dura: un
transitorio de ruido pasa-altos + una resonancia afinada corta.

**La altura no la fija la celda: la fija cuantas marcas hay ya en el tablero.** La ronda entera
trepa por una pentatonica menor de nueve grados, asi que el noveno movimiento suena apretado aunque
mecanicamente sea identico al primero. El tablero se vuelve un instrumento que se llena.

- **X = `triangle`, O = `sine` una quinta justa arriba.** Asi las dos marcas conviven sin disonar
  por mas que se alternen. Medido: 219 Hz (X, grado 1) / 389 (O) / 292 (X) / 493 (O).
- **Las dos victorias suenan distinto**: la de la X en `triangle` desde 261 Hz, la de la O en
  `sine` desde 392. El timbre lo pone el que gano.
- **El empate es lo contrario de resolver**: 220 + 247 Hz, una segunda mayor que se bate y no va a
  ningun lado.
- **La CPU no toca ese instrumento.** Antes de mover cierra dos contactos secos y sin altura, y eso
  es lo unico mecanico del juego. A proposito NO es el tictac de un pendulo: Loop ya es un reloj de
  bolsillo y los dos no se tienen que pisar.
- Techo de **8** y no 4: `sndThisFrame` cuenta osciladores CREADOS, y la fanfarria de victoria crea
  cinco de un saque. Un techo de 4 truncaria el unico momento musical del juego.

> Patron comun a todo el repo: sintesis WebAudio sin archivos, `AudioContext` creado con
> `try/catch` en el primer gesto, techo de voces por frame **con su reseteo al tope del `loop()`**,
> cooldown por voz, boton de mute con persistencia en `localStorage`, y `visibilitychange` para que
> nada continuo siga sonando con la pestana al fondo. Si el audio falla, el juego sigue andando.
> Verificado con un arnes headless que envuelve el `AudioContext` y anota cada nodo y cada rampa.
> **El arnes no escucha**: comprueba que suene lo que se diseno, cuando se diseno y con que
> parametros. La evaluacion auditiva queda pendiente.
