# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Tron light-cycle game for 1–4 players (mix of humans + AI). Each player leaves a trail; collision with any trail or wall eliminates the player. Window is 1280×720.

## Controls (per player)

- **Player 1** — `LEFT` / `DOWN`
- **Player 2** — `Q` / `W`
- **Player 3** — `O` / `P`
- **Player 4** — `V` / `B`

Each player has two keys (left-turn / right-turn), not four directions. The `directions` dict maps direction id → `[dx150, dy150, dx2, dy2, scoutDx, scoutDy]`, which is used both for movement and for AI lookahead.

Menu controls: arrows to navigate, `RETURN` to confirm, `ESC` to back out / quit.

AI logic uses `aiturn_cdtime` / `aiturn_incd` to throttle turn decisions and `dire_cdtime` / `dire_incd` to throttle direction commits. See [../TronV2/](../TronV2/) for the revision with longer scout distance arrays and `maxDistanceDir` AI target tracking.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**Motos de luz.** Un motor continuo por sesion — dos sierras desafinadas 7 cents mas una tercera a
media frecuencia que representa al ENJAMBRE de IAs vivas, todo por un lowpass resonante.

**El motor convierte en sonido un dato que el juego YA calcula para la IA**: `clearDist`, cuanto
espacio libre hay adelante. Cuanto menos queda, mas agudo y mas abierto el filtro. **Pasar raspando
una estela deja de ser solo visual.** Y una capa de enjambre por cada IA viva: medido, ganancia
0.012 con 3 cycles en pista, 0 cuando queda uno.

El motor **baja a 0, nunca para**: un oscilador detenido no se puede volver a arrancar, y cortar en
seco clickea.

Una ronda es un parcial y el set es el desenlace real: si el set termino suena **solo** `setEnd`.
Apilar los dos convierte el final en un choque de dos jingles y no se entiende ninguno.

### El bug que tenia

`audioResume()` estaba **definida y nunca se llamaba**. Ningun gesto la enganchaba, asi que el
`AudioContext` no se creaba jamas y el juego era mudo pase lo que pase — medido con el arnes: cero
contextos. Y como `buildEngine()` vive adentro de `audioResume`, el motor entero
(`buildEngine`/`engineUpdate`/`engineOff`) era codigo muerto: ninguna de las tres se llamaba.
Faltaban ademas el reseteo del techo por frame, los tres sitios de llamada de ronda/set, el handler
del boton de mute y el `visibilitychange`.

> Patron comun a todo el repo: sintesis WebAudio sin archivos, `AudioContext` creado con
> `try/catch` en el primer gesto, techo de voces por frame **con su reseteo al tope del `loop()`**,
> cooldown por voz, boton de mute con persistencia en `localStorage`, y `visibilitychange` para que
> nada continuo siga sonando con la pestana al fondo. Si el audio falla, el juego sigue andando.
> Verificado con un arnes headless que envuelve el `AudioContext` y anota cada nodo y cada rampa.
> **El arnes no escucha**: comprueba que suene lo que se diseno, cuando se diseno y con que
> parametros. La evaluacion auditiva queda pendiente.
