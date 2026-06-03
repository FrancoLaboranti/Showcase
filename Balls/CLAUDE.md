# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Physics sandbox: bouncing marbles with gravity, mass-weighted ball-ball collisions, four synthesised impact voices (glass / wood / rubber / pop), and a baked-sphere lighting effect with multiple pattern styles. Runs **exclusive fullscreen at the monitor's native resolution** (`pygame.display.set_mode((0,0), pygame.FULLSCREEN)`), so `screenX`/`screenY` are whatever the display reports — don't hardcode 750×750 or 1280×720.

Follows the repo skeleton loosely (`Sprite`, `xper/yper/sper`, `createText`, `randColorInRange`, `getAngle`/`getDist`/`getAngleForAngVel`), but **physics is pymunk-owned**: each `Ball` carries a `pymunk.Body` + `pymunk.Circle`, integration / broadphase / sequential-impulse solver / island sleeping / contact persistence all live inside `space.step()`. `self.x`/`self.y`/`self.vx`/`self.vy` are properties that read through to `body.position` / `body.velocity` so the rendering and debug overlay still look "skeleton-shaped".

The previous hand-rolled physics engine (~400 lines of impulse resolver + spatial hash + sleep state machine + BFS support-cone wake check) is preserved verbatim at [handrolled/Balls.py](handrolled/Balls.py) for reference. Treat it as historical.

## Tuning knobs

The top of [Balls.py](Balls.py) is a block of named constants — that's the intended editing surface. After the pymunk migration the physics block collapsed to gravity / restitution / friction / damping / sleep, with restitution split into ball-ball and ball-wall (overridden per-pair in `pre_solve` because pymunk's default elasticity combining is multiplicative — `0.3·0.3 = 0.09` would feel dead). Most other knobs are visuals / sound / grab feel. `SAMPLE_RATE` is the one constant **not** safe to change at runtime — it would invalidate every pre-baked sound buffer.

## Controls

| Input | Action |
|---|---|
| LMB held | Grab + throw. Passing the cursor over any ball while LMB is held grabs it (one ball at a time). On release the ball leaves with the filtered cursor velocity (`mouseVx/Vy`) and the spin that was being computed each frame. See [Grab mechanic](#grab-mechanic) below. |
| RMB (rising edge) | Flappy-bird jump: every non-grabbed, non-removing ball gets `vy = -JUMP_VELOCITY` and is woken from sleep (`body.activate()`). |
| Wheel up | Spawn a ball (capped at `MAX_BALLS`). |
| Wheel down | Mark the most-recent-but-not-first **non-grabbed** ball as `removing` (shrink animation). The grabbed ball is explicitly skipped so its radius can't collapse mid-grab and crash the glow allocation. |
| `Q` (rising edge) | Pin the currently-grabbed ball in place (nail in the air). See [Q-pin](#q-pin). |
| `R` (rising edge) | Respawn: clear all balls and spawn the same count again with freshly randomized colors/sizes/styles/voices. Resets `Ball._nextId`. |
| `SPACE` (held) | Global debug overlay (mouse pos/velocity/speed, ball count, mouse-velocity vector). Per-ball stats for ball id=1, plus a brighter halo around id=1 to spot it. **Top-10 speed bar chart** under the mouse panel: ranks the 10 fastest balls each frame, bar fill = ball's own color, sleeper labels go gray + `zZz`. |
| `F` (toggle) | FPS overlay. |
| `1` / `2` / `3` | Switch `WALL_MODE` (rebuilds wall segments). |
| `ESC` | Quit. |

## Physics — pymunk space

Single `pymunk.Space` configured up-front:

- `space.gravity = (0, GRAVITY)` — y-down, matches pygame screen coordinates.
- `space.damping = AIR_DAMPING` — per-second velocity multiplier; replaces the old `AIR_FRICTION`.
- `space.iterations = SOLVER_ITERATIONS` — solver passes per step.
- `space.sleep_time_threshold = SLEEP_DELAY`, `space.idle_speed_threshold = IDLE_SPEED` — island-based sleeping. **This single knob replaces the entire hand-rolled sleep state machine** (BFS support cone, position/velocity OR gate, settle damp, micro-bounce threshold). pymunk groups bodies into connected islands via persistent contacts and puts whole islands to sleep when their per-body speed stays below `idle_speed_threshold` for `sleep_time_threshold` seconds.

Each frame the main loop substeps physics `PHYSICS_SUBSTEPS` times (`subDt = deltaT / PHYSICS_SUBSTEPS`). Substepping has two roles: tunneling mitigation (smaller per-step displacement → fewer fast-moving balls jumping through walls or other balls) and tighter contact resolution in dense piles. Tunneling threshold for walls is `2·(WALL_THICKNESS + ball_radius) / subDt`; with `WALL_THICKNESS=2` and substeps=3, balls up to ~95 px radius are safe up to ~34900 px/s. The `GRAB_MAX_SPEED` cap on grabbed-ball velocity stays well below that.

All bodies are **always DYNAMIC** — grabbed and pinned balls are flagged but never toggled to KINEMATIC. (KINEMATIC↔DYNAMIC wipes mass/moment, which then requires re-setting them before the next `step()` or pymunk asserts. Sidestepped by overriding `body.velocity` / `body.position` directly each frame instead.) Mass is `targetRadius²` (2D area proxy); moment from `pymunk.moment_for_circle`. `float('inf')` moment is rejected by `space.step()`, so balls always have finite rotational inertia and roll under friction.

### Collision callbacks

Shapes carry `collision_type` tags (`COLLISION_TYPE_BALL = 1`, `COLLISION_TYPE_WALL = 2`) and `space.on_collision(...)` routes pre/post-solve callbacks per pair-type:

- **`pre_solve`** (`_ballBallPreSolve`, `_ballWallPreSolve`) sets `arbiter.restitution` explicitly per pair-type so the solver uses our exact value (`BALL_BALL_RESTITUTION = 0.3`, `BALL_WALL_RESTITUTION = 0.65`) instead of the multiplicative default.
- **`post_solve`** (`_ballBallPostSolve`, `_ballWallPostSolve`) queues impact sounds, gated by `arbiter.is_first_contact` — otherwise sustained pile contacts spam sound every frame. Impact speed is reconstructed from `arbiter.total_impulse` via `_vRelN_from_impulse(arbiter, inv_m_sum, e)` so the sound intensity matches the actual bounce energy.

Each shape has a `ball_ref` back-pointer to its `Ball` so callbacks can find pitch / voice / grabbed state.

## WALL_MODE

Three modes selected by `1`/`2`/`3` keys, rebuilt via `buildWalls()`:

1. All four walls bounce (default).
2. Sides wrap, top/floor bounce.
3. No walls — wrap in both axes.

Walls are `pymunk.Segment` capsules of radius `WALL_THICKNESS=2` sitting **just outside the screen**, so the collision face lines up exactly with the screen edge (e.g. left wall capsule from `x=-2t` to `x=0`, face at `x=0`). Wrap teleporting happens in `Ball.process()` step 6 — pymunk has no native wrapping.

`buildWalls()` removes the previous walls by walking `space.shapes` and filtering on `collision_type == COLLISION_TYPE_WALL`, then adds the segments for the new mode. **Don't go back to the older `for s in _wallShapes: if s in space.shapes: space.remove(s)` pattern** — that guard was unreliable and left phantom side-walls active after switching to MODE 2 (balls kept bouncing off invisible left/right walls).

### EDGE_MARGIN dead-zone

`EDGE_MARGIN = 4` is an **interior strip of pixels** treated as outside-the-zone for cursor purposes. Two roles, drawn from the same constant:

- Cursor inside the strip counts as "outside the playable zone" — gates the grab condition (no new grab) and triggers auto-release of any currently-grabbed ball. This exists because pygame on Windows clamps `pygame.mouse.get_pos()` to the window frame, so `mouseX < 0` almost never fires when the user flings toward the edge. Without `EDGE_MARGIN` the auto-release would have nothing to trigger on.
- Drawn each frame as `EDGE_MARGIN`-thick rectangles over the same strip (the visible walls). What you SEE as wall is exactly the dead zone for the cursor.

The physics walls themselves are still 2 px capsules at the actual screen edge; only the cursor logic and visual marker live in the EDGE_MARGIN band.

## Grab mechanic

Single grabbed ball at a time. Behaviour is layered in `Ball.process` (steps 3-4):

**Grab condition** — `mouseLeft AND cursorInZone AND not self.grabbed AND not self.pinned AND cursor inside this ball's radius AND no other ball is grabbed`. Click offset (`_grabOffsetX/Y`) is recorded at grab time so the grip-point on the ball stays glued to the cursor instead of the center snapping to it (prevents the ~radius/dt = 3000 px/s shove against neighbours that grabbing near an edge would otherwise generate).

**Velocity-chase while grabbed** — every frame, compute `target = mouseX - _grabOffsetX`, `dx = target - body.position`, `vx = dx / dt`, cap by `GRAB_MAX_SPEED`, assign `body.velocity = (vx, vy)`. The ball stays DYNAMIC so it collides naturally with walls/other balls. If the chase target is blocked, the ball stays put and natural impulses push the obstacles.

**Pending angular velocity** — the spin the chase would impart (`±|v|/radius`, sign from the dominant component) is computed every frame and stored in `self._pendingAngularVelocity` BUT not applied to the body. `body.angular_velocity = 0` while grabbed, so the pattern stays still under the cursor. The stored spin is committed in `release()` or in the auto-release branch — the ball leaves the hand already rolling.

**Auto-release when cursor enters EDGE_MARGIN dead-zone** — the grabbed ball is released with `body.velocity = (mouseVx, mouseVy)` (filtered cursor velocity from the low-pass with time constant `MOUSE_SMOOTH_TC=0.04`) instead of the chase-derived `(target-position)/dt`. Why: if the ball was sitting clamped against a wall while the cursor moved, the position/target gap doesn't reflect the gesture speed — the chase value would launch the ball way faster than the actual cursor velocity. Using `mouseVx/Vy` keeps the throw speed proportional to what the user actually did.

**Manual release on LMB up** — same `(mouseVx, mouseVy)` + `_pendingAngularVelocity` pattern, in `Ball.release()`. Not the body's current velocity, because if the cursor was stationary at the moment of release or the ball had already converged onto the cursor, `body.velocity` could be ~0 and the ball would drop without a throw.

The grab and auto-release use the **same** `cursorInZone` / `cursorOutsideZone` criterion (cursor position vs EDGE_MARGIN), so they're symmetric: grab is allowed iff cursor in zone, auto-release fires iff it leaves. Re-grab after auto-release is allowed inside the same LMB hold — just bring the cursor back into the zone, same ball or any other. No global or per-ball latches; just the symmetric zone gate.

### Q-pin

`pin()` flags the ball as `pinned`, captures `_pinPos = current position`, zeroes velocity. While pinned, `Ball.process` step 5 overwrites `body.position = _pinPos`, `body.velocity = (0,0)`, `body.angular_velocity = 0` every frame. The body stays DYNAMIC, so collision resolution still applies impulses on it — but our overwrite snaps it back next frame. Visually rock-solid; rough edge is that the snap-back happens at the python frame, not within physics substeps. Pinned ball is released by a fresh grab.

## Rendering — baked sphere

Each `Ball` has a cached `_sphereSurf` (Surface) built lazily by `_bakeSphere` once the ball reaches `targetRadius`. Drawing a grown ball is then a single `blit` of the pre-rendered 100-layer gradient (+ optional pattern overlay + hotspot + 1-px silhouette rim). **While growing or shrinking**, the ball falls back to the slow per-frame 12-layer draw, but only briefly (controlled by `GROWTH_RATE`).

The sphere is rotated to match the body's physics rotation: `pygame.transform.rotate(sphereSurf, -math.degrees(body.angle))`. The negation is intentional — pymunk's `body.angle` follows the math convention (positive = CCW in y-up), but in y-down screen space that visually means clockwise, and `pygame.transform.rotate` takes CCW degrees. Hotspot and light direction rotate with the pattern (not strictly correct for a sphere lit from a fixed external source, but reads as a stamped rolling ball — cheap and convincing).

The gradient currently uses `tint = 0.45 + 1.20·t` for high contrast: deep shadow (45% of base) on one side, blown-out highlight on the lit side. The light direction is baked into the sphere at `(lx, ly) = (0.35, -0.94)` — upper-right.

Other rendering touches:
- A tiny **specular hotspot** (`_drawHotspot`) is drawn on every style (solid white core + two translucent halos for a wet/glossy candy sheen).
- A **1-pixel low-alpha white rim** runs around every silhouette so balls don't blur into the black background.
- Grabbed balls (and ball id=1 while `SPACE` is held) get a **soft outward glow ring** at `1.10 × radius` in a brightened version of the base color, alpha-blended from outer (≈90) to inner (≈220).

### Ball styles

Each ball is randomly assigned a `style` in `__init__`:

| % | Style | Pattern |
|--:|---|---|
| 5% | `striped_flat` | Flat parallel bands. `_makeStripeMaskFlat` (oversized rotation buffer → rotate → centre-crop). |
| 5% | `striped_sphere` | Curved meridians wrapping the sphere. `_makeStripeMaskSphere` scan-lines per `y`, mapping bands to `x = sin(φ) · √(R² − y²)`. Accepts `fillRatio` (50% default). |
| 5% | `striped_spiral` | **Double** candy-cane spiral pole-to-pole — two strands 180° apart in longitude. Chain of overlapping circles along each path; thickness shrinks with `cos(lat)·cos(lon)` toward the silhouette. |
| 5% | `striped_diamond` | Two meridian sets crossed at 60° → diamond lattice. Reuses `_makeStripeMaskSphere` twice with `fillRatio=0.18` so gaps stay visible. |
| 5% | `striped_pinwheel` | Peppermint swirl — N bands spiraling out from the front-center. 2D polar (`phase = θ + twist · r/R · 2π`); run-length scan per row. |
| 10% | `dotted_sphere` | Center dot + ring of dots foreshortened by `cos θ` (θ ≈ 50° from the front pole). Ring dots shrink with depth. |
| 10% | `dotted_candy` | Scattered mixed-size dots, light kiss-overlap allowed. Paired with a tinted overlay color for the gumball look. |
| 10% | `dotted_hex` | Tight hex grid filling the disk, alternating two dot sizes in a checkerboard with per-ball randomized parity. |
| 45% | `plain` | Pure gradient sphere, no overlay. |

### Overlay color

For patterned styles, `__init__` picks an `overlayColor`:
- `dotted_candy` → tinted lighter shade of base (`color × 1.8`, clamped).
- All others → 60% white, 25% silkscreen-dark (`color × 0.30`), 15% complementary hue (HSV `hue + 0.5`).

Pattern overlays work by rendering a second copy of the gradient sphere in `overlayColor`, multiplying it (`BLEND_RGBA_MULT`) by the stripe/dot mask, then blitting on top of the coloured sphere. This keeps the lighting consistent.

### Dot rim

For dotted styles with a **dim overlay** (max channel < 200 — i.e., silkscreen-dark only), an alpha-blended dark rim is drawn around each dot (positions returned by the mask functions). Bright overlays (white / complementary / candy-tint) skip the rim because they already pop and a dark rim would clash. Implemented via a temporary SRCALPHA layer, `(0, 0, 0, 70)` low-alpha black, ring thickness `max(1, dotR · 0.07)`.

## Sound system

Four synthesised "voice" types, each pre-rendered into 12 pitch slots (frequencies 510–1430 Hz, bass-heavy). All buffers are built at startup via `struct.pack_into` into `bytearray`s, then wrapped as `pygame.mixer.Sound`. Total: 48 pre-baked buffers (~380 KB).

| Voice | Character | Generator |
|---|---|---|
| `marble` | Glass-on-ceramic (original "campana") | Inharmonic partials `(1, 2.05, 3.42, 5.6)` + 4 ms noise transient. |
| `wood` | Hollow "tok" knock | Two near-harmonic partials, very fast decay, 10 ms noise attack. |
| `rubber` | Cartoon boing | Pitch sweep from 1.9× → 0.55× via phase integration, smooth attack, long decay. |
| `pop` | Snap with body | Noisy attack (~12 ms) + two-partial pitched ring (fundamental + octave). |

Per-ball voice is drawn with weighted random: 30% marble / 30% wood / 10% rubber / 30% pop. Rubber is kept rare because its pitch sweep is the most distinctive — making it common would feel chaotic.

### Pitch assignment

Each ball's `soundIdx` is fixed at construction by its size (smaller → higher pitch). For ball-ball collisions, the **smaller** ball's pitch AND voice both win (`max(self.soundIdx, ball.soundIdx)` decides; if tied, `self` wins).

### Per-impact pitch jitter

`PITCH_JITTER` (currently 2 slots) shifts the natural `soundIdx` by `±PITCH_JITTER` on every hit, so the same ball doesn't sound identical on every collision. Applied inside `_playImpact` so it affects both wall and ball-ball hits uniformly.

### Per-frame queue + filter

Impact playback is decoupled from generation:

1. `_playImpact(intensity, voiceType, soundIdx, minVel)` filters sub-threshold impacts (different `minVel` for free vs grabbed) and appends `(intensity, voiceType, soundIdx)` to `_impactQueue`. The `Sound` object is looked up at flush time, not stored.
2. After the sprite loop + physics substeps, `_flushImpacts()` runs with a binary switch based on ball count:
   - **`len(sprites) < SOUND_FILTER_THRESHOLD`** (currently < 2 balls): no cooldown, no cap, play everything queued. This is the "single ball bouncing in a corner clicks twice" path.
   - **Otherwise**: apply the global `IMPACT_COOLDOWN` and pick `MAX_SOUNDS_PER_FRAME` via weighted random: `weight = intensity · (1 + PITCH_PRIORITY_BIAS · (1 − pitchNorm))`. Bass-heavy bias so big-ball thuds aren't drowned by small-ball swarms; using `random.choices` instead of a deterministic sort lets treble leak through occasionally for variety.

Two velocity thresholds for the impact filter: `IMPACT_MIN_VEL` for free balls, `IMPACT_MIN_VEL_GRABBED` (higher) when either participant is grabbed — mouse-driven velocities spike easily and would otherwise trigger constant clicks.

## Mixer init

`pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 256)` runs **before** `pygame.init()`. The order matters and the 256-sample buffer is intentionally small to keep latency low for impact responsiveness — raising it will make sounds feel laggy.

See [../CLAUDE.md](../CLAUDE.md) for the shared sprite/main-loop conventions this file partially follows.
