# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Hangman / Ahorcado, bilingual (Spanish / English) with category + hint shown above the word. 1280×720 window. Six-strikes rule (`MAX_FAILS = 6`). Spanish UI strings (`'PERDISTE'`, `'LA PALABRA ERA'`) live alongside the English ones in the `UI_TEXT` dict: keyed by `manager[0].lang` (`'es'` / `'en'`).

Follows the shared repo skeleton (`Sprite`, `deltaT`, `xper/yper/sper`, `createText`, `manager[0]`). Sprites: `Manager` (state + input), `Gallows` (draws scaffold + figure based on `m.fails`), `WordDisplay`, `LettersUsed`.

## Letter input goes through KEYDOWN events, not `keys[K_x]`

Unlike the rest of the repo, letter guesses are consumed from `key_events` (a module-level list rebuilt each frame from `pygame.event.get()` filtered to `KEYDOWN`) and read via `ev.unicode`. **Required** because the Spanish alphabet includes Ñ, which has no stable `pygame.K_*` constant: `event.unicode` is the only reliable source. Don't refactor to `keys[pygame.K_x] + flag` polling.

The main loop has a non-standard quirk: in `state == 'menu'`, only the `Manager` sprite is drawn; the others are skipped because they assume a word is active. If you add a sprite that should render in the menu, special-case it the same way at [Hangman.py:461](Hangman.py#L461).

## Word lists

`words_es.txt` and `words_en.txt` live next to the script and are loaded by `load_words(filename)` (resolved via `os.path.dirname(__file__)`, so it works regardless of cwd). Format, one entry per line:

```
PALABRA|CATEGORIA|pista
```

Category and hint are optional (drop trailing `|` segments). `#` lines and blank lines are skipped. Words are uppercased on load; the Spanish file deliberately omits accents (`ARANA`, `ATUN`) but keeps `Ñ` (`ESPAÑA`). When adding entries, match the existing convention.

State machine in `Manager.state`: `'menu'` → `'playing'` → `'won'` / `'lost'`. `ESC` from any play state returns to menu; `ESC` from menu quits. `revealed` is a `list[bool]` parallel to `word`, with spaces pre-revealed so multi-word phrases display the gap. `wins`/`losses` persist across rounds until the process exits.

The hanged-figure draw is incremental: `fails ≥ 1` head, `≥ 2` body, `≥ 3` left arm, `≥ 4` right arm, `≥ 5` left leg, `≥ 6` right leg. On the killing blow the figure switches color to red and the eyes become X marks. `Gallows.shake_t` triggers a brief horizontal shake when `fails` increases: driven by comparing `m.fails` to `self.last_fails` rather than from a callback.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop conventions.


## AUDIO (2026-09-22)

**Dry wood, rope and graphite.** Three materials and not one synthesiser with a melody. The world is
four beams, a rope and a stick figure drawn on a dark room: a prop gallows built on top of a pencil
and paper game.

- **A hit is graphite.** Short, bright noise at 2600 Hz with no defined pitch: the pencil filling in
  blanks. **One stroke per revealed square**, ascending: revealing four letters sounds like four
  strokes (measured: 2600 / 2912 / 3224 / 3536 Hz), not like one louder hit.
- **A miss is the gallows mallet.** And the ladder descends: **460 → 400 → 340 → 280 → 220 Hz** with
  the gain rising from 0.076 to 0.116. Each mistake lands lower and louder. You do not need to count
  the figure's limbs to know how much is left.
- **The sixth miss does NOT stack mallet + fall.** It is ONE single defeat voice, in `sine`. Stacked,
  the last mistake would sound like the previous five plus noise.
- **What does not play:** a letter already tried, a key outside the alphabet, and tapping the canvas
  mid-round. None of the three is a rejected action: they are non-actions.

> Pattern shared across the repo: WebAudio synthesis with no files, an `AudioContext` created
> inside `try/catch` on the first gesture, a per-frame voice ceiling **with its reset at the top of
> `loop()`**, a per-voice cooldown, a mute button persisted in `localStorage`, and
> `visibilitychange` so nothing continuous keeps playing with the tab in the background. If audio
> fails, the game keeps running. Verified with a headless harness that wraps the `AudioContext` and
> logs every node and every ramp. **The harness does not listen**: it checks that what was designed
> plays, when it was designed to, with which parameters. Judging it by ear is still pending.
