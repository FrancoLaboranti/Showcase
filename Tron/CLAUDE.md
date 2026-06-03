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
