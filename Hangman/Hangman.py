import os
import math
import time
import random
import pygame, sys
import pygame.freetype
from pygame.locals import *

# Hangman / Ahorcado --------------------------------------------------------
# Sigue el esqueleto compartido del repo (Sprite, deltaT, xper/yper/sper,
# createText). Diferencias notables:
#   - El input de letras se consume de KEYDOWN events (vía la lista global
#     `key_events`) en lugar de keys[K_x] + flag, porque el alfabeto español
#     incluye Ñ y conviene leer event.unicode directamente.
#   - Las listas de palabras viven en words_es.txt / words_en.txt al lado del
#     script (en mayúsculas, una por línea).

MAX_FAILS = 6

HERE = os.path.dirname(os.path.abspath(__file__))

ALPHABETS = {
    'es': 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ',
    'en': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
}

LANG_LABELS = {
    'es': 'ESPAÑOL',
    'en': 'ENGLISH',
}

UI_TEXT = {
    'es': {
        'title':     'AHORCADO',
        'choose':    'ELEGÍ IDIOMA',
        'arrows':    '← →  PARA CAMBIAR    ENTER PARA JUGAR',
        'fails':     'FALLOS',
        'used':      'LETRAS USADAS',
        'won':       '¡GANASTE!',
        'lost':      'PERDISTE',
        'word_was':  'LA PALABRA ERA',
        'play':      'ENTER PARA OTRA PARTIDA',
        'menu':      'ESC PARA VOLVER AL MENÚ',
        'esc_quit':  'ESC PARA SALIR',
    },
    'en': {
        'title':     'HANGMAN',
        'choose':    'CHOOSE LANGUAGE',
        'arrows':    '← →  TO SWITCH    ENTER TO PLAY',
        'fails':     'MISSES',
        'used':      'LETTERS USED',
        'won':       'YOU WIN!',
        'lost':      'YOU LOSE',
        'word_was':  'THE WORD WAS',
        'play':      'ENTER FOR ANOTHER ROUND',
        'menu':      'ESC TO RETURN TO MENU',
        'esc_quit':  'ESC TO QUIT',
    },
}


class Sprite:
    def process(self):
        pass
    def draw(self):
        pass


class Gallows(Sprite):

    def __init__(self):
        self.z = 0
        self.shake_t = 0
        self.shake_total = 0.4
        self.last_fails = 0
        gallows.append(self)

    def process(self):
        m = manager[0]
        if m.fails > self.last_fails:
            self.shake_t = self.shake_total
        self.last_fails = m.fails
        if self.shake_t > 0:
            self.shake_t = max(self.shake_t - deltaT, 0)

    def draw(self):
        m = manager[0]
        fails = m.fails

        shake_x = 0
        if self.shake_t > 0:
            phase = self.shake_t / self.shake_total
            shake_x = math.sin(self.shake_t * 80) * sper(0.005) * phase

        cx = xper(0.25)
        floor_y = yper(0.85)
        post_top = yper(0.15)
        thick = max(3, int(sper(0.006)))
        wood = (190, 150, 95)

        # base, poste, travesaño, soporte diagonal
        pygame.draw.line(windowSurface, wood, (cx - xper(0.09), floor_y), (cx + xper(0.09), floor_y), thick)
        pygame.draw.line(windowSurface, wood, (cx - xper(0.06), floor_y), (cx - xper(0.06), post_top), thick)
        pygame.draw.line(windowSurface, wood, (cx - xper(0.06), post_top), (cx + xper(0.08), post_top), thick)
        pygame.draw.line(windowSurface, wood, (cx - xper(0.06), post_top + yper(0.05)), (cx - xper(0.02), post_top), max(2, thick - 1))

        # soga
        rope_x = cx + xper(0.08)
        rope_top = post_top
        rope_bot = post_top + yper(0.07)
        pygame.draw.line(windowSurface, (200, 200, 200), (rope_x, rope_top), (rope_x, rope_bot), max(2, thick - 2))

        # muñeco
        head_r = sper(0.028)
        bx = rope_x + shake_x
        head_cy = rope_bot + head_r

        man_color = (240, 90, 90) if fails >= MAX_FAILS else (235, 220, 200)
        body_top = head_cy + head_r
        body_bot = body_top + sper(0.085)
        shoulders_y = body_top + sper(0.005)
        hip_y = body_bot
        arm_len = sper(0.055)
        leg_len = sper(0.075)
        line_w = max(3, thick - 1)

        if fails >= 1:
            pygame.draw.circle(windowSurface, man_color, (bx, head_cy), head_r, line_w)
            eo_x = head_r * 0.4
            eo_y = head_r * 0.15
            if fails >= MAX_FAILS:
                d = head_r * 0.22
                for ox in (-eo_x, eo_x):
                    pygame.draw.line(windowSurface, man_color, (bx + ox - d, head_cy - eo_y - d), (bx + ox + d, head_cy - eo_y + d), 2)
                    pygame.draw.line(windowSurface, man_color, (bx + ox - d, head_cy - eo_y + d), (bx + ox + d, head_cy - eo_y - d), 2)
                pygame.draw.arc(windowSurface, man_color, (bx - head_r*0.45, head_cy + head_r*0.05, head_r*0.9, head_r*0.6), math.pi, math.pi*2, 2)
            else:
                pygame.draw.circle(windowSurface, (0, 0, 0), (bx - eo_x, head_cy - eo_y), max(1, int(head_r * 0.13)))
                pygame.draw.circle(windowSurface, (0, 0, 0), (bx + eo_x, head_cy - eo_y), max(1, int(head_r * 0.13)))

        if fails >= 2:
            pygame.draw.line(windowSurface, man_color, (bx, body_top), (bx, body_bot), line_w)
        if fails >= 3:
            pygame.draw.line(windowSurface, man_color, (bx, shoulders_y), (bx - arm_len, shoulders_y + arm_len * 0.6), line_w)
        if fails >= 4:
            pygame.draw.line(windowSurface, man_color, (bx, shoulders_y), (bx + arm_len, shoulders_y + arm_len * 0.6), line_w)
        if fails >= 5:
            pygame.draw.line(windowSurface, man_color, (bx, hip_y), (bx - arm_len * 0.85, hip_y + leg_len), line_w)
        if fails >= 6:
            pygame.draw.line(windowSurface, man_color, (bx, hip_y), (bx + arm_len * 0.85, hip_y + leg_len), line_w)


class WordDisplay(Sprite):

    def __init__(self):
        self.z = 0
        worddisplay.append(self)

    def draw(self):
        m = manager[0]
        if not m.word:
            return

        cx = xper(0.65)

        # Categoria y pista arriba de la palabra
        if m.category:
            createText(int(sper(0.025)), m.category, 'center', (200, 200, 110), cx, yper(0.30))
        if m.hint:
            createText(int(sper(0.022)), '"%s"' % m.hint, 'center', (160, 160, 200), cx, yper(0.36))

        word = m.word
        size = int(sper(0.055))
        gap = size * 0.85
        total_w = len(word) * gap
        start_x = cx - total_w / 2 + gap / 2
        y = yper(0.48)

        for i, ch in enumerate(word):
            cx = start_x + i * gap
            if ch == ' ':
                continue
            reveal_all = m.state in ('won', 'lost')
            shown = ch if m.revealed[i] or reveal_all else ''
            if m.revealed[i]:
                color = (120, 240, 120)
            elif m.state == 'lost':
                color = (240, 110, 110)
            else:
                color = (230, 230, 230)
            if shown:
                createText(size, shown, 'center', color, cx, y - size * 0.55)
            pygame.draw.line(windowSurface, (160, 160, 160), (cx - gap * 0.4, y + size * 0.1), (cx + gap * 0.4, y + size * 0.1), max(2, int(sper(0.0025))))


class LettersUsed(Sprite):

    def __init__(self):
        self.z = 0
        lettersused.append(self)

    def draw(self):
        m = manager[0]
        alph = ALPHABETS[m.lang]
        per_row = 9
        size = int(sper(0.028))
        gap_x = sper(0.04)
        gap_y = sper(0.045)
        rows = (len(alph) + per_row - 1) // per_row
        cx = xper(0.65)
        cy = yper(0.7)
        start_x = cx - (per_row - 1) * gap_x / 2
        start_y = cy - (rows - 1) * gap_y / 2

        for i, ch in enumerate(alph):
            r = i // per_row
            c = i % per_row
            px = start_x + c * gap_x
            py = start_y + r * gap_y
            if ch in m.guessed_correct:
                color = (110, 230, 110)
            elif ch in m.guessed_wrong:
                color = (230, 90, 90)
            else:
                color = (140, 140, 140)
            createText(size, ch, 'center', color, px, py)

        createText(int(sper(0.018)), UI_TEXT[m.lang]['used'], 'center', (180, 180, 180), cx, start_y - gap_y * 0.9)


class Manager(Sprite):

    def __init__(self):
        self.z = -2
        self.state = 'menu'
        self.lang = 'es'
        self.word = ''
        self.category = ''
        self.hint = ''
        self.revealed = []
        self.fails = 0
        self.guessed_correct = set()
        self.guessed_wrong = set()
        self.wins = 0
        self.losses = 0
        self.words = {'es': load_words('words_es.txt'), 'en': load_words('words_en.txt')}
        self.flash_t = 0
        manager.append(self)

    def start_round(self):
        pool = self.words[self.lang]
        word, category, hint = random.choice(pool)
        self.word = word
        self.category = category
        self.hint = hint
        self.revealed = [ch == ' ' for ch in self.word]
        self.fails = 0
        self.guessed_correct = set()
        self.guessed_wrong = set()
        self.state = 'playing'

    def guess(self, letter):
        if not letter or self.state != 'playing':
            return
        letter = letter.upper()
        if letter not in ALPHABETS[self.lang]:
            return
        if letter in self.guessed_correct or letter in self.guessed_wrong:
            return
        if letter in self.word:
            self.guessed_correct.add(letter)
            for i, ch in enumerate(self.word):
                if ch == letter:
                    self.revealed[i] = True
            if all(self.revealed):
                self.state = 'won'
                self.wins += 1
                self.flash_t = 1.0
        else:
            self.guessed_wrong.add(letter)
            self.fails += 1
            if self.fails >= MAX_FAILS:
                self.state = 'lost'
                self.losses += 1
                self.flash_t = 1.0

    def process(self):

        if self.flash_t > 0:
            self.flash_t = max(self.flash_t - deltaT, 0)

        for ev in key_events:
            if ev.type != pygame.KEYDOWN:
                continue
            k = ev.key

            if k == pygame.K_ESCAPE:
                if self.state == 'menu':
                    pygame.quit()
                    sys.exit()
                else:
                    self.state = 'menu'
                continue

            if self.state == 'menu':
                if k in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                    self.lang = 'en' if self.lang == 'es' else 'es'
                elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.start_round()

            elif self.state == 'playing':
                ch = (ev.unicode or '').upper()
                if ch:
                    self.guess(ch)

            elif self.state in ('won', 'lost'):
                if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.start_round()

    def draw(self):
        t = UI_TEXT[self.lang]

        if self.state == 'menu':
            createText(int(sper(0.09)), t['title'], 'center', (230, 230, 230), xper(0.5), yper(0.28))
            createText(int(sper(0.03)), t['choose'], 'center', (200, 200, 200), xper(0.5), yper(0.5))

            box_w = xper(0.16)
            box_h = yper(0.1)
            for i, lang in enumerate(('es', 'en')):
                bx = xper(0.38 + i * 0.24)
                by = yper(0.6)
                selected = (lang == self.lang)
                color = (110, 230, 110) if selected else (130, 130, 130)
                rect = pygame.Rect(bx - box_w / 2, by - box_h / 2, box_w, box_h)
                pygame.draw.rect(windowSurface, color, rect, max(2, int(sper(0.003))), border_radius=int(sper(0.01)))
                createText(int(sper(0.035)), LANG_LABELS[lang], 'center', color, bx, by)

            createText(int(sper(0.022)), t['arrows'], 'center', (180, 180, 180), xper(0.5), yper(0.78))
            createText(int(sper(0.018)), t['esc_quit'], 'center', (110, 110, 110), xper(0.5), yper(0.92))
            return

        # HUD partido en curso o terminado
        createText(int(sper(0.022)), '%s: %d / %d' % (t['fails'], self.fails, MAX_FAILS), 'topleft', (200, 200, 200), xper(0.02), yper(0.02))
        createText(int(sper(0.022)), 'W %d  ·  L %d' % (self.wins, self.losses), 'topright', (200, 200, 200), xper(0.98), yper(0.02))

        if self.state == 'won':
            flash = (math.sin(time.time() * 6) * 0.5 + 0.5)
            color = (int(120 + 135 * flash), 230, int(120 + 135 * flash))
            createText(int(sper(0.07)), t['won'], 'center', color, xper(0.65), yper(0.2))
            createText(int(sper(0.024)), t['play'], 'center', (200, 200, 200), xper(0.65), yper(0.85))
            createText(int(sper(0.02)),  t['menu'], 'center', (130, 130, 130), xper(0.65), yper(0.91))
        elif self.state == 'lost':
            createText(int(sper(0.07)), t['lost'], 'center', (240, 110, 110), xper(0.65), yper(0.2))
            createText(int(sper(0.025)), t['word_was'] + ': ' + self.word, 'center', (220, 220, 220), xper(0.65), yper(0.62))
            createText(int(sper(0.024)), t['play'], 'center', (200, 200, 200), xper(0.65), yper(0.85))
            createText(int(sper(0.02)),  t['menu'], 'center', (130, 130, 130), xper(0.65), yper(0.91))


def load_words(filename):
    """Lee `PALABRA|CATEGORIA|pista` por linea. Categoria y pista son opcionales.
       Devuelve lista de tuplas (word, category, hint)."""
    path = os.path.join(HERE, filename)
    entries = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split('|')]
            word = parts[0].upper()
            category = parts[1].upper() if len(parts) >= 2 and parts[1] else ''
            hint = parts[2] if len(parts) >= 3 and parts[2] else ''
            if word:
                entries.append((word, category, hint))
    if not entries:
        raise RuntimeError('No words found in %s' % path)
    return entries


def xper(percentage):
    return percentage * screenX

def yper(percentage):
    return percentage * screenY

def sper(percentage):
    return percentage * (screenX + screenY) / 2

def randColorInRange(redLow, redHigh, greenLow, greenHigh, blueLow, blueHigh):
    return (random.randint(redLow, redHigh), random.randint(greenLow, greenHigh), random.randint(blueLow, blueHigh))

def modifyColorPerc(color, offset):
    return tuple(int(max(min(c * offset, 255), 0)) for c in color)

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
pygame.display.set_caption('Hangman / Ahorcado')

font = pygame.freetype.SysFont('Century Gothic', 0)

deltaT = 0
iniT = time.time()
clock = pygame.time.Clock()
keys = None
key_events = []
sprites = []
manager = []
gallows = []
worddisplay = []
lettersused = []

addSprite(Manager())
addSprite(Gallows())
addSprite(WordDisplay())
addSprite(LettersUsed())


# MAIN LOOP ..........................................................................

while True:

    now = time.time()
    deltaT = min(now - iniT, 0.05)
    iniT = now
    clock.tick(60)

    keys = pygame.key.get_pressed()

    key_events = []
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            key_events.append(event)

    windowSurface.fill((20, 22, 30))

    sprites.sort(key=lambda x: x.z, reverse=True)

    m = manager[0]
    for sprite in sprites:
        sprite.process()
        # En el menú solo dibujamos el manager (los otros sprites necesitan una palabra activa)
        if m.state == 'menu' and sprite is not m:
            continue
        sprite.draw()

    pygame.display.update()
