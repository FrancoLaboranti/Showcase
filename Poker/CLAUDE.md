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

**Paper on cloth, clay against clay, and wood.** None of the three materials sings. Everything comes
out of filtered, very short noise; the only tonal concession is the two notes of the result, which
live BELOW the materials and arrive after the chips, never before.

**Money is translated into A NUMBER OF CHIPS, not into volume**: `n = 2 + log2(amount / big blind)`,
clamped between 2 and 10. Measured: $20 is 2 chips, $160 is 5, an all-in of $1000 is 9 and louder.
The ear counts chips far better than it judges decibels, so you hear the size of a bet without
looking at the number. The CPU's have the same count but a closed filter and less gain: it is on the
other side of the table.

**Two funnels, not twenty hook-ups.** All money goes through `postBet()` and all cards through
`makeCard()`. Hooking in there keeps a new branch of the game from being born mute. Cards stagger
themselves: several dealt in the same frame come out one behind the other, with rhythm.

**Budget per EVENT, not per node.** The pattern's ceiling counts at SCHEDULE time, and an all-in
schedules ten chips in one frame: with a ceiling of 4, voices 5 through 10 would vanish with no
error and no symptom. Poker has no physics — its state machine serialises everything — so each
trigger counts once and creates its internal nodes without touching the counter again. Ceiling 12.

The raise-amount tick plays **only if the amount actually changed**: against the cap, holding the
button down cannot keep playing or the button is lying about what it did.

> Pattern shared across the repo: WebAudio synthesis with no files, an `AudioContext` created
> inside `try/catch` on the first gesture, a per-frame voice ceiling **with its reset at the top of
> `loop()`**, a per-voice cooldown, a mute button persisted in `localStorage`, and
> `visibilitychange` so nothing continuous keeps playing with the tab in the background. If audio
> fails, the game keeps running. Verified with a headless harness that wraps the `AudioContext` and
> logs every node and every ramp. **The harness does not listen**: it checks that what was designed
> plays, when it was designed to, with which parameters. Judging it by ear is still pending.
