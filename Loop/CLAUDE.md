# LOOP

**A roguelite arcade arena** born of crossing the rest of the repo's mechanics into a single
new game (it is not a hub or a compilation). **Web-only** like DonkeyKong/Pacman/StickFight:
there is no `.py`, everything lives in [LoopWeb/index.html](LoopWeb/index.html) (~4090 lines).
Registered in the Arcade as `landscape`, accent `#7df9ff`. **The UI is entirely in English**
(the game is called LOOP); the code's comments are in English too.

You are a **marble** that drags a **thread of light** across the **face of a clock**. The thread
deflects orbs like a Pong paddle; crossing it with itself **closes a loop** and detonates
everything caught inside. The enemies are chess pieces that telegraph their lane,
the clock's hand marks the waves, and each hour you choose **one single thing, alternating**:
a **rule** for the arena or a **card** (the 5 equipped ones make up a poker hand).

## The arrow's sweep now builds the TIP as well (2026-09-22)

Franco: *"the arrow's tip appears complete from the start"*. It was true, and it was there
on purpose — the code's comment defended it with an argument that was also true:

> in a long lane the head measures 8% of the length, so tying it to the body's advance would
> leave it almost unlit during 92% of the warning, precisely when the only thing that matters is WHERE TO.

The two are not resolved by choosing one. They are resolved by **separating shape from fill**:

- **The SHAPE is complete from frame 0**, like a ghost at alpha 0.055 — body and tip. The
  direction always reads, which was the point of the old design.
- **The FILL is ONE single clip that advances** over the complete silhouette. There are not two fills or
  two alphas: the same cut reveals the body and then the tip, in one go. A single animation.
- **The front's EDGE is the same silhouette** clipped to a narrow strip, not a rectangle: that way
  inside the head it narrows by itself to the vertex. Before it was a bar of fixed height that did not
  know what shape the arrow had.

Measured with captures at a frozen `u` (`dbgFreeze` + two `loop(t)` calls with the SAME `t`, which gives dt = 0 and
draws without advancing): at 0.12 and 0.70 the tip is outline only; at 0.97 it is built in full. At
`u = 1` the arrow is no longer there, because the piece is executing the move — that is the game, not a bug.

### The finish

A body 16% thicker (`r*1.12` -> `r*1.30`) and a proportionally longer head.

**The corners are rounded by stretching the outline**, not with curves: the SAME path is filled AND
stroked with round `lineJoin`/`lineCap` and a stroke of `pad*2`. That rounds every
vertex at once — the tip and the two shoulders where the body widens, which is the join that
looked hard.

**That is why the silhouette is built as far as `L - pad` and not as far as `L`.** The round stroke sticks out by
`pad`, so the OUTER EDGE still lands exactly on the destination. Without that correction the arrow
would point a little beyond the square the piece is going to — an error of a couple of pixels which
in a game where the telegraph IS the mechanic comes expensive.

The movement logic and the telegraph rules were not touched: `u`, `e.dur`, `e.tx/ty` and the knight's
lane were left as they were. The 8 scenarios of `qa.py` pass unchanged.

## AUDIO: the voice ceiling had a priority inversion (2026-09-21)

**You died in silence.** It is not a figure of speech: it is traced frame by frame.

`ac()` cut off at `sndThisFrame < CFG.perf.sndPerFrame` (5) and the budget was taken by whoever
got there first. In a loop-closure frame the order of execution is

    hurtEnemy (hit, 1 nodo) -> killEnemy (kill, 2) -> detonateMine (pulse, 2) = 5

and from there on they fall off, **in this order**: `claim`, `tateti`, `frenzy`, `hand` and `tight`. That is,
the whole loop closure, which is the game's central act. Without mines it happens too:
hit(1) + kill(2) + claim(2) = 5 and `tateti`, `frenzy` and `tight` are lost. And `closeLoop`'s comment
says verbatim *"That the loop was tight is already said by the golden ghost and by THE SOUND"* —
in that frame the sound was not there.

Worse: `killPlayer` calls `sfx.lose()` AFTER `sfx.hurt()` (2 nodes). With three previous routine
voices in the same frame — `wall` + `deflect` + `clack`, perfectly reachable with 14 live orbs
— the budget reaches 5 and **the player's death does not sound**. And `endRun` also calls
`droneOff()`, so the room goes quiet too: absolute silence at precisely the one moment
that cannot go unnoticed.

### The fix is not raising the ceiling

Raising it would be giving back the problem the ceiling solves. The ceiling exists to defend against the
**routine** voices — the bounce off the hoop, the clack, the ticking, the whistle —, which fire
many times in the same frame and are the only ones that can machine-gun. The **narrative** voices
(you died, you won, you closed the loop, the frenzy came in) happen at most once per frame by
construction and are exactly what has to be heard.

So there are **two budgets**, not one:

```js
function ac(prio) {
  if (!(AC && AC.state === 'running')) return false;
  return prio ? sndPrioThisFrame < CFG.perf.sndPrioPerFrame : sndThisFrame < CFG.perf.sndPerFrame;
}
```

`voice(name, cdMs, fn, prio)` raises a flag while the body runs (`enPrio`, restored in
a `finally` so it is not left stuck if the body throws), and `note()`/`noiseHit()` call `bump()`,
which charges the shot to the appropriate lane. Neither `note()` nor `noiseHit()` knows anything about this.

**`prio` does not mean "louder" or "sooner".** It means it does not share a budget with the background
noise. The reserve has a ceiling of its own (`sndPrioPerFrame: 4`), so it is not a hole: it was
verified that with `sndPrioThisFrame = 99` a narrative voice does not sound either.

**`CFG.perf.sndPerFrame` is exposed in the tuning panel (the T key) and now means something
else**: the ceiling for the routine ones, not for everything. It is documented in `CFG.perf`'s comment.

These are narrative: `loop`, `tight`, `claim`, `tateti`, `hand`, `hurt`, `chime`, `hour`, `promote`,
`boss`, `bossWind`, `frenzy`, `win`, `lose`, `mine`, `barrel`, `simon`, `simonGo` and the queen's
death. Everything else still competes for the usual ceiling.

### Five sounds that were wrongly associated

The pattern is the same in all five: one voice shared between two events the game ALREADY tells apart
visually.

| event | used | problem |
|---|---|---|
| a detonated mine | `pulse` | **the pulse is what detonates it**, in the same frame: the 200 ms cooldown ate the mine EVERY time. The code took the trouble to make the flash "say MINE" and the ear never found out |
| a barrel being born | `wall` | the warning of a hazard doing 21 damage sounded the same as the orb's bounce off the hoop, **the game's most frequent background noise**, and it shared its 40 ms cooldown |
| the knight's jump | `shot` | `shot` is the tank's shell and the boss's fan, that is, the signal for *dodge this*. The knight does not fire: it JUMPS |
| the boss warning (`wind`) | `ui` | the climax's second of reading sounded like the 30 ms click of the menu buttons |
| an enemy's death | a single `kill` | the game tells pawn/rook/queen apart with different sparks, ring and shake — and all three sounded the same |

`kill(val)` now has three steps that come from `e.T.score`, which is the data the game already
had one line earlier and was not using. Lower, longer and with more body the more the piece is worth:
**432 / 340 / 234 Hz** measured, with volumes 0.06 / 0.075 / 0.095. The cooldown is **per step**
(`'kill' + k`): with a single name, a pawn killed 20 ms earlier swallowed the queen.

### The rest

- **A backgrounded tab did not switch off the bed.** It is the game's only continuous node: two
  oscillators started once and never stopped. With the tab hidden the rAF stops,
  `updateAmbience` stops running and the 55 Hz hum keeps sounding indefinitely — on
  desktop the browser does not suspend the audio of a background tab, so it did not fix
  itself. Now `visibilitychange` calls `droneOff()` + `AC.suspend()`, and on the way back `audioResume()`
  (on mobile the context auto-suspends and the game was left mute until the first touch).
- **`simonFlash` and `updateSimon` called `note()` directly**, skipping `voice()` and therefore the
  context's state guard — precisely the lesson of the guards section further down. They also
  spent frame budget without being able to be held back by it. Now they are `sfx.simon(f)` and
  `sfx.simonGo()`.
- **`noiseHit` did not clamp the volume** before the exponential ramp and `note()` did, half a
  file away. Today no caller can pass 0 (the lowest is `wall` at 0.005), so
  it was a latent mine and not a symptom — but the next `noiseHit` scaled by intensity would step on
  it, and it fails silently.
- **`sndThisFrame = 0` was AFTER `loop()`'s early returns.** With the canvas context
  lost the frame leaves through the return, but the DOM handlers keep firing sounds
  (`onCanvasTap` touches `ui`/`hour`/`card`) and the counter pinned above the ceiling. It
  healed itself when the context was restored, which is why it was minor — but resetting right at the top
  costs nothing and the `contextlost`/`contextrestored` pair already exists, so the state is real.

### How it was verified

With a headless harness that wraps the `AudioContext` and notes every node, every ramp and every
start/stop, running a scenario that provokes the events one at a time. The decisive test forces
`sndThisFrame = 99` and checks that **the routine ones fall off (0 voices) and `lose()` sounds just the same**
(2 oscillators at 330 and 247 Hz, which are its two notes). It lives outside the repo, in the scratchpad, alongside
a `qa.py`/`qa2.py`.

**None of the suite's 68 scenarios measures audio** — they measure behaviour and resources. These
changes do not touch them: not one mechanic was moved, nor one balance number, nor one victory
condition. The only thing that changed semantically is that `sndPerFrame` now counts only the routine ones.

**This was not listened to.** The harness verifies that what was designed sounds, when it was designed and with the
parameters that were designed; it has no sound card. The listening evaluation is Franco's.

## BARRELS: what DonkeyKong contributed as a mechanic (2026-09-18)

DonkeyKong had been contributing only structure — the draft, the seeds, the combo window — and not one
mechanic. The `barrels` rule (×1.55) is the first that really comes in: barrels that arrive from
outside the clock, cross in a straight line and **hit everything**, the player and the pieces.

That last part is what makes them Donkey Kong's and not just another projectile: **a barrel is neither the enemy's
nor yours, it is the stage's.** Standing on the right side of one that is coming turns a hazard into
a tool, which is exactly the game DK proposes.

- **They do not aim at the centre** (`a + PI + rnd(-0.55, 0.55)`). If they all passed through the axis the pattern
  would always be the same and they would be dodged from memory within two hours.
- The damage TO THE PLAYER is fixed (21, the queen's, through `scaleDmg` like any piece). The damage TO
  THE PIECES goes through **`scaleHp()`**: fixed, past hour 8 the barrel would stop killing anything and
  half a rule would switch itself off. The fifth time the same mistake has turned up in this project (the loop,
  the pulse, the orb, the frenzy's healing, the barrel), so it stands as a house rule: **what has
  to keep mattering when enemy health grows, scales with it.**
- A short cooldown on hitting: without it a barrel wipes out a row in one frame; with it, it PLOUGHS it.
- **The boss, excepted.**
- Rotating the baked sprite here is the RIGHT thing, unlike on the bike or the hand: a barrel that
  rolls has to turn its own shine, because it really is turning.

### A test that measured a frozen world

The scenario's first version put the test that KILLS the player second. The player
died, `stepSim` stopped running with the state at `'over'`, and the two following tests measured
a stopped simulation — reporting "the barrel does not hit the pieces" when in fact nothing
was happening at all. **In a scenario with several tests, the one that can end the game goes
last**; otherwise everything that comes after measures a world that is no longer simulating.

## UI 2026-09-18 — fixed slots, reserved space and asymmetric feedback

### The HUD cannot reposition itself

The hand's strip lived at `pad + S * (run.combo >= 2 ? 0.178 : 0.118)`: every time the combo broke,
**it jumped upwards**. Now there are three slots with a fixed Y (`Y_SCORE`, `Y_MULT`,
`Y_HAND`) and the multiplier's gap exists whether it is visible or not. Measured: 112.3 px in both
states, and it comes back exactly.

The rule: **if a HUD element appears and disappears, what is below it cannot depend on it.** A
ternary in a Y coordinate is the easiest way to write a reflow without noticing.

### Space is reserved from the OUTSIDE in

The list of hands beside the hand ended up flush with the margin twice in a row, because it was
calculated the wrong way round: the cards took their size and the list made do with whatever was left. With
the hand centred, the left-hand gap measures `(W - total) / 2` — that is, the card size fixes it,
and the list has no say.

The right calculation goes from the outside in: `margin + list + separation` is what the hand can NOT
occupy **on each side** (on each side, because it goes centred), and the card width comes from what
is left. That way the list always has its air and the hand never moves.

### The card's frame crossed the numbers

The corner rank was at `bh*0.078` with a body of `0.185·bw`: its top edge landed at
`0.022·bw` from the card's edge, and the inner rule was at `0.058·bw`. They crossed by
construction. Solved by layout and without enlarging the card: the frame went out to `0.046` and the content
came in to `bh*0.125` (which is exactly `(0.046 + clearance + 0.5·cs) / bh`), plus the maximum widths
of the name and the effect, which were reaching the second rule.

### In a frenzy, EVERYTHING of yours eats them

Direct contact did `hurtEnemy(e, 999)` but the orb and the pulse carried on with their normal damage:
two different rules for the same state. Now all three kill in one touch during a frenzy —
**the boss explicitly excepted**, because the frenzy cannot skip the fight. Measured: an orb
120/141 → dead, a pulse 138/141 → dead, the boss 2600 → 1776.

### The TIGHT number goes; the multiplier stays

Before taking it out I had to look at what it did: `tight` **multiplies the loop's damage** up to ×3.3,
it is not decorative. What it was not contributing was the NUMBER — an "x2.4" next to a "148" adds an
unknown instead of information, and the damage is already in view. That the loop was tight is said by the
golden ghost and by the sound. The test verifies it by inspecting `closeLoop`'s source: the
multiplier has to be there, the card must not.

(The test's first attempt: close loops with the bot and look at the cards. It came out green with **zero
loops closed** — a test that almost never fires the branch it claims to watch proves nothing.)

### Asymmetric feedback on purpose

`healPlayer(n, callado)`. The frenzy's drip is thirty-odd ticks of 1 HP, and thirty-odd
green "+1"s jumping over the marble cover exactly what you need to be looking at. Damage
TAKEN still puts out its number: **a hit has to be registered, healing reads by itself on
the bar.**

### The joystick is the face in miniature

Smaller (0.155 → 0.125 of the short side) with the dead zone lowered from 0.10 to 0.075 so as not to lose
fine control — the radius IS the stick's resolution, so shrinking it is paid for and has to be
compensated. Visually: dark felt, a brass hoop, an edge of light on top, and the knob is **the
marble** with the same gradient and the same specular highlight. What you drag looks like what
you are dragging.

Two details that matter:
- It moves with **`transform`**, not with `left`/`top`: left/top forces a layout recalculation on every
  movement of the finger.
- The knob travels as far as `BASE_R - KNOB_R`, that is, it stays **always inside the hoop**, while the
  input is still measured over the full `BASE_R`. It is a linear remap of what you see: not a single
  step of precision is lost and it stops looking as if the knob were escaping.

## ALLOCATIONS pass (2026-09-17, evening)

Up to here I had always measured canvas operations. Never **allocations** — and on a phone the
collector is paid for in stutters, that is, constant garbage is exactly what produces the dips
downwards. Six sources, and **three of them I had introduced myself while optimising**:

| where | what it did | now |
|---|---|---|
| `autoDpr` | `Array.from(40).sort()` **on every frame** | a reused typed array, it evaluates every `dprEvery` |
| sprite caches | it built the key by concatenating strings per piece/orb/shell **per frame** | the sprite is remembered on the entity and a NUMBER is compared |
| sparks | one `rgba(...)` string per spark per frame (~50) | `globalAlpha` + a colour cached by value |
| drafts | `hand.concat()` + `evalHand` (with `map`+`sort`) per card **per frame** | it is computed on OPENING |
| low-health vignette | a new gradient + two strings per frame | a cached gradient + `globalAlpha` |
| the boss's closing check | `enemies.some(e => …)` = one closure per frame | a flat loop |

**The most expensive lesson of method in the session: a profiler that does not measure something does not say it is
cheap — it says it does not measure it.** It happened twice in a row: first with path construction (the
thread was 34% of the render and did not show up), now with the allocations. And both times half
of what I found I had introduced myself in the previous "optimising" pass. Every optimisation
has to be measured with the yardstick that matches what it touches.

### Cache by VALUE, not by identity

The colour-string cache started as a `WeakMap` over the colour array. It was no use: almost
every call to `spawnSparks` passes a new literal (`[120,170,230]`), so the reference
never repeats. The key is the colour packed into an integer — looking something up with a number allocates
nothing, which is the whole point of the exercise.

### What was NOT found

Nothing significant in physics, animations or "off-screen elements": the game has ONE
arena and everything that exists is in view, so there is no culling to do. Post-processing is
only the two vignettes. Worth recording so as not to go looking there again.

## The frenzy's healing goes 1 HP at a time

The same total (`healFrac` = 1/3 of the bar) and the same time; what changes is the GRAIN. Measured: with 100
maximum health it is 33 ticks of exactly 1 HP spread over 6.30 s of the 6.5; with 220, **74 ticks**
— more ticks, not fatter ticks, which is what makes the fraction the right unit.
The `while` that hands them out has a cap of 4 per frame so a long frame does not fire a burst.

## The same layout does not work for both orientations

The deck panel's table of hands goes on the LEFT in landscape (where there is width to spare): it does not
eat height and the cards grow. In PORTRAIT it goes underneath, because there what is scarce is width and a
side column stole more from them than it freed up — measured, it left the cards **19%
smaller** than before. It is the same pattern that had already turned up with `panelRects`: when a measurement
comes from `min(fraction_of_W, fraction_of_S)`, in each orientation a different one is in charge.

## Mobile resolution: a fixed base, adaptive only as a net

`CFG.perf.dprMobile = 1.4` is what a touch device STARTS with and what it keeps: a stable
resolution feels better than one that moves by itself halfway through a game. `dprCeil` is also the
tuner's CEILING, so the adaptive part can only go down, never up above the base.
Verified for devicePixelRatio 1 / 1.5 / 2 / 2.625 / 3 / 4: all those of 1.5 or more come out
exactly at 1.40, and the 1x one stays at 1.00 because you cannot render above the
native resolution (`dprMin` bounds how far the tuner can go DOWN, not the native resolution — my first
check confused the two and flagged a false positive).

## Playtest 2026-09-17 (afternoon)

### The joystick was eating the hand's strip — and only in LANDSCAPE

`elementFromPoint` over the strip's centre returned `jMove`. The zone measures 52% × 84%, and with
a small `H` —which is what happens in landscape, which is **how Loop is registered in the Arcade**— that
84% climbs up to the HUD. In portrait it does not happen. The rule: when a touch zone is defined as a
PERCENTAGE of the screen, it has to be tested in both orientations; the same number covers different
things depending on which is the short side.

The solution is not shrinking the zone (it makes the control worse, which is what we wanted to fix): the
joystick **asks** whether the point belongs to something touchable in the HUD (`hudTap`) and yields the touch to it.
It lives in `p04_input` and not inside the joystick, so any future zone consults the same thing.

**Careful when verifying it**: the fix acts at EVENT level, so `elementFromPoint` **still**
returns `jMove` and proves nothing. You have to dispatch a real `pointerdown` and look at the
behaviour. And `moveStick.active` is no use as a signal either — the joystick only turns it on when leaving
the dead zone. The honest signal is to send a `pointermove` and see whether the stick responded.

### The Simon no longer punishes

Franco: *"let the penalty come organically from losing the extra benefit"*. It all went:
there is no red sector, there is no losing by standing still, there is no expiry. The sequence waits
until you complete it or until the hour change takes the rule away. The **hint** for the
sector to hit is back (at the top nothing is shown, as before).

The principle: **an explicit punishment on top of losing the prize is charging twice for the same
decision.** If the mini-game is optional, not completing it is already the consequence.

### The deck panel LISTS the hands

It showed only the current hand, at a size illegible on mobile. But the player's question is not
"what have I got" —they can see that in the cards— but **"what is worth building"**. Now it lists all eight with
their effect and marks the current one: it stops being a status card and becomes a motive.

### The frenzy heals

*"The pressure of not taking damage is a lot."* The frenzy is already the noughts-and-crosses reward and already
makes you untouchable: adding healing to it makes it THE window to recover without inventing a new
system, and it gives you a second reason to go and close the line.

`CFG.frenzy.healFrac` goes as a **fraction of the bar**, not as HP/s. With a fixed number, the more
maximum health (VIGOUR cards) the more insignificant the healing would become — the same mistake the
loop, the pulse and the orb already made: fixed damage against health that scales. It is collected in batches of
~1/9 of a bar because `healPlayer` puts out a floating number per call and at 60 fps that would be sixty
little numbers a second.

### Adaptive resolution instead of lowering the quality by hand

`autoDpr` measures the frame's MEDIAN (not the average: a single long frame cannot move the
decision) and adjusts `dprScale`. Hysteresis of 17.5 ms / 13.5 ms so it does not pump, and a cooldown of
2.5 s because each change calls `resize()` and that re-bakes everything — **if the cure produces the
symptom, it is not a cure**. On a machine that reaches 60 it never drops.

An arithmetic trap I nearly missed: the floor `dprMin / base` can end up **above 1** on
a machine with `devicePixelRatio` 1, and then "lowering" would end up RAISING the scale. It goes bounded
with `Math.min(1, ...)`.

### An invariant cannot depend on the ORDER

`ORB-SPD: v=3.08 against a cap of 1.75` came back after being declared fixed. The first attempt
put the clamp after the orb-orb pairs, but the problem was never that particular place: there are
**five** things that push orbs (pairs, pendulums, flares, the frenzy's pull, the
chimes) and several run AFTER `updateOrbs` — `frenzyBurst` pushes them with +1.4.

`clampOrbSpeeds()` is now `stepSim`'s last word, when everybody has already pushed.

**An invariant that depends on what order things run in, or on how many times per frame they run,
is not an invariant.** It is applied once, at the end.

### And deleting by range takes neighbours with it

Taking out the hour card by deleting from `function drawIntro` to `function onCanvasTap` took
`drawEndScreen` with it, which lived in the middle. The regression caught it (`drawEndScreen is not
defined`), not me. When a block is deleted by range, you have to look at what is inside the range.

## The cost that did not depend on anything (2026-09-17)

Franco, after the previous pass: *"it's still a bit slow and that's with not much on screen at the
start"*. **That sentence is the diagnosis**: if it costs the same with the arena empty, what is expensive
is not per object — it is FIXED PER FRAME, and everything optimised before scaled with the number of
objects. When someone reports slowness, the first useful question is *with what does it scale?*

### The profiler had a hole

It counted `fill`, `stroke`, `clip`, gradients and `drawImage` — but **not path construction**.
`moveTo`/`lineTo`/`quadraticCurveTo` are per-vertex CPU work and they did not show up
anywhere. On adding them:

    34.2%  drawThread   412 path commands per frame

The thread has up to 195 points and is walked three times (a glow pass with quadratics
plus the filled ribbon, which goes out and back). **It was always there**, with or without enemies. That
is: the render's biggest cost had never appeared in the profile, and it was precisely the one that explained
the symptom. A profiler that does not measure something does not say it is cheap — it says it does not measure it.

### The two corrections

**1. Adaptive decimation of the drawing.** The points are `CFG.thread.spacing` apart (0.010 u), which on
screen is `spacing * PXR`: ~4.8 px on a monitor and ~2.3 px on a phone. Sending a vertex
every 2 px is throwing away resolution no eye sees. The step is computed so the vertices end up
~5.5 px apart, so it gives 1 on desktop (nothing changes) and 2 on small screens — the trim falls exactly
where it is needed. **The simulation still runs with all the points**: this is only how many vertices are
sent to be drawn. 412 → 214 commands, and on a tight curve no faceting is visible.

A detail that matters: the tangent is taken against the **drawn** neighbours (`i ± step`), not against
the originals. Otherwise the normal does not correspond to the polygon that is really traced and the ribbon
opens up on the curves.

**2. The simulation was running TWICE per frame.** `steps = min(3, max(1, ceil(simDt / (1/70))))`:
with `1/70`, a 60 fps frame gives `ceil(1.167) = 2` **always**. That is, the whole rope — a measured
713 constraint resolutions + 237 integrations per frame with the arena empty — was resolved twice
in the normal case. With `1/50` the 60 fps frame fits in one substep and the second only appears
below 50 fps. The work per SECOND on a slow machine does not change; what goes away is
the double cost when everything is fine.

Verified before calling it good, because the substeps exist for a reason: **tunneling 0/50** with
a still thread (5 speeds × 2 timesteps) and **0/56** with a moving thread, 14/14 bouncing.

### Lowering the cost uncovered a bug the cost was covering

On going to one substep, `frenzy50` flagged **ORB-SPD: v=3.08 with the cap at 1.75**. The change did not
break it: it *revealed* it. The speed clamp lives INSIDE `updateOrbs`'s per-orb loop, and
`resolveOrbPair` runs **after** that loop — so the impulse from a chained collision
went uncapped until the next frame. With two substeps, the second clamped it within the same
frame and the hole was never visible.

That is: **the cap was covered by the cost, not closed.** A cap that depends on how many times
per frame the physics runs is not a cap. It is fixed by applying it after resolving the
pairs as well, not by going back to two substeps.

The third time in this project the same shape has turned up: something defensive (a `|| 1`, an extra
substep, a `chk` that shares the error with the code it audits) **hides** the problem instead of
exposing it. When an optimisation breaks a test, it is worth asking whether it broke it or
uncovered it.

### And along the way

- Five `new Array(n)` per frame in `drawThread` (~1000 numbers) became `Float32Array`s that live
  between frames. At 60 fps that was constant garbage for the collector, and on a phone the collector
  is paid for in stutters.
- The mine cells' edges went from stroked polylines to `fillRect`: a one-pixel line and a
  one-pixel rectangle look the same, but `fillRect` builds no path (it was ~125
  commands per frame, now zero).

## MOBILE pass (2026-09-16) — measure before touching

Franco reported low FPS on a phone. The first thing was a **profiler**, not a hunch:
`s_prof.py` wraps each render function and attributes the expensive canvas operations by counting
the counters before and after each call. (TIMES are no use in headless — the
virtual time freezes `performance.now()` — but COUNTS are objective: 24 clips per frame are
24 clips anywhere.)

The profile said something no intuition would have said: **`drawEnemy` was 43.6% of the render**, and
a good part of that was the bevel's `clip()` the art pass had put in. An unexpected second place:
almost all of `drawEnemy`'s `fill`s **were not the piece but its shadow**.

The result, the same scene (14 pieces, 8 orbs, a 109-point thread, 14 mines):

| | before | after |
|---|---|---|
| total weight | 459 | **172** (−62 %) |
| `clip` | 16,9 | **4,0** |
| `fill` | 154,8 | **57,0** |
| `stroke` | 147,8 | **66,7** |
| gradients | 30.0 | **8.2** |

### The principle: what looks the same in every frame is drawn ONCE

None of the corrections lowers the quality — they are the same image with fewer operations.
`bakeSprite(key, half, dibujar)` (in `p03_engine`) is the only place where anything is baked.

- **Pieces**: a piece always looks the same and has only four colour states (its own, a white
  flash, frenzy blue, frenzy flickering). Baked, one `drawImage` replaces four fills, three
  strokes, a gradient and a clip. **The contact shadow goes INSIDE the sprite** (it was constant
  for everything that does not jump). The knight is excepted: its shadow depends on the jump.
- **The tank's hull**: it does not rotate, only the turret. Baked, the render's last clips go.
- **Orbs and shell heads**: the same criterion.
- **What is NOT baked**: what rotates (the bike, the hand) or what looks (the ghost's eyes). A
  rotated sprite turns its own shine, and that breaks the fixed key-light rule.

**`resize()` has to empty the caches** (`clearBakes`): everything baked depends on PXR, and otherwise
they grow without a ceiling and on top of that are left at the old scale.

**A cached gradient stores COORDINATES.** The hand's live in local space, so they only
depend on the counter-rotated light's angle: quantising it into 32 steps (an 11° step, invisible on
something that goes round once an hour) takes them out of the frame. They are emptied in the same `clearBakes`, and they are
declared **in the same file** as their cleanup: `typeof` does NOT protect against a `const`'s TDZ.

### Two more that hold for any canvas

- **Hoisting `clip`.** `drawSectors` clipped against the SAME circle once per sector (nine
  per frame), and the pieces' telegraph once per aiming piece (~16 per frame). Both
  went to a single clip outside the loop. A welcome side effect in the telegraph: the pieces
  always end up above the lanes.
- **Batching by alpha.** The fully lit mine cells share an alpha, so their edges
  accumulate in one path. **CAREFUL WITH THE ORDER**: the first version stroked the edges in a batch BEFORE
  the fills and the fill itself ate them. There are three passes: fills, edges in a batch, and
  the ones fading out one by one.
- **A 1-3 px `arc` → `fillRect`.** Additive and in motion they are the same pixel, but `arc` has
  to be tessellated. The big sparks stay round.

### The touch step

`CFG.perf.sparkMul` (0.62 on touch) is the ONLY place where anything is lowered. It touches neither resolution nor
removes effects: it lowers the number of particles in an additive effect, where twenty and thirty look
almost the same and the difference is paid for in pixel fill — exactly what is scarce on a phone.

## PORTRAIT layout: two bugs that only appear on a phone

The whole session was reviewed at 1280×720 and 1920×1080. At 500×905 two things appeared that in landscape
are not visible, and the invariant QA detects neither — you have to LOOK:

- **The streak line landed on top of the next plate.** In portrait `panelRects` stacks the
  plates with `gap = H*0.016`, but beneath each one the streak is drawn at `b.y + b.h + S*0.026`.
  The gap between plates **is not decorative**: it has to leave room for what is drawn there.
- **The draft's cards used 63% of the width.** `cw = min(W*0.19, S*0.25)`: on desktop the
  `S*0.25` cap is in charge and it is not noticeable, but on a phone (where `S == W`) the `0.19` was in charge and the
  cards came out small, with the effect text illegible and 37% of the width unused. Raising the
  factor to `0.26` only changes narrow screens.

**The lesson of method**: a `min(fraction_of_W, fraction_of_S)` behaves differently depending on which of
the two is in charge, and in landscape one is and in portrait the other. Every time that pattern turns up you have
to ask which one wins in each orientation.

### Traps when verifying mobile in headless

- **Chrome headless has a minimum width of 500 px.** Asking for `--window-size=390,...` gives a 390 px
  capture but the page reports `innerWidth = 500`: the layout is computed for 500 and the capture
  shows 390, so everything appears shifted and cut off. It looks like a centring bug and it is not. Use
  500 or more (500×1000 is a real phone's proportion).
- **Removing `body.noTouch` does not make the browser touch.** `IS_TOUCH` is a JS constant and it stays
  false, so the canvas's recharge hoops are drawn (which on touch are behind
  `if (!IS_TOUCH)`) AND the DOM buttons appear as well: you see an overlap that **on a real
  phone does not exist**. It had me chasing a bug that was not there.

## MOVEMENT vs SELECTION — the joystick was eating the taps

`#jMove` is a fixed div of **52% × 84%** with `z-index: 3` over the canvas, and it was only hidden with
`body.inMenu`. During `rule`/`card`/`slot` it stayed alive: **touching the left-hand card created a
joystick and the selection never reached the canvas.**

The solution is NOT to shrink the joystick (it makes the control worse, which is what we wanted to fix): it is
switching off the touch zones when the screen is a SELECTION one (`body.picking`, synchronised by
`syncTouchUI()` once per frame and written **only when it changes**). While you are choosing there is nothing
to move, so the finger can only mean one thing.

A detail to remember: if the zone is hidden with the finger down, the browser **does not send
`pointerup`** and the stick gets stuck. That is why `moveStick.soltar()` exists.

The `touchsel` scenario tests it with `document.elementFromPoint` over the centre of each selectable
element. **It has to remove `body.noTouch` first**: in headless `IS_TOUCH` is false, the
zones are hidden anyway, and the test would pass trivially without testing anything.

## The stick commands VELOCITY, not acceleration

```js
const ax = (inP.mx / mag) * accel;   // ax * mag = mx * accel
P.vx += ax * mag * dt;               // and the cap is maxS ALWAYS
```

It scaled the ACCELERATION: with the stick at 30% you still ended up at maximum speed, it just
took longer. On an analogue stick that is **having no fine control**. Now `mag` is the fraction of
velocity and the velocity approaches the target with `CFG.player.respHl`.

Two things at once: 30% is 30%, and starting, stopping and turning all cost the same (before, reversing
direction was 0.88 u/s braked at 4.6 u/s² = **0.34 s dragging in the wrong direction**,
which was exactly the sensation Franco described as "it drags").

Measured by the `feel` scenario:

| | before | after |
|---|---|---|
| getting to 90% | 0.172 s | **0.117 s** |
| braking to 10% | 0.282 s | **0.133 s** |
| reversing at 80% | 0.344 s | **0.150 s** |
| stick at 50% | 100% of the speed | **50%** |

It is still physics: it is an exponential approach, not a teleport of velocity. What has gone is
the residual inertia, not the weight.

## How this 5500-line file is edited

**`LoopWeb/index.html` is the source of truth and the only thing in the repo**, like the rest
of the ports: a self-contained file, with no build step. But editing an HTML of ~5500
lines by hand is unsustainable, so during long sessions it is split into thirteen files
(`p01_head.html`, `p02_core.js`, … `p13_tail.html`) in a temporary directory, patched there and
reassembled with a `cat` in that order.

**Those `parts/` are NOT versioned and do not survive the session.** When this guide mentions them,
it is talking about that working copy, not about something you will find in the repo. To pick it up again:
split `index.html` by the section comments again, or edit the monolith directly.

Two things that flow taught which are worth repeating:

- **Patches are applied with a helper that asserts the anchor exists AND is unique** (`sub()` in
  Python), never with a blind replacement. An ambiguous anchor that hits the wrong occurrence is
  the most expensive error of all because it does not fail: it compiles and does something else.
- **Before applying, run the patch against a COPY of the parts.** That is how it was caught that
  `wantPointer(false)` hanging off the `else if` chain swallowed the death and victory
  screens — the game never got to have that bug.

## Where each thing came from

| Source | What it contributed | Where it lives |
|---|---|---|
| Pong · Balls · MiniBalls | The thread **deflects** orbs; an elastic impulse solver | `threadDeflect`, `resolveOrbPair` |
| Tron · Snake | The trace as a **persistent object** with a length budget | `thread[]`, `pushThreadPoint` |
| Newton's Cradle | The charge **is contagious** along chains of orbs; pendulums with Verlet | `resolveOrbPair`, `updatePendulums` |
| Chess | Enemies that move by piece rules, with a telegraphed lane | `ETYPES`, `pickLane` |
| Noughts and Crosses | 3×3 sectors claimed by enclosing them; three in a row = a frenzy | `claimSectorsIn`, `checkTateti` |
| Poker | The 5 equipped cards are evaluated as a hand | `evalHand`, `recomputeStats` |
| Minesweeper | Hidden mines; the thread **reveals** the cells and their numbers | `seedMines`, `revealCell` |
| Simon Says | A sequence of sectors "played" by **walking through them** | `updateSimon` |
| Pac-Man | A ghost with a Pinky-style target; an edible frenzy | `updateGhost`, `startFrenzy` |
| Tank Wars | A tank with shells **returnable** with the thread; a shield with a wait | `updateTank`, `updateShells` |
| Crazy Tanks | A hand-rolled `createJoystick`; rules as an object of multipliers | `createJoystick`, `RULE` |
| Fireworks | Deaths that burst; the FIREWORKS rule | `killEnemy`, `updateFlares` |
| Clock | **The hand IS the wave timer** and a physical paddle | `updateClock` |
| DonkeyKong | A draft of modifiers; derived seeds; combos with a window; **BARRELS** | `openRuleDraft`, `mulberry32`, `updateBarrels` |
| StickFight | The file's structure, audio with `voice()`, the Arcade's shell | the whole skeleton |

## What from the repo really came in, and what was left out

The table above says where each thing came from, but several entries are there **in name more than
in substance**. This is the honest map, so as not to believe again that something is covered:

| Source | Real state |
|---|---|
| **Hangman** | **Out altogether.** THE GALLOWS was an attempt and it was removed (see its section). The pool was left with nothing from Hangman. |
| **Snake** | It contributed the SHAPE of the trace, not its RULE. In Snake crossing yourself **kills you** and eating **makes you bigger**; here crossing yourself is the REWARD and the length is a budget bought with cards. The two ideas that define Snake are inverted or absent. |
| **Tron** | Half in. LIGHT CYCLES gave the enemy side (a bike whose trail burns), but **your own thread is not a wall**: it grazes for 3.5 with a cooldown, it does not kill. In Tron the point is that YOUR line is lethal. |
| **Fireworks** | Only the burst on dying and the FIREWORKS rule. The cycle that defines it — launch, arc, burst in a pattern — is not there. |
| **Chess** | The promotion yes; the board decision no. The pieces are telegraphed threats, not an opponent making moves. |
| **DonkeyKong** | It was only structure until BARRELS came in (2026-09-18). |
| **StickFight** | The file's skeleton, `voice()`, the Arcade's shell. **Zero mechanics.** |

### Three wired-up mechanics that NOBODY can obtain

`P.thorns` (returning damage when you take it), `P.loopHeal` (healing when you close a loop) and `P.lifesteal`
exist, are reset in `recomputeStats` and **are checked in the game** — but no card and no
rule ever raises them above 0. They are code that runs for something that cannot happen.

It is not urgent to fix, but it is worth knowing for two reasons: they are slots ready if one of the
absences above needs covering, and they are exactly the kind of thing a future reader
will assume works. (The same family as the `thread[j].w || 1` that made the brush dead
code, or as `chargeCd` missing in the mirror.)

## Architecture (the non-obvious parts)

- **World space, not pixels.** The arena is a circle of **radius 1** centred on (0,0);
  the screen is derived when drawing with `sx()/sy()/sr()`. Unlike the rest of the repo's
  `sper/xper`, **a resize does not touch a single number of the simulation** — which is what
  allows ~200 thread points to be stored without ever rescaling them.
- **The thread is a simulated ROPE, not a painting** (`layThread` + `simThread`, 2026-09-14).
  Franco: *"it would improve ENORMOUSLY with better thread movement"*. A Verlet chain with
  **friction by age** (`CFG.rope`): a fresh point slides and whips behind the
  marble; an old one pins. The array's last element is always the **head, pinned to
  the marble**; the points are seeded at a **fixed step** between the last one laid down and the head (before,
  a lunge left them 10× further apart). The length budget = points × step.
- **Each point has an ANCHOR (`ax, ay`) = where it was laid down, and it returns there as it settles.**
  Without the anchor the rope shortens the curves from the inside and the head **never crosses it again: zero
  loops** (measured with the bot). With the anchor it whips for ~0.5 s and then settles EXACTLY on the
  real path, so the loop's geometry is the same as before (the bot's max area identical).
  Careful: **it is seeded from the last laid-down point's anchor, not from its current position**, or the
  anchors would trace the short cut instead of the path.
- **The hits really do kick the rope** (`kickThread`): they displace the segment's points and
  Verlet turns it into velocity; the wave travels by itself and the anchor brings it back. It replaces the
  old synthetic sinusoidal "ripple". `hitT` was left only for the glow.
- **A loop closure** = the intersection of the stretch covered this frame against the old thread
  (`findSelfCross` → `segSegT`), skipping the newest stretch. Without that skip, turning hard
  closes "loops" two pixels across. **The skip is measured in DISTANCE (`CFG.thread.skipDist`),
  not in number of points**: during a lunge the points end up 10× further apart, and counting them
  left blind precisely the straight line the lunge has just drawn — which is the one you want to close with.
- **The central balance rule**: `tight = sqrt(0.17 / area)` ⇒ **a small loop = damage,
  a big loop = points**. Without that the game would be "sweep the pitch with an enormous circle"
  and there would be no skill. If you touch this, you touch the whole game.
- **SWEPT orb↔thread collision** (`threadDeflect`): the stretch covered is tested against the
  segment, not the point position. At 2 u/s an orb advances 4 radii in a slow frame.
- **Two enemy families and nothing else**: sliders (`fam:'s'`, they wait → telegraph a
  lane → charge) and free ones (`fam:'f'`, the tank and the ghost). The boss is `fam:'b'`.
  Adding an enemy = one row in `ETYPES`.
- **The boss's armour**: `hurtEnemy(..., src)` divides the damage by 3 except for `src === 'loop'`.
  The climax forces you to use the game's central verb.
- **ONE rule at a time, not stacked** (`hourRule`). Before they accumulated for the whole run and by
  hour 7 you had pendulums + mines + mirror + resonance + fireworks at once. Franco said it
  verbatim: *"at a certain point I don't understand anything"*. The division that resulted is the game's
  golden rule: **cards = your build (they accumulate) · rules = the weather (it changes)**.
  `nextHour()` clears pendulums/mines/the sequence and runs only the current rule's `onStart`.
- **COURAGE STREAK** (`braveMul`): the price of taking away the stacking was losing the compound
  effect, and without it it was better to always play safe (the cautious bot reached hour 11
  and the daring one died in hour 3). The streak gives back the compound reward **without** giving back the
  chaos: each consecutive hour with a spicy rule raises a permanent multiplier, and CALM breaks it.
  The chaos is per hour (legible), the reward compounds (motivating), and it reads in one number.
- **A roster per hour** (`pickRoster`): not all the unlocked types come out at once, but
  1–3 rolled ones that are the only ones for that hour. With six different behaviours on screen
  nothing reads. The pawn always comes in, as filler.
- **The start-of-hour notice** (`drawIntro`) says the rule + a description. It is the screen that
  teaches; if you take it away, the sense of not understanding what is happening comes back.
- **`RULE` is an object of multipliers recomputed from scratch** (`applyRules`), never
accumulated mutable state.
- **`recomputeStats()` is recomputed in full** from `hand[]`: adding or changing a card cannot
  duplicate an effect. It preserves the **absolute** health and credits every increase of the maximum.
- **Difficulty = health and rate of fire, with a cap on damage** (`scaleHp/scaleCd/scaleDmg`).
  The TankWARS lesson: scaling damage without a cap means that by hour 10 you are killed in one touch.
- **The LUNGE's profile** (`lungeVel`) is SnakeWeb's twin-smoothstep: an exact area of 0.5
  per phase ⇒ the net advance is analytic, and the charge never changes sign ⇒ no recoil.
  It returns **velocity**: it is added in the integration, never `vx +=` (it would accumulate and fly off).
- **Bounded substeps** in the loop (max 3): they stabilise the orb-orb bounce chains.
  Careful: any logic with a per-frame distance threshold has to measure against the **last
  stored point**, not against the previous substep's position.

## What came out of the long playtest (2026-09-14)

Franco played and fired off a batch of changes that redefined several things. The decisions and
**the why**, which is what must not be broken again:

- **One decision per hour, ALTERNATING** (`endHour`): odd hours change the RULE (and it lasts
  two hours), even ones bring a CARD. Before, both screens came together *and* the hand
  filled up so fast that you spent the run discarding. With 11 transitions that gives 6 rules and
  5 cards: **the hand is completed right at the end and you never discard**.
- **Eight upgrades, two per suit** (previously sixteen). Several were so specific that they were
  no fun to choose. With eight you **repeat often**, and since duplicates stack their effect,
  drawing two the same is at once a PAIR and double the effect: only then does the poker happen.
- **Real poker names** (PAIR / TWO PAIR / THREE OF A KIND / STRAIGHT / FLUSH / FULL
  HOUSE / FOUR OF A KIND / STRAIGHT FLUSH).
- **The inventory is visible while choosing**: the hand with its free slots, always, in the draft.
- **Claiming a sector = going round the DIAMOND** at its centre (`claimSectorsIn` + `drawSectorTargets`).
  Before, the coverage was sampled 5×5 against a threshold: invisible, and it felt arbitrary
  ("it seems inconsistent"). Now there is a drawn target and the rule is visible. The diamond pulses in
  gold if closing it completes a line (`wouldCompleteLine`).
- **FRENZY remade**: they no longer flee. A gentle magnet towards the marble (`CFG.frenzy.pull`, deliberately
  SLOWER than a piece's walk: it heels them, it does not move them), you are **invulnerable**, the
  pieces stop threatening, and when it ends a **free shockwave** comes out (`frenzyBurst`).
  The previous version turned the prize into a chase.
- **The diamonds open in a WINDOW, not always** (`game.sectorsOpen`, it opens on each hour's 1st
  chime). Being there always, the noughts and crosses chained without a break. And the **frenzy comes
  once per hour** (`run.frenzyHour`).
- **The 3x3 pays ALL its lines** (`linesDone` + `newLines` + `checkLines`): the board is not
  cleared on closing a triple, so adding sectors keeps closing new combinations —
  a well-placed claim closes two together, and with all 9 the 8 come out. It is only reset when
  all nine are taken.
- **The thread UNDULATES** (`CFG.rope.waveAmp/waveK/waveSpd`): the wave displaces the **anchor**, not the
  drawing, so it goes through the same damped spring and mixes with the hits and the whip.
  It has zero mean around the recorded path ⇒ **the loop's geometry does not change**. Without
  this the settled stretch was absolutely dead and the thread read as a drawn line.
- **RESONANCE does not punish stepping on other sectors.** On a 3×3 grid, to get from one sector to the
  next you almost always cross an intermediate one: with the "wrong sector = reset" rule
  the sequence fell over the moment you moved. The only pressure is the clock. **Do not re-add it.**
- **RESONANCE is a real Simon**: four colours per sector (`SECT_CI`/`SIMON_COL`), one
  note per colour, the rest of the face **dark**, progress dots and an error warning. Before
  you could not tell whether you had got it right.
- **The thread's head AIMS** (`CFG.thread.headPts` / `headAim`): near the tip the exit
  blends towards where you are moving — it is a racket shot, not a bounce. Far away, pure physics.
  The tip is drawn with a halo of its own: if you cannot see it, you do not know which part you are hitting with.
- **The pieces are NOT swept away at the close of the hour.** Seeing them evaporate on choosing a card broke
  the continuity. The prize for lasting is the rope (14% of health) and the bonus.
- **The hour card is a compact plate** at the top, with a ribbon in the rule's colour. It does not say
  which enemies are coming (Franco asked for that: he prefers to find out).
- **`addScore` does nothing in `over`/`win`.** The background stays alive, but seeing the number move
  by itself after dying ruined the reading of the result.
- **Out** went the TRAILS rule (enemy traces) and the Hangman-style word: the first did not
  seem a good mechanic to him, the second had none at all.
- **DAMAGE and POINTS are two different languages** (`drawFloaters`): the damage is a bare number
  with a four-pointed spark beside it (it lives in the world); the points always go with a "+"
  inside a dark plate with a border (it reads as UI). Before they were the same number in a different
  colour and they were constantly confused.
- **Outfit typography** (Google Fonts). The previous one was the system-ui, which on Windows falls back to
  Segoe UI and reads square and generic — above all in the score's numbers.
- **Modes with a name and an explanation**: FREE RUN / DAILY RUN as cards with a subtitle. A bare "FREE"
  and "DAILY" said nothing.

## Second playtest (2026-09-15) — background bugs and tuning

- **QUEEN EXPLOSION (the worst bug the game has had).** The queens summoned pawns and
  the pawns that reached the centre promoted into queens: an exponential chain reaction. Worse,
  `enemyCap()` was only looked at by the clock's spawner, so promotions and summons
  came in through the back door with no cap. Three locks, **do not take them out**:
  `HARD_CAP` applied **inside `spawnEnemy`** (it covers every source), `MAX_QUEENS = 2`, and the
  queen **no longer** summons pawns. Verified: 10 hours with the player standing still → it settles at
  11 enemies and 2 queens. Before, it burst.
- **The CELL is square; what is RECTANGULAR is only where the diamond goes.** (Corrected later the
  same day: first the whole cell was squashed and that changed the clock's "#", which was not what was
  wanted.) The cell is the usual third (`SECT_Q`, `sectRect`, `sectorAt`) — it is what
  the clock draws, what is painted whole and what defines which sector you are in. The TARGET goes on
  a squashed grid (`SECT_DX/SECT_DY`): at the geometric centre of a corner cell the
  diamond landed at radius 0.94, on the edge, and **the board could never be completed**.
- **The board's cycle** (final version): the window opens past `CFG.clock.sectorsAt` of the
  hour (33%), **once only per hour** (`game.sectorsShown`), and collecting a line **clears the
  whole board** and closes the window — the sectors discharge into the frenzy. Uncollected
  sectors do persist between hours. The collected triples live in `linesDone`, which
  `resetSectors()` clears along with the board.
- **The diamonds are drawn AFTER the hand**: the centre one was covered precisely when the
  hand passed through there, which is almost always.
- **Closing accepts a GRAZE** (`CFG.thread.closeTol` ≈ the marble's radius). Measured: the undulation
  cost one closure in three by demanding the exact intersection of the centre line. The
  mental model becomes "TOUCH your thread and it closes". (The `nearClose` visual hint that had been
  planned does NOT exist in the code: it was lost in a failed patch and never redone.)
- **The thread is drawn as a FILLED RIBBON, not as a line with thickness.** With per-segment strokes
  there was always a step between layers; a filled polygon has a continuous silhouette. The colour
  goes in opaque slices that SHARE their edge vertices, so there is no seam. Each point's width
  is the one the hand had when laying it down (`thread[i].w`, see the audit further down).
- **Orb leak: the thread ALSO moves.** The orb's swept test is not enough — when the
  rope sweeps over an almost-still orb there is no intersection against the segment's current
  position. It is also tested against the PREVIOUS position (`p.px/p.py`) and the diagonal
  crossings. And `deflCd` (the BLIND window) went back to being short: at 0.15 s it was 0.26 units of flight
  with no collision. "Not being lit all the time" is solved separately with `o.chargeCd`.
- **The orbs stopped deciding the wave**: they did 26 + speed and kept 60% of the
  charge, so one orb swept whole groups and the next population was a lottery. Now it is
  17 + speed and they keep 28%. The LOOP's damage went up to compensate: your skill decides.
- **RESONANCE does not punish stepping on other sectors** (see below).

## QA audit (2026-09-15) — bugs the playtest was not finding

All of this was live and none of it threw an error. **Do not re-introduce them.**

- **The courage streak was never broken.** `chooseRule` compared `r.id === 'calma'`, but the id
  had become `'calm'` when the UI was translated. Taking CALM raised the streak just like a spicy
  rule — and the draft's own card promises the opposite, because there it does compare correctly.
  The moral: **a data id used in two files is a silent dependency**; if
  you rename one, search for the string across the WHOLE repo.
- **The diamond window reopened the frame after collecting.** `checkLines` does
  `game.sectorsOpen = false`, but `updateClock` reopens it as soon as it sees `u >= sectorsAt`, which
  remains true for the rest of the hour. The closure lasted ONE frame. Now there is
  `game.sectorsShown`: the window opens **once only per hour**.
- **Dying in the same frame the hour ends robbed you of the defeat screen.**
  `stepSim` called `updateClock` BEFORE looking at the state; with a big dt there are up to 3 substeps,
  and if you died in the first, the second crossed the hour and `endHour()` opened the draft ON TOP OF
  the defeat: a zombie game with the player dead. Measured 60/60 cases before, 0/60 after.
  **Both** state checks are needed (before and after `updateClock`).
- **The defeat screen carried on playing by itself.** In `over`/`win` the loop calls `updateOrbs`
  so the background breathes, but that deflected against the thread (`run.deflects++`) and the charged
  orbs killed pieces (`run.kills++`, the combo, drops). The final summary showed numbers
  going up. Now `updateOrbs` checks `game.state === 'play'` before touching anything that is game
  state; the orbs keep bouncing off the walls and off each other.
- **The thread's brush did not exist.** `drawThread` reads `thread[j].w` with a defensive fallback
  `|| 1`… and `newPt` never wrote `w`. The fallback ran ALWAYS: a constant width and
  `CFG.thread.speedW` with no effect. **Careful with defensive `|| value`s: they cover up precisely the
  bug they should be exposing.**
- **The canvas's font was not the one being loaded.** The `<link>` brings Outfit and the CSS applies it to the
  body, but ALL the game's text is drawn on canvas with the `FONT` constant, which was still
  Segoe UI. Now they match, and the face is re-baked with `document.fonts.ready` (otherwise the
  numerals stay in the system font forever).
- **The mirror never charged the orbs.** `mirrorDeflect` builds a ghost orb and forgot
  `chargeCd`; inside, `if (o.chargeCd <= 0)` with `undefined` gives **false**, so the reflection
  deflected but lit nothing. `undefined` in a numeric comparison does not blow up: it lies.
- **`spawnOrb` simulated one orb twice.** `updateOrbs` walks backwards; when a piece
  dies inside that loop it releases an orb, and with the table full `spawnOrb` did a `splice` of a
  neutral one. Removing an element below the current index shifts the array. Now it **replaces in
place**.
- **DAILY mode was not reproducible**, for two independent reasons:
  1. the rope's undulation used `perfT` (wall time since the page loaded), so
     the phase depended on WHEN you started. Now it uses `ropeT`, which accumulates simulation dt and
`startRun` resets it;
  2. the ambient dust called `rnd()` (the **seeded** rng) from a timer that was not
     reset between games ⇒ the whole stream shifted. The decoration now uses
     `Math.random`. **The rule: decoration never touches the seed.**
  Verified: 4000 frames bit for bit identical, with hour changes, drafts, promotions and
  death included, comparing checksums of the whole state.
- **`hitstop` survived from one game to the next** and the new one's first frame was left
  unsimulated. `startRun` clears `hitstop`, `trauma`, `flashA` and `zoomPunch`.
- **The frenzy was left hanging** on leaving for the menu or on winning: `updateFrenzy` only runs in
  `play`, so it never ended and `hurtEnemy`'s ×1.5 stayed active. `endRun` clears it and
  `backToMenu`.
- **The sector burn was not reset on leaving**: `e.sectT` only went up, so a piece that
  stepped on it for half a second and came back later burned instantly. It is a PERSISTENCE counter.
- **With the player STANDING STILL the thread's tail left the arena.** Standing still, the thread stays at 2
  points and `simThread` left early (`if (n < 3) return`), so neither the anchor nor the clip
  against the face ran — but `kickThread` did keep pushing the tail on every bounce. Measured
  in the AFK test: radius 1.14 at hour 2, 1.60 at hour 3, **2.86 at hour 4** (the arena
  has radius 1), with the thread drawn as an enormous straight line leaving the face. **An early
  exit for a "trivial case" is suspicious if something outside can keep writing that
  state.** Now the `n < 3` case applies the anchor and the clipping just the same.
- **The minesweeper was illegible**: the uncovered square was painted at alpha 0.05 (invisible) and the
  numbers ended up UNDER the telegraph lanes and the hand. Franco, verbatim: "what does that
  number mark?". Now the drawing goes in two passes — `drawMineCells()` with the background and
  `drawMineMarks()` **on top of everything alive**, because it is information, not decoration.

## Visual system (art direction, 2026-09-16)

A casino table: dark felt, golden metal, bone playing cards. Before, each screen chose its
colours and sizes by eye and that is why they looked like different games. Now there are **tokens** in
`p03_engine` and everything is written against them:

- **`C`** — the palette. Five families, **one function each**: surfaces (`void/felt/surf/
  surfHi/line/lineHi`), ink (`ink/inkDim/inkFaint`), **gold** = value (the score, the prizes, the
  clock), **ice** = you (the marble, the thread, your tools), **crimson** = what hurts you,
  **violet** = rules and resonance. If a colour does two things, it stops meaning anything.
- **`TS`** — the typographic scale in fractions of `min(W,H)`: `display/title/sub/body/cap`.
  Do not invent loose sizes.
- **`panel(x,y,w,h,r,accent,glow)`** — the ONLY place where how a plate looks is decided:
  a vertical gradient, an accent border, an edge of light on top. The draft, the menu, the hour card,
  the buttons and the stack panel all use it.
- **`txtO()`** — outlined text, for whatever flies over the arena. The offset-shadow `txtG`
  reads as text stuck on top; the outline centres the silhouette.
- The same variables exist in CSS (`:root`) so the DOM shell is not a different game.

**The performance rule that governs everything: "make it look expensive to produce, but cheap
to render".** No `shadowBlur`, no `filter`, no new particles. Depth is built
with vertical gradients, a light edge on top and a dark base — three fills and two lines.

### The damage numbers say WHO, and the size says HOW MUCH

They were three almost identical oranges (`#ff6b81 / #ff9f43 / #ffd23f`) separated by a `kind` the
player could not deduce, at a fixed size. Now:

- what **you do** → bone, shifting to **gold** the harder it hits;
- what **is done to you** → crimson, heavier (`kind: 3`, new);
- what **heals** you → green;
- the **size** comes from `dmgRef()` = what a tight loop does at that point in the game, so
  a 40 is impressive in hour 1 and routine in hour 11 — as it feels while playing;
- only the big hits earn a flash, and it uses `bloomPx`'s cached sprite. If
  everything shone, nothing would shine.

The score is a **chip** (a plate with a golden edge), not a balloon: it is another language, not another colour.

### This pass's performance decisions

- **The hand's strip is BAKED** (`bakeHandStrip`). It is the only part of the redesign that cost anything IN
  GAME: it runs on every HUD frame and each card asked for two `createLinearGradient`s — 10 per
  frame to draw something that only changes when you take a card. Now it is **one `drawImage`**,
  invalidated by `handKey()` (content + hand + size) and by the resize. The same pattern as
  `bakeDial`.
- **The FPS counter no longer runs all the time.** It had a `requestAnimationFrame` of its own alive from
  the moment the page loaded, whether or not the info panel was being looked at. Now it starts when it is opened and stops when
closing it (`startFps`/`stopFps`).
- **The entry animations end.** The rules and cards drafts come in staggered over
  0.24–0.26 s; past that time the factor is worth 1 and nothing is recomputed. The only permanent
  animation is one `Math.sin` per card in the draft (the resting float), and only while the
  draft is open.
- **The cards' shadow is two offset rects**, not `shadowBlur` — which is about the most expensive thing
  there is on mobile canvas.

### The arena (2026-09-16, second pass) — where it really shows

The first pass touched cards, panels, numbers and screens: **everything you look at for seconds**.
The face, the pieces, the orbs and the hand — what you look at ALL the time — were left as they were,
and the result was "I didn't feel much difference". A lesson that holds for any redesign here: **an
art pass is judged by what fills the screen during play, not by the menu screens.**

**One single key light.** `LIGHT` (`p03_engine`) is the light's direction in SCREEN
coordinates, top left. Everything with volume respects it: the marble, the pieces, the orbs, the
hand, the tank's turret. Before, each thing chose its own (or none) and the whole looked like a
collage of stickers. **If an object is drawn ROTATED, the light has to be counter-rotated** (the bike, the hand,
the turret): otherwise the shine turns with the object and reads as something that lights itself.

Two helpers, and there is no third place where this is decided:

- **`groundShadow(x,y,r,a)`** — two stacked ellipses, no gradient (with 24 pieces on screen, one
  `createRadialGradient` per piece per frame is a real cost and it looks the same). It is the pass's cheapest
  detail and the one that changes the most: **without a shadow the pieces float; with a shadow they are resting.**
- **`bevelShape(pathFn, w, liteA, darkA, lx, ly)`** — a light edge on top / a dark one underneath INSIDE
  the silhouette. The trick is to clip against the shape and stroke it again offset: what sticks out
  is clipped, so only the inner half of the stroke is left, which is exactly an edge of light.
  It gives volume without a gradient per object and without a single canvas shadow. `pathFn` is called three
  times, so it has to be able to rebuild the path.

**The face is an object, not a circle.** `bakeDial` is baked once per resize, so **in
there the detail is free and it is worth spending it all**: a brass bevel with a conic gradient (the
double reflection is what makes it read as metal), a chapter ring, the bevel's inner shadow
falling over the felt — that gradient alone is the whole pass's stroke of depth — and
a cloth grain by tile. The grids go **engraved**: a dark line + a light line offset towards
the light. A single line reads as drawn; two read as carved.

Three things that cost one iteration each and are worth not repeating:

- **The bevel started too light and too wide** and ate the scene — it looked like a giant
  gold hoop. A bevel FRAMES; if it shines, it has stopped being a frame.
- **The numerals shared a radius with their own hour marks** and ended up crossed. The
  ring needs TWO bands: marks outside, numbers inside.
- **Such a marked inner drop shrank the playable area.** Depth is suggested, it does not
  trim the board.

**Caching a `CanvasPattern` is a bug waiting to happen.** A pattern is born tied to the context that created it,
and each resize bakes the face into a new canvas. The **tile** is cached and
`createPattern` is called per bake.

### States (hover) and the layout trap

The hover is computed with the pointer's position, and the obvious way to get it
(`getBoundingClientRect` on every `pointermove`) is **exactly** what the brief asked to avoid:
a read that forces a layout recalculation, fired dozens of times a second. The rect is
cached in `resize()` (`cvLeft/cvTop`) and the handler only subtracts two numbers. `hovering(r)` is always
false on touch. The cursor is written **only when it changes** (`wantPointer`), the same pattern
the joystick already used: writing `style.cursor` every frame is one CSSOM write per frame for
leaving it the same.

**`wantPointer(false)` can NOT hang off the render's `else if` chain.** Since
`typeof wantPointer === 'function'` is always true, it swallowed the `'over'` and
`'win'` branches and the death and victory screens stopped being drawn. The patch's dry-run
over a copy of `parts/` caught it, not the game.

## THE CLOCKMAKER needed a BAR, not more numbers

The playtest's four complaints — "getting close is only possible if you have a shield", "it's the same
the whole time", "there are so many enemies I don't understand what's happening", "it's really hard to damage it" — were **the
same failure**: the fight had no cycle. The arms turned non-stop, the core always hurt,
the attack came out on a coin flip every 3 s, and the armour (`src !== 'loop'` → 30%) left a single
way to do damage: precisely the one that demands getting in where you get hit. **Without a moment when the
answer is "NOW", all that is left is to go in, eat the hit and come out to wait for the shield.**

Three beats, in `CFG.boss`:

| state | what happens |
|---|---|
| `idle` | the arms turn, the core hurts; it lasts less in each phase |
| `wind` (1 s) | the arms speed up and a red hoop closes inwards — a telegraph |
| `open` (2.6 s) | the arms **stop and draw in**, the core opens in ice, **it does not hurt on contact** and **takes ×3** |

Measured: 14 transitions in 30 s, the core open 40% of the time, ×3.00 confirmed, and 40 frames
standing on top of the open core = 0 damage.

Two principles that hold for any boss added here:

- **The signal is the absence of movement.** The arms stopping say "now" better than
  any card, and it does not have to be taught.
- **The attacks ALTERNATE, they are not rolled.** A pattern can be learnt; a coin cannot. `rng() < 0.5`
  between two attacks does not generate variety: it generates noise.

The armour became `CFG.boss.armor = 0.55`. The loop is still king — it does not pay it — but at
30% everything else was a tickle and the fight was a health toll. And the summons are now
capped against the pieces **that are already alive** (`CFG.boss.maxAdds`): the boss called 2-5 every 3 s
ON TOP of the hour's normal spawner, and that is why nothing could be understood.

## The hand no longer bats the orbs

It was a spinning paddle that reflected them and passed them its angular energy. On paper it sounded
good; in practice it is a force that crosses the whole face every hour, with no telegraph, sending
balls anywhere just as you are solving something else. The clock already governs through the
rules and the chimes. The boss's arms, which are hands, do not either.

**A trap when taking it out**: `ex`/`ey` (the cosine and sine of `clock.ang`) were declared INSIDE
that block, and the piece spawning still needs them — the pieces are born at the hand's tip.
Deleting the whole block left `ex is not defined` in eleven scenarios. The regression caught it, not me.

### A green test that proved nothing (twice in a row)

Verifying "the orb does not move" gave **two false positives** before it was any use:

1. the **player's magnet** pulls on the orb too;
2. `spawnOrb` **randomises radius and mass**, so two runs compared different orbs — and 30
   frames of simulation also consume RNG and spawn pieces that collide with it.

What worked was calling `updateClock(dt)` **on its own**, with the orb still on top of the hand, and
demanding **exactly zero** velocity. The rule: when you measure that something stopped happening, isolate the function you
touched instead of running the whole game and looking at the result.

## Playtest 2026-09-16 (afternoon)

### The streak is measured against an ABSOLUTE threshold, not against the other two options

The break was relative: the trio's lowest-multiplier option sent the streak to zero.
With {RESONANCE x1.45, HORDE x1.50, THE GALLOWS x1.75} that punished choosing RESONANCE — which has
real risk — only because the other two were worse. Franco, verbatim: *"I don't want it to punish
my points for choosing the simon says"*. Now there is `SAFE_RISK = 0.20` and `breaksStreak(r)`: a rule
with real risk **never** breaks the streak, even if it is the mildest of the three. The plate's colour
comes from the rule's own risk, not from its place in the trio.

The general lesson: **a relative punishment punishes for the context, not for the decision.** The player
chooses a concrete rule and expects the price to depend on that rule — not on what happened to be next to it.

### THE GALLOWS: out

Neither the mini-game nor how it looked went down well, and it did not communicate what happened on completion (it collected 34%
of maximum health and went back to zero — that it had to be asked is the verdict in itself). It was taken out
entirely: the rule, the object, the counter, the relief, the update, the drawing, the CFG and the QA checks. **Switching off a
rule and leaving its code behind is debt**: the next audit pass finds it again.

### What was "choppy" was not the animation, it was the rasterisation

The cards' float covered 4 px in 2 s: ~0.06 px per frame. The card's body moved
smoothly, but **the text is rasterised to a whole pixel**, so it stayed pinned for fifteen frames and
jumped one all at once. Smoothing the curve would never have fixed it. What does fix it is more
travel and, above all, a **minimal tilt** (±0.6°): with the canvas rotated the rasteriser
can no longer align the text to the grid and the movement becomes continuous.

A rule for next time: **if something moves less than ~0.3 px per frame and carries text, it is going to look
jumpy however smooth the curve is.** Either it moves properly, or it does not move.

### Minesweeper: the classic palette, and why it works now

The numbers used a cold ramp **on purpose**, because when they used the damage one a cell "3"
and a hit "34" read the same. The classic puts red in the 3, that is, it goes back into that territory.
It can be done because the two families are already told apart by something that **is not the colour**: the cell
number is still, anchored at the centre of a lit square and with a dark outline (`txtO`); the
damage one floats, rises, fades and never carries an outline. With that settled, the Minesweeper palette
is knowledge the player already brings with them. The original 7 and 8 (black and grey) go up to bone
and light grey: over dark felt they would not exist.

The uncovered square is drawn **sunken** (a light edge on the light's side, a dark one on the opposite), and
the mine is a metallic sphere with the same key light as everything else, with the red reserved for the hoop
that pulses — one single red element says "danger" better than a red body with red hoops.

### Riders: the target heading and the real heading

`e.dir` is the TARGET heading (always at a right angle) and `e.ang` the REAL one, which reaches it by turning at
`CFG.cycle.turnRate`. Before they were the same thing and the bike changed direction between two frames: it read
as a teleport of heading. Separating them makes it curve like the ghost without losing the circuit —
the straight stretches are still straight and the turns are still 90°, only with a radius.

With the smooth turn **"turn on reaching 0.88" is no longer enough**: while it turns it keeps advancing, so
a hard cap against the hoop (0.93) is needed which also forces its heading inwards.

`life` x `spd` is the LENGTH of the trail in units of the face (which measures 2 from end to end). It was
at 4.0 x 0.80 = 3.2 units: more than a whole lap, the face covered in orange. Now 1.5 x 0.60
= 0.9 — a wall you dodge, not a maze.

## A rule that ends cannot leave leftovers

`nextHour` says explicitly that it clears the world (pendulums, mines, the sequence) — but **the orbs
were outside that list**. `orbCap()` depends on `RULE.orbRate`, so an hour of "more
balls" filled up to 14 and the next hour kept them ALL: the cap drops, but `spawnOrb`
only REPLACES when it is full, it never trims. A temporary effect stayed permanent for the
rest of the game. Now `nextHour` prunes to the cap, taking out the neutral ones first (the same policy
`spawnOrb` already used).

`frenzy50` found it with an **intermittent** `ORB-CAP` — it depended on which rule was rolled.
A failure that appears one run in several is not noise: it is a failure with a precondition you have
not identified yet. The check's message was not enough to diagnose it, and adding the
context (the hour, `orbRate`, the rule, the state) is what made it legible.

## The loop cannot devalue itself with the hour

Enemy health scales (`scaleHp()`: ×2.6 at hour 11) and the loop's damage was **constant**.
Measured: a tight loop was worth **0.94 rooks at hour 1 and 0.36 at hour 11** — the game's
central verb switched itself off, and Franco felt it as "it didn't seem to do damage any more". Now
`closeLoop` multiplies by `scaleHp()`, so the RELATIVE power is constant (1.13 rooks in
both hours, verified). **Anything that is the player's main tool has
to scale with what scales against them**; otherwise the game becomes impossible by itself.

## RESONANCE leaves a mark, not invisible points

It paid a fixed 1600 points. With six- or seven-figure scoreboards that is not visible: you solved the
sequence and nothing legible happened. Now each solved sequence adds to `run.resonance`, which gives
**+8% thread and +15% loop, permanently** (applied in `recomputeStats`, never accumulating over the
previous value — it is still idempotent) plus a score that scales with the hour. One single thing
that stacks, not a menu of random bonuses: making a second card system would have competed
with the one that already exists.

## The streak measures RISK, not a number of rules

`run.brave++` gave the same for GRAVITY (x1.40) as for DOUBLE OR NOTHING (x2.00), and DEAD HOUR (x0.55,
where nobody spawns) built streak just like a dangerous rule. Now there is `ruleRisk(r)`:
red ones (mult >= 1.6) add 2, normal spicy ones 1, those that are not risk (mult <= 1) add 0, and
CALM still cuts it to zero. The draft's card shows the real jump.

## The poker hands have to say WHAT they give

`HAND_BONUS[i].desc` had always existed in the table and **was drawn nowhere**:
you had a pair of aces and there was no way of knowing what it was for. Now the effect goes under the
HUD's strip, and touching the strip (or `H`) opens the **stack panel**, which freezes the simulation and
shows the five cards large with their concrete effect plus the hand and its bonus. The FLUSH is the
only one whose effect depends on the suit, so it has its own table (`FLUSH_DESC`) — the old
text said "The whole suit overflows", which informs you of nothing.

**Careful with the render order:** the panel is a modal and goes LAST, after `drawToasts()`.
Put next to `drawHUD()` it ended up beneath the start-of-hour card, which covered its cards.

## The economy: a RULE by the calendar, a CARD by score

Until 2026-09-15 it alternated — odd hours a rule, even ones a card — and the rule lasted two
hours. Franco changed it: **the rule changes every hour** (two hours in a row of the same thing
became routine) and **the card is earned with POINTS** (`CARD_SCORE = [4000, 12000, 26000, 46000,
75000]`). The stated objective: *"to encourage the player to exploit the score"* — the score
stopped being a scoreboard and became the currency the build is bought with.

Details that matter:

- **Winning a card does NOT interrupt.** `addScore` only increments `run.cardsWon` and gives notice; the card
  is collected at the close of the hour, after the rule. Opening a draft in the middle of combat would be worse
  than the prize. What is immediate is the notice, not the screen.
- **They chain.** If a single hit crosses two thresholds (or you had one saved), two
  card screens come out in a row. The flow goes through `afterDraft()`, which is the only place that
  decides "another card or the next hour?" — **do not call `nextHour()` directly from a draft**.
- **The HUD shows the progress** flush with the score (a fine bar + how much is left, or `CARD READY`).
  Without that, "making points" does not feel connected to anything; that bar IS the incentive.
- A consequence for QA: **closing an hour can chain 2+ screens**, so every test helper
  that advances drafts has to empty the queue in a loop, not advance just once.

## MINEFIELD: the thread is a SONAR, not a marker

The first version: `revealed` was a `Uint8Array` of flags and the cell stayed uncovered **forever**.
After an hour of play the whole face was painted (Franco: *"I don't want all the cells to be left
marked"*), and worse: with everything uncovered the numbers told you where the mines were
**without you ever having gone near**, which was the other complaint. Both come from the same cause.

Now `revealed` is a `Float32Array` of **seconds remaining** (`CFG.mines.scanT`, with
`CFG.mines.fade` of fading). The thread refreshes the cells it passes through and the rest
goes out: the information is fresh or it is nothing. Measured: from 50+ accumulated cells to **11 lit at a
time**. The CLEAN cells (0 mines next to them) are painted much fainter than those with a number
— they were the majority and the ones making the smear.

The deliberate exception: **a mine you passed over stays registered forever** (`m.seen`).
Finding it is the prize for having gone there; what fades is the sweep, not the find.

### The bug that made the numbers noise

The mine was created with `mines.push({ c, r, ..., r: CELL * 0.34, ... })` — **two `r` keys**: the
row and the radius. In a JS literal **the last one wins**, so `m.r` was 0.0755 and the ROW
was lost silently. Hence:

- `mineCountAt` compared `|0.0755 − row| <= 1`, true only for rows 0 and 1 ⇒ the
  numbers you saw were not the count of neighbouring mines, they were noise;
- `revealCell` registered with `m.r === r`, and 0.0755 is never a whole row ⇒ **stepping on a mine's
  cell never revealed it**; the only ones that appeared were the ones that had already exploded.

The radius is now called `rad`. **A double lesson:** a repeated key in a literal gives no warning —
no error, no warning, nothing; and the field that was overwritten was precisely the one with the shortest
and most easily repeated name. If an object mixes grid coordinates with physical measurements, make sure the
names cannot collide.

**And the QA lesson, which is worse:** the `minefield` scenario verified `mineCountAt` against a manual
calculation… which read the same broken `m.r`. The oracle had the same bug as the code, so
they matched and it came out green. **An oracle that shares the data source with what it tests proves
nothing.** What did catch it was looking at the raw values (`mines at (c,r)` showed
`8,0.0755` fourteen times).

### Board numbers vs feedback numbers

The minesweeper's numbers used **exactly the same palette as the damage ones**
(`#ffd23f / #ff9f43 / #ff6b81`), the same weight 900 and the same halo: a cell "3" and a hit "34"
read the same. Now they go in a COLD ramp (`MINE_NUM`) that the damage never uses, and
smaller. A general rule for this game: **what is board information cannot share a
visual language with what is a hit's feedback.**

## RESONANCE: why the punishment measures STANDING STILL and not time

The first version ("a wrong sector = an immediate reset") was broken: on a 3×3 grid, going
from one sector to the next almost always crosses an intermediate one. The second ("punish nothing")
took away all the risk. The third —the one that is there— tells **passing through** from **standing still**:

    const spf = clamp(hyp(P.vx, P.vy) / (CFG.player.maxSpd * P.spdMul), 0, 1);
    simon.wrongT += dt * (1 - 0.85 * spf);

A bare time threshold is NOT enough, and it is measured: crossing the centre cell **diagonally**
is 0.94 u ≈ 1.07 s at maximum speed (plus the start-up), so any value that punished
standing still also punished the normal journey. Weighting by speed, at full tilt it hardly accumulates and
standing still it accumulates in full. The threshold lives in `CFG.simon.wrongT` (the `T` panel) and the wrong sector is
tinted red while it runs: the warning is visible, it does not have to be explained.

## The hour card is NOT a state

It was `game.state = 'intro'` and it froze the simulation for 2.1 s after each draft. Franco:
"don't make it pause after choosing whatever it is". Now it is `game.banner`, a counter that only
draws an overlay; you play from the hour's first frame. If you need a screen that freezes
again, **do not put it in as a `game.state` state**: the state decides whether the
simulation runs, and mixing "what is drawn" with "what is simulated" is what brought this problem.

## QA: qa.py (smoke) and qa2.py (invariants)

- `qa.py` is the usual one: it runs scenarios, takes captures and catches JS errors.
- `qa2.py` is the **auditor**: besides running, it inspects the internal state with `chk()` — NaN,
  Infinity, negative HP, positions outside the face, violated caps, arrays that grow,
  counters that go backwards. `chkEvery = 1` runs it on every frame.
- A trick for reading state: top-level `const`s do NOT end up on `window`, but
  `window.eval(expr)` is **indirect** eval ⇒ it runs in the global scope and does see the lexical environment.
  `G('sparks.length')` reaches anything without touching the game.
- **To compare two runs THREE things have to be equalised**: the seed (`mode='daily'`), the
  game's `lastT` (pump a few frames before `startRun`) and the **absolute value** of the driver's
  clock (`t = 100000` in both). Subtracting two large, close floats does not give exactly
  `STEP`: with `t ≈ 1e5` ms the error is ~1e-11 s, and the system amplifies it over ~500 frames.
- **The PER-FRAME leak detector over-reports and is not to be believed.** The `leak` scenario
  (qa.py) and `tunnel` (qa2.py) sample the orb's stretch once per frame against the thread's
  **final** position — but the thread moved during the 3 substeps, so a legitimate sweep
  counts as a "crossing". At 50 ms it gets as far as saying 100% leaks. The ones that count are `tunnel2` (a settled
  thread, one shot at a time, 5 speeds × 2 dt) and `tunnel3` (a MOVING thread, counting by
  the orb's final position): **0 of 50 and 0 of 56**. If you are going to measure collisions, measure by
  consequence (did it bounce? where did it end up?), not by geometric sampling.
- **A bot that stands still dies**, and once dead `stepSim` leaves straight away: everything you
  measure afterwards is rubbish. If the scenario needs stillness, make it immortal
  (`B.P.hp = B.P.hpMax; B.P.ifr = 9`) and, if necessary, freeze the hour (`CFG.clock.hourT = 1e6`).
- **The same with the drafts**: if the hour ends, the simulation freezes until you choose.
  Every long scenario needs its `advance()`.

## The draft cards (a legibility lesson)

The two drafts look **different on purpose**, because they are different things:

- **Cards** = real playing cards. A cream paper face over the dark arena, the rank in both
  corners, a watermark suit, and a **ribbon with the family's name in WORDS**
  (THREAD / HEALTH / GREED / ORBS). The suit's colour alone was not enough to understand what it did.
- **Rules** = engraved slate plates with a wax seal carrying the multiplier.

The `EFF` table (in `p09`/the cards section) returns each card's **concrete effect in numbers**
according to the rank it drew ("Thread +42% longer"). Before there was an abstract strength bar
and Franco's first reaction was *"I don't understand whether it's by level or what"*. The rule that stuck:
**a card has to say what it does, not hint at it**. If you add an upgrade, add its
entry in `EFF` or the card is left mute.

The heights of the card's corners are **calculated, not by eye**: with `textBaseline
'middle'` a glyph takes up ~±0.37·F, and that is why the rank goes at 0.07 and the suit at 0.175 of the height.
The family ribbon goes above the inverted corner, which used to eat it.

## Render

- The face is **baked once per resize** into `dialCv` (60 marks + 81 cells + numerals +
  the noughts-and-crosses "#"): one `drawImage` per frame instead of ~300 path calls.
- **No `shadowBlur` on entities**: the glow is `bloomPx()`, a radial-gradient sprite
  cached by quantised colour (`_glowCache`) drawn with composite `lighter`.
  It is the TankWARS/DonkeyKong lesson and what keeps the FPS up on mobile.
- The thread is drawn in **7 stretches** with the colour interpolated tail→head plus **one single**
  halo pass. A canvas gradient cannot follow a path and 200 strokes would be very expensive.
- The pieces are **vector** (`piecePath`), not Unicode chess glyphs: on several
  Androids they are missing and show up as little squares.
- **A drawing radius 1.14× the collision one** (TankWARS's `drawRadius` pattern): they read better
  without touching the balance.
- The **context-loss** trio is mandatory (Arcade iframes over the same renderer):
  if you add a new bake, invalidate it in the `contextrestored` handler.

## Controls

- **Touch**: a dynamic stick in the left half (it is born where you put your finger),
  **LUNGE** and **PULSE** bottom right. `#aimSafe` is the dead cushion between the zone and the
  buttons (a z-index sandwich of 3 < 4 < 5, a gotcha inherited from StickFight).
- **Keyboard**: WASD/the arrows · `SPACE`/`SHIFT` lunge · `E` pulse · `P` pause ·
  `ENTER` confirm · `1`/`2`/`3` choose in the drafts · `T` the tuning panel.

## Headless QA (without node)

Chrome headless with `--virtual-time-budget` **does not fire rAF in a sustained way**: the sim
is left frozen even though the timers run. The loop is prepared to be pumped by hand:

- `window.LOOP.loop(t)` is directly callable and `scheduleRaf()` has dedupe.
- A debug handle: `window.LOOP = { CFG, P, game, run, RULE, hand, enemies, orbs, thread,
  inP, moveStick, keys, simon, frenzy, hourRule, resetThread, ... , freeze, slow }`.
- **The driver has to write `moveStick`, not `inP`**: `pollInputs()` rewrites `inP`
  from the stick and the keyboard on every frame.
- **The driver's clock is called `t`.** A scenario that declares `var t` overwrites it: the pumping
  breaks and the test's loop leaves after one iteration with an absurd counter. It has happened.
- **Free runs are NOT deterministic.** To compare two configurations you have to
  force `B.game.mode = 'daily'` (a seeded rng); otherwise the difference you see is noise.
- `LOOP.freeze = true` freezes the sim and keeps drawing → a screenshot of the exact instant.
- A harness with an error catcher: `qa.py` from the 2026-09-12/14 sessions
  (menu · play · wave6 · intro · rule · card · slot · simon · frenzy · reglas · boss · over ·
  win · poker · tateti · dash · rope · leak · closes · afk). `reglas` walks ALL the rules
  one at a time; `afk` tests the player standing still for hours (the queen explosion); `leak` counts
  orbs that go through the thread without bouncing; `closes` measures closures varying the knobs.

**A hole found on 2026-09-18: `ALL` was not the list of scenarios, it was a hand-written list.**
`SCENARIOS` had 47 defined and `ALL` named 35. The TWELVE that were missing were precisely the most
recent ones - `boss`, `barriles`, `hudfijo`, `fkill`, `feedback`, `dprbase`, `heal`, `handtouch`,
`touchsel`, `feel`, and today's two - that is, a bare `python qa2.py` never ran them and they were only
executed by naming them by hand on the day they were written. They are all in `ALL` now. **When a
scenario is added it has to be added to `ALL` in the same movement**, or it is born dead: it passes once
and after that it never runs again.

Added on 2026-09-18: **`peon`** (the pawn captures diagonally and advances straight; it picks cells BY HAND
and not at random, because what is being tested is a deterministic rule - with rolled positions it would pass
by chance half the time) and **`obus`** (24 shells crossing a 112-point thread from
every angle: none may change side, and one has to reach the player anyway with the
thread in the middle).

## Playtest 2026-09-18 - the pawn decides, and the thread stops being an umbrella

### The thread no longer stops the shells

`updateShells` reflected any shell that crossed the thread and changed its side: on paper it was the
Pong + Tank Wars fusion, and it was the idea I liked most in the whole module. In the hand it did not
work, and the reason is purely geometric: the thread is almost a face long and it TRAILS
behind you, so it covers an enormous arc at all times. The shell bounced ALWAYS.
Franco said it in one line: "there's no way they can do anything to you like that". A tank that cannot hit you is
not an enemy - it is a dispenser of projectiles of your own.

Now the shell GOES THROUGH the thread and the only thing you do with it is dodge it. The ORB still
bounces, and that asymmetry is the rule, not an inconsistency: **the orb belongs to the table and you can
make it yours; the shell belongs to whoever fired it.**

Gone with the bounce: `run.reflects`, the `devolver` achievement ('10 shells returned'), the shell's
`deflCd` field and the `px/py` that only the sweep used. The achievements are only toasts (there is no
screen that lists them), so removing a key from `ACH` breaks nothing.

### The pawn: it advances straight, it captures diagonally

It was the only piece on the board with no decision - it aimed at the centre and walked. And it is precisely the
chess piece with the most distinctive rule of all, and the easiest to read from outside.

`pawnLane(e, c, r, pc, pr)` (in `p08_enemies.js`, above `pickLane`) decides ONCE, when choosing a
lane, before telegraphing:

- `adelante` = towards the face's centre, reduced to the dominant axis. That is where the pawn promotes.
- The two capture diagonals come out of `adelante` itself: an axis's perpendicular is its pair
  inverted (`p = [f[1], f[0]]`), so with `f=(1,0)` they give `(1,1)` and `(1,-1)`.
- If the player is STANDING on one of those two squares, it goes that way. A chess capture: one
  square, diagonally, and only if there is something to capture. Otherwise, it advances.

It is evaluated once only on purpose. Between the decision and the strike there is half a second of telegraph
(`aim: 0.50`), and that half second is the player's way out. A pawn that recalculated would
CHASE you, and chasing is not what a pawn does: a pawn punishes you for having stood still
in the wrong place. And it is deterministic, not rolled - if it rolled, the rule would stop being a
rule and the player could do nothing with it but get lucky.

`e.pawnBite` marks the capture and `drawTelegraphs` paints that lane in CRIMSON instead of the pawn's
bone white. Without that the rule would exist only in the code: the player would see a pawn move
oddly and would not know it was because of where they were standing.

### The card was shifted, and the reason was the rotation

The suit's ribbon rode over the bottom corner's suit. Looking at the loose numbers it did not
add up: the ribbon ran from `bh*0.700` to `0.792` and that corner's RANK is at `0.875`. What
was missing was seeing that that corner is drawn with `rotate(PI)`, so its suit, which in local
coordinates goes `+0.097` BELOW the rank, on screen lands `0.097` ABOVE it: `bh*0.778`, right
inside the ribbon.

**The general lesson: in a block rotated 180 degrees, every local displacement inverts its sign on
screen.** Any layout collision calculation has to be done in screen coordinates,
not in the block's.

The card's usable strip runs from `0.257` (the foot of the top corner) to `0.743` (the ceiling of the bottom
one, which is its SUIT and not its rank). The content block was centred at `0.585`. It went up
`0.085` WHOLE, without touching the internal spacings - what was fine inside is still the same - and the
ribbon also narrowed from `0.66` to `0.58` of the width, because its round caps reached
`0.83*bw` and the corner's suit lives at `0.820`. Two things not touching by three pixels is
not them not touching.

### The Clockmaker, with more health

From 2600 to 4400. The fight was FIXED (the open-core window, the armour from 0.30 to
0.55, the summoning cap) and with that it overshot: from an impossible toll to a formality. What
was lacking was DURATION, not difficulty - the read/dodge/punish bar is where it should be,
it just ran out before you got to play it twice. That is why the health was moved and NOTHING
ELSE: touching `armor` or `openDmg` would move the feel of the fight again.

### No decorative typography in text that gets drawn

It happened twice in a row. First the middle dot (`·`): "get rid of them across the whole game, I don't
want to see them". It was replaced by commas and by an EM DASH where it led... and on the next round
Franco asked to take the em dash out too: "I don't want it to say 'Promoted - Queen', don't use that character
for anything".

**The lesson is not changing 129 characters, it is the rule:** a separator that is neither a word nor
a common punctuation mark forces the reader to interpret it, and at this size over dark felt it reads as
a broken dash. Changing one odd sign for another odd sign fixes nothing — that is why the
first time.

The texts that are DRAWN are rewritten as SENTENCES, their separator is not swapped:
`'PROMOTED TO QUEEN'` needs none, and in the info panel each dash became a full stop and
a new sentence. Where two things genuinely had to be separated a comma or a colon goes. The name
for "no hand" in `HAND_BONUS[0]` was `—` and is now `'NONE'`: a word says the same thing and
can also be read.

In the COMMENTS, a simple hyphen. Careful with one: `0.74·r` was a MULTIPLICATION, not a separator, and
a blind replacement would have turned it into `0.74-r`. An asterisk goes there.

**Check, not memory:** after touching this you have to count the characters in the built
`index.html` (`—`, `–`, `·`, the `—` escape and `&mdash;`). All at zero.

### The INFO button is written against the CODE, not against memory

It still said that the cards arrive alternating with the rules. That stopped being true a while
back: **the RULE is by the calendar (every hour) and the CARD is by SCORE** (`CARD_SCORE`,
`nextCardAt`, `cardsDue`), and the draft opens at the moment you cross the threshold, mid-hour.
It also said that on the boss "only loops do full damage", when today the armour
is 0.55 and the open-core window multiplies by 3.

**House rule: the info panel is user documentation and it ages like any
other. Every time a mechanic changes you have to open it.** What it says today, verified against the
code: a wheel of rules per hour, cards by score with a replacement when the hand is full,
a frenzy once an hour that heals a third of the bar, and that the thread does NOT stop the shells.

## A barrel has to be a BARREL, not a sphere with little lines

Franco: "they aren't easy to tell apart by their size and they look like another kind of orb more than a barrel". The
problem was not the size. It was drawn as a SPHERE that rotated on itself, and a sphere
with two little lines is an orb with two little lines.

A barrel rolling along the floor, **seen from above**, is something else:

- Its **axis is perpendicular to the travel**. It rolls forwards, so the cylinder is lying
  across: the silhouette is longer across than along the movement, and that proportion alone
  already says where it is going. No arrow is needed.
- It is **fatter in the middle of its length**. That belly is what separates a barrel from a tin.
- **IT DOES NOT TURN IN THE SCREEN PLANE.** This was the underlying mistake. The rotation axis of a
  barrel rolling towards you is horizontal, that is, perpendicular to the camera: on screen the
  silhouette does not move at all. Rotating the sprite in the plane is a coin spinning, not a barrel.
- So you see it rolling through the **staves**: the boards run along the axis and turn with the
  surface, so on screen they sweep from one edge to the other. The metal **hoops** sit in
  planes perpendicular to the axis and stay still. **Sweeping staves + still hoops = rolling.**
  It is the cartwheel trick from old animation.

`spin` (a screen angle) became `roll` (the SURFACE's phase). And **the baking went**: it existed
because the sprite rotated, but now the silhouette is fixed and what changes are the
staves, so a bake would be regenerated entirely on every frame — it would be more expensive, not cheaper. There are
three barrels at most and only with the rule in force. The light IS counter-rotated (like the bike, the
hand and the turret): the barrel does not turn in the plane, so its shine stays where the scene's
light is.

`CFG.barrel.r` (0.048 -> 0.058) is the COLLISION radius and it sits on purpose between the drawing's two
semi-axes (0.075 across, 0.048 in the direction of travel). With an elongated silhouette a circle
is always a compromise; that it falls on the side generous to the player is the decision.

## THE FIGHTER (StickFight) — the first enemy that comes close and commits

StickFight had not contributed **a single** mechanic. What it had to give is what was missing: in the
arena there were four ways for something to threaten you — a telegraphed lane (the pieces), a chase
(the ghost), a projectile (the tank, the barrels) and a trail (the bike) — and **none comes within arm's
reach and stays there**.

It walks up to you, plants its feet and throws a flurry of three: jab, jab, lunge. **While it strikes it does
not move**, and that is the whole counterplay. The lunge reaches almost twice as far as a jab (0.200 against
0.115), so backing off a little is not enough: either you get out properly, or you eat the last one.

Three things the QA found that are worth more than the enemy:

1. **It planted itself even with its back turned.** During the wind-up it turns SLOWLY on purpose
   (so it can be juked round the side), so it could not correct half a turn and
   threw the flurry at thin air. It really happens in a game: a loop or a pulse pushes it. The fix
   is not a special case but a condition — if it is not facing you it carries on WALKING, which is the
   state where it turns fast, and it sorts itself out.
2. **The floating fist made hugging it the perfect defence.** As a disc at the arm's tip,
   the lunge hit a RING (between 0.140 and 0.260) and touched nothing inside 0.140.
   The closer you were, the less the biggest strike hit you — exactly the wrong way round. **The fix is
   not moving numbers: it is making the impact test describe what you see.** An arm that stretches out
   sweeps from the body to the tip, so the impact goes against the body->fist SEGMENT.
   The scenario went from 2 hits out of 3 up close to 3 out of 3, without touching a single reach.
3. **A stick figure puts down much less ink than a filled silhouette of the same radius**, so at the
   same `r` as a piece it reads considerably smaller. It is drawn at 1.3 times the collision radius
   (the collision radius is NOT touched: what has to be corrected is how much it TAKES UP on screen). And the
   proportions matter more than the size: with the head competing with the trunk, the whole middle
   becomes a knot and the only pose you can make out is the one stretching the arm.

The walk is procedural, not a table of frames: the foot describes an ellipse — forward lifted,
back planted — and the knee comes from bending forwards according to how much the leg shortened. The
cycle advances with what the figure ADVANCES, not with the clock: if it is slowed, it limps more slowly instead of
skating. **A walk cycle reads by the SEPARATION of the feet, not by the swing of the
body.** Light ink on the felt, which is StickFight's look turned around (there it was ink
on paper).

The telegraph is not a lane but a REACH ARC that fills while the arm draws back, and it
disappears when the fist comes out: by the time you see the fist there is nothing left to decide. The same language
as a piece's lane — the shape says where, the fill says when.

## The boss's health is MEASURED, not estimated

Two attempts by eye failed in a row: 2600 and 4400, both "much too easy". On the third the
`bossdps` scenario was made, which sweeps orbits around the boss and measures how much damage per second can
really be put into it. The result at hour 12:

    the best orbit (radius 0.20, just outside the boss)      74 /s
    the same with a damage hand (x1.7)                      163 /s
    + hitting the open-core window (the ceiling)            273 /s

At 4400 that is a **sixteen-second** fight. It is not that the boss was easy: it is that it did not
get a chance to happen. It went to **12000** — 44s at the ceiling, ~60s for a good but not perfect player.

**Why intuition falls so short here:** the open core multiplies by 3 and is open
40% of the bar, and on top of that at hour 12 the player arrives with a built hand. Two multipliers
stacked on a base that already scales with the hour. Any number chosen by eye is going to be out by
a factor, not by a margin.

**The first version of `bossdps` measured badly, and the error is the whole fight.** It modelled the expert
player as one who circles HUGGING the boss and fast: it gave 4/s with 38 loops closed, against 64/s with
only 15 loops for one circling far away and slowly. The one that closed MORE loops did LESS damage. The reason is
geometric: **a loop hurts what is left INSIDE**, and circling up close closes tiny loops
beside you that do not contain the boss. The boss is 0.15 in radius; the technique is to circle outside
that. The corrected version sweeps radii instead of guessing which is the optimum — when you do not know which
the good technique is, do not assume it, sweep for it.

**What was NOT touched, at Franco's request:** the open-core window and the hands not
batting the orbs. They are what made the fight feel like a fight. A boss that defends itself
less has to last longer; that is not a patch, it is the consequence.

## qa2.py: the temporary file carries the PID

`QA_HTML` was a fixed name (`_qa2.html`). Two QA runs at once overwrite each other: one writes its
scenario, the other overwrites it, and the first one's Chrome ends up running the second's
scenario. **It really happened** — in one report `### ruleclean` appeared with `bossdps`'s notes.

What is serious is not the collision but that it is INVISIBLE: it does not fail, it LIES. A scenario reports BAD(0)
on code it never executed. Now `QA_HTML` includes `os.getpid()`.

## Two playtest bugs, and the two tests that nearly lied

### The ghost orbited instead of hitting

Franco: "the ghosts keep circling around me instead of coming to hit me". Measured BEFORE
touching anything, and the shape of the result is the whole diagnosis:

    a STILL player               minimum distance 0.000   8 touches   ok
    circling at 0.30 (SLOWER)      minimum distance 0.120   0 touches   <-- the bug
    circling at 0.44 (level)       minimum distance 0.009   4 touches   ok
    fleeing at 0.86 (faster)       minimum distance 0.139   0 touches   correct

**It only failed against a player slower than it.** That rules out speed - it has plenty - and
points at the aiming. It was two things multiplying:

1. **The lead was a FIXED DISTANCE (0.34), not a time.** It always aimed 0.34 ahead
   of the player, even with them at 0.05. At that distance a point 0.34 ahead ends up
   almost PERPENDICULAR to their advance: it went past, came back, went past again. **The orbit
   was not a calculation error: it was the right solution to the wrong problem.** Now the
   lead is `t = distance / its own speed` — "where you are going to be when I arrive" — and up
   close it tends to zero, that is, it ends up aiming AT the player, which is the only thing that closes a
   chase.
   And it explains why the case that was easy to test by hand worked: the angular error depends on how much
   the player advances in the flight time, and against one going level with the ghost the fixed 0.34
   turned out to be almost the right value by coincidence.
2. **The turning radius was bigger than the contact.** At 0.44 u/s with 2.6 rad/s the minimum radius
   is 0.169 and contact happens at 0.069: **more than double**. Even aiming well, any error
   up close became a stable orbit with no geometric way out. Now it turns faster the closer
   it is, which is also what you expect from a ghost: it floats, it has no inertia.

A player at full tilt being able to get away is preserved, and the scenario watches it.

### The telegraphed piece jumped back to its old position

`pickLane` stores `sxp/syp` (the charge's origin) when the piece DECIDES, that is, before the
half second of telegraph. If during that time you push it - a loop, the pulse, a charge,
a barrel - the piece moves, but on starting the charge the lane interpolates from `sxp/syp` and
TELEPORTS it back.

The origin is re-anchored on starting: it leaves from where it really is. **The destination is not touched, and that is
on purpose:** `drawTelegraphs` draws the lane from the CURRENT position to the fixed destination, so
what the player saw promised was "I am going to end up there". Moving the destination would break that
promise; moving the origin keeps it. `dur` is recomputed after re-anchoring, or a piece pushed
towards its destination would arrive sooner and be left waiting.

### The two tests nearly lied, for different reasons

**The piece one came out green against the code with the bug in place.** It measured "the first frame with
`st === 'move'`", but the state change and the lane's first step do NOT happen in the same
call: they are branches of an `else if`, so the frame in which `st` becomes `'move'` is precisely the one
that has not moved anything yet. The MAXIMUM jump of a frame during the whole charge is now measured.

**And then it gave a false positive with the knight.** The bound came from `T.spd`, but the knight
jumps with a FIXED duration (0.34s) however long the jump is, so it moves faster
than its nominal speed and it is not a teleport. The bound now comes from the REAL LANE
(`length / dur`), with 3.4 of margin because the smoothing curves have a maximum slope of 3.

**The ghost one measured the escape while circling**, and circling the player CROSSES the ghost's path
again: that does not prove you can escape, it proves you can collide. Now it flees in a straight
line and it is verified that the distance GROWS.

**A method to repeat:** when a new test comes out green, run it against a copy of the
code with the bug put back by hand. If it does not fail there, it proves nothing. It was done that way with `empuje` and that
is how it was found that the first version was no use.

## ART DIRECTION (2026-09-18)

> **LOOP should feel like an open pocket watch that someone used as a gaming table
> for a hundred years.**

That sentence resolves almost every visual design question on its own: it explains why there are playing cards and
chess pieces on the same surface (someone played there), why the brass has patina (it is
old), why there is ONE single light (there is a lamp over the table) and why time matters (the
object is a clock). **Every new thing is evaluated by asking whether it belongs to that.**

**Materials - five, and each thing belongs to one only.** Felt (the arena) - Brass (the bevel, the hand,
the frames, the marble's setting) - Bone/ivory (the cards) - Crystal and light (the orbs, the shield, the frenzy)
- **Jewel (the marble, and ONLY the marble)**. If something new does not fall into one of the five, it does not belong.

**Lighting:** one lamp, top left, fixed (`LIGHT`, not to be touched). Only three things emit
light: the marble, the thread and whatever is charged. Everything else reflects it.

**Colour:** the semantic system governs the decoration. Gold = value. Ice = you. Crimson = it
hurts you. Violet = rules. Green = it heals you. **Any element that uses one of those five is
making that statement, whether it likes it or not.** Two collisions found, one corrected: the thread's
tail used the RULES' violet (corrected in Group 2); the enemies use gold for the queen,
violet for the bishop, crimson for the rook and light blue for the knight (**not corrected**: moving them
to bone is proposal N2 and needs a decision, because it risks legibility by colour at a
distance, which is a documented decision).

**Movement:** heavy, short inertia, nothing appears abruptly. The only thing that moves linearly is
the hand, because it is a mechanism.

**Sound:** C major pentatonic (`PENTA` always was) with silence as an instrument.

**Feedback hierarchy - four levels and the budget is respected.** Routine: a sound and a spark.
Good: + a ring. Excellent: + hitstop and a shake. Exceptional: + a lighting change across the whole
arena. **Closing a tight loop with three pieces inside should be the only habitual event that
reaches level four.**

**UI:** information turned into an object, or nothing. The hour lives in the chapter ring.

**It is not:** neon, sci-fi, generic arcade, Las Vegas, excessive glow. **It is:** old, fine, tactile,
mechanical, mysterious, premium, slightly worn, restrained.

## GROUP 1 - the clock sounds, sweeps and counts

### The ticking is not a metronome: it is the hand crossing the marks

The face has 60 baked marks and the hour lasts 38 s, so the ticking comes out every 0.63 s **by itself**.
There is no tempo to choose: **the tempo was already drawn on the face**. That is the difference between
putting music over the game and making the object sound.

Two alternating tones like a real escapement (A2 and E3, the tonic and the fifth) plus a very short
noise click, which is what you really hear of an escapement; the tone only places it in the key.

**In the last fifth it SUBDIVIDES to 120**, that is, the same hand marking half-marks. A clock
that changes speed stops being a clock; one that marks finer still is one, and it warns that
the hour is running out without a single UI element.

The bed (`droneSet`) is a fixed A1 with its fifth and it **never changes pitch** - changing
pitch would mean changing key, and at that point it is music. What changes is how much of it you hear: it appears in
hour 4 and rises to hour 12. For the first three hours the game sounds as it always did.

`audioHush(dur, piso)` ducks EVERYTHING. It is used twice per game: 0.75 s before the
Clockmaker wakes (its roar is RESCHEDULED to come in when the volume returns - a big hit
needs emptiness in front of it or it does not sound big) and a 0.2 s suck on entering a frenzy.

**A bug this uncovered:** `audioHush` schedules ramps on `masterGain`, which is the same node as the
mute button's. **Setting `.value` while there are ramps scheduled does nothing.** Without cancelling the
ramps first, the mute would have stopped working after the first silence - that is, after
fighting the boss for the first time. Intermittent and extremely hard to tie to its cause.

### The hand makes the transitions, and it is NOT a state

The new thing is already drawn underneath; on top there is a dark wedge covering the angle the hand has not
swept yet, with a line of brass on its edge. Six transitions, between 0.26 s and 0.52 s.

**`sweep` is a render counter, not a `game.state`.** Why is documented (the hour
card was a state, it froze the simulation and had to be taken out): it does not block input or hold up the
simulation. Measured: the player moved 0.244 units DURING the transition, and `startRun`
fires it with the game already in `play`. That is why going back to playing can feel immediate.

It advances with the REAL dt, not with `simDt`: during a draft the simulation is frozen and a sweep
tied to `simDt` would be left stuck halfway forever.

### The chapter ring is the HOUR hand

Twelve numerals, twelve hours. The rod that already exists goes round once an hour (it is the minute hand) and the
hours lived **light up** on the ring. It is not a new indicator: it is the hand that was missing.

**Two versions were thrown away before this one, and the reason is worth more than the result.** The first was
a fine band of brass between the marks and the bevel: on desktop it could barely be made out and on a phone in
landscape it **did not exist**. The problem was not the colour or the alpha: at 335 px of height the face's radius
is ~150 px, so a band of 0.014 of the radius measures **TWO PIXELS**. No amount of brightness
fixes two pixels.

**WHAT SURVIVES THE SIZE IS THE SILHOUETTE AND WHATEVER IS ALREADY DIMENSIONED TO BE READ.** The
numerals already were. A SECOND canvas (`dialLitCv`) is baked with the same numerals in live brass
and is pasted clipped against a wedge: one clip and one drawImage.

The second version had numerals AND a band, and the band was superfluous for two reasons: it was a second brass
hoop inside the bevel, and above all **it was redundant with the hand**, which already marks the advance
within the hour. Two indicators with no overlap were left: the numerals count (discrete), the
hand marks the position (continuous).

The contrast is fixed by **lowering the off state, not raising the on state**: the hours you have not
lived yet are asleep, and the face fills with light during the run.

## GROUP 2 - the thread is a cord, the marble is the jewel

### The thread

- **The tail used the RULES' violet.** Now it goes from cold steel to ice. A colour from the semantic
  system is a statement.
- **It did not rest on anything.** A single dark pass offset along the light's axis gives the shadow AND the
  contact edge: two things with one stroke.
- **The last third carries a hot CORE**, so the cord reads round where you are using it
  and flat where it was laid down.
- **Tension:** `thread[i].w` stores the hand's speed when LAYING each point down (the past). The
  tension is the present and it comes free from the player's velocity.
- **Closure anticipation, free.** `findSelfCross` ALREADY computed the distance from the head to each
  old segment to decide the graze. It is asked for the minimum and its index as a by-product: zero
  new iterations, zero changes of decision. With that, the stretch you are about to enclose lights up.

**The head was going to WHITE** and it had to be tempered: the additive core was adding on top of a
body that was already at (196,247,255). Two brightnesses added give white, and **white is the material that
turns a cord into a laser**. Bright is not white.

### The marble is the mechanism's jewel

The code said in so many words "the same material, the same light" as the orbs. The intention was
coherence; the consequence was that the protagonist was a slightly bigger orb - in a
game capture you had to LOOK FOR IT.

Now it is an **octagonal sapphire mounted in a brass setting**: the only moving object on the face
that carries the clock's material, which says by itself that the player is part of the machine. And it solves
the thread's anchoring, because something comes out of a setting.

**It is an OCTAGON and not a circle with painted facets**, for the same reason as the progress
band: in landscape it measures ~4.5 px of radius and at that size the facets do not exist. Against orbs that
are circles, an octagon reads even at five pixels.

The halo went from 3.4 radii at 55% to 2.15 at 30%: **a jewel does not radiate**, a real sapphire is dark and
what it has is hard glints.

### The cost: paying for the material with resolution that was not being used

`drawThread` jumped from 214 to **308** path commands (+44%) against a self-imposed ceiling of 15%. Two
corrections:

1. The new passes go DECIMATED (the shadow at step 3, the core at step 2). **A shadow does not need
   the resolution of the object casting it.** 308 -> 255.
2. It was still over, so it was paid for with something that was spare: **the glow is four wide additive
   strokes at 2-9% alpha and it was being traced vertex by vertex.** A diffuse halo at that
   opacity cannot show faceting. Step 2. 255 -> **224, +4.7%**.

**The resolution is spent on the SILHOUETTE, which is the only place where it shows.**

CAREFUL when measuring: the total weight of `s_prof.py`'s scenario varies between 271 and 344 depending on how many pieces
get rolled. The comparable number is `drawThread` with a fixed thread length, not the total.

### Two bugs from the group

- **`gw` already existed in `bakeDial`.** A name collision with the wear gradient: a `SyntaxError`
  and a black screen. The QA caught it on the first attempt.
- **The closure highlight got stuck.** `findSelfCross` only runs if the player moved; with
  the player perfectly still, `nearIdx` kept the value from the last frame in which they did move
  and the golden stretch was left lit forever. **The third time the same family has turned up in
  this project** (the `hitstop` that survived between games, the frenzy left hanging on leaving for the menu):
  a carried-over value that is only WRITTEN when something happens and never CLEARED when it stops happening.

### Patina, restrained

All inside `bakeDial`, zero cost per frame: irregular angular bands over the bevel (an old metal
hoop has its shine stained), four fine contact scratches, and **the felt worn where
the hand sweeps** - the only thing that always passes through the same place, hour after hour. A FIXED seed
of its own, never `rnd`: decoration does not touch the game's seed (it already broke daily mode once).

## BLACK SCREEN (2026-09-19) - two causes of mine, one confirmed and one ruled out

Franco: "it got stuck on me while playing, the screen went black".

**Frozen AND black has TWO possible signatures in this game and it is worth telling them apart:**

1. `ctxLost`. The loop does `if (ctxLost) { lastT = now; return; }` and stops drawing. If the
   browser throws away the context over memory and does not restore it, it stays black forever.
2. **An exception BEFORE the render.** `loop()` calls `scheduleRaf()` on its FIRST line, so
   the next frame has already been requested when something throws. The game carries on "alive" throwing the same
   exception on every frame, and the canvas stays frozen on the last thing it managed to draw.
   **This is the more deceptive one**, because the game is not dead: it is running and failing.

### The cause ruled out: the bake of the wrong size

`dialLitCv` (Group 1's lit numerals) was **a canvas the full size of the face**,
just like `dialCv`, to draw TWELVE NUMBERS. On desktop ~1600x1600x4 = 10 MB: the game's biggest
allocation was doubled to use 1% of its pixels.

**The lesson holds even though it was not the cause: a bake has to be the size of what it DRAWS, not
of the coordinate system it lives in.** Copying the geometry from the bake next door is the comfortable thing
(the same scale, the same coordinates, it pastes with the same numbers) and that is why it takes so long to see.

Now they are twelve small sprites through `bakeSprite`: ~130 KB against 10 MB, they live in `_bakes` (so
`clearBakes()` invalidates them by itself, one bake fewer to remember to put in the
context-restored handler), only the lit ones are drawn, and the `clip` has gone.

**It was ruled out as the cause of the report** because on Franco's phone that canvas measures less than
1 MB: doubling it is not enough to throw away a context.

### The probable cause: missing audio state guards

`droneSet` checks `AC.state !== 'running'` before touching the graph. **Its two siblings do not.**
Writing any parameter of a node of a CLOSED AudioContext throws `InvalidStateError`, and on
mobile the context suspends or interrupts itself **by itself**: a call, switching app, the page in the
background. It is not a hypothetical state.

And it fits the exact symptom: `updateAmbience` calls `droneOff()` **every half second**
while you are not playing, and it runs in `loop()` BEFORE the render. Signature number 2 above.

`acOk()` is now the ONLY place where it is decided whether the audio graph can be touched.

**The general rule that comes out of this: if a function touches the audio graph, the question is not "is there
a context" but "is the context RUNNING".** And anything that runs before the render can take
the whole frame with it.

### The invariant that was missing: `memoria`

The suite had 53 scenarios and **none could catch this**, because they all measure BEHAVIOUR and
the problem was one of RESOURCES: nothing broke, the canvas memory ran out.

`SCENARIOS['memoria']` wraps `document.createElement`, counts every canvas the game creates and
adds up its area after forcing a re-bake and playing for a while. It fails if the total goes over 64 MB or if
more than two canvases of over 1 megapixel appear (**one big one is the face and that is fine; two
means someone has copied its geometry again to draw four things**).

Measured today: **47 canvases, 3.5 MB in total, the biggest 1.5 MB, zero over 1 MP.**

It matters especially because all the Arcade's games live in iframes of the same renderer and
share the canvas ceiling - it has already happened once and it is in the project's memory.

## GROUP 3 - two grammars for the closure, two materials for the grids

### The small loop and the big one were the same animation painted a different colour

(A correction to a Group 2 note: the ghost of the non-tight loops did NOT use the rules'
violet, it used (125,249,255), which is the ice. The colour was already right.)

**TIGHT = COMPRESSION.** The polygon CONTRACTS towards its centre in 0.22 s with a hard edge. The
ring contracts too (`addRing` is passed the radii the other way round). The sparks are born AT THE
PERIMETER and go INWARDS: **the particles' direction is half the read** - it is what
turns "I blew something up" into "something closed over something". It leaves no mark: a hit does not leave
a trace.

**BIG = EXPANSION.** The polygon does not move: it lights up WHOLE at once and fades out,
with the ring expanding, and it leaves a **trace on the felt** that goes in
2.6 s. It lasts 0.55 s.

(There was a version in which the outline was traced point by point, in the same order the player
drew it. The idea was lovely - the table retracing the route - but Franco asked to
change it and he was right about something fundamental: **progressive tracing puts the accent on the PROCESS, and
what the player has just done is already over.** Lighting it all at once puts the accent on the
RESULT, which is what belongs to a prize. It also came out cheaper: it reuses the fill's same path
instead of building a second route.)

The marks go DECIMATED (`markPts`, with `ceil` and not `floor` - with floor the cap is not respected) and
with a cap of 2: without that, each mark is a polygon of hundreds of points being paid for on every frame and
the face fills with graffiti.

### Hitstop: the hierarchy was the wrong way round

Closing a loop - the game's central verb - had none, while taking a hit,
charging and the fighter's lunge did. Now: an empty loop = nothing; with something inside = a touch;
tight = clear; tight with two or more deaths = the ceiling (measured: 0.069 s, exactly
`CFG.juice.hitstop * 1.25`). **An empty loop freezes nothing: if everything freezes, nothing has weight.**

### Two grids, two materials

The 9x9 had its light line BLUISH, which made it a relative of the ice - the player's colour - and
made it compete. Neutral grey and fainter: it is background structure, not information.

The noughts-and-crosses "#" was in cyan, that is, in the LIGHT's family. **The "#" is not light: it is a
part of the mechanism.** It becomes brass, it is baked ASLEEP, and it is lit by a layer only drawn
while `game.sectorsOpen` - zero cost for the rest of the hour, and it shares `drawSectors`'s clip
so as not to add a second clip against the same circle.

The fill of a CLAIMED sector stays in ice on purpose: **the brass is the mechanism's structure,
the ice is you.** The lines belong to the machine; the marks you leave on top are
yours.

### The bug: the timer was in the wrong place

On dying, the ghost and the marks FROZE on screen, because their timers lived
inside `updatePlayer`, which starts with `if (!P.alive) return;`.

The fifth appearance of the "state that gets stuck" family in this project, but the diagnosis
is different from the other four: **the bug was not forgetting to clear, it was putting the timer
in the wrong place.** A loop ghost and a mark are EFFECTS: they live and die like the
sparks and the rings, and they have to advance where those advance. They moved to `updateEffects`.

### Cost: the same mistake that had already been corrected once

`drawChapterRing` had ended up at **21.6 of weight, the SECOND most expensive drawing in the game**, for an
hour counter: nine strokes (lit hour marks) plus nine blits (numerals)... at the
same angle, saying the same thing. It is identical to the mistake corrected in Group 1 when the
progress band was taken out. The marks went: **21.6 -> 4.5**, and the ring reads just the same.

## `bossdps` was a NOISY instrument presented as a precise one

**An important correction to what was reported on 2026-09-18.** When the boss's health was chosen
(12000), this scenario measured 163/s with a built hand and that is where the "44 s at the ceiling" came from. Measured
afterwards, over different builds and over the same one: 130, 163, 200, 200, 226, 229. **The instrument
swings by almost double.**

The cause is structural: the measurement counts the damage done in a 9-second window in which
FOUR OR FIVE loops are closed. One loop more or less moves the result by 20-25%. **Measuring something
that happens five times inside the measurement window cannot give a stable number.**

And the error of method is worse than the number: a conclusion was drawn from ONE single run, which is
exactly what the scenario claimed to be correcting when it replaced "choosing the health by eye"
with "measuring it". Measuring badly with confidence is worse than estimating knowing you are estimating.

What the scenario **does** measure well, because it was consistent across every run (74, 79, 82,
84, 92 /s):
  - that the best orbit is the one at radius ~0.20, just outside the boss;
  - that circling HUGGING it closes loops that do not contain it (the original geometric finding);
  - and it works as an ALARM: if the boss falls in less than 22 s, something has broken.

What it can **not** resolve is the absolute number of seconds of fight. The boss's health stayed at
12000 and the fight lasts, for a strong player, **between ~30 and ~55 s depending on the run**. Tuning that
better asks for playing it, not measuring it with this tool.

It now reports the MEDIAN of three samples with its spread, and the assertion's threshold went from
35 s to 22 s: it stopped pretending to be a thermometer and is what it can be, an alarm.

## CORRECTIONS 2026-09-19 (a batch separate from Group 4)

### The lane travels with the piece

Franco: "if a shockwave displaces a piece and then its planned move is executed, the
piece ends up also covering the extra distance from its new position to the destination
original".

**The previous fix was half a fix.** The ORIGIN had been re-anchored on starting the charge
(`sxp = e.x`) leaving the destination fixed, with the argument that the drawn lane promises a
destination. That removes the teleport but leaves the other thing: the lane STRETCHES and the piece covers
too much ground.

The right thing is for **the whole movement to be translated**: the same direction, the SAME DISTANCE, a different
starting point. A push moves you and your intention with you.

And there is ONE SINGLE place to do it. The six sources of displacement - the player's pulse,
the clock's chime, the frenzy's burst, the dash's charge, a charged orb and a barrel - all go
through `e.knock()`, which accumulates in `kx/ky`, and that becomes position in a single block of
`updateEnemies`. Translating `sxp/syp/tx/ty` there covers all of them, **including any
added later**. The re-anchoring was taken out: with the lane travelling it would be a second mechanism
doing the same job, which is how the bugs nobody understands are born.

A side effect that had not been looked at: during `move` the lane's lerp OVERWRITES the position on every
frame, so a push mid-charge was thrown away and hitting something mid-charge did
nothing. Measured: the destination shifts by 0.217 instead of 0.

The translated destination is bounded to radius 0.93. That is why the measured distances come out slightly NEGATIVE
(-0.016 to -0.044): a piece pushed against the edge cannot launch its charge out of the
arena. **The test's assertion is asymmetric on purpose**: covering too much ground is the bug; covering
too little can only come from the clipping.

### A single dash and pulse control

There were two implementations for the same thing: a hoop drawn on canvas (desktop) and a filled DOM
button (touch), which also said the cooldown differently - an arc that fills against
an opacity. **The only way for them not to diverge again is for there to be one single implementation, not
two that resemble each other.** The hoop is always drawn; the DOM button is left as an invisible
touch zone (`color: transparent`, not `visibility: hidden`, because it has to keep receiving
touches).

`btnRects` is cached in `resize()`: `getBoundingClientRect` forces a layout recalculation and asking for it
per frame is the mistake this project already made with the hover (hence `cvLeft/cvTop`). If it
could not be read, the drawing falls back to the desktop positions - **the control has to be visible ALWAYS,
even if it is in the wrong place.**

Two details that only appeared on looking at the capture at real size:

- `cacheBtnRects` asked `IS_TOUCH`, and **the right question is whether the buttons are
  LAID OUT**, not which device we think it is. Besides, in headless `IS_TOUCH` is false and it cannot
  be forced: with the old condition it was impossible to photograph what a phone sees, and **a
  visual change you cannot look at cannot be verified**.
- The DASH label was CUT OFF in landscape: it landed at 332 px of a 335 px canvas. A rule that
  does not need to know the platform: if it does not fit underneath, it goes above.

### The buttons' cache was built when the buttons were HIDDEN

Franco, testing the uploaded build: "they're next to each other. they aren't stacked".

`cacheBtnRects()` was called ONLY from `resize()`, and `resize()` runs when the page
loads... **when the game is in the MENU**, where `#actBtns` has `display: none`. The rect of
a hidden element comes back as zeros, the zero-size guard leaves `btnRects = null`, and the drawing
falls back to plan B: the desktop positions, which are **side by side**. And it was never recomputed
again, because `resize()` only runs if the window's size changes.

That is, going in to play from the menu without turning the phone - what everybody does - was
exactly the one route that did NOT go through the good one.

**And the verification covered it up.** The capture and the scenario removed `noTouch` and called `resize()`
by hand, that is, they measured precisely the case that does not occur in the real game. **A test that prepares the
ground for the code to work does not test the code: it tests the preparation.** Now the
scenario comes in from the menu and does not touch `resize()`, and verified the other way round: against a build with the
fix reverted, it fails ("cached rects=NO").

The fix: `ensureBtnRects()` rebuilds the cache when the VISIBILITY changes, read from the `body`'s
classes - which is what the CSS uses to hide them, that is, the source of truth. Reading classes does not
force layout; the `getBoundingClientRect` inside does, but it runs a few times per game.

Also, from the same batch: the hoops ended up **small** because they were drawn at 84% of the button and
**an outline reads smaller than a fill of the same diameter**; the button had been dimensioned from
when it was a filled circuit with the text inside, and now the text lives outside. Dash 84 -> 100,
pulse 60 -> 76, the hoop at 0.46 of the width.
And the "if the label does not fit underneath, it goes above" rule had been thought out for a single button: in a
COLUMN, above a button there is another button, and DASH's landed on the PULSE hoop. Room is made
for it underneath (38 px) instead of flipping it, and the margin is now an assertion of the scenario.

### The knight, with a knight's silhouette

It was an eight-point straight polygon and read as a splinter. Now it is a head in profile
facing right in the language of web chess pieces: a long muzzle, two ears with their
valley, a curved nape, a jaw, a wide base. The SILHOUETTE is in charge because at 20 px it is the only thing that survives
- the same lesson as the ring's band and the marble. Since the piece **is baked**, the curves are
free.

### The closure warning, reverted

Gone are the amber highlight, the recording of `nearD2`/`nearIdx` inside `findSelfCross` and the two
cleanups that existed solely for it. `findSelfCross` went back to exactly what it was: not one
extra assignment in a loop that walks hundreds of segments per frame. **The rest of Group 2's
thread stays**: the materiality, the contact shadow, the head's core, the tension, the palette.

### The test measured badly THREE times in this batch

It is worth noting them together because all three have the same shape - **the instrument measures a route the
game no longer uses, or a magnitude that is not the one it claims to measure** - and all three reported
game bugs that did not exist:

1. It pushed with `e.x += dx` by hand. That is not the real route (the game pushes through `e.knock`) and,
   with the lane travelling, it is precisely the ONE thing that does not move it.
2. It counted **the push itself** as if it were a jump of the lane. A frame's legitimate bound
   is the lane's step PLUS the push in force, not just the first one.
3. It used the lane length captured at the start, but in two seconds a fast piece finishes
   its charge and **chooses a new lane**: the value was stale.

**The rule: when a test starts failing after a fix, the first question is whether the test
is still measuring what the game does now.**

## A silence with nothing on the other side is only a drop in volume

Franco, testing: "when I activate the frenzy it's like the volume drops for a couple of seconds".

It was `startFrenzy`'s `audioHush(0.20, 0.10)`, and what he heard is exactly what was happening. **But
the problem was not the duration: it was that there was nothing on the other side.**

Before the boss the silence works because the roar comes in afterwards - the emptiness exists SO THAT the
hit sounds big, and that is why the boss's voice is rescheduled to come in when the volume
returns. In the frenzy the silence preceded nothing, so it does not read as "something happened" but as
"the volume dropped".

**The rule: silence is an instrument of CONTRAST. Without something on the other side it says nothing.**

The frenzy's was taken out. What stays is that the ticking cuts out for the whole frenzy: that is not
a drop in volume, it is the clock having left the room, and it lasts the whole 6.5 s instead
of an instant. It will be reconsidered in Group 4, when the frenzy has a sound of its own.

## GROUP 4 - the frenzy stops being a buff and becomes an ARENA EVENT

The frenzy already lasted 6.5 s, already stopped the pieces, already gave you points - but all that happened
inside the rules. The arena never found out. It was a buff with a timer, not a moment.

### What changed state, and what did NOT

Nothing that DECIDES anything was touched: not the frequency, not the duration, not the magnet, not the score,
not the damage. What changed is that now **it is noticeable from outside the character**:

- **the cloth is tinted** and the bevel lights up, that is, the frenzy happens to the CLOCK, not to you;
- **the bevel IS the timer**: the light travels round the hoop and when it runs out, it is over. There is no
  new bar - the bar is the object that was already there;
- **the thread turns gold**, which is the colour of value, because in a frenzy each loop is worth more;
- **the drone goes up an octave** instead of ducking. An octave is the SAME note: the sound
  becomes urgent without the game changing key, which is what would have happened with another note.

`frenzyT` comes in over 0.22 s and leaves over 0.55 s: it comes in abruptly because it is a fright, it leaves slowly
because it is a comedown. It is cleared in `startRun` and in `backToMenu` - a visual state that survives
a game is a bug waiting to happen.

### The ones that are not pieces live in the arena too

Franco: "the tanks and the TRON-style arrows don't change colour as part of the Frenzy".

`drawEnemy` **was already computing** the frightened colour and passing it to the baked pieces, but it called
`drawCycle` and `drawTank` without it, and each one read `e.T.col` on its own. The whole
face turned blue except those two. No new colour was needed: what had to be done was **to get them the
one the game already had**.

And then half of it was still missing: `drawCycleTrails` had its own hardcoded `[255,150,60]`, so
the bike turned blue and left an orange trail behind it. **In TRON the trail IS the enemy** - it is
more surface than the body. A hot trace crossing a face that had cooled read as if
that enemy had not found out about the frenzy.

**The lesson: when an object is drawn in more than one place, tinting it in only one leaves it split in
half.** Look for ALL the sites that choose its colour before considering the change done.

### The ghost and the fighter were not going faster: they were going TWICE

Franco: "they move straight at the player and die on reaching them, it feels too
abrupt".

It is written down that in a frenzy the pieces stop threatening and the only thing that moves them is the magnet, which
is deliberately slower than their walk - "it does not move them by itself, it heels them towards you". But
the ghost and the fighter **carried on chasing of their own accord AND also took the magnet**: two
forces added towards the same point. That is why they arrived on top of you all at once.

Their own chase was lowered from x0.8 to x0.22 inside a frenzy. The magnet takes charge,
just as with the pieces: they still come closer, but **heeled**, which is the word the magnet's
design already used. Outside a frenzy nothing changes.

**The lesson: before lowering the speed of something that feels abrupt, look at how many things are
pushing it.** The symptom "it goes too fast" and the symptom "it takes two pushes" feel the same and
are fixed differently.

### The hierarchy: killing a pawn cannot look like killing a queen

Any death fired 38 sparks, a ring of five radii and a screen shake: the
"excellent" level for the game's most routine event. And during a frenzy, where five or six fall
per second, the screen became illegible precisely at the moment it should be clearest.

The step was not invented: **`e.T.score` already encodes how much each piece is worth.** Three levels, with the
data the game already had:

| | | |
|---|---|---|
| routine (< 200) | a pawn | a sound + 9 sparks. No ring, no shake |
| good (< 800) | a rook, a bishop, a knight, a ghost, a tank, a bike, a fighter | + a small ring + a minimal shake |
| big (>= 800) | a queen, the boss | + a big ring + a shake + a punch |

### Winning cannot be the losing screen in green

It is the climax of twelve hours and a boss with 12000 health, and it was the same layout with a different title.
Now the victory **counts the score upwards** (the number is earned, not reported),
**lays out the hand in real playing cards** (you earned that build: it is shown, not named in a
table row) and **dims the arena less**, because the face was left with the twelve hours lit and
that is part of the prize. The defeat stays sober, which is right: not every ending deserves the same
celebration.

## The Simon's "get ready" indicator had the wrong SHAPE (2026-09-19)

Franco: *"the hoop when the sequence is about to start isn't drawn completely over the
sector, part of it is underneath"*.

He was right and it happened with all three classes of cell:

| cell | what you saw |
|---|---|
| the centre | the hoop was born with radius 0.35 against a half-side of 0.333: it ran out of the square on all four sides from the first frame |
| an edge | it also went past the face and was cut off by the clip |
| a corner | it was centred on the square's GEOMETRIC centre, which is 0.943 from the axis - practically on the rim -, so almost the whole hoop fell outside and a loose piece of arc was left |

**That last one is a mistake this project had already made and corrected once**: the sector
diamonds do not go at the cell's geometric centre for exactly this reason, and that is what
`SECT_DX`/`SECT_DY` exist for. The Simon's hoop never got that fix. When a geometry
constant is fixed in one place, you have to look for who else computes it on their own.

But moving the centre was not enough, because the underlying problem was a different one: **a circle does not fit in
a square that is also bitten into by a bigger circle.** Any radius that looks good
at the centre runs out in the corners, and any that fits in the corners is invisible at the
centre. There was no number that would fix this.

So the indicator stopped being a hoop and became **a square frame that closes over the
cell**: the same silhouette as the thing it points at. It is born at 1.42x and lands EXACTLY on the
rectangle `paint` already draws, so the end of the gesture is the indicator merging with its
target. And since it goes under the same clip as the face, in the edge cells it ends up cut IN THE
SAME PLACE as the cell: they coincide instead of contradicting each other.

The arc that also swept the time has gone: the shrinking IS the countdown. They were two
encodings of `u3` in the same object - the same redundancy that has already been taken out twice (the
progress band, the lit hour tick).

**The rule: an indicator that points at a thing should have the shape of that thing.** As long as the
indicator and its target have different geometries, any clip, any edge and any
change of size will separate them.

A new scenario, `aro`: it wraps `strokeRect` on the context's prototype and checks, across the nine
cells, that the indicator is concentric with its cell at the start and lands exactly at the end.
**Against the old code it fails 9 out of 9** - there was not a single concentric rectangle, because it drew
an `arc`.

## The fighter learns a second flurry: KICKS (2026-09-19)

Franco: *"the stickman is good but it could have one more combo, for example doing something with
kicks"*.

It always threw the same thing - jab, jab, lunge - and a single flurry you learn in two encounters.
Now there are two and it chooses which before planting itself:

| flurry | strikes | reach | total damage | duration |
|---|---|---|---|---|
| FISTS | jab, jab, lunge | 0.115 / 0.115 / 0.200 | 2.30 | 1.26 s |
| KICKS | low, spinning | 0.165 / 0.235 | 2.30 | 1.24 s |

**It is not a stronger flurry: it is the SAME threat distributed differently.** The totals are equal on
purpose. What changes is the shape: fewer strikes, slower, reaching much further. Each
kick on its own is easier to dodge - it takes longer to come out and the warning arc is born bigger -
but backing off is no longer enough, which was exactly the gap the fists left.

**How it chooses, and why it can be read.** It decides on planting itself, looking at the distance: outside the
jab's reach it kicks, and on top of that it kicks anyway one time in three. Moving away does not take you out of the problem,
it changes the problem. And it reads without memorising anything because **the warning arc that already existed is
drawn with the reach of the strike that is coming**: when it is going to kick, it is born bigger. The information
was already on screen; now it says two things instead of one. That is why the flurry is chosen on
PLANTING and not on striking: if it were chosen on striking, the warning would be lying throughout the
wind-up.

In the drawing the kick comes out of the LEG, with the same calculation the fist was drawn with
(a world position, not the figure's, so what you see is what hits), and the knee comes out by itself
from the formula that was already there - with the leg drawn in it bends a lot, stretched out it stays straight. The torso
leans back while the leg goes out: **that counterweight is what makes a kick
weigh something instead of looking like a leg stretching.** The low one goes along the ground and the spinning one goes high.

The `luchador` scenario went from 5 points to 7. The new point 7 is **the design's invariant
written as a test**: if the total damage or the duration of the two flurries separate by more than 15%,
or if the kick stops reaching further than the fist, it trips. Point 3 (the lunge's) now
FORCES the fists flurry: since there are two, letting it choose would make that point sometimes measure
something else without warning.

## "It is not inherited" does not mean "it does not affect it" (2026-09-19)

Franco: *"the information bar doesn't scroll on the phone"*.

The panel already had `overflow-y: auto`, `touch-action: pan-y` and `overscroll-behavior: contain`, and
beside it a comment of mine that said: *"`html, body` carry `touch-action: none`... the property is not
inherited, so this should already be able to scroll"*.

**The sentence is true and the conclusion is false.** `touch-action` is not INHERITED, but the browser does not
resolve it by inheritance: when the finger goes down, it computes the allowed gesture as the INTERSECTION of the
touched element's `touch-action` with that of ALL its ancestors. With `none` on the `body`, the
intersection is empty for any descendant, whatever it says.

And it was worse than a panel that did not work: **the `body`'s `none` was the only thing protecting the
canvas.** Since `touch-action` is not inherited, the `<canvas>` never had its own - it was living off
the global ban. Simply removing the `body`'s `none` would have fixed the panel and broken the
game: dragging your finger over the face would have started moving the page. (The new scenario
shows it: against the old CSS, the canvas reports `touch-action: auto`.)

The fix puts each ban where it belongs: `html, body` become `manipulation` (it kills the
double-tap zoom, lets scrolling through), the `<canvas>` gets its own `none`, and
`overscroll-behavior: none` stops reaching the end of something dragging the page behind it - which
matters twice as much here, because the game lives in an iframe of the Arcade.

**The rules:**
1. `touch-action`, `pointer-events` and `overflow` are resolved by the browser looking at the CHAIN of
   ancestors, not at the element alone. "It is not inherited" and "it does not affect it" are different things.
2. **A comment that explains why something should work, next to something that does not work, is a
   hypothesis written as if it were a fact.** If you have to justify that something works, you have to
   test it, not comment it.

A new scenario, `scroll`, which runs at 800x380 - a phone held sideways, which is how Franco plays -:
it checks that the panel OVERFLOWS (otherwise there would be nothing to test), that no ancestor declares
`touch-action: none`, that the canvas DOES declare it, and that the panel is a genuinely scrollable
container. Against the old CSS it fails the first two. `qa2.py` gained a `SIZES` map so a
scenario can ask for a window of its own.

## No piece moves outside its rule, not even to get out of a corner (2026-09-19)

Franco: *"I saw rooks moving diagonally"*.

`pickLane` chose among the family's directions but **did not check that the first step
landed on the board** - only the knight did that. When no direction worked, further
down a plan B came in:

```js
e.dx = -Math.sign(e.x) || 1; e.dy = -Math.sign(e.y) || 1;   // both at once = a DIAGONAL
```

For any piece. A rook cornered against the edge bounced diagonally.

Now the directions are filtered by "the first step lands on the board", and plan B chooses, among
**the piece's directions**, the one that most points at the centre; the step is SHORTENED until it fits in the
face instead of clipping x and y separately, because clipping the axes skews the direction.

**The rule: an escape case is not permission to break the rule that defines the object.** Plan B
existed to get a piece out of a corner, and in doing so it turned it into a different piece.

A new scenario, `legal`: 384 choices at the eight edges and corners, plus 96 with the piece
pushed OUTSIDE the grid, checking against each family's legal set. Against the
old code: **48/384 illegal, with "a rook at (-0.86,-0.86) chose (1,1)"** - Franco's bug,
reproduced literally.

## The rook, with a rook's profile

The old silhouette was an inverted cone: 0.86 wide at the top and 0.60 at the bottom. It tapered towards the
floor, that is, it stood on a point, which is the opposite of what a rook conveys. Franco
asked for it "straighter" and passed on the reference drawing.

The new profile is the classic one: **battlements, a neck, an almost straight shaft with a waist barely
hinted at, and a wide base that plants it.** The four battlements come from an `M` table instead of
twenty hand-written `lineTo`s, so moving one does not force the others to be recomputed. The piece is baked:
the curves cost nothing at play time.

## The pawn promotes by ARRIVING, not by finishing a move

Franco: *"I'm seeing pawns that get displaced to the centre and don't promote; they should do it
whenever they reach the centre whatever the reason"*.

The promotion was checked inside the charge's `if (u >= 1)`, that is, **only on finishing its
own move**. A pawn pushed to the centre by a pulse, a chime or a barrel
stayed there without promoting, and its next move took it away.

Now it is checked every frame, in `updateEnemies`, **right after the push has become
position** - so the frame in which it was pushed already counts.

**The rule: if a condition is about A PLACE, it is evaluated by being there, not by how you got there.**
Tying it to the end of a move turns it into a "prize for moving well", which is something else.

What still does not promote is a pawn that GOES THROUGH the centre at full speed in a single frame
(an enormous push moves it 0.6 per frame and the window measures 0.27). That is correct: it passed
over, it did not arrive. If it is ever needed, the fix is a swept check against the frame's
segment, not enlarging the window.

A new scenario, `corona`, with three points: pushed **by the real pulse** (the route
Franco reported - the player outside, the wave sends it to the centre), placed at the centre by hand, and
one far away that must NOT promote. Against the old code the pawn ends up at r=0.081 - that is, at the
centre - and does not promote.

## TEST mode

Franco asked for "a test mode with infinite health". It is a MODE and not a difficulty: it does not change
numbers, **it takes away death**. That is why it lives in `MODES` and not in `DIFFS`, and that is why it does not save a record -
a record without death is not a record.

What matters is what it does NOT do: **it does not hide the hits.** The impact is seen, heard, it shakes you,
pushes you and is still counted in `run.damage`. The only thing that does not happen is the health dropping. A test
mode that covers up the hits is no use for testing anything.

Three locks, because there are three routes to death: `hurtPlayer`, `hurtPlayerRaw` (the gallows,
which skips the invulnerability) and `killPlayer` (in case a fourth appears).

`menuRects` went over to centring `MODES.length` cards instead of having the `(i - 0.5)` for two hard-wired:
with the old calculation, adding a mode threw the whole row off-centre.

A new scenario, `modotest`: a hit of 9999, a `hurtPlayerRaw(9999)`, 600 frames standing still in the
middle of the arena at hour 9 with eight enemies, and `saveBest`. It checks both halves - that it does not
die AND that the hit is still counted and still leaves sparks.

## The list of hands, flush with the cards

Franco: *"have them a bit closer to the first card on the left, at least 50px or so"*.

The rows were drawn **left-aligned** inside a fixed-width column, so
each name ended wherever it liked and **the gap up to the first card was decided by the
text's length**: "PAIR" ended up half a screen from the hand and "STRAIGHT FLUSH" almost touching it.
It was not a badly chosen margin - it was that there was no margin, there was leftover text.

RIGHT-aligned, they all end the same distance from the card. And the separation drops from
`S*0.05` to `S*0.018`. In portrait the list goes underneath and centred, so there it stays on the left.

The active hand's highlight bar had to learn to measure: with the rows on the right it was still
measuring the whole column and half a bar was left empty on the left. `medirFit` was added, which
runs **the same shrink loop** as `txtFit` and returns the width. It runs the same loop on
purpose: if the width were computed separately, the two numbers would drift apart as soon as someone touched
one, and the result would be a box that does not fit its text and nobody would know why.

## The info panel, second round: it scrolls BY HAND

The previous round's CSS fix was correct and necessary - the `body`'s `touch-action: none`
emptied the intersection for everything inside, and the canvas was living off that
ban without having its own -, but Franco tested it and **it still did not scroll**.

The suspect is where the game lives: the Arcade puts it in an iframe and, on a portrait phone,
**rotates it 90 degrees with CSS** so it is played in landscape without turning the device.
Touch scrolling inside a rotated container depends on how each browser classifies the gesture's
direction, and `pan-y` refers to the element's LOCAL axis.

It was not worth carrying on guessing which layer was eating it: **the scrolling is done by hand**,
with pointer events - what the whole game already uses - and the iframe document's `clientY`, which
comes through the same transformation as everything else. With inertia, because a text panel that
stops dead where you lifted your finger feels broken on a phone.

The CSS stays: it is correct, it fixes the unprotected canvas, and if the native gesture ever
arrives the two routes do the same thing.

**The rule: when a "correct according to the spec" fix does not fix the symptom on the real
device, the next step is not a second theory - it is removing the dependency.**

The `scroll` scenario gained a point that dispatches real pointer events and checks that the
panel moved, in both directions. The CSS points stay: they cover the other half.

## The fighter only kicked, and why (2026-09-19)

**Measured before touching anything**, with 40 encounters under game conditions: **0 fist flurries, 40
kick ones.** The repertoire was never lost - the three fists were still there with their reach, their damage and
their timing -, what was failing was CHOOSING.

```js
e.cmb = (d > PUNOS[0].reach || rnd(0, 1) < 0.32) ? 1 : 0;
```

The distance on planting, measured, runs from **0.1293 to 0.1369**. The jab's reach is 0.115. That is,
`d > 0.115` is always true, the `||` short-circuits before reaching the random, and a kick comes out
every time.

**The underlying cause is not the threshold: it is that `d` cannot tell you anything at that point.** The fighter
plants itself JUST as it comes within `CFG.fighter.enter`, so the distance at that instant is always
worth almost the same - the window measures one walking step, 0.008. I reasoned "if it is outside the
jab's reach, kick", describing a situation the planting rule itself makes
impossible.

**The rule: a variable the code itself has just set is no use for branching.** Before
setting a threshold, ask whether the number can vary at that point.

A nuance that appeared in the tests and is worth recording: in a SUSTAINED fight - the fighter already
up against the player, without coming close again - `d` could indeed drop below 0.115 and then fists came out.
That is, it was not "never fists" in the abstract: it was **never fists on the approach**, which is the
vast majority of what you see. Both measurements are correct and they measure different things.

**The fix:** it ALTERNATES. After a flurry there is a 75% chance the other one comes out. In the long run it gives 50/50, and
it also READS: "it has just kicked" becomes useful information. And the flurry STARTS rolled instead
of at 0 - with a fixed `cmb: 0` each fighter's first flurry was 75% kicks (measured: 30 of
40), and since most do not live to throw many, the player still saw a skewed mix.

## The fighter's animations

Franco: *"they look crude and unpolished... strikes that look like simple rigid displacements of
the limbs or poses that change abruptly"*. The jumps were real and there were six.

1. **The state machine jumped and so did the body.** `cam` (how far the feet separate) went
   from 1 to 0.18 in ONE frame on planting, and the lunge's load switched off abruptly on starting to
   strike. Now there are two smoothed values on the enemy - `e.guard` (0 walking, 1 planted) and
   `e.crouch` - and everything that used to look at `e.fs` to decide a pose reads those numbers. The
   transition lasts ~0.11 s instead of one frame.
2. **The strike was a straight line.** `lerp(-0.42, 1, t)` with a linear `t`: constant speed, which is
   exactly "a limb being displaced". Now the anticipation draws back fast and STAYS
   loaded -the moment held up there is what makes the strike legible-, the exit goes with a fifth
   power (half the travel in the first 13% of the time) and the recovery comes back more
   slowly than it went. That the return is not symmetric with the going is half of why a strike
seems to weigh something.
3. **The figure mirrored in one frame on turning round.** `face` was recomputed every frame from
   `cos(ang)`. First I gave it hysteresis, and the continuity test showed that was not enough: the
   flip was still instantaneous, a 6.4 px jump in a 15.7 px figure. Now `face` is a
   CONTINUOUS NUMBER: turning, it passes through zero in ~0.07 s, the figure narrows and comes out the other side,
   which is how a paper cut-out turns.
4. **There was no body behind the strike.** Now the shoulder comes in with the fist and goes out with the kick
   (the counterweight), the hip pushes towards the strike, and the supporting foot slides forward on the
   big ones: planting and PUSHING.
5. **The elbow never straightened**: it had a fixed offset, so a fist at full stretch was still bent.
   Now it uses the same calculation as the knee - the shorter the limb ended up, the more it bends -, and the
   arm straightens on arrival. It is what kills the articulated-stick sensation.
6. **There was no follow-through.** During the exit a faint trace of the limb is drawn a few
   frames behind. It is two lines and it is the difference between a strike and a pose: without a trace, at 60
   fps the fist simply APPEARS outside.

And the bright knot at the tip came in abruptly at `ext > 0.45`; now it comes in by alpha from 0.15.

**No mechanic changed**: not the damage, not the reach, not the duration, not the rate of fire, not when it plants itself,
not the rest, not the frenzy.

### The `lucha2` scenario, and how an animation is measured

Three parts. The first two are straightforward: **that both flurries come out** (with a check that it
ALTERNATES, because the proportions could come out right with long streaks) and **that the five strikes
execute** - three fists and two kicks, each index has to have done damage at least once.

The third is the interesting one: `drawFighter` is wrapped and **the points it emits** are captured,
frame by frame. It is what reaches the canvas, not a formula copied from the game.

Three things forced me to correct the test before it measured anything:

- **The trace shifts the indices.** It is drawn before the skeleton and only during the strike's
  exit, so the first points are sometimes its. It reported a 37 px jump in a 15 px
  figure: it was not the figure, it was the test comparing the trace's tip against a hip. It is
  counted from the END: the skeleton emits 14 fixed points, that is, the last 28 numbers are
  always the same structure.
- **Walking is not jumping.** The fighter while walking moves its torso ~3 px per frame. THE
  TRANSLATION IS DISCOUNTED and the pure pose is measured.
- **The threshold has to be measured, not chosen.** The good build's peak is 2.6 px out of 15.7 (0.166)
  and that peak is the body coming in on the punch, that is, the animation doing its job. It was set at
  0.22, with 33% of margin. **Against the previous build the same test gives 11.44 px and fails**, which is
  the instantaneous mirroring.

**A rule that had already turned up and now has a third proof: when a test changes colour, the
first question is whether the test is still measuring what the game does now.**

### A NaN the patch itself put in

The patch inserted `guard: 0, crouch: 0, face: 1,` with a `//` comment at the end of the line...
and the anchor landed in the MIDDLE of a line of the source, which carried on with `gait: 0, ang: 0, bob: ...`. The
comment ate the rest: `ang` was left undefined and the fighter's position became NaN on
the first frame.

**The rule: if a replacement's anchor lands in the middle of a line, the replacement cannot end in
a line comment.** It goes above, on a line of its own.

## The frenzy's bed sounded like a phone vibrating

Franco: *"the sound in the frenzy that's like a phone vibrating, get rid of the bloody thing"*.

Mine, from the previous batch. The bed is two sines - 55 and 82.41 Hz - and in the frenzy I raised them
an octave: **110 and 164.8 Hz**, at a forced volume. A phone's speaker does not reproduce those notes,
it turns them into knocking, and besides, two low sines that close beat against each other and produce
amplitude modulation. Knocking plus modulation is, literally, the physical description of a
phone vibrating.

**The rule: on a small speaker, a low note is not heard as low - it is heard as a defect.** Everything
below ~200 Hz has to be written off as lost or as dirty.

It was taken out entirely, along with `droneSet`'s `oct` parameter and `CFG.frenzy.drone`, which nobody
else used. **I tried two things with the frenzy's bed and both were wrong**: ducking it (it was
heard as a drop in volume) and raising it (a hum). What marks the frenzy through audio is that the
TICKING CUTS OUT for the whole 6.5 s - the clock has left the room -, and that is not a change of
volume, it is an absence.

## The arrowheads

Franco: *"the tips don't quite look tidy... crude terminations"*. The cause was one of
construction, not of size. The lane was a tapering quadrilateral **with its own closed
outline**, and the tip a SEPARATE TRIANGLE on top:

- the lane ended in a stroked straight cut - a hard cap right where there should have been a
  tip;
- the triangle started at `L - 0.45·w1` with a half-width of `1.05·w1` against a lane of width
  `w1`: barely wider, so it read as a lump and not as a tip;
- and being two figures with different alphas, the seam was visible.

Now the arrow is **ONE single closed silhouette** - a tapering body, shoulders, a vertex and back -, the
outline walks the whole thing and the head measures almost twice the body's width. Rounded
joins, which at this size look finer than a spike.

An intermediate attempt I discarded: tying the head's lighting to the body's fill
REACHING it. It sounded finer and it was wrong: in a long lane the head measures 8% of the
length, so it stayed unlit during 92% of the warning - precisely when the only thing that matters is
where to. **The head says the DIRECTION: it has to be visible from the first frame.** Now it
lights with the general progress.

Neither the width, nor the length, nor the colour, nor the body's alpha changes.

## The sectors' gold: it broke the game's colour law

Franco: *"the lines that divide the sectors turn golden and I don't understand what it represents"*.

**What caused it.** `drawSectorHash` draws the noughts-and-crosses "#" lit, and it runs only
while `game.sectorsOpen` - the CLAIM WINDOW, which opens past a third of each hour and
closes on collecting a line or at the end of the hour. The rest of the time the "#" is baked into
the face, unlit. That is, the gold DID mean something: "sectors can be claimed now".

**Why it still could not be understood.** The game has a colour law of its own - **gold = value** - and
this broke it: the "#" turned gold whenever the window was open, whether it was worth anything or not,
while the diamonds of the SAME mechanic respect it (ice if they are a normal target, gold if
they complete a line). Two objects from the same mechanic speaking different languages.

**The gold was not ambiguous for being faint: it was ambiguous for lying.** A colour with an assigned
meaning used outside its meaning poisons the rest - if gold sometimes does not mean
value, it stops meaning value at all.

**The fix:** the "#" speaks the diamonds' language. ICE while the window is open, GOLD
only when some free sector would complete a line. The information is not lost - the window is
still announced, and now with the right colour -, and the gold becomes a warning with content:
there is a line one step away.

## THE MOBILE CRASH: the game was drawing inside a sprite (2026-09-20)

Franco: the stick worked, the top-right menu responded to touch but did nothing,
and the info button worked and could be scrolled.

**The symptoms were the diagnosis.** Everything that carried on working is pure DOM: the stick, the
info panel and its hand-rolled drag. Everything that "responded but did nothing" is DOM that changes
GAME STATE and needs someone to draw again: pause changes `game.paused` and it is not seen,
reset goes back to the menu and it is not seen. That is, the canvas stopped updating and the rest stayed alive.
It was not a controls problem.

### The cause

Two places OVERWROTE the global variable `ctx` to draw on an auxiliary canvas and restored it at the
end - `bakeSprite` and `bakeHandStrip`:

```js
const prev = ctx;
ctx = cv.getContext('2d');       // without checking
ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
dibujar(S / 2, S / 2);           // if this throws, there is no way back
ctx = prev;                      // it never runs
```

If something failed in the middle, **`ctx` was left pointing at the auxiliary canvas - or at `null` - for
ever**. From that frame on the game carried on running, simulating and responding, and drew
everything inside a 40 px sprite nobody looks at.

Two concrete ways to fail, both of them the phone's own:

1. **`getContext('2d')` returns `null`.** iOS has a canvas memory ceiling PER TAB and in
   the Arcade every game lives in an iframe of the same tab - this has already happened to this repo
   with Pong. Reproduced in the test: the old build throws
`Cannot read properties of null (reading 'setTransform')` in `bakeSprite`.
2. **`dibujar()` throws.** And since `_bakes.set(...)` comes AFTERWARDS, the sprite is not cached: it is
   retried the next frame, and the next, forever.

These bakes do not only run on load: `bakeSprite` runs when a new piece size or type appears
and `bakeHandStrip` every time the hand changes. That is, in the middle of a game.

### The fix

`try/finally` in both, plus a context check, plus `blit` tolerating a null sprite, plus
the same guards in the other three places that create auxiliary canvases (`bakeDial`, the glow
sprite, the felt texture).

**The rule: a global variable swap with no way back is a bomb, whatever sets it
off.** If a function overwrites global state to work, the restoration goes in `finally`, always.

### And let the next one leave a trace

Besides the cause there is a DESIGN problem which is what turned an error into a dead
game: **any exception inside `loop()` froze the canvas forever and in silence.**
`scheduleRaf()` is `loop`'s first line, so the next frame has already been requested when the
exception leaves: the loop stayed alive throwing the same error forever.

That is not a symptom: it is the reason Franco could not tell me what happened. Now a frame that
throws costs a frame, and the first time a card appears in the DOM - the only thing that stays alive
when the canvas dies - with the error's message.

A new scenario, `ctxswap`. Against the previous build it gives three failures, including
**"the game was left drawing off screen"**: Franco's crash, reproduced without a phone.

## Flush said two different things, and one of them was illegible

The HUD called `handDesc()` -the concrete effect according to the suit- and the inventory read
`HAND_BONUS[i].desc` -a generic text-. **They did not disagree through a transcription error: they read
different sources**, and one of the two did not know that the flush depends on the suit. It was unified in
`bonusDesc(i)`, which both call.

And the size: **measured, the effect was drawn at `cw * 0.25` with `cw = S * 0.037`, that is,
`S * 0.00925`. On Franco's phone held sideways that is 3.3 pixels.** The floor of the game's own
typographic system is `TS.cap = S * 0.0125`. It was not small type: it was below what
the design admits.

The fix took two steps and the first was insufficient. Raising the base size was not enough because
**the real cap was the WIDTH**: the text went centred over a strip flush with the left edge, so
it could only grow until it hit the screen's rim. Aligning it to the left with
the strip it can stretch to the right, which is where there is nothing, as far as the face's edge. So
3.3 px went to ~9.
**When a text does not fit, ask whether the problem is the size or the place.**

## Pawns do not promote in a frenzy

A side effect of yesterday's fix, and it had to turn up: since promotion is checked every
frame, the frenzy's MAGNET -which drags the pieces towards the player- started putting pawns
in the centre and every one that passed through promoted. The house rule was already written: **in a frenzy
NOTHING threatening happens**, and promoting is the threat that grows by itself.

## Two tests that did not measure what they said

Both appeared in the full suite and **neither was a regression of the game.**

### `rngdet` compared the WARM-UP run against a settled one

Bisected: it passes in the four previous commits and fails in `be01d88`. It looked like a very clear
regression. The divergence was instrumented frame by frame: the two runs separate at
**frame 1**. The decisive question was running THREE times:

    1st vs 2nd: first differing frame = 1
    2nd vs 3rd: first differing frame = -1   (identical over 700 frames)

**The seeded simulation is deterministic; what is odd is the page's FIRST run** - it starts
with the first frame after loading, with its dt and its freshly baked canvases. And the decisive part:
this happens THE SAME in the day-before-yesterday's builds, including the ones the test passed as good. The test
had been comparing a warm-up against a settled run and passing by coincidence; yesterday's changes made
the game consume randomness in a slightly different pattern per piece and that one-frame difference
stopped washing out.

The TEST was fixed: it discards the warm-up run. And what daily mode really guarantees was written
down: **the same arena, the same rules and the same cards** - everything the seed
decides -, not the same result, which depends on the player and on the frame rate.

### `barriles` left loose orbs in the boss test

It failed once in the suite and did not reproduce in 19 isolated runs. The scenario runs in FREE
mode and leaves **seven orbs bouncing** while it checks that the barrel does not hit the boss, which
is pinned at the centre. A charged orb does damage to any piece, and 4 damage is
exactly what one does.

The test said "the barrel does not hit the boss" and measured "nothing hits the boss". The orbs are
taken out of it. **A test that sometimes fails over something it is not testing is worse than not having it: it teaches you to
ignore red.**

## Details from the same batch

- **The health number** goes from `txtG` (a diagonal shadow) to `txtO` (a black outline). Over a
  bar that runs from green to yellow to red, an offset shadow does not separate the text from the background, it
  smears it. `txtO` already existed and is documented as "for whatever has to read over
  anything at all": nothing had to be invented.
- **The sweep on dying** was taken out. It is left only on the VICTORY, where it acts as a curtain before the
  scoring ceremony. Verified: `sweep.dur` is left at 0 on dying and at 0.52 on winning.
- The two text shrink loops (`txtFit` and `medirFit`) were unified in `fitPx`.

### A mistake of mine that nearly got in

I wrote `S * 0.02` inside `drawHandStrip`, where **`S` is not in scope** - it lives in
`drawHUD`. The review caught it before building. The margin is now expressed in units of the
strip itself, which is the only thing that function knows.

## THE POKER HANDS: a single table, an explicit flush and the royal flush (2026-09-20)

### The underlying problem: the effect and its text were two things

There was a chain of `if`s that applied the prizes and, separately, a table of strings that
described them. Two lists that had to say the same thing and **nothing forced them to**. It had
already claimed two victims: the FLUSH said one thing in the HUD and another in the inventory (fixed by
hand the day before, that is, patching the symptom), and the STRAIGHT FLUSH said *"Everything
doubled"*, which is not what it does - it adds five fixed things, it doubles nothing.

Now each hand is **an entry with its effect in data**:

```js
{ name: 'FULL HOUSE', eff: { dmg: 0.35, greed: 0.35 } }
```

`applyHandBonus` applies it and `bonusSegs` writes it. **The text is generated from the same object that
produces the effect, so it cannot lie.** Touching a number changes the description in the HUD
and in the inventory at the same time, by itself.

**The rule: when a text describes a behaviour, generate it FROM the behaviour.** As long as
they are two separate declarations, the only question is when they diverge, not whether.

### The flush stops being a mystery

The FLUSH gave a different effect according to the suit. Franco asked twice what it did - the second time
with the text already fixed -, that is, **the problem was not the wording but the design**: a
hand whose prize you have to go and look up somewhere else cannot be evaluated while you play.

Now: **Damage, Score and Thread +20%.** Three numbers, one line, with nothing to go and look up.

And there is a reason for it to be WIDE and not deep: in this game **the suit is decided by the card, not
by chance** (`su: up.su`, and there are two upgrades per suit). A flush is five cards of the same two
upgrades: a narrow build by construction. Rewarding it with more of the same made it narrower
still; giving it a little of the three main currencies OPENS it up.

### The royal flush

`evalHand` returned 8 for any straight flush. Now it tells 10-J-Q-K-A of the same
suit apart and returns 9. Its prize is **exactly double the straight flush's** - a relationship
that is understood at once and does not have to be memorised.

Careful with the WHEEL: A-2-3-4-5 is a straight and can be a flush, but it is **not** royal. It has the Ace,
which is exactly what would pass a lazy check of the "ends in an Ace" kind; that is why the
start is checked (`rs[0] === 10 && rs[4] === 14`) and there is a test case for it.

**The probability, told to Franco so he can decide:** it is practically unreachable. The ranks come
from a uniform `rndi(2,14)`, so five ranks forming 10-J-Q-K-A are 120 out of 371293 (0.032%), and
on top of that all five have to be of the same suit. It is implemented and it is correct; making it visible
would demand touching how the ranks are rolled, that is, balance.

### The hierarchy

Adding up the percentages as a crude measure of how much each hand gives:

    PAIR 0.12 - TWO PAIR 0.30 - TRIPS 0.25 - STRAIGHT 0.43 - FLUSH 0.60
    FULL 0.70 - FOUR OF A KIND 0.70+60 health - STRAIGHT FLUSH 2.85+80 - ROYAL 5.70+160

Monotonic except for the trips/two-pair step, which was already like that and was not touched: two pair splits
between two currencies and trips concentrates on damage, which is what tells them apart.
**Only two entries of the table changed, and both because Franco asked for them.**

### The list, aligned with the cards

The list's step was computed from the TYPOGRAPHY (`(fsN + fsD) * 1.30`) and the height came from the
step: the list measured what it measured, and its coinciding with the cards was a coincidence. It did not coincide,
so the two columns shared no edge and the eye did not associate them.

Now **the list takes up exactly the height of the cards** and the typography comes from that.

And a correction to my own first version: sharing out the height in **equal parts** made
the two long hands -straight flush and royal, with five effects each- govern the
type size of all nine. Measured at 1080p: the list dropped from 20.5 px to 11.8, that is,
"aligning it" had made worse precisely what had to be improved. It is shared out **pro rata**: each row
weighs what it needs (2.18 units with one line of effect, 3.05 with two) and the seven short ones
give back the space they do not use.

**The rule: aligning one block with another cannot cost the block's legibility. If the calculation
forces a choice, the calculation is badly framed.**

Also: the column's width dropped from `S*0.30` to `S*0.26` because the column and the cards
compete for the width and **the cards give HEIGHT back to the list** (its height IS the list's).
Measured at 1080p: with 0.30 the card ends up at 200 px and the list at 295 tall; with 0.26, 216 and 317.
The longest text still fits without shrinking.

And the active row's highlight hugs the whole BLOCK: with two lines of effect, a one-line
bar left half a row outside its own highlight.

### The tests

- `manos` walks the NINE hands with a real hand of each and measures the stat **with and without** the
  bonus to check that the applied effect is exactly the table's. That point is the one that
  guarantees the text cannot lie.
- `manopanel2` measures the GEOMETRY of what is drawn - it wraps `drawCard` and `txtFit` during the
  panel - and demands that no card runs out and that the column does not overlap the first card. Run at
  1600x900, 900x420 y 520x900.
- `evalHand`'s cases were updated: 10-J-Q-K-A of the same suit is no longer 8 but 9, and the
  flush wheel was added (which has to stay 8).

**A harness gotcha, so as not to lose time again:** `--headless=new` forces a minimum window
width of 500 px. Asking for 420 gives a capture 420 px wide but the page lays out for 500,
so the image looks cropped and it is not. A 390-wide portrait phone cannot be
reproduced with this harness; the portrait layout is proportional to the width (the cards always take up
86%), so what fits at 500 fits at 390.

## What is still on hold (2026-09-18)

Franco ruled out the proposals for **CrazyTanks** (the hand as a rival in a race; the
edge portals) and **Hangman** (the drawn, irreversible countdown). They are left without
mechanical representation and **nothing is to be implemented for those two until he asks**. The
analysis of why Hangman does not fit still holds: its mechanic IS a quiz, and a
quiz in a reflex game is always going to feel like what it felt like.

See [../CLAUDE.md](../CLAUDE.md) for the web ports' shared conventions.
