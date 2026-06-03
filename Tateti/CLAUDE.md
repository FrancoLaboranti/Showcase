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
