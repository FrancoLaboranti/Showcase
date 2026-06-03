import array
import atexit
import math
import os
import random
import threading
import time
import pygame, sys
import pygame.freetype
from pygame.locals import *

try:
    import chess
    import chess.engine
    CHESS_LIB_AVAILABLE = True
except ImportError:
    CHESS_LIB_AVAILABLE = False


class Sprite:
    def process(self):
        pass
    def draw(self):
        pass

PIECE_CHARS = {
    'K': '♚', 'Q': '♛', 'R': '♜',
    'B': '♝', 'N': '♞', 'P': '♟',
}
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
AI_TIME_BUDGET_S = 1.5         # tiempo por jugada de la IA (todos los modos)
AI_MAX_DEPTH = 10
SAMPLE_RATE = 22050
MOVE_ANIM_DURATION = 0.18


class TimeoutSignal(Exception):
    pass


class Piece:
    __slots__ = ('color', 'kind', 'has_moved')
    def __init__(self, color, kind):
        self.color = color
        self.kind = kind
        self.has_moved = False


# ====================================================================
# CHESS ENGINE
# ====================================================================

def piece_at(grid, c, r):
    if 0 <= c < 8 and 0 <= r < 8:
        return grid[c][r]
    return None

def copy_grid(grid):
    return [row[:] for row in grid]

def gen_pseudo_moves(grid, c, r, ep):
    piece = grid[c][r]
    if piece is None:
        return []
    moves = []
    if piece.kind == 'P':
        direction = -1 if piece.color == 'w' else 1
        start_row = 6 if piece.color == 'w' else 1
        promo_row = 0 if piece.color == 'w' else 7
        if piece_at(grid, c, r + direction) is None:
            extra = {'promotion': True} if r + direction == promo_row else {}
            moves.append((c, r + direction, extra))
            if r == start_row and piece_at(grid, c, r + 2*direction) is None:
                moves.append((c, r + 2*direction, {'double_push': True}))
        for dc in (-1, 1):
            nc, nr = c + dc, r + direction
            t = piece_at(grid, nc, nr)
            if t is not None and t.color != piece.color:
                extra = {'promotion': True} if nr == promo_row else {}
                moves.append((nc, nr, extra))
            if ep == (nc, nr):
                moves.append((nc, nr, {'en_passant': True}))
    elif piece.kind == 'N':
        for dc, dr in ((1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)):
            nc, nr = c + dc, r + dr
            if 0 <= nc < 8 and 0 <= nr < 8:
                t = grid[nc][nr]
                if t is None or t.color != piece.color:
                    moves.append((nc, nr, {}))
    elif piece.kind == 'K':
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                nc, nr = c + dc, r + dr
                if 0 <= nc < 8 and 0 <= nr < 8:
                    t = grid[nc][nr]
                    if t is None or t.color != piece.color:
                        moves.append((nc, nr, {}))
    else:
        dirs = []
        if piece.kind in ('B', 'Q'):
            dirs += [(1,1),(-1,1),(1,-1),(-1,-1)]
        if piece.kind in ('R', 'Q'):
            dirs += [(1,0),(-1,0),(0,1),(0,-1)]
        for dc, dr in dirs:
            nc, nr = c + dc, r + dr
            while 0 <= nc < 8 and 0 <= nr < 8:
                t = grid[nc][nr]
                if t is None:
                    moves.append((nc, nr, {}))
                else:
                    if t.color != piece.color:
                        moves.append((nc, nr, {}))
                    break
                nc += dc
                nr += dr
    return moves

def square_attacked(grid, c, r, by_color):
    pawn_from_dr = 1 if by_color == 'w' else -1
    for dc in (-1, 1):
        p = piece_at(grid, c + dc, r + pawn_from_dr)
        if p and p.color == by_color and p.kind == 'P':
            return True
    for dc, dr in ((1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)):
        p = piece_at(grid, c + dc, r + dr)
        if p and p.color == by_color and p.kind == 'N':
            return True
    for dc in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if dc == 0 and dr == 0:
                continue
            p = piece_at(grid, c + dc, r + dr)
            if p and p.color == by_color and p.kind == 'K':
                return True
    for dc, dr in ((1,0),(-1,0),(0,1),(0,-1)):
        nc, nr = c + dc, r + dr
        while 0 <= nc < 8 and 0 <= nr < 8:
            p = grid[nc][nr]
            if p:
                if p.color == by_color and p.kind in ('R', 'Q'):
                    return True
                break
            nc += dc; nr += dr
    for dc, dr in ((1,1),(-1,1),(1,-1),(-1,-1)):
        nc, nr = c + dc, r + dr
        while 0 <= nc < 8 and 0 <= nr < 8:
            p = grid[nc][nr]
            if p:
                if p.color == by_color and p.kind in ('B', 'Q'):
                    return True
                break
            nc += dc; nr += dr
    return False

def find_king(grid, color):
    for c in range(8):
        for r in range(8):
            p = grid[c][r]
            if p and p.color == color and p.kind == 'K':
                return (c, r)
    return None

def in_check(grid, color):
    k = find_king(grid, color)
    if k is None:
        return False
    enemy = 'b' if color == 'w' else 'w'
    return square_attacked(grid, k[0], k[1], enemy)

def simulate_move(grid, fc, fr, tc, tr, extra):
    g = copy_grid(grid)
    piece = g[fc][fr]
    g[fc][fr] = None
    if extra.get('en_passant'):
        g[tc][fr] = None
    if extra.get('castle'):
        if tc == 6:
            g[5][tr] = g[7][tr]; g[7][tr] = None
        elif tc == 2:
            g[3][tr] = g[0][tr]; g[0][tr] = None
    if extra.get('promotion'):
        piece = Piece(piece.color, 'Q')
    g[tc][tr] = piece
    return g

def gen_legal_moves(grid, c, r, ep):
    piece = grid[c][r]
    if piece is None:
        return []
    pseudo = gen_pseudo_moves(grid, c, r, ep)

    if piece.kind == 'K' and not piece.has_moved:
        rank = 7 if piece.color == 'w' else 0
        if c == 4 and r == rank:
            enemy = 'b' if piece.color == 'w' else 'w'
            if not square_attacked(grid, 4, rank, enemy):
                rook = grid[7][rank]
                if (rook and rook.kind == 'R' and rook.color == piece.color and not rook.has_moved
                    and grid[5][rank] is None and grid[6][rank] is None
                    and not square_attacked(grid, 5, rank, enemy)
                    and not square_attacked(grid, 6, rank, enemy)):
                    pseudo.append((6, rank, {'castle': True}))
                rook = grid[0][rank]
                if (rook and rook.kind == 'R' and rook.color == piece.color and not rook.has_moved
                    and grid[1][rank] is None and grid[2][rank] is None and grid[3][rank] is None
                    and not square_attacked(grid, 3, rank, enemy)
                    and not square_attacked(grid, 2, rank, enemy)):
                    pseudo.append((2, rank, {'castle': True}))

    legal = []
    for tc, tr, extra in pseudo:
        ng = simulate_move(grid, c, r, tc, tr, extra)
        if not in_check(ng, piece.color):
            legal.append((tc, tr, extra))
    return legal

def any_legal_move(grid, color, ep):
    for c in range(8):
        for r in range(8):
            p = grid[c][r]
            if p and p.color == color:
                if gen_legal_moves(grid, c, r, ep):
                    return True
    return False

def all_legal_moves_with(grid, color, ep):
    out = []
    for c in range(8):
        for r in range(8):
            p = grid[c][r]
            if p and p.color == color:
                for tc, tr, extra in gen_legal_moves(grid, c, r, ep):
                    out.append((c, r, tc, tr, extra))
    return out


# ====================================================================
# AI (negamax + alpha-beta + move ordering)
# ====================================================================

def evaluate(grid):
    score = 0
    for c in range(8):
        for r in range(8):
            p = grid[c][r]
            if p is None:
                continue
            val = PIECE_VALUES[p.kind]
            if p.kind in ('N', 'B'):
                center_dist = max(abs(c - 3.5), abs(r - 3.5))
                val += int((3.5 - center_dist) * 6)
            elif p.kind == 'P':
                if p.color == 'w':
                    val += (6 - r) * 5
                else:
                    val += (r - 1) * 5
                if 3 <= c <= 4:
                    val += 6
            elif p.kind == 'K':
                if 2 <= c <= 5 and 2 <= r <= 5:
                    val -= 10
            score += val if p.color == 'w' else -val
    return score

def _move_order_key(grid, mv):
    fc, fr, tc, tr, extra = mv
    s = 0
    target = grid[tc][tr]
    if target:
        s += PIECE_VALUES[target.kind] * 10 - PIECE_VALUES[grid[fc][fr].kind]
    if extra.get('promotion'):
        s += 800
    if extra.get('en_passant'):
        s += 100
    return s

def negamax(grid, depth, alpha, beta, color, ep, deadline):
    if time.time() >= deadline:
        raise TimeoutSignal()
    if depth == 0:
        sign = 1 if color == 'w' else -1
        return evaluate(grid) * sign
    moves = all_legal_moves_with(grid, color, ep)
    if not moves:
        if in_check(grid, color):
            return -100000 - depth
        return 0
    moves.sort(key=lambda mv: _move_order_key(grid, mv), reverse=True)

    best = -math.inf
    opp = 'b' if color == 'w' else 'w'
    for fc, fr, tc, tr, extra in moves:
        new_grid = simulate_move(grid, fc, fr, tc, tr, extra)
        new_ep = None
        piece = grid[fc][fr]
        if piece.kind == 'P' and extra.get('double_push'):
            new_ep = (fc, (fr + tr) // 2)
        score = -negamax(new_grid, depth - 1, -beta, -alpha, opp, new_ep, deadline)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def search_root(grid, color, ep, depth, deadline, hint):
    moves = all_legal_moves_with(grid, color, ep)
    if not moves:
        return None
    moves.sort(key=lambda mv: _move_order_key(grid, mv), reverse=True)
    if hint is not None and hint in moves:
        moves.remove(hint)
        moves.insert(0, hint)

    best_score = -math.inf
    best_move = None
    alpha = -math.inf
    beta = math.inf
    opp = 'b' if color == 'w' else 'w'
    for mv in moves:
        if time.time() >= deadline:
            raise TimeoutSignal()
        fc, fr, tc, tr, extra = mv
        new_grid = simulate_move(grid, fc, fr, tc, tr, extra)
        new_ep = None
        piece = grid[fc][fr]
        if piece.kind == 'P' and extra.get('double_push'):
            new_ep = (fc, (fr + tr) // 2)
        score = -negamax(new_grid, depth - 1, -beta, -alpha, opp, new_ep, deadline)
        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score
    return best_move

def find_best_move(grid, color, ep, max_depth, time_budget):
    """Iterative deepening with time cap. Returns (best_move, depth_reached)."""
    deadline = time.time() + time_budget
    moves = all_legal_moves_with(grid, color, ep)
    if not moves:
        return None, 0
    moves.sort(key=lambda mv: _move_order_key(grid, mv), reverse=True)
    best_move = moves[0]
    depth_reached = 0
    for depth in range(1, max_depth + 1):
        try:
            mv = search_root(grid, color, ep, depth, deadline, best_move)
            if mv is not None:
                best_move = mv
                depth_reached = depth
        except TimeoutSignal:
            break
        if time.time() >= deadline:
            break
    return best_move, depth_reached


# ====================================================================
# STOCKFISH INTEGRATION (UCI via python-chess)
# ====================================================================

_stockfish_engine = None
_stockfish_lock = threading.Lock()
_stockfish_path = None

def _find_stockfish_path():
    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base, 'stockfish', 'stockfish-windows-x86-64-avx2.exe'),
        os.path.join(base, 'stockfish', 'stockfish-windows-x86-64-bmi2.exe'),
        os.path.join(base, 'stockfish', 'stockfish-windows-x86-64.exe'),
        os.path.join(base, 'stockfish', 'stockfish.exe'),
        os.path.join(base, 'stockfish.exe'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def init_stockfish():
    global _stockfish_engine, _stockfish_path
    if not CHESS_LIB_AVAILABLE:
        return False
    _stockfish_path = _find_stockfish_path()
    if _stockfish_path is None:
        return False
    try:
        _stockfish_engine = chess.engine.SimpleEngine.popen_uci(_stockfish_path)
        return True
    except Exception as e:
        print('Stockfish init failed:', e)
        _stockfish_engine = None
        return False

def close_stockfish():
    global _stockfish_engine
    if _stockfish_engine is not None:
        try:
            _stockfish_engine.quit()
        except Exception:
            pass
        _stockfish_engine = None

atexit.register(close_stockfish)

def build_fen(grid, turn, ep):
    rows = []
    for r in range(8):
        row = ''
        empty = 0
        for c in range(8):
            p = grid[c][r]
            if p is None:
                empty += 1
            else:
                if empty > 0:
                    row += str(empty)
                    empty = 0
                letter = p.kind
                if p.color == 'b':
                    letter = letter.lower()
                row += letter
        if empty > 0:
            row += str(empty)
        rows.append(row)
    pieces = '/'.join(rows)
    turn_c = 'w' if turn == 'w' else 'b'
    castle = ''
    wk = grid[4][7]
    if wk and wk.kind == 'K' and wk.color == 'w' and not wk.has_moved:
        rr = grid[7][7]
        if rr and rr.kind == 'R' and rr.color == 'w' and not rr.has_moved:
            castle += 'K'
        rr = grid[0][7]
        if rr and rr.kind == 'R' and rr.color == 'w' and not rr.has_moved:
            castle += 'Q'
    bk = grid[4][0]
    if bk and bk.kind == 'K' and bk.color == 'b' and not bk.has_moved:
        rr = grid[7][0]
        if rr and rr.kind == 'R' and rr.color == 'b' and not rr.has_moved:
            castle += 'k'
        rr = grid[0][0]
        if rr and rr.kind == 'R' and rr.color == 'b' and not rr.has_moved:
            castle += 'q'
    if not castle:
        castle = '-'
    if ep:
        ec, er = ep
        ep_s = 'abcdefgh'[ec] + str(8 - er)
    else:
        ep_s = '-'
    return pieces + ' ' + turn_c + ' ' + castle + ' ' + ep_s + ' 0 1'

def position_key(grid, turn, ep):
    """FEN-style key for threefold repetition: board + turn + castling + en-passant.
    Excludes halfmove/fullmove counters so repeated positions match."""
    return build_fen(grid, turn, ep).rsplit(' ', 2)[0]

def has_insufficient_material(grid):
    """True when neither side can force checkmate: K vs K, K vs K+N, K vs K+B,
    or K+B vs K+B with both bishops on same-coloured squares."""
    white = []   # non-king kinds
    black = []
    white_b_sq = []   # (c+r)%2 for each white bishop
    black_b_sq = []
    for c in range(8):
        for r in range(8):
            p = grid[c][r]
            if p is None or p.kind == 'K':
                continue
            if p.kind in ('P', 'R', 'Q'):
                return False
            if p.color == 'w':
                white.append(p.kind)
                if p.kind == 'B':
                    white_b_sq.append((c + r) % 2)
            else:
                black.append(p.kind)
                if p.kind == 'B':
                    black_b_sq.append((c + r) % 2)
    if not white and not black:
        return True
    if not white and len(black) == 1 and black[0] in ('B', 'N'):
        return True
    if not black and len(white) == 1 and white[0] in ('B', 'N'):
        return True
    if (len(white) == 1 and white[0] == 'B'
        and len(black) == 1 and black[0] == 'B'
        and white_b_sq[0] == black_b_sq[0]):
        return True
    return False

def find_best_move_stockfish(grid, color, ep, time_budget):
    """Returns (move_tuple, depth_reached)."""
    if _stockfish_engine is None:
        return None, 0
    fen = build_fen(grid, color, ep)
    try:
        board = chess.Board(fen)
    except ValueError:
        return None, 0
    with _stockfish_lock:
        try:
            result = _stockfish_engine.play(
                board,
                chess.engine.Limit(time=time_budget),
                info=chess.engine.INFO_ALL,
            )
        except Exception:
            return None, 0
    if result.move is None:
        return None, 0
    sq_from = result.move.from_square
    sq_to = result.move.to_square
    fc = chess.square_file(sq_from)
    fr = 7 - chess.square_rank(sq_from)
    tc = chess.square_file(sq_to)
    tr = 7 - chess.square_rank(sq_to)
    legal = gen_legal_moves(grid, fc, fr, ep)
    for to_c, to_r, extra in legal:
        if (to_c, to_r) == (tc, tr):
            depth = 0
            if result.info:
                depth = result.info.get('depth', 0) or 0
            return (fc, fr, tc, tr, extra), depth
    return None, 0


# ====================================================================
# GAME (menu + play)
# ====================================================================

class Game(Sprite):

    def __init__(self):
        self.z = 0
        self.state = 'menu'
        self.mode = None
        self.ai_color = None
        self.human_color = None
        self.ai_both = False
        self.ai_engine_name = ''
        self.flip = False
        self.gen = 0
        self.ai_thinking = False
        self.ai_last_depth = 0
        self._ai_lock = threading.Lock()
        self._ai_result = None
        self._pending_ai = None
        self.animation = None
        self.captured = []
        self.mDown = False
        self.rKey = False
        self.nKey = False
        self.kLeft = False
        self.kLeftFire = 0.0
        self.kRight = False
        self.kRightFire = 0.0
        self.kHome = False
        self.kEnd = False
        self.dragging = False
        self.drag_from = None
        self.history = []
        self.history_index = 0
        self.reset_board()

    def reset_board(self):
        self.gen += 1
        with self._ai_lock:
            self._ai_result = None
        self.ai_thinking = False
        self.ai_last_depth = 0
        self.ai_engine_name = ''
        self._pending_ai = None
        self.animation = None
        self.captured = []
        self.position_counts = {}
        self.grid = [[None]*8 for _ in range(8)]
        for c in range(8):
            self.grid[c][6] = Piece('w', 'P')
            self.grid[c][1] = Piece('b', 'P')
        back = ['R','N','B','Q','K','B','N','R']
        for c in range(8):
            self.grid[c][7] = Piece('w', back[c])
            self.grid[c][0] = Piece('b', back[c])
        self.selected = None
        self.legal = []
        self.turn = 'w'
        self.last_move = None
        self.en_passant_target = None
        self.status = ''
        self.game_over = False
        self.dragging = False
        self.drag_from = None
        self.history = []
        self.history_index = 0
        self._record_position()
        self.push_history()

    def _record_position(self):
        key = position_key(self.grid, self.turn, self.en_passant_target)
        n = self.position_counts.get(key, 0) + 1
        self.position_counts[key] = n
        return n

    def push_history(self):
        snap = {
            'grid': copy_grid(self.grid),
            'turn': self.turn,
            'last_move': self.last_move,
            'status': self.status,
            'game_over': self.game_over,
            'captured': list(self.captured),
        }
        self.history.append(snap)
        self.history_index = len(self.history) - 1

    def is_viewing_history(self):
        return self.history_index < len(self.history) - 1

    def history_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.selected = None
            self.legal = []
            self.dragging = False
            self.drag_from = None

    def history_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.selected = None
            self.legal = []
            self.dragging = False
            self.drag_from = None

    def history_first(self):
        self.history_index = 0
        self.selected = None
        self.legal = []
        self.dragging = False
        self.drag_from = None

    def history_last(self):
        self.history_index = len(self.history) - 1
        self.selected = None
        self.legal = []
        self.dragging = False
        self.drag_from = None

    def start_game(self, mode):
        self.mode = mode
        self.ai_both = (mode == 'aiva')
        if mode == 'pvp':
            self.ai_color = None
            self.human_color = None
            self.flip = False
        elif mode == 'w':
            self.ai_color = 'b'
            self.human_color = 'w'
            self.flip = False
        elif mode == 'b':
            self.ai_color = 'w'
            self.human_color = 'b'
            self.flip = True
        else:  # 'aiva'
            self.ai_color = None
            self.human_color = None
            self.flip = False
        self.reset_board()
        self.state = 'play'

    def back_to_menu(self):
        self.state = 'menu'
        self.reset_board()

    def current_player_is_ai(self):
        if self.ai_both:
            return True
        if self.ai_color is None:
            return False
        return self.turn == self.ai_color

    def is_human_turn(self):
        return not self.current_player_is_ai()

    def cell_size(self):
        return yper(0.105)

    def board_origin(self):
        s = self.cell_size()
        return (screenX/2 - s*4, screenY/2 - s*4 + yper(0.01))

    def cell_to_screen(self, c, r):
        ox, oy = self.board_origin()
        s = self.cell_size()
        sc = 7 - c if self.flip else c
        sr = 7 - r if self.flip else r
        return (ox + sc*s, oy + sr*s)

    def square_at_pixel(self, px, py):
        ox, oy = self.board_origin()
        s = self.cell_size()
        sc = int((px - ox) // s)
        sr = int((py - oy) // s)
        if 0 <= sc < 8 and 0 <= sr < 8:
            c = 7 - sc if self.flip else sc
            r = 7 - sr if self.flip else sr
            return (c, r)
        return None

    def menu_buttons(self):
        bw = xper(0.36)
        bh = yper(0.08)
        cx = screenX / 2
        by = yper(0.36)
        gap = yper(0.018)
        return [
            ('pvp', pygame.Rect(int(cx - bw/2), int(by + 0*(bh+gap)), int(bw), int(bh)),
             '2 Jugadores'),
            ('w', pygame.Rect(int(cx - bw/2), int(by + 1*(bh+gap)), int(bw), int(bh)),
             'Jugar con Blancas  (vs IA)'),
            ('b', pygame.Rect(int(cx - bw/2), int(by + 2*(bh+gap)), int(bw), int(bh)),
             'Jugar con Negras  (vs IA)'),
            ('aiva', pygame.Rect(int(cx - bw/2), int(by + 3*(bh+gap)), int(bw), int(bh)),
             'IA vs IA  (espectador)'),
        ]

    def process(self):
        just_pressed = mouseLeft and not self.mDown
        just_released = (not mouseLeft) and self.mDown
        self.mDown = mouseLeft

        if self.state == 'menu':
            if just_pressed:
                for mode, rect, _ in self.menu_buttons():
                    if rect.collidepoint(mouseX, mouseY):
                        self.start_game(mode)
                        return
            return

        if self.animation is not None:
            self.animation['elapsed'] += deltaT
            if self.animation['elapsed'] >= self.animation['duration']:
                self.animation = None

        if self.animation is None and self._pending_ai is not None:
            mv, depth, name = self._pending_ai
            self._pending_ai = None
            if self.current_player_is_ai() and not self.game_over and mv is not None:
                self.ai_last_depth = depth
                self.ai_engine_name = name
                self.make_move(*mv)

        with self._ai_lock:
            result = self._ai_result
            self._ai_result = None
        if result is not None:
            mv, gen, depth, name = result
            self.ai_thinking = False
            if (gen == self.gen and self.current_player_is_ai()
                and not self.game_over and mv is not None):
                if self.animation is None:
                    self.ai_last_depth = depth
                    self.ai_engine_name = name
                    self.make_move(*mv)
                else:
                    self._pending_ai = (mv, depth, name)

        if (self.current_player_is_ai() and not self.ai_thinking
            and not self.game_over and self._pending_ai is None
            and self.animation is None):
            self.trigger_ai()

        viewing = self.is_viewing_history()
        if (not self.game_over and self.is_human_turn() and not self.ai_thinking
            and not viewing and self.animation is None):
            if just_pressed:
                self.handle_press()
            if just_released:
                self.handle_release()

        self._key_repeat(pygame.K_LEFT, 'kLeft', 'kLeftFire', self.history_back)
        self._key_repeat(pygame.K_RIGHT, 'kRight', 'kRightFire', self.history_forward)

        if keys[pygame.K_HOME] and not self.kHome:
            self.history_first()
            self.kHome = True
        if not keys[pygame.K_HOME]:
            self.kHome = False

        if keys[pygame.K_END] and not self.kEnd:
            self.history_last()
            self.kEnd = True
        if not keys[pygame.K_END]:
            self.kEnd = False

        r_now = keys[pygame.K_r]
        if r_now and not self.rKey:
            self.reset_board()
            self.rKey = True
        if not r_now:
            self.rKey = False

        n_now = keys[pygame.K_n]
        if n_now and not self.nKey:
            self.back_to_menu()
            self.nKey = True
        if not n_now:
            self.nKey = False

    def _key_repeat(self, key, held_attr, fire_attr, action, initial=0.4, interval=0.06):
        held = getattr(self, held_attr)
        if keys[key]:
            now = time.time()
            if not held:
                action()
                setattr(self, held_attr, True)
                setattr(self, fire_attr, now + initial)
            elif now >= getattr(self, fire_attr):
                action()
                setattr(self, fire_attr, now + interval)
        else:
            setattr(self, held_attr, False)

    def handle_press(self):
        sq = self.square_at_pixel(mouseX, mouseY)
        if sq is None:
            self.selected = None
            self.legal = []
            self.dragging = False
            return
        c, r = sq
        if self.selected:
            for tc, tr, extra in self.legal:
                if (tc, tr) == (c, r):
                    self.make_move(self.selected[0], self.selected[1], tc, tr, extra)
                    self.selected = None
                    self.legal = []
                    self.dragging = False
                    return
        piece = self.grid[c][r]
        if piece and piece.color == self.turn:
            self.selected = (c, r)
            self.legal = gen_legal_moves(self.grid, c, r, self.en_passant_target)
            self.dragging = True
            self.drag_from = (c, r)
        else:
            self.selected = None
            self.legal = []
            self.dragging = False

    def handle_release(self):
        if not self.dragging:
            return
        self.dragging = False
        from_sq = self.drag_from
        self.drag_from = None
        sq = self.square_at_pixel(mouseX, mouseY)
        if sq is None or from_sq is None:
            return
        if (sq[0], sq[1]) == from_sq:
            return
        c, r = sq
        for tc, tr, extra in self.legal:
            if (tc, tr) == (c, r):
                self.make_move(from_sq[0], from_sq[1], tc, tr, extra, animate=False)
                self.selected = None
                self.legal = []
                return
        piece = self.grid[c][r]
        if piece and piece.color == self.turn:
            self.selected = (c, r)
            self.legal = gen_legal_moves(self.grid, c, r, self.en_passant_target)
        else:
            self.selected = None
            self.legal = []

    def make_move(self, fc, fr, tc, tr, extra, animate=True):
        piece = self.grid[fc][fr]
        if extra.get('en_passant'):
            captured_piece = self.grid[tc][fr]
        else:
            captured_piece = self.grid[tc][tr]
        captured = captured_piece is not None
        if captured:
            self.captured.append((captured_piece.color, captured_piece.kind))

        if animate:
            anim = {
                'from_c': fc, 'from_r': fr,
                'to_c': tc, 'to_r': tr,
                'piece_color': piece.color,
                'piece_kind': piece.kind,
                'elapsed': 0.0,
                'duration': MOVE_ANIM_DURATION,
                'rook_anim': None,
            }
            if extra.get('castle'):
                rook_from_c = 7 if tc == 6 else 0
                rook_to_c = 5 if tc == 6 else 3
                anim['rook_anim'] = {
                    'from_c': rook_from_c, 'from_r': tr,
                    'to_c': rook_to_c, 'to_r': tr,
                }
            self.animation = anim
        else:
            self.animation = None

        new_ep = None
        if piece.kind == 'P' and extra.get('double_push'):
            new_ep = (fc, (fr + tr) // 2)
        if extra.get('en_passant'):
            self.grid[tc][fr] = None
        if extra.get('castle'):
            if tc == 6:
                rook = self.grid[7][tr]; self.grid[7][tr] = None
                self.grid[5][tr] = rook; rook.has_moved = True
            elif tc == 2:
                rook = self.grid[0][tr]; self.grid[0][tr] = None
                self.grid[3][tr] = rook; rook.has_moved = True
        self.grid[fc][fr] = None
        self.grid[tc][tr] = piece
        piece.has_moved = True
        if extra.get('promotion'):
            promoted = Piece(piece.color, 'Q')
            promoted.has_moved = True
            self.grid[tc][tr] = promoted

        self.last_move = (fc, fr, tc, tr)
        self.en_passant_target = new_ep
        self.turn = 'b' if self.turn == 'w' else 'w'

        has_move = any_legal_move(self.grid, self.turn, self.en_passant_target)
        is_check = in_check(self.grid, self.turn)
        repetition_count = self._record_position()
        insufficient = has_insufficient_material(self.grid)

        if not has_move:
            self.status = 'checkmate' if is_check else 'stalemate'
            self.game_over = True
            play_sound('end')
        elif insufficient:
            self.status = 'insufficient'
            self.game_over = True
            play_sound('end')
        elif repetition_count >= 3:
            self.status = 'repetition'
            self.game_over = True
            play_sound('end')
        else:
            self.status = 'check' if is_check else ''
            if is_check:
                play_sound('check')
            elif extra.get('promotion'):
                play_sound('promotion')
            elif extra.get('castle'):
                play_sound('castle')
            elif captured:
                play_sound('capture')
            else:
                play_sound('move')

        self.push_history()

    def trigger_ai(self):
        self.ai_thinking = True
        snap = copy_grid(self.grid)
        ep = self.en_passant_target
        color = self.turn
        gen = self.gen
        t = threading.Thread(target=self._ai_worker,
                             args=(snap, ep, color, gen), daemon=True)
        t.start()

    def _ai_worker(self, grid, ep, color, gen):
        depth = 0
        mv = None
        engine_name = ''
        if _stockfish_engine is not None:
            try:
                mv, depth = find_best_move_stockfish(grid, color, ep, AI_TIME_BUDGET_S)
                if mv is not None:
                    engine_name = 'Stockfish'
            except Exception:
                mv = None
        if mv is None:
            try:
                mv, depth = find_best_move(grid, color, ep, AI_MAX_DEPTH, AI_TIME_BUDGET_S)
                if mv is not None:
                    engine_name = 'Interno'
            except Exception:
                moves = all_legal_moves_with(grid, color, ep)
                mv = random.choice(moves) if moves else None
                depth = 0
                engine_name = 'Random' if mv else ''
        with self._ai_lock:
            self._ai_result = (mv, gen, depth, engine_name)

    def draw(self):
        if self.state == 'menu':
            self.draw_menu()
        else:
            self.draw_play()

    def draw_menu(self):
        createText(int(sper(0.06)), 'AJEDREZ', 'center',
                   (240, 240, 240), screenX/2, yper(0.16))
        createText(int(sper(0.020)), 'Elegí cómo jugar', 'center',
                   (180, 180, 180), screenX/2, yper(0.26))
        for btn in self.menu_buttons():
            rect, label = btn[1], btn[2]
            hovered = rect.collidepoint(mouseX, mouseY)
            bg = (95, 115, 95) if hovered else (55, 55, 65)
            border = (220, 220, 220) if hovered else (120, 120, 120)
            pygame.draw.rect(windowSurface, bg, rect, border_radius=10)
            pygame.draw.rect(windowSurface, border, rect, 2, border_radius=10)
            createText(int(sper(0.020)), label, 'center',
                       (240, 240, 240), rect.centerx, rect.centery)
        if _stockfish_engine is not None:
            engine_line = 'Motor: Stockfish  ·  ' + str(AI_TIME_BUDGET_S) + 's por jugada'
            engine_color = (140, 200, 140)
        else:
            engine_line = 'Motor: Interno (Stockfish no disponible)'
            engine_color = (200, 160, 100)
        createText(int(sper(0.014)), engine_line,
                   'center', engine_color, screenX/2, yper(0.90))
        createText(int(sper(0.014)), 'ESC = salir',
                   'center', (160, 160, 160), screenX/2, yper(0.94))

    def draw_captured(self, view_captured):
        """Render captured pieces in side panels: white pieces on the left,
        black pieces on the right. Adds a `+N` material-advantage label above
        the panel of the side that's ahead."""
        s = self.cell_size()
        ox, oy = self.board_origin()
        s_cap = sper(0.025)
        value_order = {'Q': 5, 'R': 4, 'B': 3, 'N': 2, 'P': 1, 'K': 0}
        white_lost = sorted([k for c, k in view_captured if c == 'w'],
                            key=lambda k: -value_order[k])
        black_lost = sorted([k for c, k in view_captured if c == 'b'],
                            key=lambda k: -value_order[k])
        panel_left_cx = ox - sper(0.050)
        panel_right_cx = ox + s*8 + sper(0.050)
        self._render_captured(white_lost, 'w', panel_left_cx, oy, s_cap)
        self._render_captured(black_lost, 'b', panel_right_cx, oy, s_cap)
        mat = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
        w_val = sum(mat[k] for k in black_lost)
        b_val = sum(mat[k] for k in white_lost)
        diff = w_val - b_val
        if diff > 0:
            createText(int(sper(0.020)), '+' + str(diff), 'center',
                       (220, 220, 100), panel_right_cx, oy - sper(0.020))
        elif diff < 0:
            createText(int(sper(0.020)), '+' + str(-diff), 'center',
                       (220, 220, 100), panel_left_cx, oy - sper(0.020))

    def _render_captured(self, kinds, color, cx, top_y, size):
        per_row = 2
        spacing_x = size * 0.95
        spacing_y = size * 0.85
        for i, kind in enumerate(kinds):
            row = i // per_row
            col = i % per_row
            px = cx + (col - 0.5) * spacing_x
            py = top_y + (row + 0.5) * spacing_y
            draw_piece(PIECE_CHARS[kind], size * 0.95, px, py, color)

    def draw_play(self):
        viewing = self.is_viewing_history()
        if viewing:
            snap = self.history[self.history_index]
            view_grid = snap['grid']
            view_turn = snap['turn']
            view_last_move = snap['last_move']
            view_status = snap['status']
            view_captured = snap.get('captured', [])
        else:
            view_grid = self.grid
            view_turn = self.turn
            view_last_move = self.last_move
            view_status = self.status
            view_captured = self.captured

        ox, oy = self.board_origin()
        s = self.cell_size()
        light = (240, 217, 181)
        dark = (181, 136, 99)

        border_color = (90, 70, 30) if viewing else (40, 28, 20)
        pygame.draw.rect(windowSurface, border_color,
                         (ox - sper(0.008), oy - sper(0.008),
                          s*8 + sper(0.016), s*8 + sper(0.016)))

        for sc in range(8):
            for sr in range(8):
                c = 7 - sc if self.flip else sc
                r = 7 - sr if self.flip else sr
                color = light if (c + r) % 2 == 0 else dark
                pygame.draw.rect(windowSurface, color,
                                 (ox + sc*s, oy + sr*s, s, s))

        if view_last_move:
            fc, fr, tc, tr = view_last_move
            overlay = pygame.Surface((s, s), pygame.SRCALPHA)
            overlay.fill((246, 246, 105, 110))
            x, y = self.cell_to_screen(fc, fr)
            windowSurface.blit(overlay, (x, y))
            x, y = self.cell_to_screen(tc, tr)
            windowSurface.blit(overlay, (x, y))

        if view_status in ('check', 'checkmate'):
            k = find_king(view_grid, view_turn)
            if k:
                overlay = pygame.Surface((s, s), pygame.SRCALPHA)
                overlay.fill((220, 50, 50, 170))
                x, y = self.cell_to_screen(k[0], k[1])
                windowSurface.blit(overlay, (x, y))

        if not viewing and self.selected:
            overlay = pygame.Surface((s, s), pygame.SRCALPHA)
            overlay.fill((90, 200, 90, 140))
            x, y = self.cell_to_screen(self.selected[0], self.selected[1])
            windowSurface.blit(overlay, (x, y))

        hover = self.square_at_pixel(mouseX, mouseY)
        if (hover and not viewing and not self.game_over and self.is_human_turn()
            and not self.ai_thinking):
            overlay = pygame.Surface((s, s), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 25))
            x, y = self.cell_to_screen(hover[0], hover[1])
            windowSurface.blit(overlay, (x, y))

        skip_cells = set()
        if not viewing and self.animation is not None:
            skip_cells.add((self.animation['to_c'], self.animation['to_r']))
            if self.animation['rook_anim']:
                ra = self.animation['rook_anim']
                skip_cells.add((ra['to_c'], ra['to_r']))

        piece_size = s * 0.82
        for c in range(8):
            for r in range(8):
                p = view_grid[c][r]
                if not p:
                    continue
                if not viewing:
                    if (c, r) in skip_cells:
                        continue
                    if self.dragging and self.drag_from == (c, r):
                        continue
                ch = PIECE_CHARS[p.kind]
                x, y = self.cell_to_screen(c, r)
                draw_piece(ch, piece_size, x + s/2, y + s/2, p.color)

        if not viewing and self.animation is not None:
            anim = self.animation
            t = min(1.0, anim['elapsed'] / anim['duration'])
            t_eased = 1 - (1 - t) ** 2
            fx, fy = self.cell_to_screen(anim['from_c'], anim['from_r'])
            tx, ty = self.cell_to_screen(anim['to_c'], anim['to_r'])
            cx_anim = fx + (tx - fx) * t_eased
            cy_anim = fy + (ty - fy) * t_eased
            ch = PIECE_CHARS[anim['piece_kind']]
            draw_piece(ch, piece_size, cx_anim + s/2, cy_anim + s/2,
                       anim['piece_color'])
            if anim['rook_anim']:
                ra = anim['rook_anim']
                rfx, rfy = self.cell_to_screen(ra['from_c'], ra['from_r'])
                rtx, rty = self.cell_to_screen(ra['to_c'], ra['to_r'])
                rcx = rfx + (rtx - rfx) * t_eased
                rcy = rfy + (rty - rfy) * t_eased
                draw_piece(PIECE_CHARS['R'], piece_size,
                           rcx + s/2, rcy + s/2, anim['piece_color'])

        if not viewing and self.animation is None:
            for tc, tr, extra in self.legal:
                x, y = self.cell_to_screen(tc, tr)
                cx, cy = x + s/2, y + s/2
                target = self.grid[tc][tr]
                if target is not None or extra.get('en_passant'):
                    pygame.draw.circle(windowSurface, (50, 180, 50),
                                       (int(cx), int(cy)), int(s*0.45),
                                       max(2, int(s*0.06)))
                else:
                    pygame.draw.circle(windowSurface, (50, 180, 50),
                                       (int(cx), int(cy)), int(s*0.13))

            if self.dragging and self.drag_from:
                p = self.grid[self.drag_from[0]][self.drag_from[1]]
                if p:
                    ch = PIECE_CHARS[p.kind]
                    draw_piece(ch, piece_size * 1.05, mouseX, mouseY, p.color)

        files_label = 'abcdefgh'
        label_size = int(sper(0.013))
        for i in range(8):
            file_c = 7 - i if self.flip else i
            rank_r = 7 - i if self.flip else i
            createText(label_size, files_label[file_c], 'center',
                       (210, 210, 210),
                       ox + i*s + s/2, oy + 8*s + sper(0.014))
            createText(label_size, str(8 - rank_r), 'center',
                       (210, 210, 210),
                       ox - sper(0.014), oy + i*s + s/2)

        self.draw_captured(view_captured)

        if viewing:
            idx = self.history_index
            if idx == 0:
                label = 'Posición inicial  ·  END = volver al presente'
            else:
                total_plies = len(self.history) - 1
                label = 'Viendo movida ' + str(idx) + ' de ' + str(total_plies) + '  ·  ←→ navegar  ·  END = al presente'
            createText(int(sper(0.020)), label, 'center',
                       (230, 220, 130), screenX/2, yper(0.04))
        elif view_status == 'checkmate':
            winner = 'Negras' if view_turn == 'w' else 'Blancas'
            createText(int(sper(0.030)), 'JAQUE MATE — Ganan ' + winner,
                       'center', (255, 90, 90), screenX/2, yper(0.04))
        elif view_status == 'stalemate':
            createText(int(sper(0.030)), 'AHOGADO — Tablas',
                       'center', (230, 220, 100), screenX/2, yper(0.04))
        elif view_status == 'repetition':
            createText(int(sper(0.030)), 'TABLAS POR REPETICIÓN',
                       'center', (230, 220, 100), screenX/2, yper(0.04))
        elif view_status == 'insufficient':
            createText(int(sper(0.030)), 'TABLAS POR FALTA DE MATERIAL',
                       'center', (230, 220, 100), screenX/2, yper(0.04))
        else:
            turn_txt = 'Turno: Blancas' if view_turn == 'w' else 'Turno: Negras'
            if self.ai_thinking:
                engine_hint = ' (' + (self.ai_engine_name or 'IA') + ')' if self.ai_engine_name else ''
                turn_txt += '   ·   Pensando' + engine_hint + '...'
                turn_color = (200, 200, 255)
            elif view_status == 'check':
                turn_txt += '   ·   JAQUE'
                turn_color = (255, 130, 130)
            else:
                turn_color = (235, 235, 235)
            createText(int(sper(0.022)), turn_txt, 'center',
                       turn_color, screenX/2, yper(0.04))

        if not viewing and not self.ai_thinking and self.ai_last_depth > 0 and not self.game_over:
            name = self.ai_engine_name or 'IA'
            createText(int(sper(0.013)),
                       'Última jugada de ' + name + ': profundidad ' + str(self.ai_last_depth),
                       'center', (140, 160, 180), screenX/2, yper(0.073))

        if self.ai_both:
            mode_txt = 'Modo: IA vs IA'
        elif self.ai_color is None:
            mode_txt = 'Modo: 2 Jugadores'
        else:
            who = 'Blancas' if self.human_color == 'w' else 'Negras'
            mode_txt = 'Modo: vs IA  ·  vos jugás ' + who
        createText(int(sper(0.014)), mode_txt, 'topright',
                   (180, 180, 180), screenX - xper(0.02), yper(0.02))

        if _stockfish_engine is not None:
            createText(int(sper(0.012)), 'Stockfish OK', 'topleft',
                       (140, 200, 140), xper(0.02), yper(0.02))
        else:
            createText(int(sper(0.012)), 'Stockfish no cargado', 'topleft',
                       (200, 160, 100), xper(0.02), yper(0.02))

        createText(int(sper(0.013)),
                   'Arrastrá o clic-clic  ·  ←→ historial  ·  HOME/END = inicio/final  ·  R = reiniciar  ·  N = menú  ·  ESC = salir',
                   'center', (180, 180, 180), screenX/2, yper(0.985))


class Manager(Sprite):

    def __init__(self):
        self.z = -10

    def process(self):
        if keys[pygame.K_ESCAPE]:
            shutdown()


def shutdown():
    """Clean exit: kill Stockfish (its non-daemon asyncio thread would otherwise
    keep the process alive after pygame closes), then exit."""
    close_stockfish()
    pygame.quit()
    sys.exit()


# ====================================================================
# HELPERS
# ====================================================================

def xper(p): return p * screenX
def yper(p): return p * screenY
def sper(p): return p * (screenX + screenY) / 2

def createText(size, content, alignment, color, posX, posY):
    rect = font.get_rect(content, size=size)
    setattr(rect, alignment, (posX, posY))
    font.render_to(windowSurface, rect, content, color, size=size)

def draw_piece(ch, size, cx, cy, color):
    size = int(size)
    if color == 'w':
        fill = (250, 250, 250); outline = (15, 15, 15)
    else:
        fill = (25, 25, 25); outline = (245, 245, 245)
    rect = piece_font.get_rect(ch, size=size)
    rect.center = (int(cx), int(cy))
    base_x, base_y = rect.x, rect.y
    off = max(1, int(size * 0.05))
    for dx, dy in ((-off, 0), (off, 0), (0, -off), (0, off),
                   (-off, -off), (off, -off), (-off, off), (off, off)):
        piece_font.render_to(windowSurface, (base_x + dx, base_y + dy),
                             ch, outline, size=size)
    piece_font.render_to(windowSurface, (base_x, base_y), ch, fill, size=size)

def addSprite(sprite):
    sprites.append(sprite)
    return sprite


# ====================================================================
# SOUND (sintetizado on init, sin assets)
# ====================================================================

def _make_buffer(samples_mono, volume):
    buf = array.array('h')
    amp = 32767 * volume
    for sm in samples_mono:
        v = int(max(-32767, min(32767, sm * amp)))
        buf.append(v)
        buf.append(v)
    return pygame.mixer.Sound(buffer=buf.tobytes())

def make_click(duration_ms, volume=0.4, freq=None):
    n = int(SAMPLE_RATE * duration_ms / 1000)
    samples = []
    decay = n * 0.18
    for i in range(n):
        env = math.exp(-i / decay)
        if freq:
            t = i / SAMPLE_RATE
            tone = math.sin(2 * math.pi * freq * t)
            noise = random.random() * 2 - 1
            samples.append((tone * 0.6 + noise * 0.4) * env)
        else:
            samples.append((random.random() * 2 - 1) * env)
    return _make_buffer(samples, volume)

def make_chord(freqs, duration_ms, volume=0.4):
    n = int(SAMPLE_RATE * duration_ms / 1000)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.sin(math.pi * i / n)
        val = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        samples.append(val * env)
    return _make_buffer(samples, volume)

def init_sounds():
    global sounds
    sounds = {}
    if not pygame.mixer.get_init():
        return
    try:
        sounds['move']      = make_click(60, 0.35, freq=420)
        sounds['capture']   = make_click(120, 0.5, freq=180)
        sounds['check']     = make_chord([880, 1100], 220, 0.30)
        sounds['castle']    = make_chord([300, 450], 180, 0.40)
        sounds['promotion'] = make_chord([600, 900, 1200], 280, 0.35)
        sounds['end']       = make_chord([220, 280, 350], 600, 0.50)
    except Exception:
        sounds = {}

def play_sound(name):
    s = sounds.get(name)
    if s:
        try:
            s.play()
        except Exception:
            pass


# ====================================================================
# INITIALIZATION
# ====================================================================

sounds = {}

try:
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
except pygame.error:
    pass
pygame.init()

screenX = 1280
screenY = 720
windowSurface = pygame.display.set_mode((screenX, screenY), depth=32, display=0)
pygame.display.set_caption('Chess')

font = pygame.freetype.SysFont('Segoe UI Semibold,Segoe UI,Calibri,Arial', 0)
piece_font = pygame.freetype.SysFont('Segoe UI Symbol,Arial Unicode MS,DejaVu Sans', 0)

init_sounds()
init_stockfish()

deltaT = 0
iniT = time.time()
clock = pygame.time.Clock()
keys = None
mouseX = mouseY = 0
mouseLeft = mouseRight = False
sprites = []

addSprite(Manager())
addSprite(Game())

# ====================================================================
# MAIN LOOP
# ====================================================================

while True:

    now = time.time()
    deltaT = min(now - iniT, 0.05)
    iniT = now
    clock.tick(60)

    keys = pygame.key.get_pressed()
    mouseX, mouseY = pygame.mouse.get_pos()
    mouseLeft, mouseMiddle, mouseRight = pygame.mouse.get_pressed()

    windowSurface.fill((25, 25, 30))

    sprites.sort(key=lambda x: x.z, reverse=True)

    for sprite in sprites:
        sprite.process()
        sprite.draw()

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == QUIT:
            shutdown()
