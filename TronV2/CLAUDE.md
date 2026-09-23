# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Revision of [../Tron/Tron.py](../Tron/Tron.py). Same 4-player concept, same 1280×720 window, same per-player two-key control scheme (P1 `LEFT`/`DOWN`, P2 `Q`/`W`, P3 `O`/`P`, P4 `V`/`B`).

Functional differences from V1:

- **`directions` arrays are 8 elements** (`[dx150, dy150, dx2, dy2, dx4, dy4, dx100, dy100]`) instead of 6: multiple scout distances for more thorough AI lookahead.
- **Player colors are injected** as a constructor parameter (`Player(i, colors, ...)`) instead of being hardcoded inside the class.
- **AI uses `maxDistanceDir`** to pick the direction with the most clear space ahead, replacing V1's `dire_cdtime` random-interval direction commits.
- Uses `pygame.freetype` (V1 does not).

V1 still exists alongside this: don't delete it. Keep both files behaviorally distinct rather than back-porting changes between them.

See [../Tron/CLAUDE.md](../Tron/CLAUDE.md) for control details and [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## AUDIO (2026-09-22)

**There is no matter, there are programs.** No mass, no friction, no impact, no gravity: it is a grid
of byte occupancy where four fixed-colour programs advance at constant speed and can only turn 90
degrees. A purely electronic vocabulary: `square` and `sawtooth`, quantised pitches, straight
envelopes, zero jitter in the player's voices: the turn is deterministic, not a collision.

**Each program has a fixed PITCH, the same way it has a fixed colour.** Measured: AI 1's de-rez plays
at 277 Hz, AI 2's at 330, AI 3's at 392. You know which one fell without looking at the minimap.

**White noise appears in ONE place in the whole game: the de-rez**, because disintegrating is the only
thing here that breaks. That is why it stands out so much: it competes with nothing in its family.

**The turn has no voice of its own**: the continuous engine JUMPS to the note for the new direction's
step (0 / +2 / +4 / +5 semitones). All that is added is a relay click well at the back, so the gesture
has an edge. The engine also opens up with proximity to a wall, using the same forward scan the game
already does.

In the menu, the VALUE sounds at its own pitch (you hear it go up) and the ROW is dull and fixed: two
different classes of gesture cannot sound the same.

> Pattern shared across the repo: WebAudio synthesis with no files, an `AudioContext` created
> inside `try/catch` on the first gesture, a per-frame voice ceiling **with its reset at the top of
> `loop()`**, a per-voice cooldown, a mute button persisted in `localStorage`, and
> `visibilitychange` so nothing continuous keeps playing with the tab in the background. If audio
> fails, the game keeps running. Verified with a headless harness that wraps the `AudioContext` and
> logs every node and every ramp. **The harness does not listen**: it checks that what was designed
> plays, when it was designed to, with which parameters. Judging it by ear is still pending.
