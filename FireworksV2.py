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

class Firework(Sprite):

    def __init__(self):

        colorPick = random.randint(0,12)
        c = colors[colorPick]

        self.z = 0
        self.x = mouseX
        self.y = mouseY
        self.radius = sper(0.0015)
        self.color = randColorInRange(c[0],c[1],c[2],c[3],c[4],c[5])
        self.acel = -sper(1.2) if not keys[pygame.K_SPACE] else -sper(1.8)
        self.grav = sper(0.2)
        self.angle = random.uniform(-sper(0.12),sper(0.12))
        self.timer = random.uniform(1,3)
        fireworks.append(self)

    def process(self):

        self.timer -= deltaT
        if self.timer <= 0:
            spritesToRemove.append(self)
            addSprite(Explosion(self.x,self.y,self.radius,False,self.color))

        self.y += (self.acel+self.grav) * deltaT
        self.x += self.angle * deltaT

        self.acel *= 0.99
        self.grav *= 1.004

        self.x = 0 if self.x > screenX else screenX if self.x < 0 else self.x

        if yper(1.5) < self.y < yper(-3):
            spritesToRemove.append(self)

    def draw(self):

        # createText(14,'acel: %s' %(str(self.grav)),'topright',(255,255,255),xper(0.95),yper(0.01))
        pygame.draw.circle(windowSurface, self.color, (self.x, self.y), self.radius)

class Explosion(Sprite):

    def __init__(self,x,y,radius,isChild,color=None,acel=None):

        colorPick = random.randint(0,12)
        c = colors[colorPick]
        color = color if color else randColorInRange(c[0],c[1],c[2],c[3],c[4],c[5])
        prob = random.random()
        modifier = 0.5 if prob < 0.1 else 1
        r = random.uniform(radius*0.5, radius*1.5)

        self.z = -1
        self.x = x
        self.y = y
        self.startRadius = r * 2 if prob < 0.2 else r
        self.radius = self.startRadius
        self.isChild = isChild
        self.type = random.randint(0,2)
        self.startColor = self.color = modifyColorPerc(color, 2)
        self.vel = sper(0.01)
        self.acel = acel if acel else random.uniform(0.5,0.8) * modifier
        self.maxSize = self.startRadius*9
        self.timer = 0.5
        explosions.append(self)

    def process(self):

        self.timer = max(self.timer - deltaT, 0)
        self.color = modifyColorPerc(self.color, 0.975)
        self.radius += self.vel
        self.vel *= self.acel
        if self.radius > self.maxSize or self.timer == 0:
            spritesToRemove.append(self)
            if not self.isChild and len(explosions) < 100:
                prob = random.random()
                color = randColorGray(200,255) if prob < 0.2 else modifyColorPerc(self.startColor,0.3)
                for i in range(3):
                    x = self.x+random.uniform(-sper(0.15),sper(0.15))
                    y = self.y+random.uniform(-sper(0.15),sper(0.15))
                    r = self.startRadius*(random.uniform(0.5,0.7))
                    addSprite(Explosion(x,y,r,True,color,self.acel))

    def draw(self):

        e1 = random.uniform(0,3)
        for i in range(1,31):
            e2 = random.uniform(0,3)
            e = (e1 if self.type == 0 else e2)
            lineStart = self.x + math.cos(math.pi*2*((i+10)/30)) * self.radius*e, self.y + math.sin(math.pi*2*((i+10)/30)) * self.radius*e
            lineEnd = self.x + math.cos(math.pi*2*i/30) * self.radius*e, self.y + math.sin(math.pi*2*i/30) * self.radius*e
            pygame.draw.line(windowSurface,self.color,lineStart,lineEnd, int(self.radius/7))

        if self.type == 2:
            pygame.draw.circle(windowSurface,self.color,(self.x,self.y),self.radius)
            for i in range(1,31):
                pygame.draw.line(windowSurface,self.color,(self.x + math.cos(math.pi*2*(i/30)+1) * self.radius*(1.7 if i % 2 == 0 else 1.1), self.y + math.sin(math.pi*2*(i/30)+1) * self.radius*(1.7 if i % 2 == 0 else 1.1)),(self.x + math.cos(math.pi*2*i/30) * self.radius*2*(1.7 if i % 2 == 0 else 1.1), self.y + math.sin(math.pi*2*i/30) * self.radius*2*(1.7 if i % 2 == 0 else 1.1)), int(self.radius/6))

class Manager(Sprite):

    def __init__(self):

        self.z = -2
        self.x = mouseX
        self.y = mouseY
        self.showFPS = False
        self.pause = False
        self.fPressed = False
        self.qPressed = False
        self.wPressed = False
        self.pPressed = False
        self.mLeft = self.mRight = self.mMiddle = False
        self.fireworkCD = 0
        self.blowCD = 0
        self.pauseBlinkCD = 0

    def process(self):

        self.x = mouseX
        self.y = mouseY

        self.fireworkCD = max(self.fireworkCD - deltaT, 0)
        self.blowCD = max(self.blowCD - deltaT, 0)

        if not self.qPressed:
            if keys[pygame.K_q]:
                for fw in fireworks:
                    spritesToRemove.append(fw)
                    if len(explosions) < 500:
                        addSprite(Explosion(fw.x,fw.y,fw.radius,True,fw.color))
                    # self.qPressed = True

        if not self.wPressed:
            if keys[pygame.K_w]:
                if self.blowCD == 0 and fireworks:
                    pos = random.randint(0,len(fireworks)-1)
                    fw = fireworks.pop(pos)
                    spritesToRemove.append(fw)
                    addSprite(Explosion(fw.x,fw.y,fw.radius,True,fw.color))
                    self.blowCD = 0.1
                    # self.wPressed = True

        if not self.fPressed:
            if keys[pygame.K_f]:
                self.showFPS = not self.showFPS
                self.fPressed = True

        if not self.pPressed:
            if keys[pygame.K_p]:
                self.pause = not self.pause
                self.pauseBlinkCD = 0
                self.pPressed = True

        if self.mRight:
            self.fireworkCD = 0

        # if self.mMiddle:
        #     pygame.quit()
        #     sys.exit()

        if self.mLeft and self.fireworkCD == 0:
            if self.mMiddle:
                for i in range(5):
                    addSprite(Firework())
            else:
                addSprite(Firework())
            self.fireworkCD = 0.1

        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()

        # if not keys[pygame.K_q]:
        #      self.qPressed = False

        if not keys[pygame.K_f]:
             self.fPressed = False

        # if not keys[pygame.K_w]:
        #      self.wPressed = False

        if not keys[pygame.K_p]:
             self.pPressed = False

        self.mLeft = mouseLeft
        self.mRight = mouseRight
        self.mMiddle = mouseMiddle

    def draw(self):

        pygame.draw.circle(windowSurface, (100,0,50), (self.x, self.y), sper(0.004))

        if self.showFPS:
            createText(14,'FPS: %s' %(str(round(clock.get_fps()))),'topleft',(255,255,255),xper(0.96),yper(0.01))
            createText(10,'spr: %s' %(len(sprites)),'topleft',(0,255,0),xper(0.015),yper(0.01))
            createText(10,'fws: %s' %(len(fireworks)),'topleft',(0,255,0),xper(0.015),yper(0.03))
            createText(10,'exp: %s' %(len(explosions)),'topleft',(0,255,0),xper(0.015),yper(0.05))
            createText(10,'toR: %s' %(len(spritesToRemove)),'topleft',(0,255,0),xper(0.015),yper(0.07))
            createText(10,'deltaReal: %s' %(str(deltaCalc)),'topleft',(155,0,0),xper(0.015),yper(0.09))
            createText(10,'usedDelta: %s' %(str(deltaT)),'topleft',(155,0,0),xper(0.015),yper(0.11))
            createText(10,'deltaDefic: %s' %(str(deltaT-deltaCalc)),'topleft',(155,0,0),xper(0.015),yper(0.13))

        if self.pause:
            self.pauseBlinkCD += deltaT
            createText(60,'PAUSE' if self.pauseBlinkCD > 0.25 else '','center',(255,255,255),xper(0.5),yper(0.5))
            if self.pauseBlinkCD > 0.5: self.pauseBlinkCD = 0

def xper(percentage):
    return percentage * screenX

def yper(percentage):
    return percentage * screenY

def sper(percentage):
    return percentage * (screenX+screenY)/2

def randColorInRange(redLow, redHigh, greenLow, greenHigh, blueLow, blueHigh):
    return (random.randint(redLow,redHigh), random.randint(greenLow,greenHigh), random.randint(blueLow,blueHigh))

def randColorGray(low, high):
    n = random.randint(low,high)
    return (n,n,n)

def modifyColorPerc(color, offset):
    return tuple(int(max(min(c*offset, 255), 0)) for c in color)

def getAngle2(prevAng, point1, point2):
    angle = math.atan2(point2[1]-point1[1], point2[0]-point1[0])
    if angle - prevAng < -math.pi: angle += math.pi*2
    if angle - prevAng >  math.pi: angle -= math.pi*2
    return angle

def getDist(point1, point2):
    return math.sqrt(abs(point1[0]-point2[0])**2+abs(point1[1]-point2[1])**2)

def createText(size, content, alignment, colorText, posX, posY):
    text_rect = font.get_rect(content, size=size)
    text_rect.midtop = (posX, posY)
    setattr(text_rect, alignment, (posX, posY))
    font.render_to(windowSurface, text_rect, content, colorText, size=size)

def addSprite(sprite):
    sprites.append(sprite)
    return sprite

def removeSprites():
    for sprite in sprites:
        if sprite in spritesToRemove:
            if sprite in fireworks:
                fireworks.remove(sprite)
            if sprite in explosions:
                explosions.remove(sprite)
            sprites.remove(sprite)
            spritesToRemove.remove(sprite)

# INITIALIZATION .....................................................................

pygame.init()

screenX = 1920
screenY = 800
# screenX = 1280
# screenY = 720
windowSurface = pygame.display.set_mode((screenX, screenY), depth=32, display=0)
pygame.display.set_caption('Fireworks')
pygame.mouse.set_visible(False)

font = pygame.freetype.SysFont('Century Gothic', 0)

deltaT = 0
iniT = time.time()
clock = pygame.time.Clock()
keys = None
mouseX = mouseY = 0
mouseLeft = mouseRight = False
sprites = []
manager = addSprite(Manager())
fireworks = []
explosions = []
spritesToRemove = []


colors = (
    (75,155,0,0,0,0),       # Rojo oscuro
    (0,0,75,155,0,0),       # Verde oscuro
    (0,0,0,0,75,155),       # Azul oscuro
    (75,155,75,155,0,0),    # Rojo y verde oscuro
    (0,0,75,155,75,155),    # Verde y azul oscuro
    (75,155,0,0,75,155),    # Rojo y azul oscuro
    (200,255,0,0,0,0),      # Rojo claro
    (0,0,200,255,0,0),      # Verde claro
    (0,0,0,0,200,255),      # Azul claro
    (200,255,200,255,0,0),  # Rojo y verde claro
    (0,0,200,255,200,255),  # Verde y azul claro
    (200,255,0,0,200,255),  # Rojo y azul claro
    (75,255,75,255,75,255), # Rojo, verde y azul claro
)

# MAIN LOOP ..........................................................................

while True:

    now = time.time()
    deltaCalc = now - iniT
    deltaT = min(deltaCalc, 0.05)
    iniT = now
    clock.tick()

    keys = pygame.key.get_pressed()
    mouseX, mouseY = pygame.mouse.get_pos()
    mouseLeft, mouseMiddle, mouseRight = pygame.mouse.get_pressed()

    windowSurface.fill((0,0,0))

    sprites.sort(key=lambda x: x.z, reverse=True)

    for sprite in sprites:
        if not manager.pause or sprite == manager:
            sprite.process()
        if yper(-0.1) < sprite.y < yper(1.1):
            sprite.draw()
    removeSprites()
    spritesToRemove.clear()

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()