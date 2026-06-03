import math
import time
import random
import itertools
import pygame, sys
import pygame.freetype
from pygame.locals import *

class Sprite:
    def process(self):
        pass
    def draw(self):
        pass

RANKS = '23456789TJQKA'
SUITS = 'shdc'
SUIT_SYMBOL = {'s':'♠','h':'♥','d':'♦','c':'♣'}
SUIT_COLOR  = {'s':(20,20,20),'c':(20,20,20),'h':(200,30,30),'d':(200,30,30)}
RANK_DISPLAY = {'T':'10'}

HAND_NAMES = {1:'High Card',2:'Pair',3:'Two Pair',4:'Three of a Kind',
              5:'Straight',6:'Flush',7:'Full House',8:'Four of a Kind',9:'Straight Flush'}

class Card(Sprite):

    def __init__(self, code, target_x, target_y, hidden, owner):

        self.z = 1
        self.code = code
        self.rank = code[0]
        self.suit = code[1]
        self.owner = owner
        self.hidden = hidden
        self.target_x = target_x
        self.target_y = target_y
        self.x = xper(0.5)
        self.y = yper(-0.1) if owner == 'cpu' else yper(1.1)
        self.flip = 0.0 if hidden else 1.0
        self.flip_target = 0.0 if hidden else 1.0
        self.width = sper(0.055)
        self.height = self.width * 1.45

        cards.append(self)
        addSprite(self)

    def reveal(self):
        self.hidden = False
        self.flip_target = 1.0

    def process(self):
        self.x += (self.target_x - self.x) * min(deltaT * 8, 1)
        self.y += (self.target_y - self.y) * min(deltaT * 8, 1)
        self.flip += (self.flip_target - self.flip) * min(deltaT * 7, 1)

    def draw(self):

        scale = abs(self.flip - 0.5) * 2
        w = max(self.width * scale, 2)
        h = self.height
        x = self.x - w/2
        y = self.y - h/2
        rect = pygame.Rect(x, y, w, h)
        radius = int(sper(0.006))
        face_up = self.flip > 0.5 and not self.hidden

        if face_up:
            pygame.draw.rect(windowSurface, (250,248,238), rect, border_radius=radius)
            pygame.draw.rect(windowSurface, (20,20,20), rect, width=2, border_radius=radius)
            if scale > 0.4:
                color = SUIT_COLOR[self.suit]
                rtxt = RANK_DISPLAY.get(self.rank, self.rank)
                createText(int(sper(0.022)), rtxt, 'topleft', color, x + w*0.08, y + h*0.05)
                createText(int(sper(0.018)), SUIT_SYMBOL[self.suit], 'topleft', color, x + w*0.1, y + h*0.28)
                createText(int(sper(0.045)), SUIT_SYMBOL[self.suit], 'center', color, x + w/2, y + h/2)
                createText(int(sper(0.022)), rtxt, 'bottomright', color, x + w*0.92, y + h*0.95)
        else:
            pygame.draw.rect(windowSurface, (30,55,115), rect, border_radius=radius)
            pygame.draw.rect(windowSurface, (210,210,230), rect, width=2, border_radius=radius)
            if scale > 0.5:
                for i in range(4):
                    for j in range(6):
                        pygame.draw.circle(windowSurface, (70,100,170),
                                           (x + w*(0.15 + i*0.23), y + h*(0.1 + j*0.16)),
                                           max(sper(0.004), 1.5))

class Button(Sprite):

    def __init__(self, label, x, y, w, h, action):
        self.z = 0
        self.label = label
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.action = action
        self.hovered = False
        self.enabled = True
        self.pressedPrev = False
        buttons.append(self)
        addSprite(self)

    def hit(self, mx, my):
        return self.x - self.w/2 <= mx <= self.x + self.w/2 and self.y - self.h/2 <= my <= self.y + self.h/2

    def process(self):
        self.hovered = self.enabled and self.hit(mouseX, mouseY)
        if self.hovered and mouseLeft and not self.pressedPrev:
            self.action()
        self.pressedPrev = mouseLeft

    def draw(self):
        if not self.enabled:
            color = (55,55,55); text_color = (120,120,120); border = (30,30,30)
        elif self.hovered:
            color = (220,185,90); text_color = (20,20,20); border = (10,10,10)
        else:
            color = (150,115,40); text_color = (250,240,200); border = (20,20,20)
        rect = pygame.Rect(self.x - self.w/2, self.y - self.h/2, self.w, self.h)
        pygame.draw.rect(windowSurface, color, rect, border_radius=int(sper(0.006)))
        pygame.draw.rect(windowSurface, border, rect, width=2, border_radius=int(sper(0.006)))
        createText(int(sper(0.017)), self.label, 'center', text_color, self.x, self.y)

class Table(Sprite):
    def __init__(self):
        self.z = 100
    def draw(self):
        pygame.draw.ellipse(windowSurface, (15,85,35), pygame.Rect(xper(0.04), yper(0.06), xper(0.92), yper(0.8)))
        pygame.draw.ellipse(windowSurface, (90,55,20), pygame.Rect(xper(0.04), yper(0.06), xper(0.92), yper(0.8)), width=int(sper(0.008)))
        pygame.draw.ellipse(windowSurface, (10,55,25), pygame.Rect(xper(0.08), yper(0.1), xper(0.84), yper(0.72)), width=2)

def hand_rank(cards5):
    vals = sorted([RANKS.index(c[0]) for c in cards5], reverse=True)
    suits = [c[1] for c in cards5]
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    by_count = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))
    is_flush = len(set(suits)) == 1
    uniq = sorted(set(vals), reverse=True)
    is_straight = False
    straight_high = 0
    if len(uniq) == 5:
        if uniq[0] - uniq[4] == 4:
            is_straight = True
            straight_high = uniq[0]
        elif uniq == [12, 3, 2, 1, 0]:
            is_straight = True
            straight_high = 3
    if is_straight and is_flush:
        return (9, straight_high)
    if by_count[0][1] == 4:
        return (8, by_count[0][0], by_count[1][0])
    if by_count[0][1] == 3 and by_count[1][1] == 2:
        return (7, by_count[0][0], by_count[1][0])
    if is_flush:
        return (6,) + tuple(vals)
    if is_straight:
        return (5, straight_high)
    if by_count[0][1] == 3:
        return (4, by_count[0][0]) + tuple(kv[0] for kv in by_count[1:])
    if by_count[0][1] == 2 and by_count[1][1] == 2:
        return (3, by_count[0][0], by_count[1][0], by_count[2][0])
    if by_count[0][1] == 2:
        return (2, by_count[0][0]) + tuple(kv[0] for kv in by_count[1:])
    return (1,) + tuple(vals)

def best_hand(seven):
    best = (0,)
    for combo in itertools.combinations(seven, 5):
        r = hand_rank(combo)
        if r > best:
            best = r
    return best

class Manager(Sprite):

    def __init__(self):
        self.z = -2
        self.showFPS = False
        self.fPressed = False
        self.altEnterPressed = False
        self.fullScreen = False

        self.player_chips = 1000
        self.cpu_chips = 1000
        self.small_blind = 10
        self.big_blind = 20
        self.button = random.choice(['player','cpu'])

        self.phase = 'idle'
        self.cpu_pending = False
        self.cpu_timer = 0
        self.hand_end_timer = 0

        self.deck = []
        self.player_hole = []
        self.cpu_hole = []
        self.community = []

        self.pot = 0
        self.player_bet = 0
        self.cpu_bet = 0
        self.last_raiser = None
        self.acted = set()
        self.current_player = 'player'

        self.raise_amount = 40
        self.message = "Click DEAL to start"

        bw = sper(0.07)
        bh = sper(0.028)
        by = yper(0.94)
        self.bDeal  = Button('DEAL', xper(0.5),  by, bw, bh, self.deal_hand)
        self.bFold  = Button('FOLD', xper(0.30), by, bw, bh, self.act_fold)
        self.bCall  = Button('CHECK', xper(0.40), by, bw, bh, self.act_call)
        self.bRaise = Button('RAISE', xper(0.50), by, bw, bh, self.act_raise)
        self.bMinus = Button('-',     xper(0.585), by, sper(0.022), bh, self.dec_raise)
        self.bPlus  = Button('+',     xper(0.66),  by, sper(0.022), bh, self.inc_raise)

        manager.append(self)

    def deal_hand(self):
        if self.phase not in ('idle','hand_end'):
            return
        if self.player_chips <= 0 or self.cpu_chips <= 0:
            self.player_chips = 1000
            self.cpu_chips = 1000
        for c in list(cards):
            spritesToRemove.append(c)
        removeSprites()

        self.deck = [r+s for r in RANKS for s in SUITS]
        random.shuffle(self.deck)
        self.player_hole = []
        self.cpu_hole = []
        self.community = []
        self.pot = 0
        self.player_bet = 0
        self.cpu_bet = 0
        self.last_raiser = None
        self.acted = set()
        self.message = ''
        self.cpu_pending = False

        self.button = 'cpu' if self.button == 'player' else 'player'
        sb_who = self.button
        bb_who = 'cpu' if self.button == 'player' else 'player'
        self.post_bet(sb_who, self.small_blind)
        self.post_bet(bb_who, self.big_blind)
        self.current_player = self.button

        for i in range(2):
            self.player_hole.append(self.deck.pop())
            self.cpu_hole.append(self.deck.pop())
        for i, code in enumerate(self.player_hole):
            Card(code, xper(0.46 + i*0.06), yper(0.76), hidden=False, owner='player')
        for i, code in enumerate(self.cpu_hole):
            Card(code, xper(0.46 + i*0.06), yper(0.18), hidden=True,  owner='cpu')

        self.phase = 'preflop'

    def post_bet(self, who, amount):
        if who == 'player':
            amount = min(amount, self.player_chips)
            self.player_chips -= amount
            self.player_bet += amount
        else:
            amount = min(amount, self.cpu_chips)
            self.cpu_chips -= amount
            self.cpu_bet += amount
        self.pot += amount

    def in_betting(self):
        return self.phase in ('preflop','flop','turn','river')

    def act_fold(self):
        if not self.in_betting() or self.current_player != 'player': return
        self.cpu_chips += self.pot
        self.pot = 0
        self.message = 'CPU wins (you folded)'
        self.phase = 'hand_end'
        self.hand_end_timer = 2.5

    def act_call(self):
        if not self.in_betting() or self.current_player != 'player': return
        diff = self.cpu_bet - self.player_bet
        if diff > 0:
            self.post_bet('player', diff)
        self.acted.add('player')
        self.current_player = 'cpu'
        self.check_round_end()

    def act_raise(self):
        if not self.in_betting() or self.current_player != 'player': return
        call_amt = max(0, self.cpu_bet - self.player_bet)
        bump = min(self.raise_amount, max(self.player_chips - call_amt, 0))
        if bump <= 0:
            return
        self.post_bet('player', call_amt + bump)
        self.last_raiser = 'player'
        self.acted = {'player'}
        self.current_player = 'cpu'

    def dec_raise(self):
        self.raise_amount = max(self.big_blind, self.raise_amount - self.big_blind)

    def inc_raise(self):
        self.raise_amount = min(max(self.player_chips, self.big_blind), self.raise_amount + self.big_blind)

    def cpu_act(self):
        if not self.in_betting() or self.current_player != 'cpu':
            return
        call_amt = max(0, self.player_bet - self.cpu_bet)

        if self.phase == 'preflop':
            r1, r2 = self.cpu_hole[0][0], self.cpu_hole[1][0]
            v1, v2 = RANKS.index(r1), RANKS.index(r2)
            pair = r1 == r2
            suited = self.cpu_hole[0][1] == self.cpu_hole[1][1]
            high, low = max(v1,v2), min(v1,v2)
            strength = 0.15 + (high/12)*0.32 + (low/12)*0.18
            if pair: strength += 0.30
            if suited: strength += 0.05
            if 1 <= high - low <= 4: strength += 0.04
        else:
            score = best_hand(self.cpu_hole + self.community)
            strength = score[0] / 9.0
            if len(score) > 1:
                strength += (score[1] / 12.0) * 0.04
        strength += random.uniform(-0.12, 0.10)

        pot_odds = call_amt / max(self.pot + call_amt, 1)

        if call_amt > 0 and strength < 0.20 + pot_odds * 0.3:
            self.cpu_chips_won_reveal = False
            self.player_chips += self.pot
            self.pot = 0
            self.message = 'You win (CPU folded)'
            self.phase = 'hand_end'
            self.hand_end_timer = 2.5
            return

        can_raise = self.cpu_chips > call_amt + self.big_blind
        will_raise = can_raise and strength > 0.62 and (self.last_raiser != 'cpu' or random.random() < 0.25)
        if will_raise:
            mult = random.choice([1,1,2,2,3])
            bump = min(self.big_blind * mult, self.cpu_chips - call_amt)
            self.post_bet('cpu', call_amt + bump)
            self.last_raiser = 'cpu'
            self.acted = {'cpu'}
            self.current_player = 'player'
            return

        if call_amt > 0:
            self.post_bet('cpu', call_amt)
        self.acted.add('cpu')
        self.current_player = 'player'
        self.check_round_end()

    def check_round_end(self):
        if self.player_bet != self.cpu_bet:
            return
        need = {'player','cpu'}
        if self.last_raiser is not None:
            need = {'player','cpu'}
        if need.issubset(self.acted):
            self.advance_phase()

    def advance_phase(self):
        self.player_bet = 0
        self.cpu_bet = 0
        self.last_raiser = None
        self.acted = set()
        non_button = 'cpu' if self.button == 'player' else 'player'
        self.current_player = non_button
        self.cpu_pending = False

        if self.phase == 'preflop':
            self.phase = 'flop'
            for i in range(3):
                code = self.deck.pop()
                self.community.append(code)
                Card(code, xper(0.36 + i*0.07), yper(0.46), hidden=False, owner='community')
        elif self.phase == 'flop':
            self.phase = 'turn'
            code = self.deck.pop()
            self.community.append(code)
            Card(code, xper(0.36 + 3*0.07), yper(0.46), hidden=False, owner='community')
        elif self.phase == 'turn':
            self.phase = 'river'
            code = self.deck.pop()
            self.community.append(code)
            Card(code, xper(0.36 + 4*0.07), yper(0.46), hidden=False, owner='community')
        elif self.phase == 'river':
            self.showdown()

    def showdown(self):
        for c in cards:
            if c.owner == 'cpu':
                c.reveal()
        p_score = best_hand(self.player_hole + self.community)
        c_score = best_hand(self.cpu_hole + self.community)
        p_name = HAND_NAMES[p_score[0]]
        c_name = HAND_NAMES[c_score[0]]
        if p_score > c_score:
            self.player_chips += self.pot
            self.message = 'You win! %s beats %s' % (p_name, c_name)
        elif c_score > p_score:
            self.cpu_chips += self.pot
            self.message = 'CPU wins! %s beats %s' % (c_name, p_name)
        else:
            half = self.pot // 2
            self.player_chips += half
            self.cpu_chips += self.pot - half
            self.message = 'Split pot - both %s' % p_name
        self.pot = 0
        self.phase = 'hand_end'
        self.hand_end_timer = 4

    def process(self):
        if keys[pygame.K_ESCAPE]:
            pygame.quit(); sys.exit()

        global windowSurface
        if not self.altEnterPressed:
            if keys[pygame.K_LALT] and keys[pygame.K_RETURN]:
                self.fullScreen = not self.fullScreen
                windowSurface = pygame.display.set_mode((screenX, screenY), depth=32, display=0,
                                                       flags=pygame.FULLSCREEN if self.fullScreen else pygame.SHOWN)
                self.altEnterPressed = True
        if not keys[pygame.K_LALT] and not keys[pygame.K_RETURN]:
            self.altEnterPressed = False

        if not self.fPressed:
            if keys[pygame.K_f]:
                self.showFPS = not self.showFPS
                self.fPressed = True
        if not keys[pygame.K_f]:
            self.fPressed = False

        if self.in_betting() and self.current_player == 'cpu':
            if not self.cpu_pending:
                self.cpu_pending = True
                self.cpu_timer = 0.9
            else:
                self.cpu_timer -= deltaT
                if self.cpu_timer <= 0:
                    self.cpu_pending = False
                    self.cpu_act()
        else:
            self.cpu_pending = False

        if self.phase == 'hand_end':
            self.hand_end_timer -= deltaT
            if self.hand_end_timer <= 0:
                if self.player_chips <= 0 or self.cpu_chips <= 0:
                    self.phase = 'idle'
                    self.message = ('You went broke - click DEAL to rebuy'
                                    if self.player_chips <= 0 else
                                    'CPU went broke - click DEAL to rebuy')
                else:
                    self.phase = 'idle'

        my_turn = self.in_betting() and self.current_player == 'player'
        call_amt = max(0, self.cpu_bet - self.player_bet)
        self.bDeal.enabled  = self.phase == 'idle'
        self.bFold.enabled  = my_turn
        self.bCall.enabled  = my_turn
        self.bRaise.enabled = my_turn and self.player_chips > call_amt
        self.bMinus.enabled = my_turn
        self.bPlus.enabled  = my_turn
        self.bCall.label  = 'CHECK' if call_amt == 0 else ('CALL $%d' % call_amt)
        self.bRaise.label = 'RAISE $%d' % self.raise_amount

    def draw(self):
        createText(int(sper(0.022)), 'CPU  $%d' % self.cpu_chips, 'center', (240,240,220), xper(0.5), yper(0.08))
        createText(int(sper(0.022)), 'YOU  $%d' % self.player_chips, 'center', (240,240,220), xper(0.5), yper(0.86))

        if self.pot > 0:
            createText(int(sper(0.026)), 'POT  $%d' % self.pot, 'center', (255,225,90), xper(0.5), yper(0.36))
        if self.cpu_bet > 0:
            createText(int(sper(0.018)), '$%d' % self.cpu_bet, 'center', (255,255,255), xper(0.5), yper(0.28))
        if self.player_bet > 0:
            createText(int(sper(0.018)), '$%d' % self.player_bet, 'center', (255,255,255), xper(0.5), yper(0.66))

        if self.button == 'player':
            createText(int(sper(0.014)), 'D', 'center', (20,20,20), xper(0.4), yper(0.72))
            pygame.draw.circle(windowSurface, (240,235,180), (xper(0.4), yper(0.72)), sper(0.011), width=2)
        else:
            createText(int(sper(0.014)), 'D', 'center', (20,20,20), xper(0.4), yper(0.22))
            pygame.draw.circle(windowSurface, (240,235,180), (xper(0.4), yper(0.22)), sper(0.011), width=2)

        if self.message:
            createText(int(sper(0.022)), self.message, 'center', (255,235,150), xper(0.5), yper(0.56))

        if self.community and self.in_betting():
            score = best_hand(self.player_hole + self.community)
            createText(int(sper(0.016)), 'Your hand: ' + HAND_NAMES[score[0]], 'center', (200,255,200), xper(0.5), yper(0.81))

        if self.in_betting():
            if self.current_player == 'player':
                pygame.draw.circle(windowSurface, (80,255,80), (xper(0.32), yper(0.76)), sper(0.008))
            else:
                pygame.draw.circle(windowSurface, (255,80,80), (xper(0.32), yper(0.18)), sper(0.008))

        if self.showFPS:
            createText(14, 'FPS: %s' % str(round(clock.get_fps())), 'topright', (255,255,255), xper(0.99), yper(0.01))

def xper(p): return p * screenX
def yper(p): return p * screenY
def sper(p): return p * (screenX + screenY) / 2

def randColorInRange(rl, rh, gl, gh, bl, bh):
    return (random.randint(rl,rh), random.randint(gl,gh), random.randint(bl,bh))

def modifyColorPerc(color, factor):
    return tuple(int(max(min(c*factor, 255), 0)) for c in color)

def createText(size, content, alignment, color, posX, posY):
    rect = font.get_rect(content, size=size)
    setattr(rect, alignment, (posX, posY))
    font.render_to(windowSurface, rect, content, color, size=size)

def addSprite(s):
    sprites.append(s)
    return s

def removeSprites():
    for s in list(sprites):
        if s in spritesToRemove:
            if s in cards: cards.remove(s)
            if s in buttons: buttons.remove(s)
            sprites.remove(s)
    spritesToRemove.clear()

pygame.init()

screenX = 1280
screenY = 720
windowSurface = pygame.display.set_mode((screenX, screenY), depth=32, display=0)
pygame.display.set_caption('Poker')

font = pygame.freetype.SysFont('Century Gothic', 0)

deltaT = 0
iniT = time.time()
clock = pygame.time.Clock()
keys = None
mouseX = mouseY = 0
mouseLeft = mouseMiddle = mouseRight = False
sprites = []
manager = []
cards = []
buttons = []
spritesToRemove = []

addSprite(Table())
addSprite(Manager())

while True:

    now = time.time()
    deltaT = min(now - iniT, 0.05)
    iniT = now
    clock.tick()

    keys = pygame.key.get_pressed()
    mouseX, mouseY = pygame.mouse.get_pos()
    mouseLeft, mouseMiddle, mouseRight = pygame.mouse.get_pressed()

    windowSurface.fill((8,28,15))

    sprites.sort(key=lambda x: x.z, reverse=True)

    for sprite in sprites:
        sprite.process()
        sprite.draw()

    removeSprites()

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
