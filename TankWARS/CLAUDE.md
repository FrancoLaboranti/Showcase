# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Top-down tank shooter with RPG-style upgrades: **distinct project from [../CrazyTanks/](../CrazyTanks/)**, which is a racing game. ~1870+ lines.

## Tank capabilities

Each `Tank` carries: `health`, `attack`, `defense`, `moveSpeed`, `primaryShotAS`, `secondaryShotAS`, `shieldCapacity`, `shieldCharge`, `shieldChargeSpeed`, `shieldAugment`, `healthRegenCD`/`healthRegenSpeed`. Combat uses primary + secondary shots with separate cooldowns and a shieldable defense layer (`shielded`, `shieldOverheat`).

## Controls

- **Player 1** (`Tank.__init__` default keys): `W`/`S`/`A`/`D` for move, `SPACE` for shield
- **TAB**: shop (manager `tabPressed` flag)
- **P**: pause
- **F**: toggle FPS
- **F1**, **F2**, **F3**: debug toggles (hitboxes / scout markers / etc.)
- **Alt+Return**: fullscreen toggle
- **ESC**: quit / back out

Window is 1280×720, recreatable in fullscreen at runtime. Sprites use a "scout" pattern (`scoutX`/`scoutY`) for AI target previews; tanks also push back against borders via `borderPushX`/`borderPushY` rather than clamping position.

Read with `offset`/`limit` rather than in one shot.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop pattern.


## The HUD health bar has two layers, and they share a scale (2026-09-26)

The green fill is `health / maxHealth`. On top of it, once you go over `maxHealth`, an additive
light-blue band shows the **overheal**, which both lifesteal and the first aid box cap at **2×**.

That band used to be divided by `maxHealth*0.5`, so it represented **half** the health per pixel
that the bar underneath it did: it filled up at 1.5× and then sat there saying nothing between 1500
and 2000 HP. It now spans a whole `maxHealth`, which is exactly how much extra you can carry, so a
pixel of the second layer is worth the same as a pixel of the first. Measured off the rendered
canvas: 25 % of the bar at 1.25×, 50 % at 1.50x, 76 % at 1.75×, full at 2×.

## What the shield stops, and what it does not (2026-09-26)

Audited every line that subtracts from the player's health. There are exactly **five** of them,
and they fall into two groups:

| source | through the shield? | damage |
|---|---|---|
| cannon shot | no, **absorbed** (or bounced, with DEFLECT) | 0 |
| missile | no, it detonates on the bubble and `detonate()` skips the shielded | 0 |
| mine | **yes** | 400 |
| Exploder blast | **yes** | 350 |
| Charger ram | **yes** | 200 |

The three that go through are all **contact**, not fire. The shield used to reduce them instead
of ignoring them, and against the player's flat 1000 HP pool the reduced figures read as nothing:
120 from a mine, 100 from an Exploder, 60 from a Charger, which is 6 % to 12 % with a 0.04 s
flash in the middle of a firefight. You could not feel them, so the shield was quietly the answer
to everything. What each one hits for **did not change**, only whether the shield cuts it. Rage
still zeroes all three, which is what rage is for.

A mine is **400 for everyone**, player and enemies alike, because it is a trap lying on the floor
and it does not care who stepped on it. It used to hit enemies for 500.

The player's health is a flat `MAXHP` of 1000 with **no upgrade that raises it**, which is why
these are readable as percentages and why the old reduced values were not.

## Telling the player the shield did something (2026-09-26)

The shield ring is always on while it is up, so by itself it says nothing about the *moment* it
stops something. A blocked missile was the worst case: `detonate()` skips shielded tanks, so the
whole event was a boom off to one side and no damage number, which reads as the missile having
missed rather than as your shield having eaten it. A green-boss missile went by unnoticed.

`Tank.flashShield(ang, big)` records where the hit came from and for how long to burn, and
`shieldRing` draws it: an arc on **that side** of the bubble that narrows and dims as it fades,
a glow at the contact point, and, for a missile, a hoop rippling outwards, a spark burst and a
shake. Cannon shots get the same thing much smaller, which reads as the bubble crackling under
fire. It is all diegetic: the bubble reacts, and there is no text over it. A `BLOCKED` popup was
tried and taken out.

The sound is `sfx.absorbBig`: the same ELECTRICITY family as `absorb`, because it is the shield
talking and the shield is not allowed to sound like metal, but with body. It is deliberately
**consonant** (1470 falling to 980, plus 980 falling to 735), because the game's one dissonance
is the shield BREAKING (1400 + 1483, a semitone) and those two must never be confused.

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
