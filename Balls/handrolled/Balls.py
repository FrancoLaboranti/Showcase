import math
import time
import random
import struct
import colorsys
import pygame, sys
import pygame.freetype
import pygame.gfxdraw
from pygame.locals import *


# --- Tuning knobs --------------------------------------------------------------

BALL_RADIUS_MIN    = 0.025    # smallest ball radius as a fraction of (screenX+screenY)/2 (passed through sper()).
                              # ↑ all balls bigger · ↓ wider size variation (smaller minimum)

BALL_RADIUS_MAX    = 0.06     # largest ball radius. Bigger balls = heavier (mass ∝ radius²) and lower pitch.
                              # ↑ more dramatic size/mass variation · ↓ more uniform size

GRAVITY            = 3000.0   # px/s² downward acceleration.
                              # ↑ fast fall, heavy feel · ↓ floaty / lunar · 0 = no gravity

JUMP_VELOCITY      = 2400.0   # px/s — upward impulse given to every ball on each mouse click (flappy-bird-style hop).
                              # ↑ higher jumps · ↓ smaller hops · 0 = no jump on click

BALL_RESTITUTION   = 0.3      # ball↔ball elasticity (0 = sticky · 1 = perfect elastic).
                              # ↑→1 balls bounce off each other hard · ↓→0 they absorb energy and clump

GRABBED_MASS_MULTIPLIER = 3   # how much heavier the grabbed ball is treated than its normal mass (used in collision math).
                              # finite (not infinite) → other balls still feel a strong impulse, but the response stays proportional and physical.
                              # ↑ approaches "godlike" immovable behavior · ↓ grabbed ball just feels a bit heavier than normal

SIDE_BOUNCE        = 0.7      # energy retained when hitting the side walls.
                              # ↑→1 near-perfect bounce · ↓→0 dies against the wall

TOP_BOUNCE         = 1        # same for the ceiling.
                              # ↑ rebounds hard downward · ↓ gets "absorbed" by the ceiling

FLOOR_BOUNCE       = 0.6      # same for the floor (this is what makes falling balls bounce back up).
                              # ↑ super-bouncy ball · ↓ dead drop (no bounce)

AIR_FRICTION       = 0.6      # per-second velocity multiplier (0.6 = loses 40 %/s in the air).
                              # ↑→1 no friction (perpetual motion) · ↓ thick air (balls slow down fast)

FLOOR_FRICTION     = 0.4      # extra per-second multiplier on vx when touching the floor.
                              # ↑→1 slippery floor (balls keep sliding) · ↓→0 rough floor (instant stop)

FRICTION_MASS_SENSITIVITY = 1 # how much size affects friction. 0 = no mass effect (all balls move alike), 1 = inverse-mass scaling, >1 = exaggerated.
                              # heavier balls hold their momentum longer; smaller balls slow down faster.
                              # ↑ more dramatic size-vs-speed contrast · ↓ all balls move more uniformly

GROWTH_RATE        = 500      # px/s — radius growth when spawning (and shrink when removing).
                              # ↑ balls fade in/out fast · ↓ slow animation

MAX_BALLS          = 100      # upper bound for scroll-up spawns.
                              # ↑ more possible chaos (may hurt fps) · ↓ fewer balls

MOUSE_SMOOTH_TC    = 0.04     # time constant (sec) of the mouse-velocity low-pass filter.
                              # ↑ more smoothing: steadier throws but laggy · ↓ more reactive but noisy

REST_VX_THRESHOLD  = 1.5      # |vx| below this snaps to 0 each frame (kills residual sliding after friction has nearly stopped a ball).
                              # ↑ balls settle sooner (stop sliding) · ↓ they keep sliding longer

REST_VY_THRESHOLD  = 60.0     # |vy| at the floor below this snaps to 0 each frame (kills micro-bounces).
                              # ↑ cuts off micro-bounces sooner (fast settle) · ↓ they keep doing tiny hops

SLEEP_POS_THRESHOLD = 1.5     # max |Δposition| per frame (px) for the POSITION arm of the sleep gate. Catches well-packed piles where balls have stable positions even if velocity is non-trivial.
                              # ↑ sleeps faster but may freeze slow-drifting balls · ↓ stricter "must be perfectly still" gate

SLEEP_VX_THRESHOLD = 50.0     # |vx| considered "near rest" for the VELOCITY arm of the sleep gate. ORed with the position check — if a ball can't reach a position-stable configuration (e.g. wedged in a tight overlap where the collision passes can't fully separate everyone) but its velocity is low, let it sleep anyway. Accepts the residual overlap as a last resort, stops the endless iteration trying to find a perfect gap.
                              # ↑ sleeps more aggressively when crammed · ↓ stricter
SLEEP_VY_THRESHOLD = 100.0    # same idea on vy. Generous because in a pile, vy oscillates ~0-50 from the per-frame gravity-then-snap cycle even when fully settled.
                              # ↑ sleeps faster while still falling slightly · ↓ stricter

# Sound
SAMPLE_RATE        = 22050    # Hz, mono 16-bit. Don't touch — would force regenerating every buffer.

IMPACT_VOL_SCALE   = 1500     # impact speed (px/s) that maps to full volume.
                              # ↑ everything quieter for the same impact · ↓ same impact sounds louder

IMPACT_MIN_VEL     = 500      # velocity threshold below which no sound plays (free balls).
                              # ↑ more silence (filters soft impacts) · ↓ even tiny taps play (click-spam)

IMPACT_MIN_VEL_GRABBED = 800  # separate, higher threshold when a grabbed ball is involved.
                              # mouse-driven velocities can spike easily; raise this if dragging triggers too many sounds.
                              # ↑ only hard slams sound · ↓ even slow drags trigger sounds

MAX_SOUNDS_PER_FRAME = 1      # hard cap on how many impact sounds can play in a single frame.
                              # impacts are collected during the frame, sorted by intensity, only the top N actually play.
                              # ↑ richer chaos (closer to "everything plays") · ↓ cleaner, only the loudest survive

IMPACT_COOLDOWN    = 0.08     # seconds — minimum time between any two impact sounds (global rate-limit).
                              # impacts queued during the cooldown window are dropped entirely.
                              # ↑ sparser, calmer audio · ↓ more frequent (closer to original busy-ness) · 0 = no rate-limit

PITCH_PRIORITY_BIAS = 4.0     # how strongly low-pitched impacts outweigh high-pitched ones in the random pick.
                              # weight(impact) = intensity · (1 + bias · (1 − pitchNorm)), so with bias=4 a bass hit is 5× as likely as a treble hit of equal intensity.
                              # ↑ even more bass dominance · ↓ closer to uniform random (more highs leak through)

PITCH_JITTER       = 2        # per-impact pitch variation in slot units (each ball's natural soundIdx is shifted by ±this on every hit).
                              # keeps the "size → pitch" correlation while preventing the same ball from sounding identical on every hit.
                              # ↑ more chaotic / less size-correlated · ↓ 0 = strict size mapping (old behavior, monotonous)

SOUND_FILTER_THRESHOLD = 2    # ball count at or above which the full IMPACT_COOLDOWN + MAX_SOUNDS_PER_FRAME limits apply (binary switch, no ramp).
                              # below this count, every queued impact plays (so a single ball bouncing in a corner can click twice).
                              # ↑ stay unfiltered with more balls on screen · ↓ start clamping sooner (2 = clamp as soon as there's any second ball)

COLLISION_ITERATIONS = 2      # number of collision-resolution passes per frame (1 full + N-1 position-only).
                              # the first pass applies impulse + sound + positional correction; the rest just push overlapping pairs apart.
                              # ↑ tighter pile separation (less visible overlap, more CPU) · ↓ cheaper but stacks compress visibly · 1 = old single-pass behavior

SLEEP_DELAY        = 1        # seconds of position-stability (|Δpos|<SLEEP_POS_THRESHOLD per frame, supported) before a ball is put to sleep.
                              # sleeping balls skip gravity, integration, walls, friction → big perf win on settled piles + no jitter.
                              # they wake up on grab, on a meaningful impulse (|vRelN| > MICRO_BOUNCE_THRESHOLD), and on the right-click jump.
                              # ↑ longer settling delay before sleeping (more chance of jitter, more frames of work) · ↓ sleep faster · 0 = effectively always asleep when at rest

SETTLE_DAMP        = 0.08     # velocity multiplier per second while a ball is in the sleep-accumulation phase (restTime > 0). UNIFORM (not mass-scaled) on purpose: it specifically corrects for big balls — under normal mass-scaled friction they carry more residual vx/vy into the sleep snap, so the snap from non-zero velocity to zero looks abrupt on them. Aggressive decay here (~98%/s loss) brings every ball's velocity near 0 BEFORE the snap, so the transition into sleep is smooth regardless of size.
                              # ↑→1 less settle damping (snap-to-zero feels harder, especially on big balls) · ↓→0 more aggressive (velocity essentially gone by the time sleep activates)

MICRO_BOUNCE_THRESHOLD = 500  # |relative-normal-velocity| (px/s) below which a collision uses restitution = 0 (no bounce, just stop).
                              # also doubles as the wake threshold: sub-micro impulses on a sleeping ball don't wake it.
                              # kills the infinite micro-bounce in gravity-fed piles (each frame gravity adds ~30 px/s; without this cap the residual bounce keeps balls jittering forever).
                              # ↑ more collisions treated as "soft" (faster settling, but real bounces start losing energy) · ↓ closer to elastic everywhere (piles jitter)
# ------------------------------------------------------------------------------


class Sprite:
    def process(self):
        pass
    def draw(self):
        pass


class Ball(Sprite):
    _nextId = 1                                                                    # class-level counter — first ball gets id=1, second gets id=2, etc.

    def __init__(self):
        self.id = Ball._nextId
        Ball._nextId += 1
        self.targetRadius = sper(random.uniform(BALL_RADIUS_MIN, BALL_RADIUS_MAX)) # final size, randomized per ball
        self.radius = sper(0.001)
        self.x = random.uniform(xper(0.05), xper(0.95))
        self.y = random.uniform(yper(0.05), yper(0.6))
        self.vx = 0.0
        self.vy = 0.0
        self.grabbed = False
        self.removing = False
        self.sleeping = False                                                      # asleep balls skip process work (gravity / integration / walls / friction). Set true after `restTime ≥ SLEEP_DELAY`; cleared on grab, on meaningful impact, on jump.
        self.pinned = False                                                        # "nailed in the air" via Q while grabbed. Like sleeping but acts as static (effectively infinite mass) in collisions and is NOT woken by impacts — only by being grabbed again.
        self.restTime = 0.0                                                        # accumulated time the ball's per-frame displacement has stayed below SLEEP_POS_THRESHOLD (resets on any meaningful motion)
        self._prevX = self.x                                                       # position at the END of the previous frame (post-collision). Compared to current x/y after collisions to compute true per-frame displacement for the position-based sleep gate.
        self._prevY = self.y
        self._inContact = False                                                    # set true each frame inside collision passes whenever another ball is actually overlapping/touching this one. Used as the "is supported" gate for sleeping: a ball won't fall asleep mid-air, and a sleeping ball whose support vanishes is woken.
        self._wallContact = [False, False, False, False]                           # left, right, top, bottom — last-frame contact state (suppresses repeat sounds while dragging along a wall)
        self.mass = self.targetRadius * self.targetRadius                          # mass ∝ area (2D); bigger ball wins more momentum in collisions
        self._sphereSurf = None                                                    # cached baked sphere (gradient + hotspot) — built once when fully grown
        hue = random.random()                                                       # store hue separately so we can build a complementary overlay later (hue + 0.5)
        rH, gH, bH = colorsys.hsv_to_rgb(hue,                                       # vivid color: full hue range, near-max saturation + value (kept tight to 1.0 so balls never look washed-out)
                                          random.uniform(0.95, 1.0),
                                          random.uniform(0.95, 1.0))
        self.color = (int(rH * 255), int(gH * 255), int(bH * 255))
        sizeMin, sizeMax = sper(BALL_RADIUS_MIN), sper(BALL_RADIUS_MAX)            # pitch ↔ size: smaller ball → higher idx in the pool → higher pitch
        sizeNorm = (self.targetRadius - sizeMin) / max(1e-6, sizeMax - sizeMin)    # 0 (smallest) → 1 (largest)
        self.soundIdx = max(0, min(N_PITCH_SLOTS - 1, int(round((1 - sizeNorm) * (N_PITCH_SLOTS - 1)))))
        self.voiceType = random.choices(('marble', 'wood', 'rubber', 'pop'),       # rubber is rarer (it's the most distinctive boing) — keep it at 10% so it pops in occasionally
                                        weights=(30, 30, 10, 30))[0]
        refMass = sper((BALL_RADIUS_MIN + BALL_RADIUS_MAX) * 0.5) ** 2             # mass of an "average" ball — used as the friction baseline
        self._frictionScale = (refMass / self.mass) ** FRICTION_MASS_SENSITIVITY   # >1 for small (more friction) · <1 for big (more inertia)
        styleRoll = random.random()                                                # 5% each striped variant (flat / sphere / spiral / diamond / pinwheel), 10% each dotted variant (sphere / candy / hex), 45% plain
        if styleRoll < 0.05:
            self.style = 'striped_flat'                                            # flat parallel rectangles (no spherical projection)
            self.styleAngle = random.uniform(0, math.pi)                           # rotation per ball → no two striped balls align identically
            self.styleNStripes = random.randint(3, 7)                              # always at least 3 visible stripes
        elif styleRoll < 0.10:
            self.style = 'striped_sphere'                                          # curved meridians (longitude bands) — bands narrow toward the silhouette
            self.styleAngle = random.uniform(0, math.pi)                           # rotation defines where the "poles" of the meridian pattern land
            self.styleNStripes = random.randint(3, 7)
        elif styleRoll < 0.15:
            self.style = 'striped_spiral'                                          # single spiral stripe (candy-cane), pole-to-pole
            self.styleAngle = random.uniform(0, 2 * math.pi)                       # rotation: where the spiral's "poles" land
            self.styleNStripes = random.randint(3, 6)                              # repurposed: number of full turns the spiral makes
            self.styleHanded   = random.choice((-1, 1))                            # spiral handedness (clockwise / counter-clockwise)
        elif styleRoll < 0.20:
            self.style = 'striped_diamond'                                         # two meridian sets crossed at 60° → diamond lattice
            self.styleAngle = random.uniform(0, math.pi)
            self.styleNStripes = random.randint(5, 8)                              # min 5: with fewer stripes the two crossed sets pile up at the poles into a near-solid white blob
        elif styleRoll < 0.25:
            self.style = 'striped_pinwheel'                                        # peppermint-candy swirl: N curved bands spiraling out from the front-center to the silhouette
            self.styleAngle = random.uniform(0, 2 * math.pi)
            self.styleNStripes = random.randint(5, 8)                              # number of coloured bands (the other halves are gaps)
            self.styleTwist    = random.uniform(0.6, 1.2) * random.choice((-1, 1)) # turns from center to rim, with random handedness
        elif styleRoll < 0.30:
            self.style = 'dotted_sphere'                                           # center + ring with cos(θ) depth scaling — dots near the silhouette shrink
            self.styleNDots = random.randint(5, 8)
        elif styleRoll < 0.40:
            self.style = 'dotted_candy'                                            # mixed dot sizes, scattered positions, tinted (lighter shade of base color)
            self.styleNDots = random.randint(6, 12)
        elif styleRoll < 0.50:
            self.style = 'dotted_hex'                                              # tight hex grid filling the visible disk — soccer-ball feel
        else:
            self.style = 'plain'

        if self.style == 'plain':                                                  # overlay color: chooses what color the pattern's bright regions take
            self.overlayColor = None
        elif self.style == 'dotted_candy':
            self.overlayColor = modifyColorPerc(self.color, 1.8)                   # candy keeps its lighter-tint-of-base behavior (chunky gumball look)
        else:                                                                       # other patterned styles: 60% white · 25% dark-shade of base · 15% complementary hue
            overlayRoll = random.random()
            if overlayRoll < 0.60:
                self.overlayColor = (255, 255, 255)
            elif overlayRoll < 0.85:
                self.overlayColor = modifyColorPerc(self.color, 0.30)              # silkscreen / printed-ink look (dark version of the base color)
            else:
                hue2 = (hue + 0.5) % 1.0                                            # complementary hue across the wheel
                r2, g2, b2 = colorsys.hsv_to_rgb(hue2, 0.95, 1.0)
                self.overlayColor = (int(r2 * 255), int(g2 * 255), int(b2 * 255))

    def process(self):

        if self.radius < self.targetRadius and not self.removing:
            self.radius = min(self.targetRadius, self.radius + deltaT * GROWTH_RATE)
        elif self.removing:
            self.radius -= deltaT * GROWTH_RATE
            if self.radius < sper(0.001):
                sprites.remove(self)
                return

        if mouseLeft and getDist((self.x, self.y), (mouseX, mouseY)) < self.radius and not any(b.grabbed for b in sprites):
            self.grabbed = True                                                    # held-LMB grab: passing the cursor over any ball while LMB is held grabs it (as long as nothing else is already grabbed)
            self.sleeping = False                                                  # waking on grab so the just-released ball integrates normally; also un-pin (grabbing a pinned ball releases it)
            self.pinned = False
            self.restTime = 0.0
        elif not mouseLeft:
            self.grabbed = False

        if self.grabbed:                                                           # cursor drives position; velocity tracks smoothed mouse motion. We FALL THROUGH to walls so wall hits still sound while dragging into a wall (skipping only gravity + integration + friction, which are pointless under mouse control).
            self.x = mouseX
            self.y = mouseY
            self.vx = mouseVx
            self.vy = mouseVy
        elif self.sleeping or self.pinned:                                         # asleep/pinned: no gravity, no integration, no walls, no friction. Wake-ups handled in _resolveCollision (sleeping only) and the grab path (both).
            return
        else:                                                                      # awake non-grabbed
            self.vy += GRAVITY * deltaT                                            # gravity integration
            self.x += self.vx * deltaT                                             # ball-ball collisions moved OUT to global `_resolveAllCollisions()` so we can run COLLISION_ITERATIONS passes consistently
            self.y += self.vy * deltaT

        wallMinVel = IMPACT_MIN_VEL_GRABBED if self.grabbed else IMPACT_MIN_VEL
        wasContact = self._wallContact
        self._wallContact = [False, False, False, False]
        onFloor = False

        if WALL_MODE == 1:                                                         # MODE 1 — all 4 walls bounce
            if self.x < self.radius:
                self.x = self.radius
                if self.vx < 0:
                    if not wasContact[0]:
                        _playImpact(-self.vx, self.voiceType, self.soundIdx, wallMinVel)
                    self.vx = -self.vx * SIDE_BOUNCE
                self._wallContact[0] = True
            elif self.x > screenX - self.radius:
                self.x = screenX - self.radius
                if self.vx > 0:
                    if not wasContact[1]:
                        _playImpact(self.vx, self.voiceType, self.soundIdx, wallMinVel)
                    self.vx = -self.vx * SIDE_BOUNCE
                self._wallContact[1] = True
        else:                                                                      # MODE 2 or 3 — sides wrap
            if self.x < -self.radius:
                self.x = screenX + self.radius
            elif self.x > screenX + self.radius:
                self.x = -self.radius

        if WALL_MODE in (1, 2):                                                    # MODE 1 or 2 — top/bottom bounce
            if self.y < self.radius:
                self.y = self.radius
                if self.vy < 0:
                    if not wasContact[2]:
                        _playImpact(-self.vy, self.voiceType, self.soundIdx, wallMinVel)
                    self.vy = -self.vy * TOP_BOUNCE
                self._wallContact[2] = True
            elif self.y > screenY - self.radius:
                self.y = screenY - self.radius
                if self.vy > 0:
                    if not wasContact[3]:
                        _playImpact(self.vy, self.voiceType, self.soundIdx, wallMinVel)
                    self.vy = -self.vy * FLOOR_BOUNCE
                self._wallContact[3] = True
                onFloor = True
        else:                                                                      # MODE 3 — top/bottom also wrap (no walls at all)
            if self.y < -self.radius:
                self.y = screenY + self.radius
            elif self.y > screenY + self.radius:
                self.y = -self.radius

        if self.grabbed:                                                           # grabbed: cursor will overwrite velocity next frame anyway, so friction + sleep accumulation are pointless
            return

        scaledDt = deltaT * self._frictionScale                                    # friction + rest snap (scaled by mass: heavier balls keep momentum longer)
        airDamp = AIR_FRICTION ** scaledDt
        self.vx *= airDamp
        self.vy *= airDamp
        if onFloor:
            self.vx *= FLOOR_FRICTION ** scaledDt
            if abs(self.vy) < REST_VY_THRESHOLD: self.vy = 0
        if abs(self.vx) < REST_VX_THRESHOLD: self.vx = 0

        # sleep accumulation lives in _resolveAllCollisions (after the collision passes), where this frame's final post-collision position is available. Velocity here would be a misleading signal — pile balls hold large dormant |vy| while their position barely moves.

    def _resolveCollision(self, ball):
        dx = self.x - ball.x
        dy = self.y - ball.y
        dist = math.sqrt(dx*dx + dy*dy) or 0.0001
        nx, ny = dx/dist, dy/dist                                                  # unit normal from `ball` → `self`
        overlap = (self.radius + ball.radius) - dist
        self._inContact = True                                                     # reaching this function means the spatial-hash dispatcher already confirmed overlap → mark both balls as "supported this frame"
        ball._inContact = True

        vRelN = (self.vx - ball.vx) * nx + (self.vy - ball.vy) * ny                # relative velocity along the normal
        hardImpact = -vRelN > MICRO_BOUNCE_THRESHOLD                               # decide UP FRONT whether this is a "real hit" (someone threw a ball at the sleeper) or a "pile contact" (gravity-fed sub-threshold tap). Drives BOTH mass selection and wake-up. Without this split, sleepers were unmovable on real hits (always infinite mass) and piles re-accumulated energy on soft taps (sleeper-as-normal-mass let dormant vy build up).

        m1 = self.mass                                                             # effective mass: pinned always static; sleeping is static ONLY for soft contacts (acts as a wall in piles → kills the gravity-fed vy accumulation chain). On a hard impact we DEMOTE the sleeper to normal mass so the impulse can actually move it before it wakes.
        if   self.pinned:                       m1 *= 1e6
        elif self.sleeping and not hardImpact:  m1 *= 1e6
        elif self.grabbed:                       m1 *= GRABBED_MASS_MULTIPLIER
        m2 = ball.mass
        if   ball.pinned:                       m2 *= 1e6
        elif ball.sleeping and not hardImpact:  m2 *= 1e6
        elif ball.grabbed:                       m2 *= GRABBED_MASS_MULTIPLIER
        totalMass = m1 + m2

        self.x += nx * overlap * (m2 / totalMass)                                  # mass-weighted position correction: heavier ball moves less out of penetration
        self.y += ny * overlap * (m2 / totalMass)
        ball.x -= nx * overlap * (m1 / totalMass)
        ball.y -= ny * overlap * (m1 / totalMass)

        if vRelN >= 0:
            return                                                                 # already separating — no impulse

        impactMinVel = IMPACT_MIN_VEL_GRABBED if (self.grabbed or ball.grabbed) else IMPACT_MIN_VEL
        if self.soundIdx >= ball.soundIdx:                                         # smaller ball (higher idx) dominates BOTH the perceived pitch AND voice
            _playImpact(-vRelN, self.voiceType, self.soundIdx, impactMinVel)
        else:
            _playImpact(-vRelN, ball.voiceType, ball.soundIdx, impactMinVel)

        useRestitution = BALL_RESTITUTION if hardImpact else 0.0                   # tiny relative velocities → no bounce (restitution 0) → kills the infinite micro-jitter in piles
        factor = (1 + useRestitution) / totalMass                                  # standard mass-aware impulse: Δv1 = -(1+e)·m2/(m1+m2)·vRelN, Δv2 = +(1+e)·m1/(m1+m2)·vRelN
        dv1 = -m2 * factor * vRelN
        dv2 =  m1 * factor * vRelN
        self.vx += dv1 * nx
        self.vy += dv1 * ny
        ball.vx += dv2 * nx
        ball.vy += dv2 * ny
        if hardImpact:                                                             # only "real" impacts wake sleeping balls — pinned balls NEVER wake from impacts (only on grab)
            if not self.pinned:
                self.sleeping = False
                self.restTime = 0.0
            if not ball.pinned:
                ball.sleeping = False
                ball.restTime = 0.0

    def _resolvePosition(self, ball):
        """Position-only collision relaxation — no impulse, no sound, no wake. Used in extra iteration passes to push
        piled-up balls apart without re-applying bounce impulses, re-queuing impact sounds, or waking sleeping balls.
        Sleeping balls can be silently nudged into stable positions; the only thing that wakes them is a real impulse."""
        dx = self.x - ball.x
        dy = self.y - ball.y
        dist = math.sqrt(dx*dx + dy*dy) or 0.0001
        overlap = (self.radius + ball.radius) - dist
        if overlap <= 0:
            return
        self._inContact = True                                                     # same support flagging as _resolveCollision — relaxation passes still count as contact
        ball._inContact = True
        nx, ny = dx/dist, dy/dist
        m1 = self.mass                                                             # mirror the same (pinned/sleeping) ≫ grabbed ≫ free hierarchy from _resolveCollision so position correction is consistent across passes
        if   self.pinned or self.sleeping:  m1 *= 1e6
        elif self.grabbed:                   m1 *= GRABBED_MASS_MULTIPLIER
        m2 = ball.mass
        if   ball.pinned or ball.sleeping:  m2 *= 1e6
        elif ball.grabbed:                   m2 *= GRABBED_MASS_MULTIPLIER
        totalMass = m1 + m2
        self.x += nx * overlap * (m2 / totalMass)
        self.y += ny * overlap * (m2 / totalMass)
        ball.x -= nx * overlap * (m1 / totalMass)
        ball.y -= ny * overlap * (m1 / totalMass)

    def _bakeSphere(self):
        """Render gradient + (optional pattern) + hotspot into a per-ball Surface once (when fully grown).
        All per-frame draw becomes a single blit. Pattern overlay (stripes/dots) re-renders the gradient in white and masks it on top."""
        r = int(self.targetRadius)
        size = r * 2 + 4
        cx, cy = size * 0.5, size * 0.5
        lx, ly = 0.35, -0.94                                                       # fixed light direction (upper-right) baked into every ball
        layers = 100                                                               # 100 concentric shaded discs → nearly continuous gradient (cached, so 1-time cost)

        def renderLayers(target, baseColor):
            for i in range(layers):
                t = i / (layers - 1)
                layerRadius = r * (1 - 0.55 * t)
                offset = r * 0.45 * t
                tint = 0.45 + 1.20 * t                                              # gradient contrast: deeper shadow (0.45 → was 0.65) + steeper falloff for a sharper highlight pop
                pygame.draw.circle(target, modifyColorPerc(baseColor, tint), (cx + lx * offset, cy + ly * offset), layerRadius)

        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        renderLayers(surf, self.color)                                             # base colored sphere

        patternStyles = ('striped_flat', 'striped_sphere', 'striped_spiral', 'striped_diamond', 'striped_pinwheel', 'dotted_sphere', 'dotted_candy', 'dotted_hex')
        if self.style in patternStyles:                                            # pattern overlay: shaded sphere masked by stripes/dots
            overlaySphere = pygame.Surface((size, size), pygame.SRCALPHA)
            renderLayers(overlaySphere, self.overlayColor)                         # overlay color was decided in __init__ (white / dark-shade / complementary / candy tint)
            dotPositions = None
            if   self.style == 'striped_flat':     mask = _makeStripeMaskFlat    (size, self.styleNStripes, self.styleAngle)
            elif self.style == 'striped_sphere':   mask = _makeStripeMaskSphere  (size, self.styleNStripes, self.styleAngle)
            elif self.style == 'striped_spiral':   mask = _makeStripeMaskSpiral  (size, self.styleNStripes, self.styleAngle, self.styleHanded)
            elif self.style == 'striped_diamond':  mask = _makeStripeMaskDiamond (size, self.styleNStripes, self.styleAngle)
            elif self.style == 'striped_pinwheel': mask = _makeStripeMaskPinwheel(size, self.styleNStripes, self.styleAngle, self.styleTwist)
            elif self.style == 'dotted_sphere':    mask, dotPositions = _makeDotMaskSphere(size, r, self.styleNDots)
            elif self.style == 'dotted_candy':     mask, dotPositions = _makeDotMaskCandy (size, r, self.styleNDots)
            else:                                  mask, dotPositions = _makeDotMaskHex   (size, r)
            if dotPositions and max(self.overlayColor) < 200:                      # subtle darker rim around each dot → "printed on the surface" feel — only for dim overlays (silkscreen, dark tints). Bright overlays (white, complementary, candy) already pop on their own and a dark rim makes them look pixelated.
                rimLayer = pygame.Surface((size, size), pygame.SRCALPHA)           # alpha-blended pass: soft shadow that darkens whatever is underneath
                rimColor = (0, 0, 0, 70)
                for px, py, dotR in dotPositions:
                    rimR = dotR + max(1.0, dotR * 0.07)                            # thin ring
                    pygame.draw.circle(rimLayer, rimColor, (int(px), int(py)), int(rimR))
                surf.blit(rimLayer, (0, 0))
            overlaySphere.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT) # clip shaded overlay to mask regions
            surf.blit(overlaySphere, (0, 0))                                       # overlay onto the base colored sphere

        specR = max(2.0, r * 0.06)                                                 # tiny specular highlight — drawn on every style now (was plain-only) for consistent 3D feel
        hotCx = cx + lx * r * 0.6
        hotCy = cy + ly * r * 0.6
        _drawHotspot(surf, hotCx, hotCy, specR)
        pygame.draw.circle(surf, (255, 255, 255, 35), (int(cx), int(cy)), r, 1)    # 1-px low-alpha white rim → subtle silhouette pop against the black background (barely visible against other balls)
        self._sphereSurf = surf

    def draw(self):
        if self.grabbed or (showInfo and self.id == 1):                            # thin SOFT glow ring blit underneath the sphere — selection feedback for the grabbed ball, AND on ball id=1 only while SPACE is held (so it lines up with the stats overlay top-right)
            haloColor = modifyColorPerc(self.color, 1.7)                           # brighter than the base color (clamped to 255 per channel)
            glowLayers = 6
            outerR = self.radius * 1.10                                            # thin extension (10% beyond the silhouette)
            glowSize = int(outerR * 2) + 4
            glowSurf = pygame.Surface((glowSize, glowSize), pygame.SRCALPHA)
            hcx, hcy = glowSize // 2, glowSize // 2
            for i in range(glowLayers):                                            # layers drawn from outer (visible at the edge) → inner (most opaque); alpha blending accumulates inward
                u = i / (glowLayers - 1)
                r = int(outerR - (outerR - self.radius) * u)
                alpha = int(90 + 130 * u)                                          # outer 90 (visible against black) → inner 220 (strong fringe right at the ball edge)
                pygame.gfxdraw.filled_circle(glowSurf, hcx, hcy, r, (*haloColor, alpha))
            windowSurface.blit(glowSurf, (self.x - hcx, self.y - hcy))

        if self.radius < self.targetRadius:                                        # GROWING or SHRINKING — slow per-frame draw at the current radius (baked sphere only used at full size)
            lightX, lightY = xper(0.5), -yper(0.2)
            dx, dy = lightX - self.x, lightY - self.y
            d = math.sqrt(dx*dx + dy*dy) or 1
            lx, ly = dx/d, dy/d
            growLayers = 12                                                        # fewer layers during the brief growth animation (still smooth enough)
            for i in range(growLayers):
                t = i / (growLayers - 1)
                layerRadius = self.radius * (1 - 0.55 * t)
                offset = self.radius * 0.45 * t
                tint = 0.45 + 1.20 * t                                              # gradient contrast: deeper shadow (0.45 → was 0.65) + steeper falloff for a sharper highlight pop
                pygame.draw.circle(windowSurface, modifyColorPerc(self.color, tint), (self.x + lx * offset, self.y + ly * offset), layerRadius)
        else:                                                                      # GROWN — single blit of the baked sphere (cheap)
            if self._sphereSurf is None:
                self._bakeSphere()
            half = self._sphereSurf.get_width() * 0.5
            windowSurface.blit(self._sphereSurf, (self.x - half, self.y - half))

        if showInfo and self.id == 1:
            speed = math.sqrt(self.vx*self.vx + self.vy*self.vy)
            createText(20, "Speed: %.0f" % speed, 'topright', (255, 150, 0), xper(0.99), yper(0.015))
            createText(20, "Vx: %.0f" % self.vx,  'topright', (0, 200, 200), xper(0.99), yper(0.045))
            createText(20, "Vy: %.0f" % self.vy,  'topright', (255, 0, 255), xper(0.99), yper(0.075))
            pygame.draw.line(windowSurface, (255, 0, 255), (self.x, self.y), (self.x + self.vx*0.05, self.y + self.vy*0.05), 5)

pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=256)
pygame.init()

windowSurface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, depth=32, display=0)  # exclusive fullscreen at the monitor's native resolution
screenX, screenY = windowSurface.get_size()
pygame.display.set_caption('Balls')

font = pygame.freetype.SysFont('Century Gothic', 0)


def _makeMarble(freq, duration=0.18, amp=0.40,
                ratios=(1.0, 2.05, 3.42, 5.6),                                     # near-harmonic body + inharmonic shimmer = glass on ceramic
                partialAmps=(1.0, 0.5, 0.28, 0.15),
                noiseAmp=0.7, noiseTime=0.004):
    """Glass-marble-on-ceramic strike: bright fundamental with inharmonic partials + sharp noise transient. The original 'campana' sound."""
    n = int(SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    decayTimes  = [duration * 0.45 / (1 + 0.55 * i) for i in range(len(ratios))]   # higher partials decay faster (energy bleeds off treble first)
    omegas      = [2 * math.pi * freq * r for r in ratios]
    normSum     = sum(partialAmps)
    noiseSamples = max(1, int(SAMPLE_RATE * noiseTime))
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        for k in range(len(ratios)):
            s += partialAmps[k] * math.exp(-t / decayTimes[k]) * math.sin(omegas[k] * t)
        s /= normSum
        if i < noiseSamples:                                                       # 3 ms noise burst at the strike — the "clack" before the ring
            s += (random.random() * 2 - 1) * noiseAmp * (1 - i / noiseSamples)
        v = int(s * amp * 32767)
        struct.pack_into('<h', buf, i * 2, max(-32768, min(32767, v)))
    return pygame.mixer.Sound(buffer=bytes(buf))


def _makeWood(freq, duration=0.13, amp=0.42):
    """Hollow wooden knock: two near-harmonic partials, very fast decay, longer/louder noise attack. Tok-tok vibe."""
    n = int(SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    ratios      = (1.0, 1.45)                                                      # near-harmonic (less inharmonic than marble → woodier)
    partialAmps = (1.0, 0.35)
    decayTimes  = (0.045, 0.025)                                                   # very short — wood doesn't ring
    omegas      = [2 * math.pi * freq * r for r in ratios]
    normSum     = sum(partialAmps)
    noiseSamples = max(1, int(SAMPLE_RATE * 0.010))                                # 10 ms noise — longer, gives a heftier knock attack
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        for k in range(len(ratios)):
            s += partialAmps[k] * math.exp(-t / decayTimes[k]) * math.sin(omegas[k] * t)
        s /= normSum
        if i < noiseSamples:
            s += (random.random() * 2 - 1) * 0.55 * (1 - i / noiseSamples)
        v = int(s * amp * 32767)
        struct.pack_into('<h', buf, i * 2, max(-32768, min(32767, v)))
    return pygame.mixer.Sound(buffer=bytes(buf))


def _makeRubber(freq, duration=0.22, amp=0.45):
    """Cartoon boing: instantaneous frequency sweeps from ~1.9·freq down to ~0.55·freq exponentially,
    with a smooth attack and a long-ish smooth decay. The pitch movement is what makes it instantly
    recognizable against the static voices — sounds like a rubber band / spring release."""
    n = int(SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    decay = 0.075
    attackSamples = max(1, int(SAMPLE_RATE * 0.004))                               # 4 ms smooth attack — no click
    sweepTau = 0.038                                                               # exponential sweep time-constant (~38 ms half-life)
    fStart, fEnd = freq * 1.9, freq * 0.55
    phase = 0.0                                                                    # integrate instantaneous frequency to keep phase coherent during the sweep
    dt = 1.0 / SAMPLE_RATE
    for i in range(n):
        t = i * dt
        currentFreq = fEnd + (fStart - fEnd) * math.exp(-t / sweepTau)
        phase += 2 * math.pi * currentFreq * dt
        attackEnv = min(1.0, i / attackSamples)
        decayEnv  = math.exp(-t / decay)
        s = math.sin(phase) * attackEnv * decayEnv
        v = int(s * amp * 32767)
        struct.pack_into('<h', buf, i * 2, max(-32768, min(32767, v)))
    return pygame.mixer.Sound(buffer=bytes(buf))


def _makePop(freq, duration=0.10, amp=0.52):
    """Snap with body: a noisy attack on top of a two-partial pitched ring (fundamental + octave) that lingers slightly.
    Still distinct from rubber's tonal sweep (pop has no pitch movement and a noisy front), but with enough sustain to read
    as a proper 'pop' rather than just a tap."""
    n = int(SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    noiseDecay = 0.012                                                             # ~12 ms noise body — still snappy
    toneDecay1 = 0.045                                                             # fundamental rings a bit longer → adds body
    toneDecay2 = 0.025                                                             # octave decays faster (treble bleeds first)
    omega1 = 2 * math.pi * freq * 1.30                                             # fundamental — slight pitched bias keeps it brighter than marble
    omega2 = 2 * math.pi * freq * 2.60                                             # octave above for richer body
    for i in range(n):
        t = i / SAMPLE_RATE
        noise = (random.random() * 2 - 1) * 0.65 * math.exp(-t / noiseDecay)       # noise attack — slightly trimmed to make room for the louder body
        tone  = (0.50 * math.sin(omega1 * t) * math.exp(-t / toneDecay1)           # fundamental — main body voice
              +  0.20 * math.sin(omega2 * t) * math.exp(-t / toneDecay2))          # octave — adds brightness without ringing too long
        s = noise + tone
        v = int(s * amp * 32767)
        struct.pack_into('<h', buf, i * 2, max(-32768, min(32767, v)))
    return pygame.mixer.Sound(buffer=bytes(buf))

_impactQueue = []                                                                  # collected during the frame; flushed in the main loop
_lastImpactTime = 0.0                                                              # for the global cooldown between sound plays

def _playImpact(intensity, voiceType, soundIdx, minVel=IMPACT_MIN_VEL):
    """Queue an impact at the requested intensity (px/s), voice (marble/wood/rubber/pop) and pitch slot.
    Sub-threshold impacts are dropped immediately. Applies a ±PITCH_JITTER random shift to the slot."""
    if intensity < minVel:
        return
    if PITCH_JITTER:
        soundIdx = max(0, min(N_PITCH_SLOTS - 1, soundIdx + random.randint(-PITCH_JITTER, PITCH_JITTER)))
    _impactQueue.append((intensity, voiceType, soundIdx))

def _flushImpacts():
    """Play queued impacts. Binary switch on ball count: below SOUND_FILTER_THRESHOLD every queued impact plays;
    at or above it, the full IMPACT_COOLDOWN + MAX_SOUNDS_PER_FRAME limits apply (weighted bass-heavy pick)."""
    global _lastImpactTime
    if not _impactQueue:
        return
    now = time.time()
    if len(sprites) < SOUND_FILTER_THRESHOLD:                                      # few-ball regime: no cooldown, no cap, play everything queued
        for intensity, voice, idx in _impactQueue:
            sound = ballHitSounds[voice][idx]
            sound.set_volume(min(1.0, intensity / IMPACT_VOL_SCALE))
            sound.play()
        _lastImpactTime = now
        _impactQueue.clear()
        return
    if now - _lastImpactTime < IMPACT_COOLDOWN:                                    # full filter mode: still in cooldown → drop everything queued this frame
        _impactQueue.clear()
        return
    weights = [intensity * (1 + PITCH_PRIORITY_BIAS * (1 - idx / max(1, N_PITCH_SLOTS - 1)))  # bass-heavy bias: low idx → high weight (voice doesn't affect priority)
               for intensity, _voice, idx in _impactQueue]
    k = min(MAX_SOUNDS_PER_FRAME, len(_impactQueue))
    picks = random.choices(_impactQueue, weights=weights, k=k)                     # weighted random — bass dominates but treble can still leak through occasionally
    for intensity, voice, idx in picks:
        sound = ballHitSounds[voice][idx]
        sound.set_volume(min(1.0, intensity / IMPACT_VOL_SCALE))
        sound.play()
    _lastImpactTime = now
    _impactQueue.clear()


def _clampAllToWalls():
    """Push every ball back inside the playfield (respects WALL_MODE).
    Called after each collision pass so corrections that shove a ball through a wall get reverted
    immediately (otherwise the per-process wall handler wouldn't fix the violation until next frame)."""
    bounceX = (WALL_MODE == 1)
    bounceY = (WALL_MODE in (1, 2))
    if not (bounceX or bounceY):
        return
    for ball in sprites:
        if bounceX:
            if   ball.x < ball.radius:           ball.x = ball.radius
            elif ball.x > screenX - ball.radius: ball.x = screenX - ball.radius
        if bounceY:
            if   ball.y < ball.radius:           ball.y = ball.radius
            elif ball.y > screenY - ball.radius: ball.y = screenY - ball.radius


def _resolveAllCollisions():
    """Global collision step using a spatial hash to skip pairs that can't possibly overlap.
    Grid `cellSize = 2 × max-radius`, so any overlapping pair lives in either the same cell or an adjacent one.
    For each cell we check pairs WITHIN it + pairs against the 4 forward neighbors (E, SE, S, SW); that
    pattern guarantees every unique pair is visited exactly once (no double-counting).
    Pass 1 applies the full physics (impulse + sound + position). The remaining COLLISION_ITERATIONS-1 passes
    are position-only relaxation. A wall-clamp follows each pass to keep corrections inside the playfield."""
    n = len(sprites)
    if n == 0:
        return
    for s in sprites:                                                              # reset per-frame contact flags before any pass — collision dispatchers will re-set them on overlap
        s._inContact = False
    cellSize = max(2, int(sper(BALL_RADIUS_MAX) * 2.0 + 2))                        # 2× max radius is just enough; the +2 is a safety margin against rounding
    FORWARD  = ((1, 0), (-1, 1), (0, 1), (1, 1))                                   # right, down-left, down, down-right — covers each unique cell pair once

    def runPass(method):
        grid = {}                                                                  # cell_key → list of sprite indices
        for i in range(n):
            a = sprites[i]
            key = (int(a.x // cellSize), int(a.y // cellSize))
            grid.setdefault(key, []).append(i)
        for (cx, cy), bucket in grid.items():
            m = len(bucket)
            for ii in range(m):
                a = sprites[bucket[ii]]
                ax, ay, ar = a.x, a.y, a.radius
                for jj in range(ii + 1, m):                                        # pairs WITHIN the same cell
                    b = sprites[bucket[jj]]
                    dx = ax - b.x
                    dy = ay - b.y
                    d2 = dx*dx + dy*dy
                    rSum = ar + b.radius
                    if d2 < rSum * rSum:
                        method(a, b)
                        ax, ay = a.x, a.y                                          # `method` may have moved a — refresh cache
                    elif d2 < (rSum + 2.0) * (rSum + 2.0):                         # close-but-not-overlapping (within 2px slack): still counts as in-contact for sleep. Without this, a ball wedged at exactly d=rSum between neighbours never gets _inContact set (strict-overlap dispatcher misses it) and can never accumulate sleep, leaving it awake with tiny residual velocity forever.
                        a._inContact = True
                        b._inContact = True
                for dcx, dcy in FORWARD:                                           # pairs with the 4 forward-neighbor cells
                    other = grid.get((cx + dcx, cy + dcy))
                    if not other:
                        continue
                    for bi in other:
                        b = sprites[bi]
                        dx = ax - b.x
                        dy = ay - b.y
                        d2 = dx*dx + dy*dy
                        rSum = ar + b.radius
                        if d2 < rSum * rSum:
                            method(a, b)
                            ax, ay = a.x, a.y
                        elif d2 < (rSum + 2.0) * (rSum + 2.0):
                            a._inContact = True
                            b._inContact = True

    runPass(Ball._resolveCollision)                                                # pass 1: full physics
    _clampAllToWalls()
    for _ in range(COLLISION_ITERATIONS - 1):                                      # passes 2..N: position-only
        runPass(Ball._resolvePosition)
        _clampAllToWalls()

    floorY = screenY                                                               # wake any sleeping ball that has lost reachability to a real anchor (floor or awake/grabbed/pinned ball). A pure proximity-to-any-neighbour check is NOT enough: sleepers can mutually support each other in a chain that floats in mid-air (an arc, a ring) once their floor anchors are removed. BFS from anchors through the contact graph is the correct test.
    floorActive = WALL_MODE in (1, 2)
    contactSlack = 2.0
    anchored = set()
    worklist = []
    for s in sprites:                                                              # seed anchors: not-sleeping balls are anchored by definition, plus sleepers actually touching the floor
        if not s.sleeping:
            anchored.add(s)
            worklist.append(s)
            continue
        if s.pinned or (floorActive and s.y + s.radius >= floorY - 1):
            anchored.add(s)
            worklist.append(s)
    while worklist:                                                                # BFS through proximity-touching neighbours WITH a gravity-aware support cone — `a` only supports `b` if `a` is sufficiently below `b`. Pure conectividad (the previous BFS) wrongly anchored arcs/bridges via lateral contacts; with the cone, only contacts within 60° of vertical count, so side-attached balls don't get propagated as anchors.
        a = worklist.pop()
        ax, ay, ar = a.x, a.y, a.radius
        for b in sprites:
            if b in anchored or not b.sleeping:
                continue
            rSum = ar + b.radius
            if ay - b.y < 0.5 * rSum:                                             # a not sufficiently below b → can't physically hold it up against gravity. 0.87*rSum ≈ cos(30°)*rSum, which restricts the support cone to ±30° from vertical (strict). Only near-directly-below contacts count; lateral / diagonal-shallow contacts won't propagate the anchor.
                continue
            dx = ax - b.x
            dy = ay - b.y
            rSumSlack = rSum + contactSlack
            if dx*dx + dy*dy < rSumSlack * rSumSlack:
                anchored.add(b)
                worklist.append(b)
    for s in sprites:                                                              # any sleeper not reached by the BFS is floating with no path to a real anchor → wake it
        if s.sleeping and s not in anchored:
            s.sleeping = False
            s.restTime = 0.0

    for s in sprites:                                                              # sleep accumulation: POSITION-based. Compare current (post-collision) position to last frame's post-collision position. Piled balls hold large dormant |vy| but their actual displacement per frame is tiny (the collision passes correct the gravity-driven integration almost completely), so position is a far more reliable "is this ball actually moving" signal than velocity.
        if s.grabbed or s.pinned:
            s._prevX = s.x
            s._prevY = s.y
            s.restTime = 0.0
            continue
        if s.sleeping:                                                             # already asleep — just keep _prevX/Y in sync (the wake check above may have moved this ball into the wake branch already)
            s._prevX = s.x
            s._prevY = s.y
            continue
        onFloor = floorActive and (s.y + s.radius >= floorY - 1)
        isSupported = onFloor or s._inContact
        dx = s.x - s._prevX
        dy = s.y - s._prevY
        posStable = abs(dx) < SLEEP_POS_THRESHOLD and abs(dy) < SLEEP_POS_THRESHOLD  # primary signal: did this ball actually move this frame? Catches well-packed piles cleanly.
        velStable = abs(s.vx) < SLEEP_VX_THRESHOLD and abs(s.vy) < SLEEP_VY_THRESHOLD # fallback: ball can't reach position-stable (stuck in residual overlap that the collision passes can't fully separate) but motion is small → accept the overlap and let it sleep. Without this, tight pile-ups iterate forever trying to find a perfect gap.
        if isSupported and (posStable or velStable):
            s.restTime += deltaT
            settleDamp = SETTLE_DAMP ** deltaT                                      # exponential decay applied EVERY frame the ball is accumulating sleep time. NOT mass-scaled (unlike normal friction) — see the SETTLE_DAMP knob comment. By the time restTime reaches SLEEP_DELAY, vx/vy are near 0 and the final snap is invisible.

            s.vx *= settleDamp
            s.vy *= settleDamp
            if s.restTime >= SLEEP_DELAY:
                s.sleeping = True
                s.vx = 0.0
                s.vy = 0.0
        else:
            s.restTime = 0.0
        s._prevX = s.x
        s._prevY = s.y


_IMPACT_FREQS  = (510, 580, 645, 720, 795, 870, 960, 1040, 1125, 1220, 1320, 1430)  # 12 pitch slots shared across all voice types
N_PITCH_SLOTS  = len(_IMPACT_FREQS)
ballHitSounds  = {                                                                 # voiceType → list of 12 pre-rendered Sound buffers (one per pitch slot)
    'marble': [_makeMarble(f) for f in _IMPACT_FREQS],
    'wood':   [_makeWood  (f) for f in _IMPACT_FREQS],
    'rubber': [_makeRubber(f) for f in _IMPACT_FREQS],
    'pop':    [_makePop   (f) for f in _IMPACT_FREQS],
}


def _drawHotspot(surf, cx, cy, specR):
    """Specular hotspot: sharp solid-white core + two soft translucent halos around it for a wet/glossy candy sheen."""
    ix, iy = int(cx), int(cy)
    rCore = max(2, int(specR))
    haloSize = rCore * 8                                                           # SRCALPHA temp surface so the low-alpha halos blend cleanly into the baked sphere
    halo = pygame.Surface((haloSize, haloSize), pygame.SRCALPHA)
    hcx, hcy = haloSize // 2, haloSize // 2
    pygame.gfxdraw.filled_circle(halo, hcx, hcy, rCore * 3, (255, 255, 255, 22))   # outer wide soft glow
    pygame.gfxdraw.filled_circle(halo, hcx, hcy, rCore * 2, (255, 255, 255, 55))   # inner brighter halo
    surf.blit(halo, (ix - hcx, iy - hcy))
    pygame.gfxdraw.filled_circle(surf, ix, iy, rCore, (255, 255, 255, 255))        # sharp white core on top


def _makeStripeMaskFlat(size, nStripes, angle):
    """White-on-transparent mask of `nStripes` flat parallel stripes (no spherical projection), rotated by `angle` (radians)."""
    big = int(size * 1.8)                                                          # oversize so rotation never clips a stripe out of view
    flat = pygame.Surface((big, big), pygame.SRCALPHA)
    cxBig = big * 0.5
    bandSpacing = size / nStripes                                                  # spacing between band CENTERS, measured in the original ball width
    bandW = bandSpacing * 0.5                                                      # 50 % white, 50 % gap
    for i in range(nStripes):
        offset = (i - (nStripes - 1) * 0.5) * bandSpacing                          # symmetric around the center → all bands visible after rotation/crop
        x = cxBig + offset - bandW * 0.5
        pygame.draw.rect(flat, (255, 255, 255, 255), (int(x), 0, int(bandW), big))
    rotated = pygame.transform.rotate(flat, math.degrees(angle))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    rx = (rotated.get_width() - size) // 2
    ry = (rotated.get_height() - size) // 2
    mask.blit(rotated, (-rx, -ry))
    return mask


def _makeStripeMaskSphere(size, nStripes, angle, fillRatio=0.5):
    """White-on-transparent mask of `nStripes` curved meridian stripes that follow the sphere's surface
    (narrowing/curving toward the silhouette), then rotated by `angle` radians.
    `fillRatio` controls equator fill (0.5 = original 50/50 white/gap; smaller = thinner bands)."""
    big = int(size * 1.8)                                                          # oversize so rotation never clips a stripe out of view
    flat = pygame.Surface((big, big), pygame.SRCALPHA)
    cxBig, cyBig = big * 0.5, big * 0.5
    sphereR = size * 0.5
    phiStep = math.pi / nStripes                                                   # longitude spacing between band centers (front hemisphere spans π)
    halfW   = phiStep * 0.5 * fillRatio                                            # equator fill driven by fillRatio
    yMin = max(0, int(cyBig - sphereR))
    yMax = min(big - 1, int(cyBig + sphereR))
    for yPix in range(yMin, yMax + 1):                                             # scan-line per y → row-by-row segments of each band
        dy = yPix - cyBig
        crossR = math.sqrt(max(0.0, sphereR*sphereR - dy*dy))                      # horizontal cross-section of the sphere at this y (0 at the poles)
        for i in range(nStripes):
            phiC = -math.pi * 0.5 + (i + 0.5) * phiStep                            # band center longitude in [-π/2, π/2]
            xL = cxBig + math.sin(phiC - halfW) * crossR                           # spherical projection: x = sin(φ)·√(R²−y²)
            xR = cxBig + math.sin(phiC + halfW) * crossR
            if xR > xL:
                pygame.draw.line(flat, (255, 255, 255, 255), (int(xL), yPix), (int(xR), yPix))
    rotated = pygame.transform.rotate(flat, math.degrees(angle))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    rx = (rotated.get_width() - size) // 2
    ry = (rotated.get_height() - size) // 2
    mask.blit(rotated, (-rx, -ry))
    return mask


def _makeStripeMaskSpiral(size, nTurns, angle, handed=1):
    """White-on-transparent mask of a DOUBLE SPIRAL (two parallel candy-cane stripes 180° apart in longitude),
    wrapping the sphere pole-to-pole. Each spiral is parametrized by t∈[0,1]: lat = −π/2 + t·π,
    lon = handed · t · nTurns · 2π (+0 or +π for the second strand). Only the front hemisphere (cos(lon) ≥ 0)
    is drawn, and the stripe thickness shrinks with depth (cos(lat)·cos(lon)) so the band naturally tapers
    toward the silhouette. Implemented as a chain of overlapping circles along each path."""
    big = int(size * 1.8)                                                          # oversize so rotation never clips the stripe out of view
    flat = pygame.Surface((big, big), pygame.SRCALPHA)
    cxBig, cyBig = big * 0.5, big * 0.5
    sphereR = size * 0.5
    bandR   = sphereR * 0.11                                                       # band half-thickness — slightly thinner than the single-spiral version so two strands don't crowd
    nSteps  = max(120, int(sphereR * nTurns * 6))
    for i in range(nSteps + 1):
        t = i / nSteps
        lat = -math.pi * 0.5 + t * math.pi
        lonBase = handed * t * nTurns * 2 * math.pi
        for lonOffset in (0.0, math.pi):                                           # two parallel spirals 180° apart in longitude → classic 2-stripe candy cane
            lon = lonBase + lonOffset
            lonN = ((lon + math.pi) % (2 * math.pi)) - math.pi                     # normalize to (−π, π] for hemisphere test
            if not (-math.pi * 0.5 <= lonN <= math.pi * 0.5):
                continue
            cosLat, sinLat = math.cos(lat), math.sin(lat)
            cosLon, sinLon = math.cos(lonN), math.sin(lonN)
            depth = cosLat * cosLon
            rEff = bandR * max(0.25, depth)
            px = cxBig + sphereR * cosLat * sinLon
            py = cyBig - sphereR * sinLat
            pygame.draw.circle(flat, (255, 255, 255, 255), (px, py), rEff)
    rotated = pygame.transform.rotate(flat, math.degrees(angle))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    rx = (rotated.get_width() - size) // 2
    ry = (rotated.get_height() - size) // 2
    mask.blit(rotated, (-rx, -ry))
    return mask


def _makeStripeMaskDiamond(size, nStripes, angle):
    """White-on-transparent mask: two sets of meridian stripes (`_makeStripeMaskSphere`) crossed at 60° → diamond lattice.
    Each set uses a thin `fillRatio` so the diamond gaps stay clearly visible — otherwise two 50% sets would overlap
    to ~75% coverage and the ball would look almost solid white."""
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    setA = _makeStripeMaskSphere(size, nStripes, angle,                fillRatio=0.18)
    setB = _makeStripeMaskSphere(size, nStripes, angle + math.pi / 3,  fillRatio=0.18)  # 60° offset → diamond grid
    mask.blit(setA, (0, 0))                                                        # both masks are white-on-transparent;
    mask.blit(setB, (0, 0))                                                        # ordinary alpha-blend → white survives wherever either set is white
    return mask


def _makeStripeMaskPinwheel(size, nStripes, angle, twist):
    """White-on-transparent mask of a peppermint-candy pinwheel: `nStripes` curved bands spiraling out from the front-center
    to the silhouette. Each band's angular position depends on radius via a logarithmic-spiral-like twist
    (`twist` = how many turns from r=0 to r=R; sign chooses handedness). Computed in 2D polar coordinates and
    stamped face-on (no spherical projection — the pattern lives on the front cap of the sphere)."""
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size * 0.5, size * 0.5
    sphereR = size * 0.5
    period = 2 * math.pi / nStripes                                                # angular period: one stripe + one gap
    halfPeriod = period * 0.5                                                      # 50% fill ratio (stripe occupies first half of each period)
    twoPiTwist = twist * 2 * math.pi                                               # cached: how much phase to add per unit r/R
    yMin = max(0, int(cy - sphereR))
    yMax = min(size - 1, int(cy + sphereR))
    for yPix in range(yMin, yMax + 1):
        dy = yPix - cy
        if abs(dy) > sphereR:
            continue
        crossR = math.sqrt(sphereR*sphereR - dy*dy)                                # row's chord through the sphere
        xMin = max(0, int(cx - crossR))
        xMax = min(size - 1, int(cx + crossR))
        inStripe = False                                                           # run-length scan: collect contiguous stripe segments and draw each as a single line
        runStart = xMin
        for xPix in range(xMin, xMax + 1):
            dx = xPix - cx
            r = math.sqrt(dx*dx + dy*dy)
            if r > sphereR:
                nowStripe = False
            else:
                theta = math.atan2(dy, dx) + angle                                 # per-ball rotation just shifts the starting phase
                phase = theta + twoPiTwist * (r / sphereR)                         # linear twist with radius — gives the classic peppermint spiral
                pos = phase % period
                nowStripe = pos < halfPeriod
            if nowStripe != inStripe:
                if inStripe:
                    pygame.draw.line(mask, (255, 255, 255, 255), (runStart, yPix), (xPix - 1, yPix))
                runStart = xPix
                inStripe = nowStripe
        if inStripe:
            pygame.draw.line(mask, (255, 255, 255, 255), (runStart, yPix), (xMax, yPix))
    return mask


def _makeDotMaskSphere(size, sphereR, nDots):
    """Center dot + ring of dots placed on a small circle around the front pole of the sphere.
    Both the ring radius and dot size are computed from a single angular distance θ (great-circle from the front pole),
    so dots near the silhouette are foreshortened (shrunk by cos θ) — gives a 'wrapped on a sphere' look.
    Returns (mask, positions) where positions is a list of (cx, cy, radius) — used by _bakeSphere to paint a darker rim."""
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    positions = []
    cx, cy = size * 0.5, size * 0.5
    centerR = sphereR * 0.28                                                       # central dot facing the viewer (no foreshortening)
    pygame.draw.circle(mask, (255, 255, 255, 255), (cx, cy), centerR)
    positions.append((cx, cy, centerR))
    theta       = math.radians(50)                                                 # angular distance of the ring from the front pole (lower = ring pulled in from the silhouette)
    depthScale  = math.cos(theta)                                                  # foreshortening factor — same for every dot on the ring
    ringR2D     = sphereR * math.sin(theta)                                        # 2D projected ring radius
    ringDotR    = centerR * depthScale                                             # ring dots shrink with cos(θ)
    rotation = random.uniform(0, math.pi * 2)
    for i in range(nDots):
        a = rotation + (i / nDots) * math.pi * 2
        dx = cx + math.cos(a) * ringR2D
        dy = cy + math.sin(a) * ringR2D
        pygame.draw.circle(mask, (255, 255, 255, 255), (dx, dy), ringDotR)
        positions.append((dx, dy, ringDotR))
    return mask, positions


def _makeDotMaskCandy(size, sphereR, nDots):
    """Scattered dots of mixed sizes — bigger than dotted_sphere and allowed to overlap a bit so they fuse into
    a chunky candy/gumball cluster. Combined with a tinted overlay color (set in _bakeSphere).
    Returns (mask, positions) for the rim pass in _bakeSphere."""
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size * 0.5, size * 0.5
    safeR  = sphereR * 0.85                                                        # keep dot CENTERS inset from the silhouette (dots themselves can overlap the rim slightly)
    minDotR, maxDotR = sphereR * 0.16, sphereR * 0.28                              # smaller max → individual dots stay distinct instead of merging into one mega-blob
    placed = []
    attempts = 0
    while len(placed) < nDots and attempts < 400:                                  # rejection sampling — light kiss-overlap only (no fusing into shapeless blobs)
        attempts += 1
        rDot = random.uniform(minDotR, maxDotR)
        d    = math.sqrt(random.random()) * max(0.0, safeR - rDot * 0.4)
        a    = random.uniform(0, 2 * math.pi)
        px, py = cx + math.cos(a) * d, cy + math.sin(a) * d
        if all(math.hypot(px - q[0], py - q[1]) > (rDot + q[2]) * 0.82 for q in placed):  # 0.82 (was 0.55) → centers stay almost apart, rims just touch / overlap ~10%
            placed.append((px, py, rDot))
            pygame.draw.circle(mask, (255, 255, 255, 255), (px, py), rDot)
    return mask, placed


def _makeDotMaskHex(size, sphereR):
    """Tight hexagonal grid of small dots filling the visible disk — soccer-ball / billiard-ball density.
    Cells alternate between two dot sizes (big/small checkerboard) for a staggered candy look.
    Grid spacing is a fixed proportion of sphereR, so larger balls just get more dots.
    Returns (mask, positions) for the rim pass in _bakeSphere."""
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    positions = []
    cx, cy = size * 0.5, size * 0.5
    spacing  = sphereR * 0.30                                                      # distance between dot centers along a row
    dotRBig  = spacing * 0.34
    dotRSmall= spacing * 0.20                                                      # alternating size — every other cell gets a smaller dot
    cellW    = spacing
    cellH    = spacing * math.sqrt(3) * 0.5                                        # hex row height = √3/2 × spacing
    clipR    = sphereR - dotRBig * 1.6                                             # pull edge dots away from the silhouette so they don't look glued to the rim
    bigParity = random.randint(0, 1)                                               # per-ball random: which checkerboard parity gets the big dots (the other gets the small ones)
    nRows = int(sphereR / cellH) + 2
    nCols = int(sphereR / cellW) + 2
    for row in range(-nRows, nRows + 1):
        rowOff = cellW * 0.5 if (row & 1) else 0.0                                 # shift every other row by half a cell → hex packing
        for col in range(-nCols, nCols + 1):
            px = cx + col * cellW + rowOff
            py = cy + row * cellH
            dx, dy = px - cx, py - cy
            if dx*dx + dy*dy <= clipR * clipR:
                dotR = dotRBig if ((row + col) & 1) == bigParity else dotRSmall    # checkerboard size alternation, parity randomized per ball
                pygame.draw.circle(mask, (255, 255, 255, 255), (px, py), dotR)
                positions.append((px, py, dotR))
    return mask, positions



def xper(percentage):
    return percentage * screenX

def yper(percentage):
    return percentage * screenY

def sper(percentage):
    return percentage * (screenX+screenY)/2

def randColor():
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))

def randColorInRange(rmin,rmax,gmin,gmax,bmin,bmax):
    return (random.randint(rmin,rmax), random.randint(gmin,gmax), random.randint(bmin,bmax))

def modifyColor(color, offset):
    return tuple(max(min(c+offset, 255), 0) for c in color)

def modifyColorPerc(color, offset):
    return tuple(int(max(min(c*offset, 255), 0)) for c in color)

def getAngle(point1, point2):
    return math.atan2(point2[1]-point1[1], point2[0]-point1[0])

def getAngleForAngVel(prevAng, point1, point2):
    angle = math.atan2(point2[1]-point1[1], point2[0]-point1[0])
    if angle - prevAng < -math.pi: angle += math.pi*2
    if angle - prevAng >  math.pi: angle -= math.pi*2
    return angle

def getDist(point1, point2):
    return math.sqrt(abs(point1[0]-point2[0])**2+abs(point1[1]-point2[1])**2)

def createText(size, content, alignment, colorText, posX, posY):
    textRect = font.get_rect(content, size=size)
    textRect.midtop = (posX, posY)
    setattr(textRect, alignment, (posX, posY))
    font.render_to(windowSurface, textRect, content, colorText, size=size)

def addSprite(sprite):
    sprites.append(sprite)
    return sprite

deltaT = 0
iniT = time.time()
clock = pygame.time.Clock()
keys = None
mouseX, mouseY = pygame.mouse.get_pos()
mouseLeft = mouseRight = False
prevMouseLeft = False                                                              # for rising-edge detection on left-click → grab (prevents re-grabbing after Q-pin while LMB stays held)
prevMouseRight = False                                                             # for rising-edge detection on right-click → flappy-bird jump
showFPS = False                                                                    # toggled by F key
prevFKey = False                                                                   # for F-key rising-edge detection
prevRKey = False                                                                   # for R-key rising-edge detection (respawn)
prevQKey = False                                                                   # for Q-key rising-edge detection (pin the grabbed ball)
prevMouseX, prevMouseY = mouseX, mouseY
mouseVx = 0.0
mouseVy = 0.0
sprites = []
showInfo = None
WALL_MODE = 1                                                                      # 1 = all 4 walls bounce · 2 = sides wrap, top/floor bounce · 3 = no walls (everything wraps)

addSprite(Ball())

while True:

    now = time.time()
    deltaT = min(now - iniT, 0.01)
    iniT = now
    clock.tick()

    keys = pygame.key.get_pressed()
    showInfo = keys[pygame.K_SPACE]
    if keys[pygame.K_1]:   WALL_MODE = 1
    elif keys[pygame.K_2]: WALL_MODE = 2
    elif keys[pygame.K_3]: WALL_MODE = 3

    mouseX, mouseY = pygame.mouse.get_pos()
    mouseLeft, _, mouseRight = pygame.mouse.get_pressed()

    if mouseRight and not prevMouseRight:                                          # right-click rising edge → flappy-bird jump for every ball (also wakes anything that was sleeping)
        for sprite in sprites:
            if isinstance(sprite, Ball) and not sprite.removing and not sprite.grabbed:
                sprite.vy = -JUMP_VELOCITY
                sprite.sleeping = False
                sprite.restTime = 0.0
    prevMouseRight = mouseRight

    fKey = keys[pygame.K_f]                                                        # F-key rising edge → toggle the FPS overlay
    if fKey and not prevFKey:
        showFPS = not showFPS
    prevFKey = fKey

    rKey = keys[pygame.K_r]                                                        # R-key rising edge → respawn the same NUMBER of balls but as freshly randomized ones (new colors/sizes/styles)
    if rKey and not prevRKey:
        nBalls = len(sprites)
        sprites.clear()
        _impactQueue.clear()                                                       # drop any pending impact sounds from the old balls
        Ball._nextId = 1                                                           # reset id counter so debug overlay still tracks "ball 1"
        for _ in range(nBalls):
            addSprite(Ball())
    prevRKey = rKey

    qKey = keys[pygame.K_q]                                                        # Q-key rising edge → pin the currently-grabbed ball in place (nail in the air)
    if qKey and not prevQKey:
        for sprite in sprites:
            if isinstance(sprite, Ball) and sprite.grabbed:
                sprite.grabbed = False
                sprite.pinned = True
                sprite.vx = 0.0
                sprite.vy = 0.0
                sprite.restTime = 0.0
                break                                                               # only one ball can be grabbed at a time
    prevQKey = qKey

    if deltaT > 0:                                                                 # low-pass-filter raw mouse velocity
        rawVx = (mouseX - prevMouseX) / deltaT
        rawVy = (mouseY - prevMouseY) / deltaT
        smoothing = 1 - math.exp(-deltaT / MOUSE_SMOOTH_TC)
        mouseVx += (rawVx - mouseVx) * smoothing
        mouseVy += (rawVy - mouseVy) * smoothing
    prevMouseX, prevMouseY = mouseX, mouseY

    windowSurface.fill((0,0,0))

    for sprite in sprites[:]:                                                      # iterate a copy: process() may remove a shrinking ball
        sprite.process()
    prevMouseLeft = mouseLeft                                                      # update AFTER process() so the rising-edge grab check inside process saw the prior-frame value
    _resolveAllCollisions()                                                        # global multi-pass collision step (replaces the per-ball collision loop that used to live inside process)
    for sprite in sprites:
        sprite.draw()
    _flushImpacts()                                                                # play only the top MAX_SOUNDS_PER_FRAME loudest impacts queued this frame

    if showInfo:
        mouseSpeed = math.sqrt(mouseVx*mouseVx + mouseVy*mouseVy)
        createText(20, "Mouse: (%s, %s)" % (mouseX,mouseY),'topleft',(200,0,0),xper(0.01),yper(0.015))
        createText(20, "Velocity: (%.0f, %.0f)" % (mouseVx,mouseVy),'topleft',(0,0,255),xper(0.01),yper(0.045))
        createText(20, "Speed: %.0f px/s" % mouseSpeed,'topleft',(255,255,0),xper(0.01),yper(0.075))
        createText(20, "Balls: %s" % len(sprites),'topleft',(200,150,75),xper(0.01),yper(0.105))
        pygame.draw.line(windowSurface, (0,0,255), (mouseX,mouseY),(mouseX-mouseVx*0.05,mouseY-mouseVy*0.05), 2)

        topBalls = sorted(sprites, key=lambda b: -(b.vx*b.vx + b.vy*b.vy))[:10]    # debug: top-10 by speed, bar-charted. Useful to spot which balls refuse to settle (residual jitter) and which have actually slept (gray label, empty bar).
        if topBalls:
            chartX  = int(xper(0.01))
            chartY  = int(yper(0.14))
            labelW  = 38
            barW    = 220
            barH    = 12
            rowGap  = 18
            topSpeed = max(1.0, math.sqrt(topBalls[0].vx**2 + topBalls[0].vy**2))
            createText(14, "Top 10 speeds  (max %.0f px/s)" % topSpeed, 'topleft', (180,180,180), chartX, chartY)
            for i, b in enumerate(topBalls):
                speed = math.sqrt(b.vx*b.vx + b.vy*b.vy)
                y = chartY + 22 + i * rowGap
                labelColor = (110,110,110) if b.sleeping else (220,220,220)
                createText(14, "#%d" % b.id, 'topleft', labelColor, chartX, y)
                barX = chartX + labelW
                pygame.draw.rect(windowSurface, (40,40,40), (barX, y, barW, barH))
                fillW = int(barW * speed / topSpeed)
                if fillW > 0:
                    pygame.draw.rect(windowSurface, b.color, (barX, y, fillW, barH))
                createText(14, "%.0f%s" % (speed, " zZz" if b.sleeping else ""), 'topleft', labelColor, barX + barW + 6, y)
    if showFPS:
        createText(15,'FPS: %s' %(str(round(clock.get_fps()))),'topright',(255,255,255),xper(0.99),yper(0.97))

    if keys[pygame.K_ESCAPE]:
        pygame.quit()
        sys.exit()

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.MOUSEWHEEL:
            if event.y == 1 and len(sprites) < MAX_BALLS:
                addSprite(Ball())
            elif event.y == -1 and len(sprites) > 1:
                for ball in reversed(sprites):
                    if not ball.removing and not ball.grabbed and sprites.index(ball) > 0:
                        ball.removing = True
                        break
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
