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


class Player(Sprite):
    def __init__(self, i, colors, totalplayers,mode):
        self.id = i
        self.direction = 0
        self.directions = {
            0: [0,-150, 0,-2, 0,-4, 0,-100],
            1: [150,0, 1,0, 4,0, 100,0],
            2: [0,150, 0,1, 0,4, 0,100],
            3: [-150,0, -2,0, -4,0, -100,0]
        }
        self.currentMode = mode
        self.leftpressed = False
        self.rightpressed = False
        self.stop = False
        self.aiTurnInCD = 0
        self.aiRandDistToTurnCD = 2
        self.maxDistanceDir = None

        startpos = {
            0: (xper(0.75) if totalplayers < 4 else xper(0.8),yper(0.95)),
            1: (xper(0.25) if totalplayers < 4 else xper(0.2),yper(0.65) if totalplayers == 4 else yper(0.95)),
            2: (xper(0.5) if totalplayers < 4 else xper(0.6),yper(0.85) if totalplayers == 4 else yper(0.95)),
            3: (xper(0.4),yper(0.75))
        }

        controls = {
            0: (pygame.K_LEFT,pygame.K_DOWN),
            1: (pygame.K_q,pygame.K_w),
            2: (pygame.K_o,pygame.K_p),
            3: (pygame.K_v,pygame.K_b)
        }

        self.color = colors[self.id]
        self.x, self.y = startpos[self.id]
        self.left, self.right = controls[self.id]

    def process(self):

        if self.id == 0 or self.currentMode == 1:
            if not self.leftpressed:

                if keys[self.left]:
                    self.direction = (self.direction-1) % len(self.directions)
                    self.leftpressed = True

            if not self.rightpressed:

                if keys[self.right]:
                    self.direction = (self.direction+1) % len(self.directions)
                    self.rightpressed = True

            if not keys[self.left]:
                self.leftpressed = False

            if not keys[self.right]:
                self.rightpressed = False

        else:

            self.aiRandDistToTurnCD += deltaT
            self.aiTurnInCD += deltaT

            if self.aiRandDistToTurnCD > 2:

                self.directions[0][7] = random.randint(-100,-25)
                self.directions[1][6] = random.randint(25,100)
                self.directions[2][7] = random.randint(25,100)
                self.directions[3][6] = random.randint(-100,-25)

                self.aiRandDistToTurnCD = 0

            maxDistances = [0,0,0,0]

            for distanceTop in range(2,screenY):
                if windowSurface.get_at((int(self.x % screenX),int((self.y-distanceTop) % screenY))) != (0,0,0):
                    maxDistances[0] = distanceTop
                    break

            for distanceBot in range(2,screenY):
                if windowSurface.get_at((int(self.x % screenX),int((self.y+distanceBot) % screenY))) != (0,0,0):
                    maxDistances[2] = distanceBot
                    break

            for distanceLeft in range(2,screenX):
                if windowSurface.get_at((int((self.x-distanceLeft) % screenX),int(self.y % screenY))) != (0,0,0):
                    maxDistances[3] = distanceLeft
                    break

            for distanceRight in range(2,screenX):
                if windowSurface.get_at((int((self.x+distanceRight) % screenX),int(self.y % screenY))) != (0,0,0):
                    maxDistances[1] = distanceRight
                    break

            self.premaxDistanceDir = self.maxDistanceDir
            self.maxDistanceDir = maxDistances.index(max(maxDistances))

            if self.aiTurnInCD > 0.05:

                if windowSurface.get_at((int((self.x+self.directions[self.direction][2]) % screenX), int((self.y+self.directions[self.direction][3]) % screenY))) != (0,0,0):
                    self.direction = self.maxDistanceDir
                    self.aiTurnInCD = 0

                elif windowSurface.get_at((int((self.x+self.directions[self.direction][4]) % screenX), int((self.y+self.directions[self.direction][5]) % screenY))) != (0,0,0):
                    self.direction = self.maxDistanceDir
                    self.aiTurnInCD = 0

                elif windowSurface.get_at((int((self.x+self.directions[self.direction][6]) % screenX), int((self.y+self.directions[self.direction][7]) % screenY))) != (0,0,0):
                    self.direction = self.maxDistanceDir
                    self.aiTurnInCD = 0

                elif self.maxDistanceDir != self.premaxDistanceDir:
                    self.direction = self.maxDistanceDir
                    self.aiTurnInCD = 0

                elif random.randint(0,1000) == 0:
                    canTurnRight = windowSurface.get_at((int((self.x+self.directions[(self.direction+1) % len(self.directions)][2]) % screenX), int((self.y+self.directions[(self.direction+1) % len(self.directions)][3]) % screenY))) == (0,0,0)
                    canTurnLeft = windowSurface.get_at((int((self.x+self.directions[(self.direction-1) % len(self.directions)][2]) % screenX), int((self.y+self.directions[(self.direction-1) % len(self.directions)][3]) % screenY))) == (0,0,0)
                    if random.randint(0,1) == 0 and canTurnRight and windowSurface.get_at((int((self.x+self.directions[(self.direction+1) % len(self.directions)][4]) % screenX), int((self.y+self.directions[(self.direction+1) % len(self.directions)][5]) % screenY))) == (0,0,0):
                        self.direction = (self.direction+1) % len(self.directions)
                    elif canTurnLeft and windowSurface.get_at((int((self.x+self.directions[(self.direction-1) % len(self.directions)][4]) % screenX), int((self.y+self.directions[(self.direction-1) % len(self.directions)][5]) % screenY))) == (0,0,0):
                        self.direction = (self.direction-1) % len(self.directions)
                    self.aiTurnInCD = 0

        self.x = 0 if self.x > screenX else screenX if self.x < 0 else self.x
        self.y = 0 if self.y > screenY else screenY if self.y < 0 else self.y

        if windowSurface.get_at((int((self.x+self.directions[self.direction][2]) % screenX), int((self.y+self.directions[self.direction][3]) % screenY))) != (0,0,0):
            sprites.remove(self)

        if not self.stop:
            self.x += self.directions[self.direction][0] * deltaT *1.5
            self.y += self.directions[self.direction][1] * deltaT *1.5

    def draw(self):
        pygame.draw.circle(windowSurface, self.color, (self.x, self.y), 1)


class GameHandler(Sprite):

    def __init__(self):

        self.menu = True
        self.currentOption = 0
        self.currentPlayers = 0
        self.currentMode = 0
        self.options = (0,1)
        self.players = (0,1,2)
        self.modes = (0,1)
        self.keyPressed = False
        self.playerColors = {
            0: (0,155,255),
            1: (255,0,155),
            2: (255,155,0),
            3: (0,255,155)
        }
        self.titleColor = random.choice(self.playerColors)
        self.titleColorOffset = 1
        self.titleColorOffsetTimer = 0
        self.titleColorUpping = True

    def process(self):
        
        if self.menu:
            if not self.keyPressed:

                self.currentOption = (self.currentOption + (-1 if keys[pygame.K_UP] else 1 if keys[pygame.K_DOWN] else 0)) % len(self.options)

                if self.currentOption == 0:
                    self.currentMode = (self.currentMode + (-1 if keys[pygame.K_LEFT] else 1 if keys[pygame.K_RIGHT] else 0)) % len(self.modes)
                else:
                    self.currentPlayers = (self.currentPlayers + (-1 if keys[pygame.K_LEFT] else 1 if keys[pygame.K_RIGHT] else 0)) % len(self.players)

                if keys[pygame.K_RETURN] and self.menu:
                    self.startGame(self.playerColors,self.currentPlayers,self.currentMode)
                    self.menu = False

                if keys[pygame.K_ESCAPE]:
                    pygame.quit()
                    sys.exit()

                self.keyPressed = keys[pygame.K_UP] or keys[pygame.K_DOWN] or [pygame.K_LEFT] or [pygame.K_RIGHT]

        if len(sprites) <= 2:
            for sprite in sprites:
                sprite.stop = True

            if keys[pygame.K_RETURN] and not self.menu:
                while len(sprites) > 1:
                    for sprite in sprites:
                        if sprite != self:
                            sprites.remove(sprite)

                self.startGame(self.playerColors,self.currentPlayers,self.currentMode)

        if keys[pygame.K_ESCAPE]:
            while len(sprites) > 1:
                for sprite in sprites:
                    if sprite != self:
                        sprites.remove(sprite)

            windowSurface.fill((0,0,0))
            self.menu = True
            self.keyPressed = True

        if not keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT] and not keys[pygame.K_UP] and not keys[pygame.K_DOWN] and not keys[pygame.K_ESCAPE]:
            self.keyPressed = False

    def draw(self):

        if self.menu:

            if self.titleColorOffset > 1.5:
                self.titleColorUpping = False
            if self.titleColorOffset < 0 and not self.titleColorUpping:
                self.titleColorUpping = True
                color = self.titleColor
                while color == self.titleColor:
                    self.titleColor = random.choice(self.playerColors)

            self.titleColorOffsetTimer += deltaT
            if self.titleColorOffsetTimer > 0.01:
                self.titleColorOffset = (self.titleColorOffset + (deltaT*30 if self.titleColorUpping else -deltaT*30))
                self.titleColorOffsetTimer = 0

            titleColor = modifyColorPerc(self.titleColor,self.titleColorOffset)

            windowSurface.fill((0,0,0))
            createText(170,'TRON','center',titleColor,xper(0.5),yper(0.2))
            createText(50,'Single Player' if self.currentMode == 0 else 'Multi Player','center',(255,255,255) if self.currentOption == 0 else (60,60,60),xper(0.5),yper(0.5))
            createText(50,'%s Colors' % (self.currentPlayers+2),'center',(255,255,255) if self.currentOption == 1 else (60,60,60),xper(0.5),yper(0.65))
            createText(25,'Enter to Start','center',(100,100,150),xper(0.5),yper(0.85))
            createText(25,'ESC to Exit','center',(100,100,150),xper(0.5),yper(0.9))

        if len(sprites) == 2:
            for sprite in sprites:
                if sprite != self:
                    winner = sprite.id
                    color = sprite.color

            createText(100,'%s Wins!' % ('Player 1' if winner == 0 else 'Player 2' if winner == 1 else 'Player 3' if winner == 2 else 'Player 4'),'center',color,xper(0.5),yper(0.45))
            createText(60,'Enter to Restart','center',(255,255,255),xper(0.5),yper(0.6))

    def startGame(self, colors, players, mode):
        players += 2
        windowSurface.fill((0,0,0))
        for i in range(players):
            addSprite(Player(i,colors,players,mode))

pygame.init()

screenX = 1280
screenY = 720

windowSurface = pygame.display.set_mode((screenX, screenY), depth=32, display=0)
pygame.display.set_caption('Tron')

font = pygame.freetype.SysFont('Century Gothic', 0)

def xper(percentage):
    return percentage * screenX

def yper(percentage):
    return percentage * screenY

def randColor():
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))

def randColorInRange(rmin,rmax,gmin,gmax,bmin,bmax):
    return (random.randint(rmin,rmax), random.randint(gmin,gmax), random.randint(bmin,bmax))

def modifyColor(color, offset):
    return tuple(max(min(c+offset, 255), 0) for c in color)

def modifyColorPerc(color, offset):
    return tuple(int(max(min(c*offset, 255), 0)) for c in color)

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
keys = None
mouseX = mouseY = 0
mouseLeft = mouseRight = False
sprites = []

addSprite(GameHandler())

while True:

    now = time.time()
    deltaT = min(now - iniT, 0.01)
    iniT = now

    keys = pygame.key.get_pressed()
    mouseX, mouseY = pygame.mouse.get_pos()
    mouseLeft, _, mouseRight = pygame.mouse.get_pressed()

    for sprite in sprites:
        sprite.process()
        sprite.draw()

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()