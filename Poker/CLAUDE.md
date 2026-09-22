# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Heads-up Texas Hold'em vs CPU. No menu — `DEAL` button starts the hand straight from the table. Both sides rebuy to $1000 when broke. 1280×720 window. English UI throughout.

Follows the repo skeleton (`Sprite`, `deltaT`, `xper/yper/sper`, `createText`, `manager[0]`) plus a `Button` sprite with an `action` callback and an `enabled`/`hovered` flag set each frame by `Manager.process`.

## Card representation

Cards are 2-char strings (rank + suit): rank in `RANKS = '23456789TJQKA'` (so `'T'` is ten), suit in `SUITS = 'shdc'`. `SUIT_SYMBOL` / `SUIT_COLOR` / `RANK_DISPLAY` translate to display. Red suits are hearts and diamonds.

`Card` (sprite) holds its own animated `(x, y)` and a `flip` ∈ [0, 1] that lerps toward `flip_target`; `draw` renders the back when `flip ≤ 0.5` and the face when `> 0.5`, with horizontal scale `abs(flip - 0.5) * 2` so the card visually flips edge-on at the midpoint. `target_x/y` are set once in `deal_hand` / `advance_phase` — cards animate themselves toward those positions.

## Hand evaluation

`hand_rank(cards5)` returns a comparable tuple where the first element is the hand class (1=high card … 9=straight flush) and the rest are tiebreakers. `best_hand(seven)` iterates all `itertools.combinations(seven, 5)` and returns the max. The wheel (A-2-3-4-5) is detected explicitly as `uniq == [12, 3, 2, 1, 0]` with `straight_high = 3`. Ace-high straight is the normal sequential check.

Showdown uses raw tuple comparison (`p_score > c_score`); ties split the pot, odd chip goes to CPU (`self.pot - half`).

## Betting / phases

`Manager.phase` cycles: `'idle'` → `'preflop'` → `'flop'` → `'turn'` → `'river'` → `'hand_end'` → `'idle'`. `in_betting()` is true only for the four named betting rounds.

`button` flips between `'player'` and `'cpu'` each hand. In heads-up the button posts the small blind and acts first preflop; non-button acts first postflop — set in `advance_phase` (`non_button = ...`).

Round-end is detected in `check_round_end`: bets equalised AND both seats have `acted`. A raise wipes `acted` to just the raiser, forcing the other side to respond before the round can close.

## CPU policy

`cpu_act` is a rough heuristic, not a solver:
- **Preflop**: scores from high card / low card / pair / suited / connector with a uniform noise of `[-0.12, +0.10]`.
- **Postflop**: `strength = best_hand_class / 9` plus a small top-card bonus, same noise.
- Folds when facing a bet and `strength < 0.20 + pot_odds * 0.3`.
- Raises when `strength > 0.62` and (it didn't raise last, or 25% reroll), sized as `big_blind * choice([1,1,2,2,3])`.

The CPU "thinks" for 0.9 s (`cpu_timer`) before acting — driven from `Manager.process`, gated by `cpu_pending`. Don't move `cpu_act` into the inner loop; the delay is what makes the hand feel like a hand.

## Sprite deletion

This game **adds and removes sprites mid-session** (cards come and go). The pattern: append to `spritesToRemove`, then call `removeSprites()` (which also cleans `cards` / `buttons`). `removeSprites()` is invoked once per frame after the sprite loop in the main loop **and** once inside `deal_hand` before re-dealing. The double-call is intentional — `deal_hand` needs the list emptied before it creates new `Card` instances at the same target positions.

If you add a new typed sprite list, mirror the cleanup in `removeSprites`.

## Buttons

`Manager` builds six `Button` sprites in `__init__` (`bDeal`, `bFold`, `bCall`, `bRaise`, `bMinus`, `bPlus`) and toggles their `enabled` + relabels `bCall`/`bRaise` each frame in `process` based on `current_player`, `phase`, and call amount. Don't move the label logic into `Button.process` — it needs `Manager` state.

`Alt+Enter` toggles fullscreen; `F` toggles FPS overlay; `ESC` quits. Same pattern as the other games.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop conventions.


## AUDIO (2026-09-22)

**Papel sobre pano, arcilla contra arcilla y madera.** Ninguno de los tres materiales canta. Todo
sale de ruido filtrado y muy corto; la unica concesion tonal son las dos notas del resultado, que
viven POR DEBAJO de los materiales y llegan despues de las fichas, nunca antes.

**La plata se traduce a CANTIDAD DE FICHAS, no a volumen**: `n = 2 + log2(monto / ciega grande)`,
topeado entre 2 y 10. Medido: $20 son 2 fichas, $160 son 5, un all-in de $1000 son 9 y mas fuerte.
El oido cuenta fichas mucho mejor de lo que juzga decibeles, asi que el tamano de la apuesta se
escucha sin mirar el numero. Las de la CPU tienen el mismo conteo pero el filtro cerrado y menos
volumen: esta del otro lado de la mesa.

**Dos embudos, no veinte enganches.** Toda la plata pasa por `postBet()` y todas las cartas por
`makeCard()`. Engancharlos ahi evita que una rama nueva del juego nazca muda. Las cartas se
escalonan solas: varias repartidas en el mismo frame salen una atras de otra, con ritmo.

**Presupuesto por EVENTO, no por nodo.** El techo del patron cuenta al PROGRAMAR, y un all-in
programa diez fichas en un mismo frame: con el techo de 4 las voces 5 a 10 desaparecerian sin error
y sin sintoma. Poker no tiene fisica — su maquina de estados serializa todo —, asi que cada disparo
cuenta una vez y crea sus nodos internos sin volver a tocar el contador. Techo 12.

El tick del monto de la raise suena **solo si el monto cambio de verdad**: contra el tope, seguir
apretando no puede seguir sonando o el boton miente sobre lo que hizo.

> Patron comun a todo el repo: sintesis WebAudio sin archivos, `AudioContext` creado con
> `try/catch` en el primer gesto, techo de voces por frame **con su reseteo al tope del `loop()`**,
> cooldown por voz, boton de mute con persistencia en `localStorage`, y `visibilitychange` para que
> nada continuo siga sonando con la pestana al fondo. Si el audio falla, el juego sigue andando.
> Verificado con un arnes headless que envuelve el `AudioContext` y anota cada nodo y cada rampa.
> **El arnes no escucha**: comprueba que suene lo que se diseno, cuando se diseno y con que
> parametros. La evaluacion auditiva queda pendiente.
