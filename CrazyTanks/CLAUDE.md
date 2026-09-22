# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Top-down 4-tank racing game with menu, tournament mode, 10 tracks, 3 race lengths (10/20/40 laps), 4 AI difficulties, and a ramming/bomb combat layer. ~1087 lines — read with `offset`/`limit` rather than in one shot.

## Controls

- **Player 1** — Arrows + `SPACE` (shoot)
- **Player 2** — `WASD` + `LCTRL` (shoot, two-player mode only)
- **Menus** — Arrows to navigate, `RETURN` to confirm, `ESC` to back out / quit
- **In-race debug** — `F1` toggles tank hitboxes, `F2` toggles trackpoint markers

## Architecture notes

- Sprite classes: `Tank`, `Bomb`, `Wall`, `TrackPoint`, `MainHandler` (menus + state), `AuxiliaryHandler` (in-race state — countdown, pause, tournament scoring). Parallel lists `tanks`, `bombs`, `walls`, `trackpoints` mirror subsets of `sprites`.
- **Track data is huge inline literals.** Wall rectangles live in `Wall.__init__`'s `maps` tuple; centerline waypoints live in `TrackPoint.__init__`'s `maps` list, populated by per-track loops (`PARK`, `HALLWAYS`, `MESSY`, `PORTAL`, `ZIGZAG`, `SMILEY`, `TWAINPORTALS`, `SNAIL`, `COMBINED`, `BOXES`). Per-track `(nWalls, nTrackpoints)` counts are also hard-coded in `MainHandler.process` and `AuxiliaryHandler.process` — edit both when adding/removing geometry.
- **Resolution-dependent physics.** `Tank.process` scales velocity/angular velocity differently based on `SCREEN_X` thresholds (`>=1400`, `>=1000`, `>=500`). Don't simplify without testing across window sizes.
- **AI lap-following.** `Tank.process` finds the nearest trackpoint, then aims at the point 8 ahead (`(closest.id+8) % len(trackpoints)`). Lap counting uses `lap_checkpoint` (0→1 near start, 1→2 near end, →0 crossing finish).

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**Chapa de acero y eslabones de oruga sobre un piso que cambia.** No son autos: son cajas metalicas
con traccion por cadena, y eso manda DOS capas continuas y no una. Un auto tiene una sola voz; un
tanque tiene el motor y tiene lo que el motor arrastra.

### La oruga cambia de material con el bioma

`THEME_HANDLING` le da a cada bioma un agarre lateral distinto (0.01 en nieve, 0.40 en desierto), y
ese numero YA existe y ya decide como se maneja el tanque. La oruga lo usa para cambiar de
material. Medido:

| bioma | agarre | ganancia de la oruga | filtro |
|---|---|---|---|
| desierto | 0.40 | 0.032 | 1920 Hz — duro, granulado |
| nieve | 0.01 | 0.010 | 520 Hz — sordo, apagado |

**El piso se escucha antes de verlo derrapar.**

El motor va de 34 a 80 Hz con la velocidad; el pulso del diesel sale del batido entre dos sierras
casi juntas. El nitro es un **tercer tap del MISMO buffer de ruido** que la oruga, no una fuente
nueva: un `BufferSource` es de un solo uso, pero sus salidas se ramifican todas las veces que haga
falta.

Las tres capas continuas son **un solo grafo por sesion**: se modulan, no se recrean. Se reescriben
a 20 Hz — escribir seis `AudioParam` por frame no aporta nada audible.

Discretos: el disparo es una **TOS de mortero, no un laser** (esto tira bombas por un cano corto),
el impacto es la chapa primero y el hueco del casco despues, y la cuenta regresiva dispara por
FLANCO — `seg` se recalcula cada frame y sin el flanco seria un zumbido continuo.

Solo suenan las vueltas del JUGADOR: siete tanques cruzando la meta serian siete campanadas sin
sentido.

> Patron comun a todo el repo: sintesis WebAudio sin archivos, `AudioContext` creado con
> `try/catch` en el primer gesto, techo de voces por frame **con su reseteo al tope del `loop()`**,
> cooldown por voz, boton de mute con persistencia en `localStorage`, y `visibilitychange` para que
> nada continuo siga sonando con la pestana al fondo. Si el audio falla, el juego sigue andando.
> Verificado con un arnes headless que envuelve el `AudioContext` y anota cada nodo y cada rampa.
> **El arnes no escucha**: comprueba que suene lo que se diseno, cuando se diseno y con que
> parametros. La evaluacion auditiva queda pendiente.
