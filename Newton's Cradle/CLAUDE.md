# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Newton's cradle simulator — pendulum balls hanging by strings, dragging one and releasing transfers momentum through the chain. Window is 1280×720. Press **UP** to add a ball, **DOWN** to remove one (capped between 1 and 10 balls).

Spanish identifiers throughout (`radio`, `velocidad`, `angulo`, `colisiona`, `colision_ryp`, `colision_circulos`, `orig_x/orig_y`). Folder name contains an apostrophe — quote the path when running: `python "Newton's Cradle\Newton's Cradle.py"`.

Diverges from the repo skeleton: no `Sprite` base class, no `xper`/`yper` helpers, no `deltaT` (uses fixed-step physics). The `Ball` class manages its own pendulum integration via `angulo` and `velocidad` around its anchor `orig_x, orig_y`.

See [../CLAUDE.md](../CLAUDE.md) for the shared conventions this file does not follow.
