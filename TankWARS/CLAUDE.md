# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Top-down tank shooter with RPG-style upgrades — **distinct project from [../CrazyTanks/](../CrazyTanks/)**, which is a racing game. ~1870+ lines.

## Tank capabilities

Each `Tank` carries: `health`, `attack`, `defense`, `moveSpeed`, `primaryShotAS`, `secondaryShotAS`, `shieldCapacity`, `shieldCharge`, `shieldChargeSpeed`, `shieldAugment`, `healthRegenCD`/`healthRegenSpeed`. Combat uses primary + secondary shots with separate cooldowns and a shieldable defense layer (`shielded`, `shieldOverheat`).

## Controls

- **Player 1** (`Tank.__init__` default keys): `W`/`S`/`A`/`D` for move, `SPACE` for shield
- **TAB** — shop (manager `tabPressed` flag)
- **P** — pause
- **F** — toggle FPS
- **F1**, **F2**, **F3** — debug toggles (hitboxes / scout markers / etc.)
- **Alt+Return** — fullscreen toggle
- **ESC** — quit / back out

Window is 1280×720, recreatable in fullscreen at runtime. Sprites use a "scout" pattern (`scoutX`/`scoutY`) for AI target previews; tanks also push back against borders via `borderPushX`/`borderPushY` rather than clamping position.

Read with `offset`/`limit` rather than in one shot.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**Chapa, cordita y electricidad.** Acero grueso y hueco, chasis placados con orugas, cajas de
madera reforzada. Nada aca suena a videojuego retro: suena a maquinas pesadas rompiendose en un
galpon.

**Cinco familias, cada una con una funcion exclusiva y sin solaparse en el registro.** Esa
separacion es lo que permite entender una pantalla con veinte cosas pasando a la vez sin mirarla:

| familia | que es | donde |
|---|---|---|
| CHAPA | bandpass 180-320 Hz, Q alto, cola corta | todo impacto metalico (la mas frecuente) |
| CORDITA | ruido lowpass con sub | disparos, misiles, minas, muertes |
| ELECTRICIDAD | senos limpios 680-1700 Hz | escudo, absorcion. Lo unico que no es materia |
| MADERA | bandpass 520 Hz, Q bajo | las cajas destructibles, y NADA mas |
| ORO | el unico registro brillante y limpio | monedas y lootbox |

**Lo propio y lo ajeno se separan por CUERPO y volumen, no por timbre.** Tu canon lleva un sub de
88 Hz que el del enemigo no tiene, y el enemigo suena a 0.028 contra tus 0.075. Un canonazo es un
canonazo venga de donde venga; lo que cambia es quien lo tiene al lado.

Los registros medidos no se pisan: **mina 68 Hz** (la mas grave del juego, para que no se confunda
con ningun misil), muerte grande 91, explosion 97, misil propio 140.

- **El critico es una capa ADITIVA sobre el impacto, no un reemplazo**: primero se oye que pegaste
  y despues que pegaste bien.
- **El ping de la lootbox SUBE con lo poco que le queda**: 900 Hz entera, 1580 Hz a punto de
  romperse. Se oye sin mirar la barra.
- **El escudo roto es la UNICA disonancia del juego** (1400 + 1483 Hz, un semitono). Por eso se
  entiende al instante que algo se rompio y que era tuyo.
- El escudo activo es el unico nodo continuo: dos senos a un hercio de distancia que baten lento.
  No es un tono, es una presencia.

`window.__sfx` expone el vocabulario para el arnes headless: todo el juego vive dentro de un IIFE y
si no, no hay forma de verificarlo. Mismo criterio que el objeto `QA` de Loop; no toca estado.

> Patron comun a todo el repo: sintesis WebAudio sin archivos, `AudioContext` creado con
> `try/catch` en el primer gesto, techo de voces por frame **con su reseteo al tope del `loop()`**,
> cooldown por voz, boton de mute con persistencia en `localStorage`, y `visibilitychange` para que
> nada continuo siga sonando con la pestana al fondo. Si el audio falla, el juego sigue andando.
> Verificado con un arnes headless que envuelve el `AudioContext` y anota cada nodo y cada rampa.
> **El arnes no escucha**: comprueba que suene lo que se diseno, cuando se diseno y con que
> parametros. La evaluacion auditiva queda pendiente.
