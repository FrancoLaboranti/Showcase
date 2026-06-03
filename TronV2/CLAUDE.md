# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Revision of [../Tron/Tron.py](../Tron/Tron.py). Same 4-player concept, same 1280×720 window, same per-player two-key control scheme (P1 `LEFT`/`DOWN`, P2 `Q`/`W`, P3 `O`/`P`, P4 `V`/`B`).

Functional differences from V1:

- **`directions` arrays are 8 elements** (`[dx150, dy150, dx2, dy2, dx4, dy4, dx100, dy100]`) instead of 6 — multiple scout distances for more thorough AI lookahead.
- **Player colors are injected** as a constructor parameter (`Player(i, colors, ...)`) instead of being hardcoded inside the class.
- **AI uses `maxDistanceDir`** to pick the direction with the most clear space ahead, replacing V1's `dire_cdtime` random-interval direction commits.
- Uses `pygame.freetype` (V1 does not).

V1 still exists alongside this — don't delete it. Keep both files behaviorally distinct rather than back-porting changes between them.

See [../Tron/CLAUDE.md](../Tron/CLAUDE.md) for control details and [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.
