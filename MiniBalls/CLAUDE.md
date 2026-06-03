# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A trimmer variant of [../Balls/Balls.py](../Balls/Balls.py): 1280×720 window, smaller balls (`sper(0.01)` max radius vs `0.05`), random RGB colors instead of light/shadow shading, cap raised to **300** balls via mouse wheel, minimum `forceSpeed` clamped to 500 (so balls never fully come to rest). The light-vector draw block from Balls is removed, but the SPACE-toggled debug overlay is still wired up.

Same controls as Balls: **LMB** drag, **wheel** add/remove, **SPACE** debug, **RMB** FPS, **ESC** quit. The eight-branch wall-bounce logic in `Ball.process` is identical to Balls — keep them in sync if behavior changes.

See [../Balls/CLAUDE.md](../Balls/CLAUDE.md) for the wall-bounce note and [../CLAUDE.md](../CLAUDE.md) for shared conventions.
