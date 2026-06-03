# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A non-grid Snake: the head smoothly chases the mouse cursor, each body segment chases the segment in front of it. Window is 1280×720, toggleable to fullscreen at runtime (the main loop recreates `windowSurface` with `pygame.FULLSCREEN` when `self.fullScreen` flips).

**LMB held** = sprint (head speed ×1.5). Each `SnakePiece` adjusts its `vel` and `angVel` based on distance to its target, so the body undulates naturally around tight turns. New segments inherit position and angle from the previous-tail segment.

Body coloring alternates: every 4th segment uses a brighter green range (`randColorInRange(10,40,225,255,10,40)`), the rest use a darker green. Per-segment `wave_time`/`wave_time_total` drives a sine-wave breathing animation.

The `manager` global is a single-element list `[Manager()]` — index it as `manager[0]` (see `SnakePiece.process` reading `manager[0].gameOver` and `manager[0].pause`). This is unusual for the repo; don't replace it with a plain object without updating every read site.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.
