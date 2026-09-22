# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A trimmer variant of [../Balls/Balls.py](../Balls/Balls.py): 1280×720 window, smaller balls (`sper(0.01)` max radius vs `0.05`), random RGB colors instead of light/shadow shading, cap raised to **300** balls via mouse wheel, minimum `forceSpeed` clamped to 500 (so balls never fully come to rest). The light-vector draw block from Balls is removed, but the SPACE-toggled debug overlay is still wired up.

Same controls as Balls: **LMB** drag, **wheel** add/remove, **SPACE** debug, **RMB** FPS, **ESC** quit. The eight-branch wall-bounce logic in `Ball.process` is identical to Balls — keep them in sync if behavior changes.

See [../Balls/CLAUDE.md](../Balls/CLAUDE.md) for the wall-bounce note and [../CLAUDE.md](../CLAUDE.md) for shared conventions.


## AUDIO — correccion (2026-09-22)

`audioResume()` creaba el `AudioContext` **sin `try/catch`**, y es la PRIMERA sentencia del handler
de `pointerdown` del canvas. Si el constructor tira (una WebView sin audio, Safari con demasiados
contextos), la excepcion se lleva puesto el resto del handler y nunca corren
`canvas.setPointerCapture()` ni la creacion del estado del puntero: **el juego no quedaba mudo,
quedaba SIN INPUT**. Tambien faltaba el `.catch()` del `resume()`.

Pendiente (ver la auditoria): toda la capa de impactos esta estrangulada — un solo bucket con
cooldown de 120 ms, o sea un techo duro de 8.3 clicks/s pase lo que pase, y el que suena es el
primer par que pasa el cooldown, no el mas fuerte.
