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


## AUDIO (2026-09-22)

**Plate, cordite and electricity.** Thick hollow steel, plated chassis with tracks, reinforced wooden
crates. Nothing here sounds like a retro video game: it sounds like heavy machines breaking in a
shed.

**Five families, each with an exclusive function and no overlap in register.** That separation is
what lets you read a screen with twenty things happening at once without looking at it:

| family | what it is | where |
|---|---|---|
| PLATE | bandpass 180-320 Hz, high Q, short tail | every metallic impact (the most frequent) |
| CORDITE | lowpassed noise with a sub | shots, missiles, mines, deaths |
| ELECTRICITY | clean sines 680-1700 Hz | shield, absorption. The only thing that is not matter |
| WOOD | bandpass 520 Hz, low Q | the destructible crates, and NOTHING else |
| GOLD | the only bright, clean register | coins and lootbox |

**Yours and theirs are separated by BODY and volume, not by timbre.** Your cannon carries an 88 Hz
sub the enemy's does not have, and the enemy plays at 0.028 against your 0.075. A cannon shot is a
cannon shot wherever it comes from; what changes is who has it next to them.

The measured registers do not overlap: **mine 68 Hz** (the lowest in the game, so it cannot be
confused with any missile), big death 91, explosion 97, own missile 140.

- **A critical is an ADDITIVE layer over the impact, not a replacement**: first you hear that you
  hit, then that you hit well.
- **The lootbox ping RISES as less of it is left**: 900 Hz intact, 1580 Hz about to break. You hear
  it without looking at the bar.
- **The broken shield is the game's ONLY dissonance** (1400 + 1483 Hz, a semitone). That is why it
  reads instantly as something breaking and as something of yours.
- The active shield is the only continuous node: two sines a hertz apart beating slowly. It is not a
  tone, it is a presence.

`window.__sfx` exposes the vocabulary to the headless harness: the whole game lives inside an IIFE
and without it there is no way to verify it. Same criterion as Loop's `QA` object; it touches no
state.

> Pattern shared across the repo: WebAudio synthesis with no files, an `AudioContext` created
> inside `try/catch` on the first gesture, a per-frame voice ceiling **with its reset at the top of
> `loop()`**, a per-voice cooldown, a mute button persisted in `localStorage`, and
> `visibilitychange` so nothing continuous keeps playing with the tab in the background. If audio
> fails, the game keeps running. Verified with a headless harness that wraps the `AudioContext` and
> logs every node and every ramp. **The harness does not listen**: it checks that what was designed
> plays, when it was designed to, with which parameters. Judging it by ear is still pending.
