import math
import time
import random
import pygame, sys
import pygame.freetype
from pygame.locals import *

# Tateti / Tic-tac-toe ------------------------------------------------------
# Sigue el esqueleto compartido del repo (Sprite, deltaT, xper/yper/sper,
# createText, manager[0]). Estados del juego en Manager.state:
#   'menu'  -> elegir modo (2 jugadores / vs CPU)
#   'play'  -> partida en curso
#   'over'  -> partida terminada (gana X, gana O, o empate)
# El tablero es una lista de 9 enteros: 0 vacío, 1 X, 2 O.
# CPU usa minimax completo (3x3 es chico, ~ms).

class Sprite:
    def process(self):
        pass
    def draw(self):
        pass


class Board(Sprite):

    def __init__(self):
        self.z = 0
        self.cells = [0]*9
        self.turn = 1
        self.winner = 0
        self.winLine = None
        self.winAnim = 0
        self.winAnimTotal = 0.5
        self.hoverIdx = -1
        self.placeAnim = [0.0]*9
        self.placeAnimTotal = 0.25
        self.cpuThinkCD = 0
        board.append(self)

    def reset(self, startingTurn=1):
        self.cells = [0]*9
        self.turn = startingTurn
        self.winner = 0
        self.winLine = None
        self.winAnim = 0
        self.placeAnim = [0.0]*9
        self.cpuThinkCD = 0

    def boardRect(self):
        size = min(xper(0.6), yper(0.7))
        cx, cy = xper(0.5), yper(0.55)
        return (cx - size/2, cy - size/2, size)

    def cellAt(self, mx, my):
        bx, by, size = self.boardRect()
        if mx < bx or my < by or mx > bx + size or my > by + size:
            return -1
        col = int((mx - bx) / (size/3))
        row = int((my - by) / (size/3))
        col = max(0, min(2, col))
        row = max(0, min(2, row))
        return row*3 + col

    def cellCenter(self, idx):
        bx, by, size = self.boardRect()
        cellSize = size/3
        row, col = idx // 3, idx % 3
        return (bx + cellSize*(col+0.5), by + cellSize*(row+0.5))

    def play(self, idx, mark):
        if self.cells[idx] != 0 or self.winner != 0:
            return False
        self.cells[idx] = mark
        self.placeAnim[idx] = self.placeAnimTotal
        result = checkWinner(self.cells)
        if result is not None:
            w, line = result
            self.winner = w
            self.winLine = line
            self.winAnim = self.winAnimTotal
            m = manager[0]
            m.state = 'over'
            if w == 1: m.scoreX += 1
            elif w == 2: m.scoreO += 1
            else: m.scoreD += 1
        else:
            self.turn = 2 if self.turn == 1 else 1
        return True

    def process(self):
        m = manager[0]

        for i in range(9):
            if self.placeAnim[i] > 0:
                self.placeAnim[i] = max(self.placeAnim[i] - deltaT, 0)
        if self.winAnim > 0:
            self.winAnim = max(self.winAnim - deltaT, 0)

        if m.state != 'play':
            self.hoverIdx = -1
            return

        cpuTurn = (m.mode == 'cpu' and self.turn == m.cpuMark)

        if cpuTurn:
            self.hoverIdx = -1
            if self.cpuThinkCD == 0:
                self.cpuThinkCD = 0.35
            else:
                self.cpuThinkCD = max(self.cpuThinkCD - deltaT, 0)
                if self.cpuThinkCD == 0:
                    move = bestMove(self.cells, self.turn)
                    if move >= 0:
                        self.play(move, self.turn)
        else:
            self.hoverIdx = self.cellAt(mouseX, mouseY)
            if mouseLeft and not m.mPressed and self.hoverIdx >= 0:
                self.play(self.hoverIdx, self.turn)

    def draw(self):
        m = manager[0]
        bx, by, size = self.boardRect()
        cellSize = size/3
        lineW = max(2, int(sper(0.004)))

        bgCol = (24, 26, 34)
        pygame.draw.rect(windowSurface, bgCol, (bx, by, size, size), border_radius=int(sper(0.015)))

        if m.state == 'play' and self.hoverIdx >= 0 and self.cells[self.hoverIdx] == 0:
            cpuTurn = (m.mode == 'cpu' and self.turn == m.cpuMark)
            if not cpuTurn:
                row, col = self.hoverIdx // 3, self.hoverIdx % 3
                hx = bx + col*cellSize
                hy = by + row*cellSize
                hoverCol = modifyColorPerc(colorForMark(self.turn), 0.25)
                pygame.draw.rect(windowSurface, hoverCol, (hx+lineW, hy+lineW, cellSize-lineW*2, cellSize-lineW*2), border_radius=int(sper(0.01)))

        gridCol = (70, 75, 90)
        for i in range(1, 3):
            pygame.draw.line(windowSurface, gridCol, (bx + cellSize*i, by + sper(0.01)), (bx + cellSize*i, by + size - sper(0.01)), lineW)
            pygame.draw.line(windowSurface, gridCol, (bx + sper(0.01), by + cellSize*i), (bx + size - sper(0.01), by + cellSize*i), lineW)

        for i in range(9):
            if self.cells[i] != 0:
                cx, cy = self.cellCenter(i)
                anim = 1 - (self.placeAnim[i] / self.placeAnimTotal) if self.placeAnim[i] > 0 else 1
                scale = easeOutBack(anim)
                self.drawMark(self.cells[i], cx, cy, cellSize*0.32*scale)

        if self.winLine is not None:
            a, b, c = self.winLine
            ax, ay = self.cellCenter(a)
            cx, cy = self.cellCenter(c)
            t = 1 - (self.winAnim / self.winAnimTotal) if self.winAnim > 0 else 1
            t = easeOutCubic(t)
            ex, ey = ax + (cx - ax)*t, ay + (cy - ay)*t
            col = colorForMark(self.winner)
            pygame.draw.line(windowSurface, col, (ax, ay), (ex, ey), int(sper(0.012)))
            pygame.draw.circle(windowSurface, col, (ax, ay), int(sper(0.008)))
            pygame.draw.circle(windowSurface, col, (ex, ey), int(sper(0.008)))

    def drawMark(self, mark, cx, cy, r):
        col = colorForMark(mark)
        thick = max(3, int(sper(0.012)))
        if mark == 1:
            pygame.draw.line(windowSurface, col, (cx - r, cy - r), (cx + r, cy + r), thick)
            pygame.draw.line(windowSurface, col, (cx + r, cy - r), (cx - r, cy + r), thick)
        else:
            pygame.draw.circle(windowSurface, col, (cx, cy), r, thick)


class Manager(Sprite):

    def __init__(self):
        self.z = -2
        self.state = 'menu'
        self.mode = 'pvp'        # 'pvp' o 'cpu'
        self.cpuMark = 2          # qué marca usa la CPU (1 X, 2 O)
        self.menuIdx = 0
        self.showFPS = False
        self.fPressed = False
        self.altEnterPressed = False
        self.mPressed = False
        self.upPressed = False
        self.downPressed = False
        self.enterPressed = False
        self.rPressed = False
        self.fullScreen = False
        self.scoreX = 0
        self.scoreO = 0
        self.scoreD = 0
        self.startingTurn = 1
        manager.append(self)

    def process(self):
        global windowSurface

        if keys[pygame.K_ESCAPE]:
            if self.state == 'menu':
                pygame.quit()
                sys.exit()
            else:
                self.state = 'menu'
                board[0].reset()

        if not self.altEnterPressed:
            if keys[pygame.K_LALT] and keys[pygame.K_RETURN]:
                self.fullScreen = not self.fullScreen
                windowSurface = pygame.display.set_mode((screenX, screenY), depth=32, display=0, flags=pygame.FULLSCREEN if self.fullScreen else pygame.SHOWN)
                self.altEnterPressed = True

        if not self.fPressed:
            if keys[pygame.K_f]:
                self.showFPS = not self.showFPS
                self.fPressed = True

        if self.state == 'menu':
            self.processMenu()
        elif self.state == 'over':
            if mouseLeft and not self.mPressed:
                self.newRound()
            if not self.rPressed and keys[pygame.K_r]:
                self.resetScores()
                self.rPressed = True

        if not keys[pygame.K_f]: self.fPressed = False
        if not keys[pygame.K_r]: self.rPressed = False
        if not keys[pygame.K_LALT] and not keys[pygame.K_RETURN]: self.altEnterPressed = False
        if not keys[pygame.K_UP] and not keys[pygame.K_w]: self.upPressed = False
        if not keys[pygame.K_DOWN] and not keys[pygame.K_s]: self.downPressed = False
        if not keys[pygame.K_RETURN] and not keys[pygame.K_SPACE]: self.enterPressed = False
        self.mPressed = mouseLeft

    def processMenu(self):
        up = (keys[pygame.K_UP] or keys[pygame.K_w]) and not self.upPressed
        down = (keys[pygame.K_DOWN] or keys[pygame.K_s]) and not self.downPressed
        enter = (keys[pygame.K_RETURN] or keys[pygame.K_SPACE]) and not self.enterPressed

        options = 3
        if up:
            self.menuIdx = (self.menuIdx - 1) % options
            self.upPressed = True
        if down:
            self.menuIdx = (self.menuIdx + 1) % options
            self.downPressed = True

        # Mouse hover sobre opciones del menú
        for i in range(options):
            ox, oy = xper(0.5), yper(0.45) + i*yper(0.09)
            if abs(mouseX - ox) < xper(0.18) and abs(mouseY - oy) < yper(0.04):
                self.menuIdx = i
                if mouseLeft and not self.mPressed:
                    enter = True

        if enter:
            self.enterPressed = True
            if self.menuIdx == 0:
                self.mode = 'pvp'
                self.startGame()
            elif self.menuIdx == 1:
                self.mode = 'cpu'
                self.cpuMark = 2
                self.startGame()
            elif self.menuIdx == 2:
                self.mode = 'cpu'
                self.cpuMark = 1
                self.startGame()

    def startGame(self):
        self.scoreX = 0
        self.scoreO = 0
        self.scoreD = 0
        self.startingTurn = 1
        board[0].reset(self.startingTurn)
        self.state = 'play'

    def newRound(self):
        self.startingTurn = 2 if self.startingTurn == 1 else 1
        board[0].reset(self.startingTurn)
        self.state = 'play'

    def resetScores(self):
        self.scoreX = 0
        self.scoreO = 0
        self.scoreD = 0

    def draw(self):
        if self.state == 'menu':
            self.drawMenu()
        else:
            self.drawHUD()

        if self.showFPS:
            createText(14, 'FPS: %s' % (str(round(clock.get_fps()))), 'topright', (255,255,255), xper(0.99), yper(0.01))

    def drawMenu(self):
        createText(int(sper(0.06)), 'TATETI', 'center', (235, 235, 245), xper(0.5), yper(0.22))
        createText(int(sper(0.018)), 'elegí modo', 'center', (140, 145, 160), xper(0.5), yper(0.33))

        labels = [
            ('2 JUGADORES', (235,235,245)),
            ('VS CPU  (vos X)', colorForMark(1)),
            ('VS CPU  (vos O)', colorForMark(2)),
        ]
        for i, (label, col) in enumerate(labels):
            y = yper(0.45) + i*yper(0.09)
            selected = (self.menuIdx == i)
            size = int(sper(0.032)) if selected else int(sper(0.026))
            if selected:
                pygame.draw.rect(windowSurface, (40, 44, 56), (xper(0.5) - xper(0.2), y - yper(0.035), xper(0.4), yper(0.07)), border_radius=int(sper(0.012)))
                pygame.draw.rect(windowSurface, col, (xper(0.5) - xper(0.2), y - yper(0.035), xper(0.4), yper(0.07)), max(2, int(sper(0.003))), border_radius=int(sper(0.012)))
            createText(size, label, 'center', col if selected else modifyColorPerc(col, 0.55), xper(0.5), y)

        createText(int(sper(0.014)), '↑ ↓  PARA ELEGIR    ENTER PARA JUGAR    ESC PARA SALIR', 'center', (110, 115, 130), xper(0.5), yper(0.92))

    def drawHUD(self):
        b = board[0]

        bx, by, size = b.boardRect()
        topY = by - yper(0.06)

        if self.state == 'play':
            mark = b.turn
            label = 'TURNO DE  ' if self.mode == 'pvp' else ('TU TURNO' if mark != self.cpuMark else 'PENSANDO...')
            createText(int(sper(0.022)), label, 'midright' if self.mode == 'pvp' else 'center', (200, 205, 220),
                       xper(0.5) - (sper(0.02) if self.mode == 'pvp' else 0), topY)
            if self.mode == 'pvp':
                col = colorForMark(mark)
                pulse = 1 + math.sin(time.time()*5) * 0.08
                self.drawTopMark(mark, xper(0.5) + sper(0.018), topY, sper(0.018)*pulse, col)
        elif self.state == 'over':
            if b.winner == 1 or b.winner == 2:
                if self.mode == 'cpu':
                    won = (b.winner != self.cpuMark)
                    txt = '¡GANASTE!' if won else 'GANA LA CPU'
                    col = colorForMark(b.winner)
                else:
                    txt = 'GANA X' if b.winner == 1 else 'GANA O'
                    col = colorForMark(b.winner)
                createText(int(sper(0.028)), txt, 'center', col, xper(0.5), topY)
            else:
                createText(int(sper(0.028)), 'EMPATE', 'center', (200, 205, 220), xper(0.5), topY)

        # Marcador
        scoreY = by + size + yper(0.05)
        xCol = colorForMark(1)
        oCol = colorForMark(2)

        if self.mode == 'cpu':
            youMark = 1 if self.cpuMark == 2 else 2
            youCol = colorForMark(youMark)
            cpuCol = colorForMark(self.cpuMark)
            youScore = self.scoreX if youMark == 1 else self.scoreO
            cpuScore = self.scoreX if self.cpuMark == 1 else self.scoreO
            createText(int(sper(0.016)), 'VOS', 'midbottom', youCol, xper(0.5) - xper(0.18), scoreY - yper(0.005))
            createText(int(sper(0.032)), str(youScore), 'midtop', youCol, xper(0.5) - xper(0.18), scoreY)
            createText(int(sper(0.016)), 'EMPATES', 'midbottom', (160,165,180), xper(0.5), scoreY - yper(0.005))
            createText(int(sper(0.032)), str(self.scoreD), 'midtop', (200,205,220), xper(0.5), scoreY)
            createText(int(sper(0.016)), 'CPU', 'midbottom', cpuCol, xper(0.5) + xper(0.18), scoreY - yper(0.005))
            createText(int(sper(0.032)), str(cpuScore), 'midtop', cpuCol, xper(0.5) + xper(0.18), scoreY)
        else:
            createText(int(sper(0.016)), 'X', 'midbottom', xCol, xper(0.5) - xper(0.18), scoreY - yper(0.005))
            createText(int(sper(0.032)), str(self.scoreX), 'midtop', xCol, xper(0.5) - xper(0.18), scoreY)
            createText(int(sper(0.016)), 'EMPATES', 'midbottom', (160,165,180), xper(0.5), scoreY - yper(0.005))
            createText(int(sper(0.032)), str(self.scoreD), 'midtop', (200,205,220), xper(0.5), scoreY)
            createText(int(sper(0.016)), 'O', 'midbottom', oCol, xper(0.5) + xper(0.18), scoreY - yper(0.005))
            createText(int(sper(0.032)), str(self.scoreO), 'midtop', oCol, xper(0.5) + xper(0.18), scoreY)

        # Pie
        if self.state == 'over':
            blink = (math.sin(time.time()*3) + 1) * 0.5
            col = tuple(int(120 + 100*blink) for _ in range(3))
            createText(int(sper(0.018)), 'CLICK PARA OTRA PARTIDA    R PARA RESETEAR MARCADOR    ESC PARA EL MENÚ', 'center', col, xper(0.5), yper(0.95))
        else:
            createText(int(sper(0.014)), 'ESC PARA EL MENÚ', 'center', (110, 115, 130), xper(0.5), yper(0.95))

    def drawTopMark(self, mark, cx, cy, r, col):
        thick = max(2, int(sper(0.006)))
        if mark == 1:
            pygame.draw.line(windowSurface, col, (cx - r, cy - r), (cx + r, cy + r), thick)
            pygame.draw.line(windowSurface, col, (cx + r, cy - r), (cx - r, cy + r), thick)
        else:
            pygame.draw.circle(windowSurface, col, (cx, cy), r, thick)


# Lógica del tateti -----------------------------------------------------------

WIN_LINES = (
    (0,1,2), (3,4,5), (6,7,8),
    (0,3,6), (1,4,7), (2,5,8),
    (0,4,8), (2,4,6),
)


def checkWinner(cells):
    for line in WIN_LINES:
        a, b, c = line
        if cells[a] != 0 and cells[a] == cells[b] == cells[c]:
            return cells[a], line
    if all(v != 0 for v in cells):
        return 0, None
    return None


def bestMove(cells, mark):
    # Minimax con poda alfa-beta. 3x3 es trivial pero queda prolijo.
    best = -10
    bestMoves = []
    other = 2 if mark == 1 else 1
    for i in range(9):
        if cells[i] == 0:
            cells[i] = mark
            score = -negamax(cells, other, -10, 10, mark)
            cells[i] = 0
            if score > best:
                best = score
                bestMoves = [i]
            elif score == best:
                bestMoves.append(i)
    if not bestMoves:
        return -1
    return random.choice(bestMoves)


def negamax(cells, mark, alpha, beta, rootMark):
    result = checkWinner(cells)
    if result is not None:
        w, _ = result
        if w == 0: return 0
        return 1 if w == rootMark else -1
    other = 2 if mark == 1 else 1
    best = -10
    for i in range(9):
        if cells[i] == 0:
            cells[i] = mark
            score = -negamax(cells, other, -beta, -alpha, rootMark)
            cells[i] = 0
            if score > best: best = score
            if best > alpha: alpha = best
            if alpha >= beta: break
    return best


# Helpers ---------------------------------------------------------------------

def colorForMark(mark):
    if mark == 1: return (240, 90, 95)
    if mark == 2: return (90, 170, 240)
    return (200, 205, 220)


def xper(percentage):
    return percentage * screenX

def yper(percentage):
    return percentage * screenY

def sper(percentage):
    return percentage * (screenX + screenY)/2


def modifyColorPerc(color, factor):
    return tuple(int(max(min(c*factor, 255), 0)) for c in color)


def easeOutBack(t):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t-1)**3 + c1 * (t-1)**2


def easeOutCubic(t):
    return 1 - (1 - t)**3


def createText(size, content, alignment, colorText, posX, posY):
    text_rect = font.get_rect(content, size=size)
    text_rect.midtop = (posX, posY)
    setattr(text_rect, alignment, (posX, posY))
    font.render_to(windowSurface, text_rect, content, colorText, size=size)


def addSprite(sprite):
    sprites.append(sprite)
    return sprite


# INITIALIZATION .....................................................................

pygame.init()

screenX = 1280
screenY = 720
windowSurface = pygame.display.set_mode((screenX, screenY), depth=32, display=0)
pygame.display.set_caption('Tateti')

font = pygame.freetype.SysFont('Century Gothic', 0)

deltaT = 0
iniT = time.time()
clock = pygame.time.Clock()
keys = None
mouseX = mouseY = 0
mouseLeft = mouseRight = False
sprites = []
manager = []
board = []

addSprite(Manager())
addSprite(Board())

# MAIN LOOP ..........................................................................

while True:

    now = time.time()
    deltaT = min(now - iniT, 0.05)
    iniT = now
    clock.tick()

    keys = pygame.key.get_pressed()
    mouseX, mouseY = pygame.mouse.get_pos()
    mouseLeft, mouseMiddle, mouseRight = pygame.mouse.get_pressed()

    windowSurface.fill((14, 16, 22))

    sprites.sort(key=lambda x: x.z, reverse=True)

    for sprite in sprites:
        sprite.process()
        sprite.draw()

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
