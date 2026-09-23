# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Revision of [../Fireworks/Fireworks.py](../Fireworks/Fireworks.py). Two functional differences from V1:

- **Window is 1920×800** (ultrawide) instead of 800×800, and firework base `radius` is smaller (`sper(0.0015)` vs `sper(0.005)`).
- **Pause actually pauses.** The main loop guards `sprite.process()` with `if not manager.pause or sprite == manager`, and a blinking "PAUSE" text is drawn via `pauseBlinkCD`. In V1 the pause flag exists but the loop ignores it.

All other behavior, controls (`LMB`/`MMB`/`RMB`/`SPACE`/`Q`/`W`/`F`/`P`/`ESC`), color palette, recursion structure, matches V1. See [../Fireworks/CLAUDE.md](../Fireworks/CLAUDE.md) for control details and [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO, fixes (2026-09-22)

Identical to `Fireworks/`, the two games' audio blocks are the same but for the comments, and
**touching one means touching the other**:

1. `audioResume()` with no `try/catch`: the game became unplayable if the context could not be created.
2. No `visibilitychange`: the looping ambience kept playing with the app in the background.
