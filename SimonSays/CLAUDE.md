# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Classic Simon memory game — watch a growing sequence of colored/sounding buttons, repeat it back. 700×700 window. Spanish identifiers (`fuente`, `colors`, `buttons`, `swidth`, `sheight`).

## ⚠️ This file is ~660 KB — do NOT read it in full

The `sounds` list at module top contains four `pygame.mixer.Sound(buffer=b'...')` calls with **raw PCM audio sample buffers pasted as bytes literals** — that's where all the bulk lives. The actual game logic is small (~212 lines visually but most of the line count is the audio bytes spread across long lines).

When editing:

- Use `Grep` to find code sections rather than reading the file.
- When reading with the `Read` tool, always pass `offset` and `limit` — a bare `Read` will exceed the token cap.
- Treat the four bytes literals inside `sounds = [...]` as opaque binary; don't reformat or modify them.

Mixer is pre-initialized with `pygame.mixer.pre_init(frequency=44100, size=-16)` before `pygame.init()` — the order matters; don't reorder.

See [../CLAUDE.md](../CLAUDE.md) for shared conventions.


## AUDIO — correccion (2026-09-22)

`playTone()` se llama desde `update()`, que corre dentro de `loop()`, y el `requestAnimationFrame`
esta al final. Si la creacion del contexto tiraba, Simon no quedaba mudo: quedaba **CONGELADO para
siempre**. Ahora `audioResume()` va en `try/catch` y `playTone` exige `actx.state === 'running'` —
un contexto interrumpido tira al crear el nodo.

Pendiente, del lado Python: la auditoria midio que **los cuatro tonos no se distinguen entre si y
uno es inaudible**. En un juego de memoria donde el tono ES la mnemotecnia, eso rompe la funcion
del audio, no solo la estetica. Los cuatro buffers viven como literales de bytes en `SimonSays.py`.
