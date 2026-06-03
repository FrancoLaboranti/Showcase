# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Full chess with menu (2 players / vs IA as White / vs IA as Black / **IA vs IA spectator**), drag-and-drop **and** click-click moves, **conditionally slide-animated** moves (click-click animates, drag-and-drop snaps; AI always animates — `MOVE_ANIM_DURATION = 0.18 s`), history scrubbing with ←/→/HOME/END, captured-pieces side panels with material-advantage indicator, draw detection (threefold repetition + insufficient material), synthesised piece-move sounds, and **Stockfish** as the primary AI engine (with the internal negamax kept as fallback). 1280×720 window. Spanish UI labels (`'JAQUE MATE'`, `'Pensando...'`, `'Turno: Blancas'`); engine + AI identifiers are English.

Follows the repo skeleton loosely (`Sprite`, `xper/yper/sper`, `createText`) — `deltaT` is now used (for the move animation timer); everything else is event-driven.

## Engine

`grid` is **column-major**: `grid[c][r]` where `c` is the file (0=a, 7=h) and `r` is the rank from the top (0=rank 8, 7=rank 1). Don't transpose without auditing every helper — `find_king`, `square_attacked`, `simulate_move`, `cell_to_screen` all assume this layout.

`Piece` uses `__slots__ = ('color', 'kind', 'has_moved')` for cheap copies during search. `copy_grid` is a shallow per-column copy that **shares `Piece` objects** between snapshots — `has_moved` is mutated in `make_move` (real game) but the AI search calls `simulate_move` which builds new `Piece` only on promotion. Safe today because the AI never sets `has_moved`; if you change that, switch to deep copies.

Move tuples are `(c, r, extra_dict)` for pseudo/legal generation and `(fc, fr, tc, tr, extra)` for `all_legal_moves_with`. `extra` may contain `'promotion'`, `'double_push'`, `'en_passant'`, `'castle'`. Promotion is always to queen (no UI to pick).

En passant target is tracked in `Game.en_passant_target` as `(c, r)` of the *square the capturing pawn lands on*, set only after a double push and cleared on the next move.

## AI — Stockfish (primary) + internal negamax (fallback)

`_ai_worker` tries Stockfish first; if Stockfish is unavailable or fails, it falls back to the internal `find_best_move`. The result tuple is `(mv, gen, depth, engine_name)` — `engine_name` is `'Stockfish'`, `'Interno'`, or `'Random'` and surfaces in the UI as "Pensando (Stockfish)..." / "Última jugada Stockfish: profundidad N".

**Stockfish** ([init_stockfish](Chess.py)): UCI engine binary lives at `Chess/stockfish/stockfish-windows-x86-64-avx2.exe` (gitignored — see `.gitignore`). `_find_stockfish_path` walks a list of candidate names so an alternative SF build (BMI2, generic x86-64) works without code changes. Communicated via `python-chess` (`pip install chess`); if the import fails, `CHESS_LIB_AVAILABLE = False` and the internal engine takes over silently. The engine process is opened once at startup, guarded by `_stockfish_lock` for thread-safe `play()` calls, and closed by `atexit.register(close_stockfish)`.

**FEN conversion** (`build_fen`): my column-major grid + `Game.en_passant_target` + per-piece `has_moved` flags get serialised into a standard FEN. Castling rights are reconstructed from `has_moved` (king + relevant rook). The halfmove clock and fullmove number are hardcoded to `0 1` — no 50-move-rule or threefold support. After Stockfish returns a `chess.Move`, we convert square indices back to `(c, r)` with `7 - chess.square_rank(...)` and then look up the matching entry in `gen_legal_moves` to recover the `extra` dict (so castle/en-passant/promotion flags survive the round-trip).

**Internal engine** (`find_best_move`): negamax + alpha-beta + MVV/LVA-ish move ordering (`_move_order_key`), driven by iterative deepening with a wall-clock deadline. Tunables: `AI_TIME_BUDGET_S` (current default `1.5 s`, set near the top of the file — applies to **all** modes including IA vs IA), `AI_MAX_DEPTH = 10`. `TimeoutSignal` is raised mid-search when `time.time() >= deadline` — caught at each ID iteration to fall back to the best move from the previous depth.

**Threading contract** (applies to both engines):

- `Game._ai_lock` guards `_ai_result` only. `_stockfish_lock` is a separate lock that serialises calls to the single Stockfish process (Stockfish is single-threaded over UCI per session).
- `Game.gen` is a generation counter bumped on `reset_board` / `back_to_menu`. The worker stamps its result with the `gen` it started with; the main thread discards results whose `gen` no longer matches (prevents a stale move landing on a fresh board).
- The worker only **reads** a snapshot (`copy_grid(self.grid)` + `en_passant_target` + `turn`) and writes back through the lock — never touches live game state.

If you add fields the AI worker reads, snapshot them in `trigger_ai` before starting the thread.

## Move animation

`make_move(..., animate=True)` optionally kicks off an animation via `Game.animation = {from_c, from_r, to_c, to_r, piece_color, piece_kind, elapsed, duration, rook_anim}`. `process()` advances `elapsed` by `deltaT` and clears the dict when finished. The grid is updated **immediately** in `make_move`; the animation is purely visual — it skips drawing the piece at `to_cell` (and the rook's `to_cell` for castles) and draws the sliding piece at the interpolated position with a quadratic ease-out.

**When to animate** — by callsite:
- `handle_press` (click-click landing on a legal target): default `animate=True`. The piece didn't move with the cursor, so the slide is the only visual cue.
- `handle_release` (drag-and-drop completion): explicit `animate=False`. The user already dragged the piece visually to the destination — re-animating after release looks like the piece "jumps back and then forward". Snap it.
- AI moves (`process` applying `_ai_result` or `_pending_ai`): default `animate=True`. Same reasoning as click-click — the user didn't see the piece move.

While `animation is not None`: human input is gated off (no press/release), and the AI worker is **not** triggered. If an AI result arrives during animation, it's queued in `Game._pending_ai = (mv, depth, engine_name)` and applied on the next frame after `animation` clears. This keeps move visuals one-at-a-time even in IA-vs-IA mode where both sides would otherwise step on each other.

History scrubbing also disables the animation overlay — when `is_viewing_history()` is true, `draw_play` skips the animated-piece block entirely (the snapshot is rendered as-is).

## Mode model

- `mode`: `'pvp'` / `'w'` / `'b'` / `'aiva'`
- `ai_color`, `human_color`: set for `'w'` and `'b'`; both `None` for `'pvp'` and `'aiva'`
- `ai_both = True` only for `'aiva'`
- `current_player_is_ai()` is the only correct way to ask "should AI play now?" — it returns true if `ai_both` or the side-to-move matches `ai_color`. `is_human_turn()` is its negation.
- `flip = True` only when the human plays Black (mode `'b'`); IA vs IA keeps the white-bottom orientation.

## Sounds

Synthesised at startup in `init_sounds` — no asset files. Mixer is pre-init'd before `pygame.init()` (`pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)`); the order matters. `_make_buffer` writes int16 stereo (each mono sample written twice) into `array.array('h')`. `make_click` does decaying noise with optional tone; `make_chord` sums sines under a sine envelope. If `pygame.mixer.get_init()` returns false or any sound fails to build, `sounds = {}` and `play_sound` becomes a no-op — don't add asserts.

## History / navigation

`Game.history` is a list of snapshots (`grid`, `turn`, `last_move`, `status`, `game_over`, `captured`) pushed in `make_move` and on `reset_board`. `history_index` is the currently-viewed snapshot; `is_viewing_history()` is true when not at the tail. While viewing history, input handling is suppressed (`handle_press`/`handle_release` skipped) and the board border tints brown to signal the locked state. `END` returns to the live position, `HOME` jumps to the initial setup.

`_key_repeat(key, held_attr, fire_attr, action, initial=0.4, interval=0.06)` is the auto-repeat helper for ←/→ scrubbing — used because chess history needs key-repeat behaviour the simple "press flag" pattern in other games doesn't provide.

## Captured pieces / material advantage

`Game.captured` is a list of `(color, kind)` tuples appended in `make_move` *before* the destination square is mutated (so we can read the captured `Piece` first). The en-passant case captures from `(tc, fr)` not `(tc, tr)` — handled explicitly. Promotions are **not** captures and never appended.

`draw_captured(view_captured)` renders two side panels: the left shows captured white pieces (rendered with `color='w'` styling), the right shows captured black pieces. Pieces are sorted high-to-low by value (Q>R>B>N>P) and laid out in 2-column mini grids (`_render_captured`). A `+N` label in amber goes **above** the panel of the side that's ahead, where `N` is the standard material balance (P=1, N=B=3, R=5, Q=9). When `view_captured` comes from a history snapshot, the panels reflect that point in the game.

## Draw detection

Three forced draw rules beyond stalemate, checked at the end of `make_move` after turn change. Priority order: **mate > insufficient material > threefold repetition > continue**.

- **Threefold repetition** (`position_key` + `Game.position_counts`): `position_key` is `build_fen(...)` with the halfmove/fullmove suffix stripped — so it compares board + side-to-move + castling rights + en-passant target. `_record_position()` increments the count and returns it; when it reaches 3, `status = 'repetition'`. The initial position is counted (via `reset_board`'s explicit `_record_position()` call) so a position that recurs twice in play plus the start counts as three.
- **Insufficient material** (`has_insufficient_material(grid)`): returns true for K-vs-K, K-vs-K+N, K-vs-K+B, and K+B-vs-K+B with both bishops on same-coloured squares (`(c+r) % 2`). Any pawn / rook / queen on the board short-circuits to false.

`position_counts` is **not** snapshotted into `history`; navigating back doesn't rewind the counter (correct — repetition only applies to the live timeline). The terminal `status` *is* in the snapshot, so when scrubbing to the moment of repetition/material-draw the banner shows correctly.

## Rendering

Two freetype fonts: `font` (`'Segoe UI Semibold, Segoe UI, Calibri, Arial'` fallback chain) for UI text, `piece_font` (`'Segoe UI Symbol, Arial Unicode MS, DejaVu Sans'`) for the Unicode chess glyphs (`PIECE_CHARS`). The Segoe chain was picked over Century Gothic because Century Gothic ships without the `←` `→` glyphs needed by the history scrubbing label — they rendered as empty boxes. Segoe UI has them. Both piece colors share the same Unicode codepoint — colour is achieved by `draw_piece` rendering an 8-direction outline pass in the opposite colour then the fill on top. If a glyph is missing from the system font, pieces vanish; the fallback chain is intentional.

**Text layout above the board** is one main line at `yper(0.04)` that mutates by state (history banner / mate-stalemate-repetition-insufficient banner / `'Turno: X · Pensando (Stockfish)...'` / `'Turno: X · JAQUE'` / plain turn) and an optional secondary line at `yper(0.073)` showing the last AI move's depth. Board top is at `yper(~0.09)` so both lines clear it. Bottom controls live at `yper(0.985)` with size `sper(0.013)` — pushed down from the labels row to avoid the textual collision the smaller gap created.

Hovered/selected/last-move/check overlays are SRCALPHA surfaces blitted per-cell, not blended via `pygame.draw` with alpha (which doesn't support alpha on rect).

`flip = True` (when playing as Black) inverts both render order and `square_at_pixel` — both `cell_to_screen` and `square_at_pixel` apply the same `7 -` transform, so picking and drawing stay consistent.

## Setup (Stockfish)

The repo ships a `.gitignore` excluding `stockfish/`, so the binary is **not** committed. To re-set up on a fresh clone:

1. `pip install chess` — the python-chess UCI wrapper.
2. Download Stockfish for Windows from [the official releases](https://github.com/official-stockfish/Stockfish/releases) (or use the AVX2 build that's already extracted). Drop the `stockfish/` folder under `Chess/` so the binary lands at `Chess/stockfish/stockfish-windows-x86-64-avx2.exe`.
3. Run normally — `init_stockfish` finds it automatically; the menu shows "Motor: Stockfish" in green when ready, "Motor: Interno (Stockfish no disponible)" in amber when not.

If the AVX2 build crashes on an older CPU, swap in `stockfish-windows-x86-64.exe` (no SIMD extensions required); `_find_stockfish_path` already lists that filename.

## Controls (recap, since they're not all on screen)

- LMB on a piece → select (legal targets shown as green dots / rings).
- LMB-drag → drag-and-drop move.
- LMB on a target square while a piece is selected → click-click move.
- ←/→ scrub history (auto-repeat after 0.4 s).
- `HOME` / `END` → first / latest position.
- `R` → restart current game; `N` → back to menu; `ESC` → quit.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop conventions this file partially follows.
