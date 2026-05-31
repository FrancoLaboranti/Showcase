import math
import time
import random
import pygame, sys
import pygame.freetype
from pygame.locals import *


class Sprite:
    def process(self):
        pass
    def draw(self):
        pass


class Ball(Sprite):
    def __init__(self):
        self.radius = sper(0.001)
        self.x = random.uniform(xper(0.05),xper(0.95))
        self.y = random.uniform(yper(0.05),yper(0.6))
        self.forceAng = math.pi/2
        self.forceSpeed = 0
        self.fallTime = 0
        self.floorBounce = 0
        self.weight = 3000
        self.grabbed = False
        self.removing = False

    def process(self):

        if self.radius < sper(0.05) and not self.removing:
            self.radius += deltaT*300
        elif self.removing:
            self.radius -= deltaT*300
            if self.radius < sper(0.001):
                sprites.remove(self)

        if mouseLeft and getDist((self.x,self.y), (mouseX,mouseY)) < self.radius and not any(ball.grabbed for ball in sprites):
            self.grabbed = True
        elif not mouseLeft:
            self.grabbed = False

        if self.grabbed:
            self.x = mouseX
            self.y = mouseY
            self.forceAng = mouseDirection
            self.forceSpeed = mouseSpeed*40
            self.fallTime = 0
            self.floorBounce = 0
        else:
            self.fallTime = (self.fallTime + deltaT) if self.y < screenY - self.radius else 0
            self.y += math.sin(math.pi/2)*(self.weight*self.fallTime)*deltaT

        if not self.forceAng and not self.fallTime and not self.forceSpeed:
            self.forceAng = math.pi/2

        for ball in sprites:
            if self.collides(ball):

                hitAng = getAngle((ball.x,ball.y),(self.x,self.y))
                selfForceSpeed = self.forceSpeed

                self.x += math.cos(hitAng)*ball.radius/40
                self.y += math.sin(hitAng)*ball.radius/40
                self.forceAng = random.uniform(hitAng-math.pi*0.1,hitAng+math.pi*0.1)
                self.forceSpeed = max(300, ball.forceSpeed) if self.fallTime > 0.3 else ball.forceSpeed
                self.fallTime = 0
                self.floorBounce = 0

                ball.x -= math.cos(hitAng)*self.radius/40
                ball.y -= math.sin(hitAng)*self.radius/40
                ball.forceAng = -random.uniform(hitAng-math.pi*0.1,hitAng+math.pi*0.1)
                ball.forceSpeed = max(300, selfForceSpeed) if ball.fallTime > 0.3 else selfForceSpeed
                ball.fallTime = 0
                ball.floorBounce = 0

        self.x += math.cos(self.forceAng)*self.forceSpeed*deltaT
        self.y += math.sin(self.forceAng)*self.forceSpeed*deltaT + math.sin(-math.pi/2)*self.floorBounce*deltaT

        if self.x < 0 + self.radius or self.x > screenX - self.radius:
            self.x = 0 + self.radius if self.x < 0 + self.radius else screenX - self.radius
            self.forceSpeed *= 0.9

            if -math.pi*0.3 <= self.forceAng <= -math.pi*0.1:                  # bounce R to L top side
                self.forceAng += -math.pi/2
            elif -math.pi*0.9 <= self.forceAng <= -math.pi*0.7:                # bounce L to R top side
                self.forceAng += math.pi/2
            elif math.pi*0.3 >= self.forceAng >= math.pi*0.1:                  # bounce R to L bot side
                self.forceAng += math.pi/2
            elif math.pi*0.9 >= self.forceAng >= math.pi*0.7:                  # bounce L to R bot side
                self.forceAng += -math.pi/2
            elif -math.pi/2 <= self.forceAng <= -math.pi*0.3:                  # bounce R to L top side (weak angle)
                self.forceAng += -math.pi*0.3
            elif -math.pi*0.7 <= self.forceAng <= -math.pi/2:                  # bounce L to R top side (weak angle)
                self.forceAng += math.pi*0.3
            elif math.pi/2 >= self.forceAng >= math.pi*0.3:                    # bounce R to L bot side (weak angle)
                self.forceAng += math.pi*0.3
            elif math.pi*0.7 >= self.forceAng >= math.pi/2:                    # bounce L to R bot side (weak angle)
                self.forceAng += -math.pi*0.3                
            else:                                                              # direct horizontal bounce
                self.forceAng += math.pi

        if self.y < 0 + self.radius or self.y > screenY - self.radius:
            self.y = 0 + self.radius if self.y < 0 + self.radius else screenY - self.radius

            if self.y == 0 + self.radius:
                self.forceAng = -self.forceAng                                 # we can just invert the angle when hitting the roof
                self.forceSpeed *= 0.6

            else:
                if math.pi*0.9 >= self.forceAng >= math.pi*0.1:                # we can just invert the angle when hitting the floor
                    self.forceAng = -self.forceAng

                self.floorBounce = min(self.fallTime * 1000, 600) if self.fallTime > 0.01 else 0

        self.forceSpeed = min(self.forceSpeed * 0.9995 if self.forceSpeed > 10 else 0, 8000)

    def draw(self):

        lightAng = getAngle((xper(0.5),-yper(0.2)),(self.x,self.y))
        lightDist = getDist((xper(0.5),-yper(0.2)),(self.x,self.y))

        pygame.draw.circle(windowSurface, (200,200,200), (self.x, self.y), self.radius)

        if self.radius >= sper(0.05):
            pygame.draw.circle(windowSurface, (255,255,255), (self.x - math.cos(lightAng)*(lightDist*0.05), self.y - max(20, math.sin(lightAng)*(lightDist*0.023))), min(10, self.radius*(lightDist*0.0005)))
            pygame.draw.circle(windowSurface, (190,190,190), (self.x + math.cos(lightAng)*(lightDist*0.05), self.y + max(20, math.sin(lightAng)*(lightDist*0.023))), min(10, self.radius*(lightDist*0.0004)))

        if showInfo:
            createText(20, "FallingTime: %s" % str(self.fallTime),'topright',(0,200,200),xper(0.99),yper(0.015))
            createText(20, "ForceAng: %s" % str(self.forceAng),'topright',(255,0,255),xper(0.99),yper(0.045))
            createText(20, "ForceSpeed: %s" % str(self.forceSpeed),'topright',(255,150,0),xper(0.99),yper(0.075))
            createText(20, "FloorBounce: %s" % str(self.floorBounce),'topright',(150,150,150),xper(0.99),yper(0.105))
            createText(20, "LightAngle: %s" % str(lightAng),'topright',(255,255,255),xper(0.99),yper(0.135))
            createText(20, "LightDist: %s" % str(lightDist),'topright',(100,255,0),xper(0.99),yper(0.165))
            pygame.draw.line(windowSurface, (255,0,255), (self.x,self.y),(self.x + math.cos(self.forceAng)*self.radius*3,self.y + math.sin(self.forceAng)*self.radius*3), 5)
            pygame.draw.line(windowSurface, (255,255,255), (self.x,self.y),(xper(0.5),-yper(0.2)), 2)

    def collides(self, ball):
        return self != ball and getDist((self.x, self.y),(ball.x, ball.y)) < self.radius + ball.radius

pygame.init()

screenX = 750
screenY = 750

windowSurface = pygame.display.set_mode((screenX, screenY), depth=32, display=0)
pygame.display.set_caption('Balls')

font = pygame.freetype.SysFont('Century Gothic', 0)

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
mouseX = mouseY = 0
mouseLeft = mouseRight = False
prevMousePos = (0,0)
mousePosTimer = 0
sprites = []
showInfo = None

addSprite(Ball())

while True:

    now = time.time()
    deltaT = min(now - iniT, 0.01)
    iniT = now
    clock.tick()

    keys = pygame.key.get_pressed()
    showInfo = keys[pygame.K_SPACE]

    mouseX, mouseY = pygame.mouse.get_pos()
    mouseLeft, _, mouseRight = pygame.mouse.get_pressed()
    
    mousePosTimer += deltaT
    if mousePosTimer > 0.02:
        prevMousePos = (mouseX,mouseY)
        mouseDirection = newMouseDirection
        mouseSpeed = newMouseSpeed
        mousePosTimer = 0

    newMouseDirection = getAngle(prevMousePos,(mouseX,mouseY))
    newMouseSpeed = getDist(prevMousePos,(mouseX,mouseY))

    windowSurface.fill((0,0,0))

    for sprite in sprites:
        sprite.process()
        sprite.draw()

    if showInfo:
        createText(20, "Previous point: %s" % str(prevMousePos),'topleft',(0,200,0),xper(0.01),yper(0.015))
        createText(20, "Current point: %s" % str((mouseX,mouseY)),'topleft',(200,0,0),xper(0.01),yper(0.045))
        createText(20, "Direction: %s" % str(newMouseDirection),'topleft',(0,0,255),xper(0.01),yper(0.075))
        createText(20, "Speed: %s" % newMouseSpeed,'topleft',(255,255,0),xper(0.01),yper(0.105))
        createText(20, "Balls: %s" % len(sprites),'topleft',(200,150,75),xper(0.01),yper(0.135))
        pygame.draw.circle(windowSurface, (0,200,0), (prevMousePos), 2)
        pygame.draw.line(windowSurface, (0,0,255), (mouseX,mouseY),prevMousePos, 1)
    if mouseRight:
        createText(15,'FPS: %s' %(str(round(clock.get_fps()))),'topright',(255,255,255),xper(0.99),yper(0.97))

    if keys[pygame.K_ESCAPE]:
        pygame.quit()
        sys.exit()

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.MOUSEWHEEL:
            if event.y == 1 and len(sprites) < 70:
                addSprite(Ball())
            elif event.y == -1 and len(sprites) > 1:
                for ball in reversed(sprites):
                    if not ball.removing and sprites.index(ball) > 0:
                        ball.removing = True
                        break
        if event.type == QUIT:
            pygame.quit()
            sys.exit()