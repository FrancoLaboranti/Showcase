# StickFight

**Platformer-brawler sandbox** of articulated stickmen with a Fancy Pants look (beige paper + leaf
shadows, blue-stone terrain in ink with scratches, ink characters with orange trousers). You cross a
level of floating platforms punching enemies down until you reach the EXIT; if they take you down you
respawn at the start (enemies already downed stay down). **Web-only** (like DonkeyKong/Pacman): there
is no `.py`, everything lives in [StickFightWeb/index.html](StickFightWeb/index.html). Registered in
the Arcade (`landscape`).

> Careful: it was born as a 1v1 MK-style fighter (2026-07-22) and Franco pivoted it to a sandbox
> (2026-07-23). The camera follows ONLY the player (`CFG.cam.frac` = figure height / screen ≈ 0.16,
> FPA scale); the enemies are N instances of `Fighter` with a brain (`newBrain()`) and an aggro
> radius with hysteresis.

## Architecture (the non-obvious parts)

- **Logic/render split.** Each fighter has TWO 14-point skeletons:
  - `logicPts` = FK of `targetPose` (the nominal keytracks of the moves) → **hitboxes**.
    Deterministic: the springs never alter the frame data.
  - `renderPts` = FK of `poseCur` (critically damped springs per joint) + leg IK + ragdoll blend →
    **drawing and hurtboxes** (dodging by moving really does dodge).
- **Pose in 3 layers** (`buildPose`): (a) base locomotion computed from the movement (lean by
  acceleration + lean by velocity, air poses by vy — the Fancy Pants law: animation is COMPUTED, not
  played back); (b) the attack keytrack, a masked overwrite with weight; (c) additives (flinch,
  landing squash, breathing).

### THE GOLDEN RULE for touching strike animation

A strike's reach is defined ONLY by the FK chain that reaches the limb. Looking at `fk()`:

| strike | chain | BOUND joints | FREE joints |
|---|---|---|---|
| punch (limb = hand) | pelvis → spine → shoulder → arm | `torso`, `chest`, `dx`, `dy`, striking arm | head, free arm, legs |
| kick (limb = foot) | pelvis → leg | `lRu`, `lRl`, `dy`, `dx` | head, `torso`, `chest`, **both arms**, support leg |

The legs do **not** inherit the angle of the torso or of `chest`, which is why in a kick the whole
upper body is free. `dx` moves the pelvis, i.e. the root of EVERY chain: it is always bound.
For what is bound there are three resources, all verified with the headless probe:

1. **Anticipation** keys at `at <= startup − 0.033` (2 frames of cushion at 60 Hz): they fall outside
   the active window *and* outside the swept capsule of the first active frame (which looks at the
   PREVIOUS frame's pose — hence the cushion, otherwise the sweep gets longer and the strike reaches
   further).
2. **PIN** keys at the middle and end of the active window carrying the exact values of the old curve
   (`probe_moves.js` prints them); from the pin on, the recovery is free territory.
3. Additives with `safeAddW()`, which is **exactly 0** across the whole active window (and 2 frames
   before). That is how `atkDrive`'s sink/push, the take-off anticipation and the landing cycle get in.

Watch out for a silent fourth route: the **base layer** leaks into the joints the mask does not cover.
`MASK_PUNCH` does not include `dy`, so anything the base puts on the pelvis moves the shoulder and
with it the reach — which is why `baseLoco` uses `idlePose(tp, quiet)` during a strike (no guard
bounce, no noise, `dy` exactly that of `POSES.idle`, as it always was).

### Why the strikes felt short (2026-09-21) — measure the TRAVEL, not the reach

A strike reads as big by how far the limb TRAVELS, not by where it ends up. Measured with the probe:
the arm is 76 px long and in the old wind-up the hand sat **46 px from the shoulder, i.e. 63 % already
extended**; the leg is 95 px and the chambered foot sat 65-78 px out (knee almost straight). With
those numbers the jab could only travel the 37 % it had left: hence it looked like a flick of the
wrist, even though the final extension was at maximum.

The root cause was not in the keytracks but in the **resting poses**: `idle`/`stance`/`block` had the
hands stretched forward instead of at the chin. Every strike is born from there.

Fix: hands at the chin (25-36 px) and real chambers (foot at ~30 px). Measured result:

| | travel | most folded |
|---|---|---|
| jab | 77 → 124 px | 46 → 30 px |
| cross | 110 → 145 px | 39 → 20 px |
| roundhouse | 354 → 408 px | 65 → 28 px |
| spinkick | 373 → 442 px | 72 → 29 px |

**What makes this NOT a change of reach**: the contact point and the frame data are untouched. Folding
the wind-up further lengthens the swept capsule of the first active frame *towards the body* (7-21 px),
never outwards — and that zone was already covered by the radius (`hitR` + hurt ≈ 46 px) of the contact
frame's capsule, so it enables no new hit. The probe measures the two directions separately:
**`+REACH` (outward growth) ≤ +0.13 px across the 11 moves**.

Two keys that CANNOT be touched even though they sit before the startup, because their segment enters
the active window: the uppercut's `0.07` (it governs 0.10-0.13, and the active window starts at 0.10)
and the sweep's `0.06`. In the sweep the chamber moved to a new key at `0.045` and the `0.06` one went
back to its original values; in the uppercut the arm was simply left as it was.

### Weight and footwork (where the weight transfer lives)

The pelvis cannot move during a strike without moving the reach, so weight is told with the FEET,
which are in no hitbox chain:

- `atkWeight()` gives the curve −1 (loaded back) → +1 (unloaded forward) → 0.
- `m.fw = {rear, front, heel}` applies it as a TEMPORARY offset on the foot's target (never on `f.px`,
  so the planting never finds out and there is no drift). In a kick only the support leg exists: there
  that offset *is* the balance compensation.
- **Root-motion shuffle**: while the strike's envelope pushes the body, the feet sweep along with it
  (`dampHL(f.px, stanceX, 0.055, dt)`). Without this the torso travelled and the feet stayed: combo
  after combo the figure ended up toppling over. Measured with the `desbalance` metric (pelvis ahead of
  the midpoint of the feet): 0.30·CH before → 0.17·CH now.
- `m.drive = {sink, rise, twB, twF}` is what the pelvis and the torso CAN do outside the active window.

### Procedural locomotion

- `runCycle()` computes the whole cycle from the gait phase: contralateral arms, forearm with lag
  (`elbLag` = overlapping action), torso sway at twice the frequency, head that levels itself.
  **`CFG.run.armC/armA` are in WORLD angle**: the arms are children of the torso, so its lean is
  subtracted (`- tor`). Authoring them relative was exactly what gave the runner "carrying a tray" —
  the more it leaned, the further forward its arms went.
- The **slide** branch of `feetIK` (`SLIDE_STATES` = skid and dash): the feet do NOT plant, they drag
  with the body in a wide base. Planting them while the body leaves at 0.34·S is exactly what gave the
  spider-leg stretch.
- `idlePose()` blends idle ↔ `POSES.stance` by how close the opponent is and adds a guard bounce. The
  difference between `idle` and `stance` is almost entirely in the ARMS **on purpose**: the hurtboxes
  come out of `renderPts`, so lowering the head or the pelvis in the guard would be giving away or
  stealing target.
- `airPose()` consults `groundAt()` when `vy > 0` and blends towards `POSES.airLand` as the ground
  approaches: without that anticipation the jump reads as a flying statue.
- **A planted foot = the height of the CURRENT ground.** If `f.py` does not match the surface the body
  is standing on, it is left over from another platform and is corrected at once (no little step). With
  a single level it did not show; with several heights the foot stayed nailed to the old height and
  ended up ABOVE the pelvis. Also careful: getting up from a knockdown needs an explicit
  `replantFeet()`.
- **Procedural gait cycle** (`strideParams` + the `gait` branch of `feetIK`, tunable in `CFG.gait`):
  each leg alternates STANCE (the foot stays NAILED in the world — the phase advances by distance with
  cycle = `2·half/duty`, so the derivative of the foot in stance is exactly 0 → zero skating) and SWING
  (a `sin(π·u)` arc with the knee forward via IK). Stride/duty/height scale with speed. There used to
  be a "replant by stretch" system that looked like spider legs — do not go back to that. `feetIK` runs
  ALSO with dt=0 (hitstop freeze): otherwise the legs snap to the raw FK pose.
- **The spring half-life table is the "looseness" dial** (`CFG.spr`): the striking limb drops to
  `hStrike=0.02 s` during the active frames (it converges to the frame data exactly when it lands);
  head and free hand run 1.4× slower (free follow-through).
- **Damping per channel** (`CFG.spr.z*`, `springToZ`): 1 = critical (arrives and stays); < 1 = the
  joint OVERSHOOTS the target and comes back. Overshoot = `exp(−zπ/√(1−z²))` of the distance travelled
  (0.62 ≈ 7 %, 0.55 ≈ 12 %). Only the head, the free hand and the limb in recovery use it; with z = 1
  the function falls into the usual fast path (no trigonometry).
- **The keytrack sampler interpolates PER CHANNEL** (`sampleMove`): for each joint it looks for the
  previous and the next key *that define it*. Before, it picked one global "next key", so adding a key
  for the head split the leg's segment — i.e. changed its trajectory, i.e. its hitbox. With independent
  channels you can author a kick's upper body without grazing the foot's arc. With the old data it
  gives identical results (every key defined all of its bound joints).
- **13 DOF** in a `Float64Array` (order in `J`), authored facing RIGHT; `facing` mirrors in the FK.
  Convention: chains "hang" (0 = down, dirDown), the torso points up. Knees: flexion = NEGATIVE values
  of `lLl/lRl`.

### Proportions: shoulders, neck and head (2026-09-21b)

The torso looked like it sat *below* the head. Measured over a 16-pose portrait: the shoulder was at
**0.23·CH** above the pelvis and the base of the head at **0.382·CH** → **0.152·CH of bare neck, 15 %
of the character's height**. On top of that the shirt closed to a POINT at shoulder height, so the arms
looked like they came out of the neck.

The gap was split across three small moves, because each one has its cost:

| | before | now | cost |
|---|---|---|---|
| `B.torso` | 0.30 | **0.31** | raises the shoulder ⇒ raises the punches' impact point |
| `B.neck` | 0.08 | **0.022** | — |
| `B.headR` | 0.10 | **0.108** | moves the head's hurtbox |
| `B.shoDrop` | 0.07 | **0.04** | raises the shoulder |
| shoulder above pelvis | 0.23 | **0.27** | |
| bare neck | 37 px | **16 px** | |

Three more fixes, all of them drawing:

1. **The shirt ends in a SHOULDER LINE** (`wSho = 0.088·CH`), not a point, with a conical silhouette
   (`wChest 0.068`, `wWaist 0.046`), the waist raised to the hip and **corners rounded with `arcTo`** —
   with sharp vertices the back shoulder came out pointed every time the torso leaned, because the
   width is perpendicular to the spine.
2. **The neck is drawn BEFORE the shirt.** Drawn after, its round cap bit into the neckline and left a
   smear of skin over the chest (visible across the 16 poses).
3. **The head pivots at the ATLAS**, not at the base of the neck (`fk()`). Before, the `head` DOF
   rotated neck+head from below with a 0.13·CH lever: looking down (crouching, taking a hit) the neck
   looked stretched diagonally. Now the neck follows the upper spine and only the skull rotates, with
   the `B.headR` lever. **With `head = 0` the point is identical** (the two segments are collinear), so
   there is no pose migration. The atlas is a DERIVED point in `drawStick` (it was not added to `P_`:
   neither `NP` nor the ragdoll changed).

**What it cost the combat** (measured, see below): the punches land **8-10 px higher** because the
shoulder went up; the **horizontal reach is identical** (≤ 0.79 px across the 11 moves, and that one is
the uppercut, which is vertical). The `lunge` was the only flat strike and it lost real reach against
crouchers (0.66 → 0.50 CH), so it now **sinks the hip by those same px during the strike**
(`MASK_PUNCH_DY`, `dy` authored across its 7 keys): the fist lands exactly where it used to, the arm
just as extended.

#### The ONLY thing the proportion change moved in the combat

The `probe_conecta.js` matrix, deterministic, 1430 cells, HEAD vs now: **21 different cells (8 gained,
13 lost) — 1.5 %**. One step of the matrix is 0.055 CH ≈ 13.5 px.

| strike | target | max reach (CH) |
|---|---|---|
| jab · cross · airpunch | crouching / low block | −0.055 |
| cross | standing | **+0.110** |
| hook | standing | **+0.055**; low block −0.110 |
| uppercut | crouching | same reach, an internal gap |
| lunge | high / low block | −0.055 |
| sweep | high block −0.055 · low block **+0.055** |
| spinkick | low block | **+0.055** |
| roundhouse · dropkick · airkick | all | **unchanged** |

The cause is not the fist but the **defender**: their head hurtbox dropped ~10 px with the new
proportions. That is also why rows for kicks whose contact is identical to the pixel move.
Compensating by growing `CFG.fight.hurtHead` by 8 % was evaluated and DISCARDED (it would raise the
radius by only 2.4 px and would enlarge the target in every other matchup).

**The combos did not change** (`probe_combo.js`, 4 chains × 16 distances): the same number of strikes
connected and the same total damage in every cell, except that three chains hold their high count ONE
step further out. Nothing lost.

### Blending between states (2026-09-21b)

`targetPose` used to jump **by as much as 2.37 rad in ONE frame** on a state change (measured over 18
scenarios: `idle→jump` 2.37 on `aRu`, `idle→dash` 2.01, `run→jump` 1.98, `skid→run` 1.95, `fall→idle`
1.90). The spring absorbs them, but a STEP in the target makes it start at maximum acceleration: that
is what felt like "it starts all at once".

`buildPose` now crosses the target with a `smoothstep` from the last pose of the previous state
(`CFG.anim.blendT = 0.075 s`): it arrives at the same place, in the same time, but with zero derivative
at the start and at the end. **Never during an attack** — there `targetPose` IS the frame data, and the
probe confirms 0.000 px of difference. Measured afterwards: **maximum 0.46 rad** (−81 %).

Two more things from the same batch:

- **Continuous `dirN`** in `runCycle`. It was ±1 and jumped from −1 to +1 when crossing `vx = 0`: on
  changing direction the torso flipped its lean all at once (and with it the arms, which are authored
  in world angle). Now it crosses zero continuously.
- **HITSTUN has its own pose** (`hurtPose`). It had no branch in `baseLoco`: it fell through to
  `idlePose()` and the only record of the hit was the flinch layer. The ARMS now tell the impact — and
  the arms are **not a hurtbox** (`hurtboxes()` uses the head, pelvis→neck and pelvis→feet), so it does
  not move a single pixel of damage box. HITSTUN also joined `IK_STATES` and **`SLIDE_STATES`**: before,
  the legs came out of pure FK and the feet travelled with the body while you were being pushed
  (measured 4.83 px/frame, the worst of all controllable states). It goes in the drag and not in the
  planting on purpose: nailing them with the body leaving IS the spider-leg stretch.

### Spine in two segments (2026-09-21)

The torso was ONE rigid pelvis→neck bone and that ran into everything: the body could not hunch (the
roll was never a ball — the pelvis→head distance was constant), the shoulders could not turn
independently of the hip, and there was nothing to counterbalance with. Now:

- A new point `P_.chest` (NP 13 → 14) at 42 % of the torso; `B.spineLo` + `B.spineUp` = `B.torso`, with
  the sum done by SUBTRACTION so it is exact.
- New DOF (NJ 11 → 13, **added at the end** so no existing index shifts):
  - `chest` = flexion of the upper segment. Head, shoulders and **both arms** hang from it, so rotating
    it turns the whole upper body while the hip stays still.
  - `dx` = lateral displacement of the pelvis (in CH, local space). The torso sways OVER the planted
    feet instead of dragging them.
- `J_LINEAR = [J.dy, J.dx]`: these are LENGTHS. In `springs` they are not wrapped with `wrapPi`.

**The property that made the migration safe**: with `chest = 0` and `dx = 0` the FK returns exactly the
same points as the single-bone version. Verified with the probe: **0.000 px across the 11 moves** before
touching any animation. Each pose was migrated afterwards, one at a time.

**Which DOF enters the strike chain** (see the golden-rule table above):

| DOF | punch | kick | why |
|---|---|---|---|
| `chest` | **bound** | free | moves the shoulder, and the arm hangs from the shoulder |
| `dx` | **bound** | **bound** | moves the pelvis, and both the shoulder AND the hip hang from it |

That is why the punches carry arm angles **re-solved by IK** at the contact key and at the pins: the
desired `chest` is chosen and the arm is recomputed so the hand lands in the SAME position relative to
the pelvis (`probe_retarget.js`, measured error 0.00000 px). The solution is analytic and forces the
natural elbow side —`l = +acos(...)`, which in this rig is always positive— because choosing the branch
by proximity **inverted the joint** (tested: the elbow jumped 12 px to the other side). Since the total
reach is fixed, advancing the shoulder forces the arm to shorten: hence the contact values are modest
(the arm ends at 96-98 % extension) and the large rotation lives in the wind-up and the recovery, which
are free zones.

**Trap of the per-channel sampler with `dx`**: defining it in the load and then not again until the
recovery makes it interpolate ACROSS the active window (and moves the strike 1:1). It has to stay
nailed at 0 at the contact key and at both pins. It cost 5-8 px of reach until it was caught.

**Hurtboxes**: `hurtboxes()` still uses the straight pelvis→neck capsule (it was not split in two so as
not to touch the combat). With the spine bent the chest leaves that line, but barely: measured 1.1-1.6
px in the defensive poses. What does matter is that the neck moves when the torso bends, so **the poses
in which you can be hit carry a bounded `chest`** (idle exactly 0, stance 0.06, block 0.07, crouch 0.09
→ the head shifts ≤ 7.8 px over a radius of 29). The expressive ones go all the way (ballRoll 0.95,
getup 0.34) because there you are either invulnerable or the body really is folded.

**Ragdoll**: `RAG_BONES` adds pelvis→chest and chest→neck, and the shoulders hang from the chest (just
as in the FK). The floor needs the new point's rest offset. The torso now bends on falling instead of
staying like a stick.

**Foot roll, with NO new DOF**: the foot used to be drawn always horizontal (planting was stamping a
seal). `footRoll()` in `drawStick` derives the angle from the shin and weighs it by how far the foot is
off the ground: planted = flat, in flight or kicking = pointed. Zero degrees of freedom, zero points.
Wrists and ankles were discarded as real DOF: with `cam.frac = 0.11` the figure is ~80 px on screen and
a hand is 4 px — at that scale the only thing that reads is the SILHOUETTE.
- **`ik2(bendDir)` gotcha**: with the canvas's y-down, rotating +θ is visually CLOCKWISE → for the knee
  to point forward you have to pass `-facing` (the legs in `feetIK` already do). Passing `facing` gives
  bird legs — it already happened and Franco spotted it immediately.
- **`ik2Blend` blends the TARGET, never the solved points.** The average of two valid poses is not a
  valid pose: interpolating elbow and hand between the FK and the IK solution stretches the bones
  (measured 89 % error in the arm on releasing the ledge in a climb). By blending the target, the chain
  is solved once and the lengths stay exact by construction.
- **Root motion of strikes/dash**: `lungeVel()` returns instantaneous VELOCITY — it is added in the
  integration (`x += (vx + rootVx)·dt`), **never** `vx +=` (it would accumulate and fly off; it already
  happened).
- **Verlet ragdoll** (13 particles, constraints with the rest taken on activation) only in KNOCKDOWN/KO;
  the floor projects with a rest offset PER PART (the head over its radius) — without that the body ends
  up flat.
- **Hitstop per entity**: `hitstopT` freezes the pair's `simDt`; the knockback is held in `pendKb` and
  applied on UNFREEZING.
- **Stun with decay + requested recoveries** (`CFG.fight.stun*`/`kd*`/`airTechT`): before, every hit
  RESET the stun to 100 %, so a 4-hit combo left the player 2.39 s unable to do anything (measured). Now:
  1. `stunDecay`/`stunFloor`: each successive hit of the same chain stuns less (the analogue of
     `jugScale` for damage). `hitChain`/`hitChainT` live on the DEFENDER.
  2. **Air tech** (`airTechT`): in LAUNCHED, jump/punch/kick gives control back. The knockback and the
     damage are untouched; what is shortened is the stretch with no way to react.
  3. **Ukemi on landing**: if you are asking for something as you touch the ground, you land ROLLING
     (0.38 s) instead of knockdown + getup (~0.6 s). A held button counts, as does a buffered one:
     mashing works.
  4. **Quick getup** (`kdQuickT`) and a **hard ceiling** (`kdMax`) in case the ragdoll does not settle.
  The AI holds direction in LAUNCHED/KNOCKDOWN, so it gets the ukemi and the quick getup: the cut is not
  only for the player. The air tech does belong to whoever presses a button.
  Measured: a 4-hit combo taken goes from **2.39 s → 2.15 s** passive, and **0.95 s** if you recover.
- **AI with honest perception**: it reads snapshots from `reactionMs` ago (never the current state);
  archetypes as rows of data (`ARCHS`); difficulty scales ONLY reaction/blocking/combo drop.

### Level generated from sections + navigation graph (2026-09-21)

**The level is built every round** (`buildLevel(seed)` in `startMatch`, and afterwards `bakeBg()` +
`bakeTerrain()` because the bakes are world-space). `ARENA` is an object that is **mutated**, not
replaced: all the rest of the game references it through `ARENA.surfs` / `.exit` / … and never noticed.

The variety does not come from throwing platforms around at random: there are **14 hand-authored
sections** plus the exit tower, and what varies is which ones come up, in what order, with what
parameters and whether they are mirrored. Six patterns were added to the original repertoire
(staircase, bridge, arch, pyramid, zigzag, balcony, columns, double route) in 2026-09-21b:
**solapadas** (two slabs that overlap in x: you pass under or over), **bifurcacion** (two branches that
leave the same landing and reconnect), **saltitos** (a chain of small platforms, linked jumps),
**islote** (a high platform with a single entrance), **pozo** (a compact sector: two walls of ledges
and a lid) and **voladizo** (asymmetric: one very long slab and a short stub above).

#### Solid blocks, split floor and finishes (2026-09-21c)

Franco: *"the levels all feel the same. the same number of enemies in all of them. the exit always in
the same place up a few platforms. 0 novel design in what surrounds the floor and the walls"*. He was
right on all three, and the third hid something worse: **the only walls in the game were the two edges
of the map** (every platform is `oneway`, you pass through them sideways), so wallslide, walljump and
hanging from a ledge almost never showed up.

**`ARENA.muros`** is the primitive that was missing: an AABB with real lateral collision whose top is
also registered in `surfs` as a NON-oneway surface. Out of that single primitive come plateaus (floor
relief), ramparts, chimneys, pillars and outcrops.

Four things had to be solved to make it work, all of them measured:

1. **Collision order.** Horizontal resolution came BEFORE landing, so on the first frame the feet
   dropped off a block's top the resolver read it as "I am inside" and ejected it **130 px sideways**
   before the platform loop could stand it up. The AI never climbed onto a block *at all*, at any
   height (0/6). With the right order: 6/6 up to 230 px.
2. **The floor splits into runs.** A block resting on the ground cuts it, and each run is a node of
   the graph. Without this the graph saw ALL the floor as a single node, never generated the route
   "left run → top → right run" and the AI just kept pushing the wall. Two blocks less than 0.95·CH
   apart are MERGED (otherwise you get a pit there is no way out of).
3. **`LVL.riseBloque = 228`, different from `LVL.riseMax = 267`.** Climbing onto a block's top is not
   the same as onto a floating slab: against the wall you cannot take a run-up or pass underneath.
   Measured with the 4 archetypes: **6/6 up to 230 px, 2/6 at 250, 0/6 from 270**.
4. **A safety net below the floor.** Since the floor splits, there is nothing underneath. A lateral
   shove (body separation, knockback) that puts someone inside a block makes them lose the surface,
   and the support check requires coming FROM ABOVE: they fell forever (measured: y = 184,686). They
   are now returned to the nearest terrain.

Two reflexes were added to the AI, neither of which touches the combat brain: **jumping the wall** in
front of it if its top is within the jump (the graph does not generate that route because the floor,
on the other side, is the same node) and **walljump** on entering WALLSLIDE — but only if the top is
OUT of reach, because if it is within reach, bouncing took it away from exactly where it wanted to
climb.

**Finishes**: the EXIT has four shapes (`torre` zigzag, `meseta` a solid mass with two accesses,
`chimenea` over a pit between two towers, `espiral` around a pillar) and it goes into **any slot** of
the sequence of runs, not at the end. Before, `tx` was always the right-hand end: measured, the exit
went from sitting at ~78 % of the width in every level to spreading between ~23 % and ~50 %. And the
gaps between runs carry **outcrops** (50 % probability): without those, between one section and the
next the floor is a straight line and the level reads flat however many floating platforms it has.

**Roster per level** (`plantelDeNivel`): the number of enemies comes from the stage and who shows up
(and with which archetype) from the seed. Measured: **4-6 / 5-7 / 6-8 / 7-9** per stage and 68
different archetype mixes across 192 levels. `game.totalEnem` replaces `enemies.length` in the HUD and
in the "CLEAR!" check.

**Generator trap**: a link's `tx` pointed at the CENTRE of the destination surface. With the floor
split that is still reasonable, but with the whole floor it was the centre of the map: the test flight
crossed the level and almost every section with blocks was rejected (and the AI, on landing on the
floor, walked towards the middle of the arena). It now points at the USEFUL point closest to the
take-off.

#### Difficulty stages (2026-09-21b)

`game.nivel` grows on reaching the EXIT (`siguienteNivel()`, heals 45 %) and the stage comes from
`etapaDe(nivel)` — **two levels per stage**. The difficulty is STRUCTURAL: it touches nobody's damage,
health, speed or brain.

| stage | levels | patterns | `wK` | `gap` | tower |
|---|---|---|---|---|---|
| INITIAL | 1-2 | 5 | 1.14 | 296-372 | 5 |
| INTERMEDIATE | 3-4 | 9 | 1.00 | 304-384 | 6 |
| ADVANCED | 5-6 | 13 | 0.90 | 312-396 | 7 |
| EXPERT | 7+ | 14 | 0.82 | 322-408 | 7 |

`wK` scales the width of each platform (floor 0.62·CH): the more advanced, the less surface to land on
and therefore the larger the effective gaps, **without moving a single jump**. Measured over 200 seeds
per stage: median width **297 → 275 → 252 → 231 px**.

**`secs` is NOT a lever**: the arena width (8000 px) cuts in before the counter does. With `secs = 7`
the generator truncated silently and EXPERT came out SHORTER than ADVANCED. It is set high on purpose
(8) so the level always fills the arena and its length does not depend on the stage.

**A section's total width is DERIVED** from its platforms (`max(dx + w)`), it is no longer authored by
hand: authoring it was the source of the odd overlaps when mirroring.

`buildLevel(seed, nivel)` is reproducible: same seed + same level ⇒ same geometry (verified 32/32,
dirtying the state between the two runs). `armarNivel(semilla)` and `startMatch(semilla)` take an
optional seed — that is what the QA uses.

**`NAV` is a graph over the surfaces** and TWO things use it:
1. The AI, to chase across heights.
2. The **generator, to validate**: if the exit is not reachable from the floor, if some platform cannot
   get back to the floor, or if some platform is an **island** (you can only fall onto it), the roll is
   discarded and another is generated. Measured: 0 failures of any kind across 300 levels.

The links come from the **real physics of the jump**, not from constants: `alcanceSubiendo(rise)`
solves for the instant the parabola comes back down through `rise` and multiplies it by the running
speed (≈ 390 px for a maximum jump, ≈ 540 at the same level). With the fixed `320` it had before,
**281 platforms across 300 levels ended up as islands**. The next-jump table is all-pairs by reverse
BFS, computed once per level (18 nodes, 324 entries, 0.20 ms): at runtime the AI does an O(1) lookup.

### AI navigation (`aiNavegar`)

It runs **before** DEFEND and returns `false` as soon as they share a surface: from there on the usual
combat brain is in charge, so **the archetypes fight exactly as before** (measured: TECHNICAL 19
punches/2 kicks, BRAWLER the one that gets closest at 0.32·CH).

- **The bug it fixes**: the aggro required `|Δy| < 2.2·CH` to latch on. With the player three platforms
  up, 0 of 4 enemies got there and **all 4 stood literally still**. The condition is now that A ROUTE
  EXISTS in the graph; the horizontal radius (3.2·CH) did not change, so each one still guards its zone.
- **PREDICTIVE jump**: there is no "jump when I am near a magic point". The real parabola is solved with
  the current velocity (and with the velocity it would gain accelerating in the air) and it jumps on the
  frame where the landing falls inside the destination platform. The versions with a fixed per-archetype
  anticipation failed 2 of 6 attempts and the result depended on the archetype; with the prediction it
  is 6/6 on all four, in ~4 s.
- **Dropping down**: if the destination is directly below and the platform is one-way, it holds DOWN +
  jump (drop-through); otherwise it walks until past the edge and lets itself fall.
- **A lane per enemy** (`br.navLane`), bounded by the overlap the destination can take: without it all
  nine aimed at the same take-off point, shoved each other with `separateBodies` and none of them got
  up. Without the cap, the lane shifted the take-off by up to 83 px and the jump never made it.
- **Anti-stall**: if it does not change surface in 2 s, it drops off wherever it is and rebuilds the
  route from the floor. It breaks any cycle of jumps.
- Measured cost: **0.3 µs/frame for all 9 enemies** (a frame at 60 fps is 16,700 µs).

> QA gotcha: `startMatch()` generates a RANDOM level. For a reproducible test the seed has to be fixed
> AFTER calling it, not before (it happened to me: I was comparing two builds over different levels).
> And standing on the EXIT platform completes the level and **freezes the AI** (`game.state` stops being
> `'play'`), so the chase scenarios use the highest one that is not that.
- `separateBodies`: minimum clinch 0.24·CH — shorter than usual because the uppercut only reaches
  0.17·CH forward; if you grow it, the uppercut of the P,P,P combo stops connecting.
- **Style**: palette in `PAPER/ROCK/INK` (p07). The background is TWO world-space bakes baked once:
  `bgCanvas` (leaf shadows, parallax 0.45) and `terrainCanvas` (rock+ink+scratches+EXIT door, parallax
  1). Nothing additive in the effects: over light paper the 'lighter' composite washes out to white.
- The speed cap is NOT drag-vs-accel: it only accelerates below `maxRun` (with a gentle drag above for
  the dash's run-out). With a weak drag the equilibrium sat 65 % above the cap.

## Headless QA (no node)

New probes from 2026-09-21b (all in the scratchpad, injected before `</body>`):

- **`probe_conecta.js`** — a DOES IT CONNECT? matrix of 11 strikes × 5 target states (standing,
  crouching, high block, low block, in the air) × 26 distances = 1430 cells. It is the only test that
  measures EFFECTIVE REACH instead of geometry. **Watch out for two traps that cost a whole run**: (a)
  the target has to be nailed at an ABSOLUTE x — re-anchoring it to `P1.x` makes it chase the attacker
  through the root motion and the distance lies; (b) `this.T` (the breathing clock) is born at
  `rnd(0, 9)`, so without fixing it the matrix is not reproducible **even against itself** (measured: 9
  different rows between two runs of the same build). With `P1.T` and `E.T` fixed: 0 rows.
- **`probe_continuidad.js`** — it measures rather than assumes: the jump in `targetPose` at each state
  change, jerk per joint, planted-foot skating PER STATE, pelvis-vs-support imbalance, torso
  articulation. A window of ~6 frames after each teleport of the test itself has to be discarded
  (`resetFighter` overwrites `poseCur` outright: without the filter the jerk and the skating measure
  nothing).
- **`probe_niveles.js`** — reproducibility, a sweep of 200 seeds × 4 stages, the repertoire of patterns
  per stage, AI chasing per stage and match progression (8 levels in a row).
- **`probe_humo.js`** — 6 minutes of real play with reproducible pseudo-random input: NaN, states
  outside the enum, hp out of range, fighters outside the world, feet above the pelvis.
- **`probe_huesos.js`** / **`probe_retrato.js`** — large portraits with and without the joints marked on
  top. Numbers are not enough to judge proportions: you have to look.
- **`ejes.py`** — decomposes a strike's change into AXES. `compare.py` measures `+REACH` **radially**
  from the root, so raising the hand 9 px gives it +5.5 px even though the horizontal reach does not
  change.


Chrome headless + `--virtual-time-budget` does NOT fire rAF in a sustained way: **the sim stays frozen
even though the timers run**. The loop is set up to be pumped by hand:

- `loop(t)` is global and `scheduleRaf()` has dedupe → an injected driver can call `loop(qaNow += 16.7)`
  from a `setInterval` without duplicating the rAF chain.
- Debug handle: `window.SF = {P1, P2, CFG, game, cam, MOVES, POSES, ST, simT}`; `SF.simT` is the
  accumulated simulation clock — schedule test actions by `simT`, not by real time.
- `dbgFreeze = true` freezes the sim (it keeps drawing) → an exact screenshot of the desired instant.
- The full pattern (error catcher + per-scenario driver + status dump): the `qa.py` harness from the
  2026-07-22/23 session; useful scenarios: menu/fight/run/skid/jump/jab/combo/kick/ko/hang/boxes.
- **`--virtual-time-budget` is not even needed**: `loop(t)` can be pumped SYNCHRONOUSLY in a `for`,
  which makes the scenarios deterministic and fast. The driver has to drive `keys` (the keyboard),
  **not** `inP1`: `pollInputs()` rewrites all of `inP1` every frame.
- Three harnesses from the animation session (2026-09-20), in the scratchpad:
  1. **move probe**: it reconstructs layer (b) of `buildPose` and samples the limb's trajectory every
     1 ms → it compares the exact frame data, the deviation inside the active window, the **one-sided
     Hausdorff of the swept capsule** and, the metric that really matters, **`+REACH`**: how much
     further from the root the new sweep gets. Positive = the strike reaches further (that really would
     be changing the reach); ≤0 = it only grew towards the body, which is harmless. It runs at 60 and
     30 Hz. It also measures the limb's **travel** and how much it folds in the wind-up, which is the
     number to look at when a strike "feels short".
  2. **simulation harness**: ~30 scripted scenarios with a per-frame validator (finiteness, bone
     lengths, foot above pelvis, foot far from the body, skating in stance, jerk, pelvis/feet imbalance,
     real tip-to-tip reach). It runs at 16.7 / 33.3 / 50 ms.
  3. **frame strips**: it reassigns the global `ctx` and calls `drawStick()` to paint N poses in a grid,
     and takes ONE screenshot. It is the only practical way to *see* an animation here.
- Careful when comparing runs: `Fighter` starts with `this.T = rnd(0, 9)` (breathing phase), so
  scenarios where a strike connects right at the limit give ±8 px of difference **between runs of the
  same build**. Before blaming a change, run the same build twice.
- Live debug keys: `T` tuning panel (sliders over `CFG`), `H` hit/hurtboxes, `G` slow motion, `Y` dump
  the pose to the console; a triple-tap in the menu version opens the panel on mobile.

## Gotchas

- All the game's DOM is declared BEFORE the main script (the TankWARSWeb gotcha); the tail script
  (info/FPS/mute) goes after `arcade-shell.js`.
- The context-loss trio invalidates `bgCanvas`, `skyGrad` and `_glowCache` — if you add a new bake, add
  it there too (the spark sprites keep the ref in the particle: they regenerate via a cache Map).
- The keytrack times (`poses[].at`) are ABSOLUTE within the move and the sampler starts from `atkPose0`
  (the real pose at the start of the strike) — a partial pose without a key "holds" the last defined
  value.


## AUDIO — fix (2026-09-22)

**Dying sounded exactly like winning.** `setBanner()` ended up calling `sfx.banner()`
unconditionally — the RISING celebration pair — and `onKO` uses `setBanner` to announce the player's
death (`'YOU WENT DOWN…'`).

`setBanner` now takes a fifth parameter `snd` holding the banner's voice. It still defaults to
`sfx.banner`, which is what a banner almost always means; death passes `sfx.ko`. Measured: the
normal banner gives `square` 373 → 529 Hz (rising), the death one gives `sawtooth` 378 + `square`
206 at gain 0.1 (falling).
