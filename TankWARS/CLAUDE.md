# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Top-down tank shooter with RPG-style upgrades — **distinct project from [../CrazyTanks/](../CrazyTanks/)**, which is a racing game. ~1870+ lines.

## Tank capabilities

Each `Tank` carries: `health`, `attack`, `defense`, `moveSpeed`, `primaryShotAS`, `secondaryShotAS`, `shieldCapacity`, `shieldCharge`, `shieldChargeSpeed`, `shieldAugment`, `healthRegenCD`/`healthRegenSpeed`. Combat uses primary + secondary shots with separate cooldowns and a shieldable defense layer (`shielded`, `shieldOverheat`).

## Controls

- **Player 1** (`Tank.__init__` default keys): `W`/`S`/`A`/`D` for move, `SPACE` for shield
- **TAB** — shop (manager `tabPressed` flag)
- **P** — pause
- **F** — toggle FPS
- **F1**, **F2**, **F3** — debug toggles (hitboxes / scout markers / etc.)
- **Alt+Return** — fullscreen toggle
- **ESC** — quit / back out

Window is 1280×720, recreatable in fullscreen at runtime. Sprites use a "scout" pattern (`scoutX`/`scoutY`) for AI target previews; tanks also push back against borders via `borderPushX`/`borderPushY` rather than clamping position.

Read with `offset`/`limit` rather than in one shot.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.
