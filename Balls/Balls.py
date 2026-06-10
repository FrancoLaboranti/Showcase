import math
import time
import random
import struct
import colorsys
import pygame, sys
import pygame.freetype
import pygame.gfxdraw
from pygame.locals import *
import pymunk


# --- Tuning knobs --------------------------------------------------------------
#
# This is the pymunk-based rewrite. The hand-rolled physics engine (with its own
# sleep state machine, BFS wake check, settle damp, position+velocity gates,
# spatial hash, impulse resolver) is in handrolled/Balls.py — see that file for
# the history of what each constant meant before.
#
# Now pymunk owns: integration, broadphase, sequential-impulse solver, island
# sleeping, contact persistence. So this knob block is mostly visuals / sound /
# UX — physics knobs collapse down to gravity, restitution, friction, damping.
# ------------------------------------------------------------------------------

BALL_RADIUS_MIN    = 0.02     # smallest ball radius as a fraction of (screenX+screenY)/2 (passed through sper()).
BALL_RADIUS_MAX    = 0.065    # largest ball radius. Bigger balls = heavier (mass ∝ radius²) and lower pitch.

GRAVITY            = 3000.0   # px/s² downward (positive y = down in screen coords; matches pymunk's gravity direction conventions when y-axis isn't flipped).
JUMP_VELOCITY      = 2400.0   # px/s — upward impulse on each right-click jump (flappy-bird hop).

BALL_FRICTION      = 0.4      # ball↔ball tangential friction. Higher = more rolling / less sliding.
WALL_FRICTION      = 0.6      # walls vs balls (controls how much horizontal speed bleeds off when sliding along floor/walls).

# Restitution is overridden per pair-type in pre_solve callbacks (see _ballBallPreSolve / _ballWallPreSolve).
# This decouples "ball-ball bounce" from "ball-wall bounce" — pymunk's default combining is multiplicative,
# which means setting shape.elasticity to e gives 0.4·0.4 = 0.16 ball-ball and 0.4·0.7 = 0.28 ball-wall:
# both feel dead, especially the floor. By overriding the arbiter directly we get exact control.
BALL_BALL_RESTITUTION = 0.3   # how bouncy ball-on-ball is. Higher = livelier piles (more jitter risk), lower = sticky/dampened.
BALL_WALL_RESTITUTION = 0.65  # how bouncy ball-on-wall is. Matches the old hand-rolled FLOOR_BOUNCE feel.

AIR_DAMPING        = 0.6      # space.damping per-second velocity multiplier (0.6 = loses 40 %/s in the air). Direct equivalent of the old AIR_FRICTION.

GROWTH_RATE        = 500      # px/s — visual radius animation on spawn/remove. The physics body is added to the world only once the visual radius reaches targetRadius (and removed immediately on shrink-out).
MAX_BALLS          = 100      # upper bound for scroll-up spawns.

MOUSE_SMOOTH_TC    = 0.04     # time constant (sec) of the mouse-velocity low-pass filter (used as throw velocity on release).

GRAB_MAX_SPEED     = 15000.0   # px/s cap on the velocity-chase used while a ball is grabbed. Keeps the grabbed ball from tunneling through walls or other balls when the user flicks the mouse hard. Far below the wall/ball tunneling thresholds, so safe.
AUTO_FLING_ENABLED = False     # False = disable the "cursor leaves the playable zone → auto-release with fling velocity" behaviour. Ball stays grabbed even when the cursor enters the EDGE_MARGIN strip; you have to release LMB manually. Useful for testing without the auto-fling getting in the way.

# pymunk space configuration
SOLVER_ITERATIONS  = 10       # space.iterations. Default is 10. Higher = more accurate (less penetration), lower = cheaper. Replaces the old COLLISION_ITERATIONS knob.
PHYSICS_SUBSTEPS   = 3        # number of pymunk steps per render frame. Smaller per-step displacement → fewer tunneling cases AND more accurate collision resolution in tight piles. CPU cost scales linearly; 3 is plenty for ~100 balls.
SLEEP_DELAY        = 0.5      # seconds an island must be at rest before pymunk puts it to sleep. Single knob replaces SLEEP_DELAY + SLEEP_POS_THRESHOLD + SLEEP_VX_THRESHOLD + SLEEP_VY_THRESHOLD + SETTLE_DAMP from the hand-rolled version.
IDLE_SPEED         = 30.0     # |v| below which a body counts as "at rest" for sleep accumulation. pymunk's default (0) auto-derives from gravity; setting it explicitly here for predictability.

# Collision-type tags (used by space.on_collision to route post_solve callbacks)
COLLISION_TYPE_BALL = 1
COLLISION_TYPE_WALL = 2

# --- Sound --------------------------------------------------------------------

SAMPLE_RATE        = 22050    # Hz, mono 16-bit. Don't touch — would invalidate every pre-baked sound buffer.

IMPACT_VOL_SCALE   = 1500     # impact speed (px/s) that maps to full volume.
IMPACT_MIN_VEL     = 500      # velocity threshold below which no sound plays (free balls).
IMPACT_MIN_VEL_GRABBED = 800  # separate, higher threshold when a grabbed ball is involved (mouse velocities spike easily).

MAX_SOUNDS_PER_FRAME = 1      # hard cap on how many impact sounds can play per frame.
IMPACT_COOLDOWN    = 0.12     # seconds — minimum time between any two impact sounds (global rate-limit).

PITCH_PRIORITY_BIAS = 4.0     # bass-heavy weight: weight(hit) = intensity · (1 + bias · (1 − pitchNorm)).
PITCH_JITTER       = 2        # per-impact pitch variation in slot units (±this many slots randomly).

SOUND_FILTER_THRESHOLD = 2    # ball count at or above which IMPACT_COOLDOWN + MAX_SOUNDS_PER_FRAME apply. Below: every queued impact plays.

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
        self.radius = sper(0.001)                                                  # visual radius starts tiny and grows toward targetRadius; physics body is only added to the world once we reach targetRadius
        self.grabbed = False
        self.pinned = False
        self.removing = False
        self._inWorld = False                                                      # tracks whether body+shape are currently part of pymunk space (false while growing in, false after starting to shrink out)
        self._sphereSurf = None

        # Visuals: color, voice, pitch slot, style, overlay color — same logic as the hand-rolled version
        hue = random.random()
        rH, gH, bH = colorsys.hsv_to_rgb(hue, random.uniform(0.95, 1.0), random.uniform(0.95, 1.0))
        self.color = (int(rH * 255), int(gH * 255), int(bH * 255))
        sizeMin, sizeMax = sper(BALL_RADIUS_MIN), sper(BALL_RADIUS_MAX)
        sizeNorm = (self.targetRadius - sizeMin) / max(1e-6, sizeMax - sizeMin)
        self.soundIdx = max(0, min(N_PITCH_SLOTS - 1, int(round((1 - sizeNorm) * (N_PITCH_SLOTS - 1)))))
        self.voiceType = random.choices(('marble', 'wood', 'rubber', 'pop'), weights=(30, 30, 10, 30))[0]
        styleRoll = random.random()
        if styleRoll < 0.05:
            self.style = 'striped_flat'
            self.styleAngle = random.uniform(0, math.pi)
            self.styleNStripes = random.randint(3, 7)
        elif styleRoll < 0.10:
            self.style = 'striped_sphere'
            self.styleAngle = random.uniform(0, math.pi)
            self.styleNStripes = random.randint(3, 7)
        elif styleRoll < 0.15:
            self.style = 'striped_spiral'
            self.styleAngle = random.uniform(0, 2 * math.pi)
            self.styleNStripes = random.randint(3, 6)
            self.styleHanded   = random.choice((-1, 1))
        elif styleRoll < 0.20:
            self.style = 'striped_diamond'
            self.styleAngle = random.uniform(0, math.pi)
            self.styleNStripes = random.randint(5, 8)
        elif styleRoll < 0.25:
            self.style = 'striped_pinwheel'
            self.styleAngle = random.uniform(0, 2 * math.pi)
            self.styleNStripes = random.randint(5, 8)
            self.styleTwist    = random.uniform(0.6, 1.2) * random.choice((-1, 1))
        elif styleRoll < 0.35:
            self.style = 'dotted_sphere'
            self.styleNDots = random.randint(5, 8)
        elif styleRoll < 0.45:
            self.style = 'dotted_candy'
            self.styleNDots = random.randint(6, 12)
        elif styleRoll < 0.55:
            self.style = 'dotted_hex'
        else:
            self.style = 'plain'

        if self.style == 'plain':
            self.overlayColor = None
        elif self.style == 'dotted_candy':
            self.overlayColor = modifyColorPerc(self.color, 1.8)
        else:
            overlayRoll = random.random()
            if overlayRoll < 0.60:
                self.overlayColor = (255, 255, 255)
            elif overlayRoll < 0.85:
                self.overlayColor = modifyColorPerc(self.color, 0.30)
            else:
                hue2 = (hue + 0.5) % 1.0
                r2, g2, b2 = colorsys.hsv_to_rgb(hue2, 0.95, 1.0)
                self.overlayColor = (int(r2 * 255), int(g2 * 255), int(b2 * 255))

        # pymunk body + shape. moment_for_circle gives the proper rotational inertia.
        # Balls DO rotate physically (rolling friction works correctly), but the rendered sphere is blitted axis-aligned —
        # the pattern doesn't visually rotate. That's a deliberate trade-off: real rolling physics + simple render.
        # (float('inf') moment to disable rotation entirely is NOT allowed by pymunk — step() requires moment < inf.)
        self.mass = self.targetRadius * self.targetRadius                          # mass ∝ area (2D); kept consistent with the hand-rolled version for momentum feel
        self._moment = pymunk.moment_for_circle(self.mass, 0, self.targetRadius)   # cached so we can restore it after KINEMATIC↔DYNAMIC transitions wipe it (pymunk doesn't preserve mass/moment across body_type changes)
        self.body = pymunk.Body(self.mass, self._moment)
        self.body.position = (random.uniform(xper(0.05), xper(0.95)),
                              random.uniform(yper(0.05), yper(0.6)))
        self.shape = pymunk.Circle(self.body, self.targetRadius)
        self.shape.elasticity = BALL_BALL_RESTITUTION                              # only matters if a pre_solve callback isn't installed; we override the arbiter in pre_solve so this is mostly a fallback
        self.shape.friction = BALL_FRICTION
        self.shape.collision_type = COLLISION_TYPE_BALL
        self.shape.ball_ref = self                                                 # backref so collision handlers can look up the Ball from the shape

    # --- Position / velocity properties — read directly from the pymunk body so the rest of the code (rendering, debug overlay, RMB jump) can keep using self.x / self.y / self.vx / self.vy as if they were plain attributes
    @property
    def x(self): return self.body.position.x
    @property
    def y(self): return self.body.position.y
    @property
    def vx(self): return self.body.velocity.x
    @property
    def vy(self): return self.body.velocity.y
    @property
    def sleeping(self):
        try:
            return self.body.is_sleeping
        except Exception:
            return False                                                            # bodies not in a space raise; treat those as not-sleeping

    def addToWorld(self):
        if not self._inWorld:
            space.add(self.body, self.shape)
            self._inWorld = True

    def removeFromWorld(self):
        if self._inWorld:
            space.remove(self.body, self.shape)
            self._inWorld = False

    def grab(self):
        """The ball stays DYNAMIC; we just flip a flag. The chase logic in process() overrides body.velocity every frame
        to make the ball converge on the mouse position. This way the ball still collides naturally with walls and
        other balls (no KINEMATIC tunneling, no body_type toggling, no mass/moment to restore on release).

        Records the cursor-to-ball-center offset so the grip-point on the ball stays glued to the cursor. With this
        offset, the first chase frame has dx=dy=0 by construction (target = cursor − offset = ball center, equal to
        the current body position), so the ball stays put on grab and doesn't fire into a neighbor — same anti-shove
        guarantee as snapping the cursor to the ball center, but without the side-effect of `pygame.mouse.set_pos`,
        which under pygame.SCALED can land the cursor in an unexpected place (we were seeing cursor jumps to the
        opposite corner when grabbing near an edge)."""
        if not self._inWorld:
            return
        self.grabbed = True
        self.pinned = False
        self.body.activate()                                                       # in case the ball was sleeping when grabbed
        self._grabOffsetX = mouseX - self.body.position.x
        self._grabOffsetY = mouseY - self.body.position.y

    def release(self):
        """Commit the throw on LMB release: linear velocity from the filtered cursor velocity (mouseVx/Vy), and
        angular derived from the same vx (ω = vx/radius) so spin and throw stay in lock-step. Why not body.velocity
        / a separately tracked pending spin: if the cursor was stationary, clamped against a wall, or the ball had
        already converged onto the cursor, the chase-derived numbers would be ~0 and the ball would drop with no
        throw and no spin. mouseVx/Vy uses the actual cursor speed at the moment of release for both."""
        if not self.grabbed:
            return
        self.grabbed = False
        vx, vy = mouseVx, mouseVy
        speed_sq = vx*vx + vy*vy
        cap2 = GRAB_MAX_SPEED * GRAB_MAX_SPEED
        if speed_sq > cap2:
            scale = GRAB_MAX_SPEED / math.sqrt(speed_sq)
            vx *= scale
            vy *= scale
        self.body.velocity = (vx, vy)
        self.body.angular_velocity = vx / self.radius

    def pin(self):
        """Q-pin: ball stays DYNAMIC but its position+velocity are overwritten every frame to keep it nailed in place.
        Stays effectively static against other balls because impulses on it are wiped each frame; visually rock solid."""
        if not self._inWorld:
            return
        self.grabbed = False
        self.pinned = True
        self._pinPos = (self.body.position.x, self.body.position.y)
        self.body.velocity = (0, 0)

    def unpin(self):
        if not self.pinned:
            return
        self.pinned = False

    def jump(self):
        if not self._inWorld or self.grabbed or self.pinned:
            return
        self.body.activate()                                                       # wake any sleeping island so the jump takes effect
        self.body.velocity = (self.body.velocity.x, -JUMP_VELOCITY)                # preserve horizontal velocity, override vertical

    def process(self):
        # 1. Growth animation: visual radius ramps to targetRadius. Once fully grown, the body is added to pymunk.
        if self.radius < self.targetRadius and not self.removing:
            self.radius = min(self.targetRadius, self.radius + deltaT * GROWTH_RATE)
            if self.radius >= self.targetRadius and not self._inWorld:
                self.addToWorld()
            return                                                                  # don't apply grab logic / wrap while still growing

        # 2. Shrink animation on removal: body is removed from pymunk immediately, visual continues to shrink.
        if self.removing:
            if self._inWorld:
                self.removeFromWorld()
            self.radius -= deltaT * GROWTH_RATE
            if self.radius < sper(0.001):
                sprites.remove(self)
            return

        # 3. Held-LMB grab: passing the cursor over any ball while LMB is held grabs it. Requires the cursor to be
        # INSIDE the playable zone — without this guard, an auto-released ball pinned against a wall would re-grab
        # itself on the very next frame (cursor outside the screen edge is still inside the ball's radius), then
        # immediately auto-release again, looping at 0 velocity and looking "stuck". With the guard, the user has
        # to bring the cursor back into the zone to grab again (same ball or any other — that's the desired flow).
        cursorInZone = True
        if WALL_MODE == 1 and (mouseX < EDGE_MARGIN or mouseX > screenX - EDGE_MARGIN or mouseY < EDGE_MARGIN or mouseY > screenY - EDGE_MARGIN):
            cursorInZone = False
        elif WALL_MODE == 2 and (mouseY < EDGE_MARGIN or mouseY > screenY - EDGE_MARGIN):
            cursorInZone = False
        if mouseLeft and cursorInZone and not self.grabbed and not self.pinned:
            if getDist((self.x, self.y), (mouseX, mouseY)) < self.radius and not any(b.grabbed for b in sprites):
                self.grab()
        elif not mouseLeft and self.grabbed:
            self.release()

        # 4. Velocity-chase while grabbed: compute the velocity needed to land on the mouse position this frame,
        # cap it (anti-tunneling), and assign. The ball is DYNAMIC so it collides with walls/other balls correctly —
        # if the path to the mouse is blocked, the ball stays put and natural impulses push the obstacles instead.
        if self.grabbed and deltaT > 0:
            targetX = mouseX - self._grabOffsetX                                    # chase toward (cursor − click-offset) so the grip-point on the ball stays glued to the cursor instead of the center snapping to it
            targetY = mouseY - self._grabOffsetY
            r = self.radius
            # Auto-release trigger uses the CURSOR position (not target) — same criterion as the grab check above,
            # so the two are symmetric: grab is allowed iff cursor is in the zone, auto-release fires iff it leaves.
            # If we used "target outside playfield" instead, a large ball grabbed by its edge would auto-release the
            # moment the cursor approached the screen edge — even though the cursor is still on-screen.
            cursorOutsideZone = False
            if AUTO_FLING_ENABLED:
                if WALL_MODE == 1 and (mouseX < EDGE_MARGIN or mouseX > screenX - EDGE_MARGIN or mouseY < EDGE_MARGIN or mouseY > screenY - EDGE_MARGIN):
                    cursorOutsideZone = True
                elif WALL_MODE == 2 and (mouseY < EDGE_MARGIN or mouseY > screenY - EDGE_MARGIN):
                    cursorOutsideZone = True
            if cursorOutsideZone:
                # Fling-release velocity = filtered mouse velocity (mouseVx/Vy is a low-pass with MOUSE_SMOOTH_TC).
                # NOT (target − position)/dt: if the ball was sitting clamped against a wall while the cursor moved
                # across the zone, that gap would launch the ball way faster than the actual gesture. Using mouseVx/Vy
                # makes the throw speed match the cursor's actual speed at the moment of crossing the edge.
                vx, vy = mouseVx, mouseVy
            else:                                                                   # normal chase: clamp target into the playfield so the ball doesn't "load" against a wall when held there (dx=0 → vx=0, no stored push), then chase the target at one frame's worth of velocity.
                if WALL_MODE == 1:
                    targetX = max(r, min(screenX - r, targetX))
                if WALL_MODE in (1, 2):
                    targetY = max(r, min(screenY - r, targetY))
                dx = targetX - self.body.position.x
                dy = targetY - self.body.position.y
                vx = dx / deltaT
                vy = dy / deltaT
            speed_sq = vx*vx + vy*vy
            cap2 = GRAB_MAX_SPEED * GRAB_MAX_SPEED
            if speed_sq > cap2:
                scale = GRAB_MAX_SPEED / math.sqrt(speed_sq)
                vx *= scale
                vy *= scale
            self.body.velocity = (vx, vy)
            # Spin model: rolling on a horizontal floor with the rotation axis horizontal in 3D (out-of-plane in
            # this 2D side-view). Only the horizontal velocity contributes — ω = vx/radius. Vertical motion
            # doesn't induce spin (a ball flung straight up doesn't roll). Positive vx → positive ω (clockwise
            # visually in y-down screen, the natural rolling direction for rightward motion).
            # While grabbed the body stays visually still (angular_velocity = 0); spin is committed on release.
            self.body.angular_velocity = 0.0
            if cursorOutsideZone:                                                   # auto-release: the ball becomes a free dynamic body carrying the fling velocity above. Spin derived from the same vx we just assigned, so throw and roll stay coupled. The grab condition (step 3) also requires cursor-in-zone, so we won't re-grab the same ball this frame — only after the cursor comes back into the playable zone.
                self.body.angular_velocity = vx / self.radius
                self.grabbed = False
            return                                                                  # grabbed balls skip wrap

        # 5. Pin: pin-position + zero velocity overwritten each frame. Other balls colliding into it nudge it
        # within the step, but our overwrite snaps it back next frame — visually nailed in place.
        if self.pinned:
            self.body.position = self._pinPos
            self.body.velocity = (0, 0)
            self.body.angular_velocity = 0                                          # pinned balls don't spin either — rock solid
            return

        # 6. Wrap modes (sides and/or top/bottom). pymunk has no native wrapping — we teleport here.
        r = self.radius
        pos = self.body.position
        x, y = pos.x, pos.y
        if WALL_MODE in (2, 4):                                                     # x-axis wrap en los modos sin laterales (2 = techo+piso, 4 = sin nada)
            if x < -r:
                x = screenX + r
            elif x > screenX + r:
                x = -r
        if WALL_MODE in (3, 4):                                                     # y-axis wrap en los modos sin techo/piso (3 = sólo laterales, 4 = sin nada)
            if y < -r:
                y = screenY + r
            elif y > screenY + r:
                y = -r
        if x != pos.x or y != pos.y:
            self.body.position = (x, y)

    def _bakeSphere(self):
        """Render gradient + (optional pattern) + hotspot into a per-ball Surface once (when fully grown).
        All per-frame draw becomes a single blit."""
        r = int(self.targetRadius)
        size = r * 2 + 4
        cx, cy = size * 0.5, size * 0.5
        lx, ly = 0.35, -0.94                                                       # fixed light direction (upper-right) baked into every ball
        layers = 100

        def renderLayers(target, baseColor):
            for i in range(layers):
                t = i / (layers - 1)
                layerRadius = r * (1 - 0.55 * t)
                offset = r * 0.45 * t
                tint = 0.45 + 1.20 * t
                pygame.draw.circle(target, modifyColorPerc(baseColor, tint), (cx + lx * offset, cy + ly * offset), layerRadius)

        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        renderLayers(surf, self.color)

        patternStyles = ('striped_flat', 'striped_sphere', 'striped_spiral', 'striped_diamond', 'striped_pinwheel', 'dotted_sphere', 'dotted_candy', 'dotted_hex')
        if self.style in patternStyles:
            overlaySphere = pygame.Surface((size, size), pygame.SRCALPHA)
            renderLayers(overlaySphere, self.overlayColor)
            dotPositions = None
            if   self.style == 'striped_flat':     mask = _makeStripeMaskFlat    (size, self.styleNStripes, self.styleAngle)
            elif self.style == 'striped_sphere':   mask = _makeStripeMaskSphere  (size, self.styleNStripes, self.styleAngle)
            elif self.style == 'striped_spiral':   mask = _makeStripeMaskSpiral  (size, self.styleNStripes, self.styleAngle, self.styleHanded)
            elif self.style == 'striped_diamond':  mask = _makeStripeMaskDiamond (size, self.styleNStripes, self.styleAngle)
            elif self.style == 'striped_pinwheel': mask = _makeStripeMaskPinwheel(size, self.styleNStripes, self.styleAngle, self.styleTwist)
            elif self.style == 'dotted_sphere':    mask, dotPositions = _makeDotMaskSphere(size, r, self.styleNDots)
            elif self.style == 'dotted_candy':     mask, dotPositions = _makeDotMaskCandy (size, r, self.styleNDots)
            else:                                  mask, dotPositions = _makeDotMaskHex   (size, r)
            if dotPositions and max(self.overlayColor) < 200:
                rimLayer = pygame.Surface((size, size), pygame.SRCALPHA)
                rimColor = (0, 0, 0, 70)
                for px, py, dotR in dotPositions:
                    rimR = dotR + max(1.0, dotR * 0.07)
                    pygame.draw.circle(rimLayer, rimColor, (int(px), int(py)), int(rimR))
                surf.blit(rimLayer, (0, 0))
            overlaySphere.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(overlaySphere, (0, 0))

        specR = max(2.0, r * 0.06)
        hotCx = cx + lx * r * 0.6
        hotCy = cy + ly * r * 0.6
        _drawHotspot(surf, hotCx, hotCy, specR)
        pygame.draw.circle(surf, (255, 255, 255, 35), (int(cx), int(cy)), r, 1)
        self._sphereSurf = surf

    def draw(self):
        if self.grabbed or self.pinned or (showInfo and self.id == 1):             # glow ring for selection feedback + the SPACE-overlay tracking ball
            haloColor = modifyColorPerc(self.color, 1.7)
            glowLayers = 6
            outerR = self.radius * 1.10
            glowSize = int(outerR * 2) + 4
            glowSurf = pygame.Surface((glowSize, glowSize), pygame.SRCALPHA)
            hcx, hcy = glowSize // 2, glowSize // 2
            for i in range(glowLayers):
                u = i / (glowLayers - 1)
                rL = int(outerR - (outerR - self.radius) * u)
                alpha = int(90 + 130 * u)
                pygame.gfxdraw.filled_circle(glowSurf, hcx, hcy, rL, (*haloColor, alpha))
            windowSurface.blit(glowSurf, (self.x - hcx, self.y - hcy))

        if self.radius < self.targetRadius:                                        # GROWING or SHRINKING — slow per-frame draw at the current radius
            lightX, lightY = xper(0.5), -yper(0.2)
            dx, dy = lightX - self.x, lightY - self.y
            d = math.sqrt(dx*dx + dy*dy) or 1
            lx, ly = dx/d, dy/d
            growLayers = 12
            for i in range(growLayers):
                t = i / (growLayers - 1)
                layerRadius = self.radius * (1 - 0.55 * t)
                offset = self.radius * 0.45 * t
                tint = 0.45 + 1.20 * t
                pygame.draw.circle(windowSurface, modifyColorPerc(self.color, tint), (self.x + lx * offset, self.y + ly * offset), layerRadius)
        else:                                                                      # GROWN — blit the baked sphere, rotated by the body's current angle so the pattern visually rolls with the physics. Pymunk's moment_for_circle gives finite rotational inertia, so balls spin from friction / glancing impacts. The hotspot + gradient rotate with the pattern (not strictly correct for a sphere lit from a fixed direction, but reads as a stamped rolling ball — cheap and convincing).
            if self._sphereSurf is None:
                self._bakeSphere()
            angle = self.body.angle
            if angle == 0.0:                                                       # fast path for unrotated balls (newly spawned, or balls that never got spun)
                half = self._sphereSurf.get_width() * 0.5
                windowSurface.blit(self._sphereSurf, (self.x - half, self.y - half))
            else:
                rotated = pygame.transform.rotate(self._sphereSurf, -math.degrees(angle))  # negative because pygame's y-axis is flipped vs the screen orientation pymunk uses for angle convention
                rw, rh = rotated.get_width(), rotated.get_height()
                windowSurface.blit(rotated, (self.x - rw * 0.5, self.y - rh * 0.5))

        if showInfo and self.id == 1:
            speed = math.sqrt(self.vx*self.vx + self.vy*self.vy)
            createText(20, "Speed: %.0f" % speed, 'topright', (255, 150, 0), xper(0.99), yper(0.015))
            createText(20, "Vx: %.0f" % self.vx,  'topright', (0, 200, 200), xper(0.99), yper(0.045))
            createText(20, "Vy: %.0f" % self.vy,  'topright', (255, 0, 255), xper(0.99), yper(0.075))
            pygame.draw.line(windowSurface, (255, 0, 255), (self.x, self.y), (self.x + self.vx*0.05, self.y + self.vy*0.05), 5)


pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=256)
pygame.init()

_desktopSize = pygame.display.get_desktop_sizes()[0]                              # SCALED requires explicit dimensions — (0,0) is rejected. Query the display's native size and pass it through.
windowSurface = pygame.display.set_mode(_desktopSize, pygame.FULLSCREEN | pygame.SCALED, depth=32, display=0, vsync=1)   # vsync=1 syncs the framebuffer flip to the monitor refresh — kills the horizontal tearing line that shows up under high motion. SCALED is needed in SDL2 for vsync to be enforced strictly (without it the driver may ignore the hint). Tearing doesn't appear in screenshots (capture reads the composed buffer, not the in-progress scanout).
screenX, screenY = windowSurface.get_size()
pygame.display.set_caption('Balls')

font = pygame.freetype.SysFont('Century Gothic', 0)


# --- Sound synthesis (unchanged from the hand-rolled version) ------------------

def _makeMarble(freq, duration=0.18, amp=0.40,
                ratios=(1.0, 2.05, 3.42, 5.6),
                partialAmps=(1.0, 0.5, 0.28, 0.15),
                noiseAmp=0.7, noiseTime=0.004):
    """Glass-marble-on-ceramic strike."""
    n = int(SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    decayTimes  = [duration * 0.45 / (1 + 0.55 * i) for i in range(len(ratios))]
    omegas      = [2 * math.pi * freq * r for r in ratios]
    normSum     = sum(partialAmps)
    noiseSamples = max(1, int(SAMPLE_RATE * noiseTime))
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        for k in range(len(ratios)):
            s += partialAmps[k] * math.exp(-t / decayTimes[k]) * math.sin(omegas[k] * t)
        s /= normSum
        if i < noiseSamples:
            s += (random.random() * 2 - 1) * noiseAmp * (1 - i / noiseSamples)
        v = int(s * amp * 32767)
        struct.pack_into('<h', buf, i * 2, max(-32768, min(32767, v)))
    return pygame.mixer.Sound(buffer=bytes(buf))


def _makeWood(freq, duration=0.13, amp=0.42):
    """Hollow wooden knock."""
    n = int(SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    ratios      = (1.0, 1.45)
    partialAmps = (1.0, 0.35)
    decayTimes  = (0.045, 0.025)
    omegas      = [2 * math.pi * freq * r for r in ratios]
    normSum     = sum(partialAmps)
    noiseSamples = max(1, int(SAMPLE_RATE * 0.010))
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
    """Cartoon boing."""
    n = int(SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    decay = 0.075
    attackSamples = max(1, int(SAMPLE_RATE * 0.004))
    sweepTau = 0.038
    fStart, fEnd = freq * 1.9, freq * 0.55
    phase = 0.0
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
    """Snap with body."""
    n = int(SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    noiseDecay = 0.012
    toneDecay1 = 0.045
    toneDecay2 = 0.025
    omega1 = 2 * math.pi * freq * 1.30
    omega2 = 2 * math.pi * freq * 2.60
    for i in range(n):
        t = i / SAMPLE_RATE
        noise = (random.random() * 2 - 1) * 0.65 * math.exp(-t / noiseDecay)
        tone  = (0.50 * math.sin(omega1 * t) * math.exp(-t / toneDecay1)
              +  0.20 * math.sin(omega2 * t) * math.exp(-t / toneDecay2))
        s = noise + tone
        v = int(s * amp * 32767)
        struct.pack_into('<h', buf, i * 2, max(-32768, min(32767, v)))
    return pygame.mixer.Sound(buffer=bytes(buf))


_IMPACT_FREQS  = (510, 580, 645, 720, 795, 870, 960, 1040, 1125, 1220, 1320, 1430)
N_PITCH_SLOTS  = len(_IMPACT_FREQS)
ballHitSounds  = {
    'marble': [_makeMarble(f) for f in _IMPACT_FREQS],
    'wood':   [_makeWood  (f) for f in _IMPACT_FREQS],
    'rubber': [_makeRubber(f) for f in _IMPACT_FREQS],
    'pop':    [_makePop   (f) for f in _IMPACT_FREQS],
}


# --- Sound queue (unchanged interface, fed from collision handlers now) --------

_impactQueue = []
_lastImpactTime = 0.0

def _playImpact(intensity, voiceType, soundIdx, minVel=IMPACT_MIN_VEL):
    if intensity < minVel:
        return
    if PITCH_JITTER:
        soundIdx = max(0, min(N_PITCH_SLOTS - 1, soundIdx + random.randint(-PITCH_JITTER, PITCH_JITTER)))
    _impactQueue.append((intensity, voiceType, soundIdx))

def _flushImpacts():
    global _lastImpactTime
    if not _impactQueue:
        return
    now = time.time()
    if len(sprites) < SOUND_FILTER_THRESHOLD:
        for intensity, voice, idx in _impactQueue:
            sound = ballHitSounds[voice][idx]
            sound.set_volume(min(1.0, intensity / IMPACT_VOL_SCALE))
            sound.play()
        _lastImpactTime = now
        _impactQueue.clear()
        return
    if now - _lastImpactTime < IMPACT_COOLDOWN:
        _impactQueue.clear()
        return
    weights = [intensity * (1 + PITCH_PRIORITY_BIAS * (1 - idx / max(1, N_PITCH_SLOTS - 1)))
               for intensity, _voice, idx in _impactQueue]
    k = min(MAX_SOUNDS_PER_FRAME, len(_impactQueue))
    picks = random.choices(_impactQueue, weights=weights, k=k)
    for intensity, voice, idx in picks:
        sound = ballHitSounds[voice][idx]
        sound.set_volume(min(1.0, intensity / IMPACT_VOL_SCALE))
        sound.play()
    _lastImpactTime = now
    _impactQueue.clear()


# --- Drawing helpers (unchanged from the hand-rolled version) ------------------

def _drawHotspot(surf, cx, cy, specR):
    ix, iy = int(cx), int(cy)
    rCore = max(2, int(specR))
    haloSize = rCore * 8
    halo = pygame.Surface((haloSize, haloSize), pygame.SRCALPHA)
    hcx, hcy = haloSize // 2, haloSize // 2
    pygame.gfxdraw.filled_circle(halo, hcx, hcy, rCore * 3, (255, 255, 255, 22))
    pygame.gfxdraw.filled_circle(halo, hcx, hcy, rCore * 2, (255, 255, 255, 55))
    surf.blit(halo, (ix - hcx, iy - hcy))
    pygame.gfxdraw.filled_circle(surf, ix, iy, rCore, (255, 255, 255, 255))


def _makeStripeMaskFlat(size, nStripes, angle):
    big = int(size * 1.8)
    flat = pygame.Surface((big, big), pygame.SRCALPHA)
    cxBig = big * 0.5
    bandSpacing = size / nStripes
    bandW = bandSpacing * 0.5
    for i in range(nStripes):
        offset = (i - (nStripes - 1) * 0.5) * bandSpacing
        x = cxBig + offset - bandW * 0.5
        pygame.draw.rect(flat, (255, 255, 255, 255), (int(x), 0, int(bandW), big))
    rotated = pygame.transform.rotate(flat, math.degrees(angle))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    rx = (rotated.get_width() - size) // 2
    ry = (rotated.get_height() - size) // 2
    mask.blit(rotated, (-rx, -ry))
    return mask


def _makeStripeMaskSphere(size, nStripes, angle, fillRatio=0.5):
    big = int(size * 1.8)
    flat = pygame.Surface((big, big), pygame.SRCALPHA)
    cxBig, cyBig = big * 0.5, big * 0.5
    sphereR = size * 0.5
    phiStep = math.pi / nStripes
    halfW   = phiStep * 0.5 * fillRatio
    yMin = max(0, int(cyBig - sphereR))
    yMax = min(big - 1, int(cyBig + sphereR))
    for yPix in range(yMin, yMax + 1):
        dy = yPix - cyBig
        crossR = math.sqrt(max(0.0, sphereR*sphereR - dy*dy))
        for i in range(nStripes):
            phiC = -math.pi * 0.5 + (i + 0.5) * phiStep
            xL = cxBig + math.sin(phiC - halfW) * crossR
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
    big = int(size * 1.8)
    flat = pygame.Surface((big, big), pygame.SRCALPHA)
    cxBig, cyBig = big * 0.5, big * 0.5
    sphereR = size * 0.5
    bandR   = sphereR * 0.11
    nSteps  = max(120, int(sphereR * nTurns * 6))
    for i in range(nSteps + 1):
        t = i / nSteps
        lat = -math.pi * 0.5 + t * math.pi
        lonBase = handed * t * nTurns * 2 * math.pi
        for lonOffset in (0.0, math.pi):
            lon = lonBase + lonOffset
            lonN = ((lon + math.pi) % (2 * math.pi)) - math.pi
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
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    setA = _makeStripeMaskSphere(size, nStripes, angle,                fillRatio=0.18)
    setB = _makeStripeMaskSphere(size, nStripes, angle + math.pi / 3,  fillRatio=0.18)
    mask.blit(setA, (0, 0))
    mask.blit(setB, (0, 0))
    return mask


def _makeStripeMaskPinwheel(size, nStripes, angle, twist):
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size * 0.5, size * 0.5
    sphereR = size * 0.5
    period = 2 * math.pi / nStripes
    halfPeriod = period * 0.5
    twoPiTwist = twist * 2 * math.pi
    yMin = max(0, int(cy - sphereR))
    yMax = min(size - 1, int(cy + sphereR))
    for yPix in range(yMin, yMax + 1):
        dy = yPix - cy
        if abs(dy) > sphereR:
            continue
        crossR = math.sqrt(sphereR*sphereR - dy*dy)
        xMin = max(0, int(cx - crossR))
        xMax = min(size - 1, int(cx + crossR))
        inStripe = False
        runStart = xMin
        for xPix in range(xMin, xMax + 1):
            dx = xPix - cx
            r = math.sqrt(dx*dx + dy*dy)
            if r > sphereR:
                nowStripe = False
            else:
                theta = math.atan2(dy, dx) + angle
                phase = theta + twoPiTwist * (r / sphereR)
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
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    positions = []
    cx, cy = size * 0.5, size * 0.5
    centerR = sphereR * 0.28
    pygame.draw.circle(mask, (255, 255, 255, 255), (cx, cy), centerR)
    positions.append((cx, cy, centerR))
    theta       = math.radians(50)
    depthScale  = math.cos(theta)
    ringR2D     = sphereR * math.sin(theta)
    ringDotR    = centerR * depthScale
    rotation = random.uniform(0, math.pi * 2)
    for i in range(nDots):
        a = rotation + (i / nDots) * math.pi * 2
        dx = cx + math.cos(a) * ringR2D
        dy = cy + math.sin(a) * ringR2D
        pygame.draw.circle(mask, (255, 255, 255, 255), (dx, dy), ringDotR)
        positions.append((dx, dy, ringDotR))
    return mask, positions


def _makeDotMaskCandy(size, sphereR, nDots):
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size * 0.5, size * 0.5
    safeR  = sphereR * 0.85
    minDotR, maxDotR = sphereR * 0.16, sphereR * 0.28
    placed = []
    attempts = 0
    while len(placed) < nDots and attempts < 400:
        attempts += 1
        rDot = random.uniform(minDotR, maxDotR)
        d    = math.sqrt(random.random()) * max(0.0, safeR - rDot * 0.4)
        a    = random.uniform(0, 2 * math.pi)
        px, py = cx + math.cos(a) * d, cy + math.sin(a) * d
        if all(math.hypot(px - q[0], py - q[1]) > (rDot + q[2]) * 0.82 for q in placed):
            placed.append((px, py, rDot))
            pygame.draw.circle(mask, (255, 255, 255, 255), (px, py), rDot)
    return mask, placed


def _makeDotMaskHex(size, sphereR):
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    positions = []
    cx, cy = size * 0.5, size * 0.5
    spacing  = sphereR * 0.30
    dotRBig  = spacing * 0.34
    dotRSmall= spacing * 0.20
    cellW    = spacing
    cellH    = spacing * math.sqrt(3) * 0.5
    clipR    = sphereR - dotRBig * 1.6
    bigParity = random.randint(0, 1)
    nRows = int(sphereR / cellH) + 2
    nCols = int(sphereR / cellW) + 2
    for row in range(-nRows, nRows + 1):
        rowOff = cellW * 0.5 if (row & 1) else 0.0
        for col in range(-nCols, nCols + 1):
            px = cx + col * cellW + rowOff
            py = cy + row * cellH
            dx, dy = px - cx, py - cy
            if dx*dx + dy*dy <= clipR * clipR:
                dotR = dotRBig if ((row + col) & 1) == bigParity else dotRSmall
                pygame.draw.circle(mask, (255, 255, 255, 255), (px, py), dotR)
                positions.append((px, py, dotR))
    return mask, positions


# --- Geometry / color helpers (shared with the rest of the repo) ---------------

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


# --- Globals -------------------------------------------------------------------

deltaT = 0
iniT = time.time()
clock = pygame.time.Clock()
keys = None
mouseX, mouseY = pygame.mouse.get_pos()
mouseLeft = mouseRight = False
prevMouseRight = False
showFPS = False
prevFKey = False
prevRKey = False
prevQKey = False
prevMouseX, prevMouseY = mouseX, mouseY
mouseVx = 0.0
mouseVy = 0.0
sprites = []
showInfo = None
WALL_MODE = 1


# --- pymunk space + walls + collision handlers ---------------------------------

space = pymunk.Space()
space.gravity = (0, GRAVITY)
space.damping = AIR_DAMPING                                                        # per-second velocity multiplier — directly replaces the old AIR_FRICTION
space.iterations = SOLVER_ITERATIONS
space.sleep_time_threshold = SLEEP_DELAY                                           # seconds an island must rest before sleeping
space.idle_speed_threshold = IDLE_SPEED                                            # |v| considered "at rest" for the sleep accumulator

_wallShapes = []                                                                   # rebuilt whenever WALL_MODE changes

WALL_THICKNESS = 500                                                               # half-thickness of the segment capsule. Walls are invisible (offscreen entirely) but THICK toward the outside — collision face still aligns with the screen edge (because the centerline sits at -t and the capsule has radius t), but the capsule body extends 2*WALL_THICKNESS pixels offscreen. Side effect (the point): a ball pushed slightly past the screen edge by a high-impulse collision is still INSIDE the capsule, so pymunk's overlap resolution shoves it back in; same for WALL_MODE transitions that leave a ball in the off-screen zone (3 → 2 or 1 now finds the ball inside the capsule and corrects it). Tunneling threshold = 2*(WALL_THICKNESS + ball.radius) / subDt; with t=100 and substeps=3 the threshold is ~70 000 px/s, well beyond any natural ball velocity.
EDGE_MARGIN    = 5                                                                 # interior pixels reserved as "wall zone" — cursor inside this strip counts as outside-the-playable-zone (so auto-release fires when the cursor reaches the wall, not only when it leaves the OS window — pygame clamps mouse pos to the window on Windows, so `mouseX < 0` rarely triggers). Also the visible thickness of the wall lines drawn each frame.

def buildWalls():
    """(Re)build the static wall segments based on current WALL_MODE.
       MODE 1: all 4 walls. MODE 2: top + floor only (sides wrap). MODE 3: no walls (everything wraps).
       Centerlines sit OUTSIDE the visible playfield by WALL_THICKNESS so the capsule's inner face lines up exactly
       with the screen edge. The capsule itself is off-screen and invisible — balls appear to bounce at the screen
       boundary, just like the hand-rolled clamp."""
    global _wallShapes
    # Remove every wall the engine still knows about. Walking space.shapes (instead of just iterating _wallShapes)
    # is paranoid by design: if anything in the past missed a remove (e.g. a previous buildWalls that bailed out, a
    # space reset, etc.) we'd leak collision faces that show up as "phantom bounces" — exactly the WALL_MODE 2
    # symptom of balls still bouncing on the sides after switching away from MODE 1.
    for s in list(space.shapes):
        if getattr(s, "collision_type", None) == COLLISION_TYPE_WALL:
            space.remove(s)
    _wallShapes = []
    t = WALL_THICKNESS
    # Top/floor segments are extended laterally past the side-wrap threshold (x = ±max_ball_radius) so a ball
    # near the top or floor that's about to wrap in x can't slip into the gap between the wall endpoint and the
    # wrap threshold — that gap has no collision face and gravity would accelerate the ball indefinitely there
    # (we've seen ~5600 px/s, which is ~2 s of free-fall).
    wrapBuffer = sper(BALL_RADIUS_MAX) + 50                                         # past the wrap threshold by a comfortable margin
    sides = [
        ((-t, -t), (-t, screenY + t)),                                              # left:  capsule from x=-2t to x=0, face at x=0
        ((screenX + t, -t), (screenX + t, screenY + t)),                            # right: capsule from x=screenX to x=screenX+2t, face at x=screenX
    ]
    topbot = [
        ((-wrapBuffer, -t), (screenX + wrapBuffer, -t)),                            # top:   face at y=0, extended laterally so wrap-in-x can't slip past the endpoint
        ((-wrapBuffer, screenY + t), (screenX + wrapBuffer, screenY + t)),          # floor: face at y=screenY, same extension
    ]
    segs = []
    if WALL_MODE == 1:
        segs = sides + topbot
    elif WALL_MODE == 2:                                                            # sin laterales: techo y piso, wrap horizontal
        segs = topbot
    elif WALL_MODE == 3:                                                            # sin techo/piso: laterales, wrap vertical
        segs = sides
    # MODE 4: sin paredes, wrap en ambos ejes — segs queda vacío.
    for (a, b) in segs:
        seg = pymunk.Segment(space.static_body, a, b, t)
        seg.elasticity = BALL_WALL_RESTITUTION                                     # fallback only — pre_solve callback overrides this on every contact
        seg.friction = WALL_FRICTION
        seg.collision_type = COLLISION_TYPE_WALL
        space.add(seg)
        _wallShapes.append(seg)


def _vRelN_from_impulse(arbiter, mass_inv_sum, e):
    """Recover the pre-collision relative normal velocity from the impulse pymunk just applied.
       J = (1+e) * m_eff * vRelN_pre  ⇒  vRelN_pre = J * (1/m1 + 1/m2) / (1+e).
       Returns 0 for "infinite mass on both sides" cases (which shouldn't fire post_solve anyway)."""
    if mass_inv_sum <= 0:
        return 0.0
    j = arbiter.total_impulse.length
    return j * mass_inv_sum / max(0.05, 1 + e)


def _ballBallPreSolve(arbiter, space, data):
    """Override the combined restitution before the solver runs. pymunk's default is multiplicative
    (shape_a.elasticity * shape_b.elasticity), which gives 0.09 for our 0.3·0.3 shapes — way too dead.
    Setting arbiter.restitution explicitly to BALL_BALL_RESTITUTION gives the bounce we actually want."""
    arbiter.restitution = BALL_BALL_RESTITUTION
    return True


def _ballWallPreSolve(arbiter, space, data):
    """Same, for ball-wall: override to BALL_WALL_RESTITUTION so the floor actually bounces."""
    arbiter.restitution = BALL_WALL_RESTITUTION
    return True


def _ballBallPostSolve(arbiter, space, data):
    if not arbiter.is_first_contact:                                               # only fire on the first frame of contact — sustained pile/touch contacts would otherwise spam sound every frame
        return
    a, b = arbiter.shapes
    ballA = getattr(a, 'ball_ref', None)
    ballB = getattr(b, 'ball_ref', None)
    if ballA is None or ballB is None:
        return
    # All balls are DYNAMIC always (grabbed/pinned are flagged but still dynamic), so masses are always finite.
    inv_a = 1.0 / a.body.mass
    inv_b = 1.0 / b.body.mass
    vRelN = _vRelN_from_impulse(arbiter, inv_a + inv_b, arbiter.restitution)       # use the overridden restitution that pre_solve installed, so the sound calc matches the actual bounce
    if vRelN <= 0:
        return
    minVel = IMPACT_MIN_VEL_GRABBED if (ballA.grabbed or ballB.grabbed) else IMPACT_MIN_VEL
    # Smaller ball wins both pitch and voice (higher soundIdx = smaller = higher pitch).
    if ballA.soundIdx >= ballB.soundIdx:
        _playImpact(vRelN, ballA.voiceType, ballA.soundIdx, minVel)
    else:
        _playImpact(vRelN, ballB.voiceType, ballB.soundIdx, minVel)


def _ballWallPostSolve(arbiter, space, data):
    if not arbiter.is_first_contact:                                               # same: skip continuous-contact frames (ball resting on floor would otherwise sound every frame)
        return
    a, b = arbiter.shapes
    if a.collision_type == COLLISION_TYPE_BALL:
        ball_shape, wall_shape = a, b
    else:
        ball_shape, wall_shape = b, a
    ball = getattr(ball_shape, 'ball_ref', None)
    if ball is None:
        return
    inv_m = 1.0 / ball_shape.body.mass
    vRelN = _vRelN_from_impulse(arbiter, inv_m, arbiter.restitution)
    if vRelN <= 0:
        return
    minVel = IMPACT_MIN_VEL_GRABBED if ball.grabbed else IMPACT_MIN_VEL
    _playImpact(vRelN, ball.voiceType, ball.soundIdx, minVel)


space.on_collision(COLLISION_TYPE_BALL, COLLISION_TYPE_BALL, pre_solve=_ballBallPreSolve, post_solve=_ballBallPostSolve)
space.on_collision(COLLISION_TYPE_BALL, COLLISION_TYPE_WALL, pre_solve=_ballWallPreSolve, post_solve=_ballWallPostSolve)

buildWalls()
addSprite(Ball())


# --- Main loop -----------------------------------------------------------------

while True:

    now = time.time()
    deltaT = min(now - iniT, 1 / 60)                                               # cap dt — pymunk's solver explodes on very large timesteps
    iniT = now
    clock.tick()

    keys = pygame.key.get_pressed()
    showInfo = keys[pygame.K_SPACE]
    newMode = WALL_MODE
    if keys[pygame.K_1]:   newMode = 1
    elif keys[pygame.K_2]: newMode = 2
    elif keys[pygame.K_3]: newMode = 3
    elif keys[pygame.K_4]: newMode = 4                                              # sin paredes ni wrap — las bolas se van al vacío y se quedan ahí
    if newMode != WALL_MODE:
        WALL_MODE = newMode
        buildWalls()

    mouseX, mouseY = pygame.mouse.get_pos()
    mouseLeft, _, mouseRight = pygame.mouse.get_pressed()

    if mouseRight and not prevMouseRight:                                          # RMB rising edge → jump everyone (also wakes any sleeping islands automatically)
        for sprite in sprites:
            if isinstance(sprite, Ball):
                sprite.jump()
    prevMouseRight = mouseRight

    fKey = keys[pygame.K_f]
    if fKey and not prevFKey:
        showFPS = not showFPS
    prevFKey = fKey

    rKey = keys[pygame.K_r]                                                        # R = respawn: nuke and re-spawn the same count, all freshly randomized
    if rKey and not prevRKey:
        nBalls = len(sprites)
        for s in sprites[:]:
            if isinstance(s, Ball):
                s.removeFromWorld()
        sprites.clear()
        _impactQueue.clear()
        Ball._nextId = 1
        for _ in range(nBalls):
            addSprite(Ball())
    prevRKey = rKey

    qKey = keys[pygame.K_q]                                                        # Q = pin the currently-grabbed ball in place
    if qKey and not prevQKey:
        for sprite in sprites:
            if isinstance(sprite, Ball) and sprite.grabbed:
                sprite.pin()
                break
    prevQKey = qKey

    if deltaT > 0:                                                                 # low-pass-filter the raw mouse velocity for steadier throws
        rawVx = (mouseX - prevMouseX) / deltaT
        rawVy = (mouseY - prevMouseY) / deltaT
        smoothing = 1 - math.exp(-deltaT / MOUSE_SMOOTH_TC)
        mouseVx += (rawVx - mouseVx) * smoothing
        mouseVy += (rawVy - mouseVy) * smoothing
    prevMouseX, prevMouseY = mouseX, mouseY

    windowSurface.fill((0,0,0))

    # Draw the active walls as EDGE_MARGIN-thick bars along the screen edge. Physics walls are still 2px capsules
    # sitting just OUTSIDE the screen (collision face exactly at x=0/x=screenX/etc) — the visual bar overlaps the
    # interior strip that's now "outside the playable zone" for cursor purposes, so what you SEE as wall is exactly
    # the dead zone for the cursor.
    wallColor = (30, 30, 30)
    if WALL_MODE in (1, 2):
        pygame.draw.rect(windowSurface, wallColor, (0, 0, screenX, EDGE_MARGIN))                             # top
        pygame.draw.rect(windowSurface, wallColor, (0, screenY - EDGE_MARGIN, screenX, EDGE_MARGIN))         # floor
    if WALL_MODE == 1:
        pygame.draw.rect(windowSurface, wallColor, (0, 0, EDGE_MARGIN, screenY))                             # left
        pygame.draw.rect(windowSurface, wallColor, (screenX - EDGE_MARGIN, 0, EDGE_MARGIN, screenY))         # right

    for sprite in sprites[:]:                                                      # input/grow/grab/wrap BEFORE physics step (a copy because process() may remove a shrinking ball)
        sprite.process()

    subDt = deltaT / PHYSICS_SUBSTEPS                                              # substep the physics so the per-step displacement is smaller. Halves tunneling risk for fast bodies and improves solver convergence in tight piles. pymunk: integration + broadphase + solver + sleep happen inside each step.
    for _ in range(PHYSICS_SUBSTEPS):
        space.step(subDt)

    for sprite in sprites:
        sprite.draw()
    _flushImpacts()

    if showInfo:
        mouseSpeed = math.sqrt(mouseVx*mouseVx + mouseVy*mouseVy)
        createText(20, "Mouse: (%s, %s)" % (mouseX,mouseY),'topleft',(200,0,0),xper(0.01),yper(0.015))
        createText(20, "Velocity: (%.0f, %.0f)" % (mouseVx,mouseVy),'topleft',(0,0,255),xper(0.01),yper(0.045))
        createText(20, "Speed: %.0f px/s" % mouseSpeed,'topleft',(255,255,0),xper(0.01),yper(0.075))
        createText(20, "Balls: %s" % len(sprites),'topleft',(200,150,75),xper(0.01),yper(0.105))
        offscreen = sum(1 for b in sprites if isinstance(b, Ball) and (b.x + b.radius*2 < 0 or b.x - b.radius*2 > screenX or b.y + b.radius*2 < 0 or b.y - b.radius*2 > screenY))
        createText(20, "Off-screen: %s" % offscreen,'topleft',(200,150,75),xper(0.01),yper(0.135))
        pygame.draw.line(windowSurface, (0,0,255), (mouseX,mouseY),(mouseX-mouseVx*0.05,mouseY-mouseVy*0.05), 2)

        topBalls = sorted(sprites, key=lambda b: -(b.vx*b.vx + b.vy*b.vy))[:10]    # debug: top-10 by speed, bar-charted. Sleeper labels go gray + "zZz" so you can see what's settled.
        if topBalls:
            chartX  = int(xper(0.01))
            chartY  = int(yper(0.17))
            labelW  = 38
            barW    = 220
            barH    = 12
            rowGap  = 18
            topSpeed = max(1.0, math.sqrt(topBalls[0].vx**2 + topBalls[0].vy**2))
            createText(14, "Top 10 speeds  (max %.0f px/s)" % topSpeed, 'topleft', (180,180,180), chartX, chartY)
            for i, b in enumerate(topBalls):
                speed = math.sqrt(b.vx*b.vx + b.vy*b.vy)
                y = chartY + 22 + i * rowGap
                isSleeping = b.sleeping
                labelColor = (110,110,110) if isSleeping else (220,220,220)
                createText(14, "#%d" % b.id, 'topleft', labelColor, chartX, y)
                barX = chartX + labelW
                pygame.draw.rect(windowSurface, (40,40,40), (barX, y, barW, barH))
                fillW = int(barW * speed / topSpeed)
                if fillW > 0:
                    pygame.draw.rect(windowSurface, b.color, (barX, y, fillW, barH))
                createText(14, "%.0f%s" % (speed, " zZz" if isSleeping else ""), 'topleft', labelColor, barX + barW + 6, y)
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
