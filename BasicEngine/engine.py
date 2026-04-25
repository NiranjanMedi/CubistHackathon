import json
import os
import random
import time
from .board import Board, Move

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# ── Tunable evaluation weights ────────────────────────────────────────────────

WEIGHTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "weights.json")

_DEFAULT_WEIGHTS = {
    "passed_pawn":    1.0,  # scales passed-pawn rank bonus
    "pawn_structure": 1.0,  # scales doubled/isolated penalties
    "bishop_pair":    1.0,  # scales bishop pair bonus
    "rook_open_file": 1.0,  # scales rook on open/semi-open file
    "king_safety":    1.0,  # blends mg/eg king PST (>1 = more safety-focused)
    "niche_bias":     1.0,  # scales niche-move bonuses at root selection
}


def load_weights() -> dict:
    try:
        with open(WEIGHTS_FILE) as f:
            w = json.load(f)
        return {k: w.get(k, 1.0) for k in _DEFAULT_WEIGHTS}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_DEFAULT_WEIGHTS)


def save_weights(w: dict):
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(w, f, indent=2)


def get_weights() -> dict:
    return dict(_W)


def set_weights(w: dict):
    global _W
    _W = {k: max(0.1, min(3.0, float(w.get(k, 1.0)))) for k in _DEFAULT_WEIGHTS}
    save_weights(_W)


_W = load_weights()

# Niche-but-sound opening book. Each entry maps a move history tuple to a list
# of acceptable replies; one is chosen randomly. All listed moves are
# theoretically respectable but rarely seen below master level — the goal is
# to take humans out of memorized theory while never playing a bad move.
OPENING_BOOK: dict[tuple, list[str]] = {
    # === FIRST MOVES (white) — pick from a sound but varied repertoire ===
    (): [
        'b2b3',   # Nimzo-Larsen Attack
        'g1f3',   # Réti / King's Indian Attack starter
        'f2f4',   # Bird's Opening
        'd2d4',   # Queen's Pawn (mainline branches into Trompowsky/London/Veresov)
        'e2e4',   # King's Pawn (branches into Vienna/Closed Sicilian)
        'c2c4',   # English Opening
    ],

    # === NIMZO-LARSEN (1.b3) ===
    ('b2b3',):                                       ['e7e5', 'g8f6', 'd7d5'],
    ('b2b3', 'e7e5'):                                ['c1b2'],
    ('b2b3', 'e7e5', 'c1b2'):                        ['b8c6', 'd7d6', 'g8f6'],
    ('b2b3', 'e7e5', 'c1b2', 'b8c6'):                ['e2e3', 'g1f3'],
    ('b2b3', 'd7d5'):                                ['c1b2'],
    ('b2b3', 'd7d5', 'c1b2'):                        ['g8f6', 'e7e6'],
    ('b2b3', 'g8f6'):                                ['c1b2'],
    ('b2b3', 'g8f6', 'c1b2'):                        ['g7g6', 'e7e6', 'd7d5'],

    # === BIRD'S OPENING (1.f4) ===
    ('f2f4',):                                       ['d7d5', 'g8f6', 'e7e5', 'c7c5'],
    ('f2f4', 'd7d5'):                                ['g1f3'],
    ('f2f4', 'd7d5', 'g1f3'):                        ['g8f6', 'c8g4', 'g7g6'],
    ('f2f4', 'g8f6'):                                ['g1f3'],
    ('f2f4', 'e7e5'):                                ['f4e5'],   # accepts From's Gambit safely
    ('f2f4', 'e7e5', 'f4e5'):                        ['d7d6'],

    # === RÉTI / KIA (1.Nf3) ===
    ('g1f3',):                                       ['d7d5', 'g8f6', 'c7c5', 'e7e6'],
    ('g1f3', 'd7d5'):                                ['c2c4', 'g2g3'],
    ('g1f3', 'd7d5', 'c2c4'):                        ['d5c4', 'e7e6', 'c7c6'],
    ('g1f3', 'd7d5', 'g2g3'):                        ['g8f6', 'c7c5'],
    ('g1f3', 'g8f6'):                                ['g2g3', 'c2c4'],
    ('g1f3', 'g8f6', 'g2g3'):                        ['g7g6', 'd7d5'],
    ('g1f3', 'c7c5'):                                ['g2g3', 'c2c4'],
    ('g1f3', 'e7e6'):                                ['g2g3', 'd2d4'],

    # === TROMPOWSKY / VERESOV / LONDON (1.d4) ===
    ('d2d4',):                                       ['g8f6', 'd7d5', 'e7e6', 'f7f5', 'c7c5'],
    ('d2d4', 'g8f6'):                                ['c1g5', 'g1f3', 'b1c3'],   # Trompowsky / London / Veresov
    ('d2d4', 'g8f6', 'c1g5'):                        ['e7e6', 'd7d5', 'c7c5', 'g7g6'],
    ('d2d4', 'g8f6', 'c1g5', 'e7e6'):                ['e2e4'],
    ('d2d4', 'g8f6', 'c1g5', 'd7d5'):                ['e2e3', 'g5f6'],
    ('d2d4', 'd7d5'):                                ['b1c3', 'g1f3'],          # Veresov / London
    ('d2d4', 'd7d5', 'b1c3'):                        ['g8f6', 'e7e6', 'c8f5'],
    ('d2d4', 'd7d5', 'b1c3', 'g8f6'):                ['c1g5'],                  # Veresov
    ('d2d4', 'd7d5', 'b1c3', 'g8f6', 'c1g5'):        ['e7e6', 'c7c6', 'b8d7'],
    ('d2d4', 'd7d5', 'g1f3'):                        ['g8f6', 'e7e6', 'c7c6'],
    ('d2d4', 'd7d5', 'g1f3', 'g8f6'):                ['c1f4'],                  # London System
    ('d2d4', 'd7d5', 'g1f3', 'g8f6', 'c1f4'):        ['e7e6', 'c7c5', 'c8f5'],
    ('d2d4', 'e7e6'):                                ['c2c4', 'g1f3'],
    ('d2d4', 'f7f5'):                                ['g1f3', 'c2c4', 'c1g5'],   # Trompowsky-vs-Dutch
    ('d2d4', 'c7c5'):                                ['d4d5'],                   # Benoni-style

    # === VIENNA GAME / CLOSED SICILIAN (1.e4) ===
    ('e2e4',):                                       ['e7e5', 'c7c5', 'e7e6', 'c7c6', 'd7d5'],
    ('e2e4', 'e7e5'):                                ['b1c3'],                  # Vienna Game
    ('e2e4', 'e7e5', 'b1c3'):                        ['g8f6', 'b8c6', 'f8c5'],
    ('e2e4', 'e7e5', 'b1c3', 'g8f6'):                ['f2f4'],                  # Vienna Gambit
    ('e2e4', 'e7e5', 'b1c3', 'g8f6', 'f2f4'):        ['d7d5', 'e5f4'],
    ('e2e4', 'e7e5', 'b1c3', 'b8c6'):                ['g2g3', 'f1c4'],
    ('e2e4', 'c7c5'):                                ['b1c3'],                  # Closed Sicilian
    ('e2e4', 'c7c5', 'b1c3'):                        ['b8c6', 'd7d6', 'g8f6'],
    ('e2e4', 'c7c5', 'b1c3', 'b8c6'):                ['g2g3'],
    ('e2e4', 'c7c5', 'b1c3', 'b8c6', 'g2g3'):        ['g7g6', 'g8f6'],
    ('e2e4', 'e7e6'):                                ['d2d4'],                  # French
    ('e2e4', 'e7e6', 'd2d4'):                        ['d7d5'],
    ('e2e4', 'e7e6', 'd2d4', 'd7d5'):                ['b1c3', 'b1d2', 'e4e5'],
    ('e2e4', 'c7c6'):                                ['b1c3'],                  # Caro-Kann sideline
    ('e2e4', 'c7c6', 'b1c3'):                        ['d7d5', 'g8f6'],
    ('e2e4', 'd7d5'):                                ['e4d5'],                  # Scandinavian

    # === ENGLISH OPENING (1.c4) ===
    ('c2c4',):                                       ['e7e5', 'g8f6', 'c7c5', 'e7e6'],
    ('c2c4', 'e7e5'):                                ['b1c3'],
    ('c2c4', 'e7e5', 'b1c3'):                        ['g8f6', 'b8c6'],
    ('c2c4', 'g8f6'):                                ['b1c3', 'g1f3'],
    ('c2c4', 'c7c5'):                                ['g1f3', 'b1c3'],
    ('c2c4', 'e7e6'):                                ['g1f3', 'b1c3'],
}

# Piece-square tables (white perspective; row 0 = rank 8, row 7 = rank 1).
PST = {
    'P': [
        [ 0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [ 5,  5, 10, 25, 25, 10,  5,  5],
        [ 0,  0,  0, 20, 20,  0,  0,  0],
        [ 5, -5,-10,  0,  0,-10, -5,  5],
        [ 5, 10, 10,-20,-20, 10, 10,  5],
        [ 0,  0,  0,  0,  0,  0,  0,  0],
    ],
    'N': [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50],
    ],
    'B': [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ],
    'R': [
        [ 0,  0,  0,  0,  0,  0,  0,  0],
        [ 5, 10, 10, 10, 10, 10, 10,  5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [ 0,  0,  0,  5,  5,  0,  0,  0],
    ],
    'Q': [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [ -5,  0,  5,  5,  5,  5,  0, -5],
        [  0,  0,  5,  5,  5,  5,  0, -5],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20],
    ],
    # Middlegame king — stay safe behind pawns
    'K': [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [ 20, 20,  0,  0,  0,  0, 20, 20],
        [ 20, 30, 10,  0,  0, 10, 30, 20],
    ],
    # Endgame king — centralize
    'K_end': [
        [-50,-40,-30,-20,-20,-30,-40,-50],
        [-30,-20,-10,  0,  0,-10,-20,-30],
        [-30,-10, 20, 30, 30, 20,-10,-30],
        [-30,-10, 30, 40, 40, 30,-10,-30],
        [-30,-10, 30, 40, 40, 30,-10,-30],
        [-30,-10, 20, 30, 30, 20,-10,-30],
        [-30,-30,  0,  0,  0,  0,-30,-30],
        [-50,-30,-30,-30,-30,-30,-30,-50],
    ],
}

INF = 10 ** 9
_MATE = 100000
_MAX_DEPTH = 12

# ── Zobrist hashing ────────────────────────────────────────────────────────────

_PIECES = ['wP','wN','wB','wR','wQ','wK','bP','bN','bB','bR','bQ','bK']
_rng = random.Random(0xDEADBEEF)
_ZOBRIST: dict[tuple, int] = {
    (p, r, c): _rng.getrandbits(64)
    for p in _PIECES for r in range(8) for c in range(8)
}
_ZOBRIST_TURN = _rng.getrandbits(64)   # XOR when it's black's turn


def board_hash(board: Board) -> int:
    h = 0
    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p != '..':
                h ^= _ZOBRIST[(p, r, c)]
    if board.turn == 'b':
        h ^= _ZOBRIST_TURN
    return h


# ── Transposition table ────────────────────────────────────────────────────────

_TT_EXACT = 0
_TT_LOWER = 1   # alpha (failed low — upper bound)
_TT_UPPER = 2   # beta  (failed high — lower bound)
_TT: dict[int, tuple] = {}   # hash → (depth, score, flag, best_move)
_TT_MAX = 1 << 20            # ~1M entries


def _tt_store(h, depth, score, flag, best_m):
    if len(_TT) >= _TT_MAX:
        _TT.clear()
    _TT[h] = (depth, score, flag, best_m)


# ── Evaluation ────────────────────────────────────────────────────────────────

_MG_MATERIAL = PIECE_VALUES['Q'] * 2 + PIECE_VALUES['R'] * 4 + PIECE_VALUES['B'] * 4 + PIECE_VALUES['N'] * 4


def _game_phase(board: Board) -> float:
    """0.0 = full endgame, 1.0 = full middlegame."""
    mat = 0
    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p != '..' and p[1] != 'P' and p[1] != 'K':
                mat += PIECE_VALUES.get(p[1], 0)
    return min(1.0, mat / _MG_MATERIAL)


def _pst(kind, r, c, color, phase=1.0):
    if kind == 'K':
        ks = _W["king_safety"]
        mg = PST['K'][r][c] if color == 'w' else PST['K'][7 - r][c]
        eg = PST['K_end'][r][c] if color == 'w' else PST['K_end'][7 - r][c]
        blended_phase = min(1.0, phase * ks)
        return int(blended_phase * mg + (1 - blended_phase) * eg)
    table = PST.get(kind)
    if table is None:
        return 0
    return table[r][c] if color == 'w' else table[7 - r][c]


def evaluate(board: Board) -> int:
    """Static evaluation: positive = good for white, negative = good for black."""
    phase = _game_phase(board)
    score = 0

    w_pawns_on_file = [0] * 8
    b_pawns_on_file = [0] * 8
    w_bishops = b_bishops = 0

    # Collect pawn/bishop counts
    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p == '..':
                continue
            if p == 'wP':
                w_pawns_on_file[c] += 1
            elif p == 'bP':
                b_pawns_on_file[c] += 1
            elif p == 'wB':
                w_bishops += 1
            elif p == 'bB':
                b_bishops += 1

    # Bishop pair bonus
    bp_bonus = int(30 * _W["bishop_pair"])
    if w_bishops >= 2:
        score += bp_bonus
    if b_bishops >= 2:
        score -= bp_bonus

    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p == '..':
                continue
            color, kind = p[0], p[1]
            val = PIECE_VALUES.get(kind, 0) + _pst(kind, r, c, color, phase)

            # Pawn structure
            if kind == 'P':
                ps = _W["pawn_structure"]
                pp = _W["passed_pawn"]
                if color == 'w':
                    if w_pawns_on_file[c] > 1:
                        val -= int(20 * ps)
                    neighbors = (w_pawns_on_file[c - 1] if c > 0 else 0) + \
                                (w_pawns_on_file[c + 1] if c < 7 else 0)
                    if neighbors == 0:
                        val -= int(15 * ps)
                    passed = True
                    for pr in range(r - 1, -1, -1):
                        for pc in range(max(0, c - 1), min(8, c + 2)):
                            if board.squares[pr][pc] == 'bP':
                                passed = False
                                break
                        if not passed:
                            break
                    if passed:
                        rank_bonus = [0, 10, 20, 35, 55, 80, 110, 0]
                        val += int(rank_bonus[7 - r] * pp)
                else:
                    if b_pawns_on_file[c] > 1:
                        val -= int(20 * ps)
                    neighbors = (b_pawns_on_file[c - 1] if c > 0 else 0) + \
                                (b_pawns_on_file[c + 1] if c < 7 else 0)
                    if neighbors == 0:
                        val -= int(15 * ps)
                    passed = True
                    for pr in range(r + 1, 8):
                        for pc in range(max(0, c - 1), min(8, c + 2)):
                            if board.squares[pr][pc] == 'wP':
                                passed = False
                                break
                        if not passed:
                            break
                    if passed:
                        rank_bonus = [0, 10, 20, 35, 55, 80, 110, 0]
                        val += int(rank_bonus[r] * pp)

            # Rook on open/semi-open file
            elif kind == 'R':
                rof = _W["rook_open_file"]
                if color == 'w':
                    if w_pawns_on_file[c] == 0:
                        val += int((15 if b_pawns_on_file[c] == 0 else 10) * rof)
                else:
                    if b_pawns_on_file[c] == 0:
                        val += int((15 if w_pawns_on_file[c] == 0 else 10) * rof)

            score += val if color == 'w' else -val

    return score


# ── Move ordering ─────────────────────────────────────────────────────────────

def _order_moves(board: Board, moves, killers=None, history=None, tt_move=None):
    """Score moves: TT move > captures (MVV-LVA) > killers > history > quiet."""
    tt_key = tt_move and (tt_move.from_row, tt_move.from_col,
                          tt_move.to_row, tt_move.to_col, tt_move.promotion)

    def key(m):
        mk = (m.from_row, m.from_col, m.to_row, m.to_col, m.promotion)
        if mk == tt_key:
            return -10_000_000
        target = board.squares[m.to_row][m.to_col]
        if target != '..':
            victim = PIECE_VALUES.get(target[1], 0)
            attacker = PIECE_VALUES.get(board.squares[m.from_row][m.from_col][1], 0)
            return -(victim * 10 - attacker + 1_000_000)
        if killers:
            for i, k in enumerate(killers):
                if k and k.from_row == m.from_row and k.from_col == m.from_col \
                       and k.to_row == m.to_row and k.to_col == m.to_col:
                    return -(500_000 - i * 10)
        if history:
            return -(history[m.from_row * 8 + m.from_col][m.to_row * 8 + m.to_col])
        return 0

    return sorted(moves, key=key)


# ── Quiescence search ─────────────────────────────────────────────────────────

def _quiesce(board: Board, alpha: int, beta: int, depth: int = 4) -> int:
    stand_pat = evaluate(board) if board.turn == 'w' else -evaluate(board)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat
    if depth == 0:
        return alpha

    captures = [m for m in board.legal_moves()
                if board.squares[m.to_row][m.to_col] != '..']
    for m in _order_moves(board, captures):
        nb = board.copy()
        nb.make_move(m)
        score = -_quiesce(nb, -beta, -alpha, depth - 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


# ── Main search ───────────────────────────────────────────────────────────────

def _negamax(board: Board, depth: int, alpha: int, beta: int,
             killers, history, null_ok: bool = True) -> int:
    orig_alpha = alpha
    h = board_hash(board)

    # Transposition table lookup
    tt = _TT.get(h)
    tt_move = None
    if tt and tt[0] >= depth:
        tt_depth, tt_score, tt_flag, tt_move = tt
        if tt_flag == _TT_EXACT:
            return tt_score
        if tt_flag == _TT_UPPER and tt_score >= beta:
            return beta
        if tt_flag == _TT_LOWER and tt_score <= alpha:
            return alpha
    elif tt:
        tt_move = tt[3]

    if depth == 0:
        return _quiesce(board, alpha, beta)

    moves = board.legal_moves()
    if not moves:
        kr, kc = board.find_king(board.turn)
        opp = 'b' if board.turn == 'w' else 'w'
        if board.is_attacked(kr, kc, opp):
            return -_MATE + depth
        return 0

    # Null move pruning (skip in endgames to avoid zugzwang)
    if null_ok and depth >= 3:
        phase = _game_phase(board)
        if phase > 0.2:
            kr, kc = board.find_king(board.turn)
            opp = 'b' if board.turn == 'w' else 'w'
            if not board.is_attacked(kr, kc, opp):
                nb = board.copy()
                nb.turn = opp
                null_score = -_negamax(nb, depth - 3, -beta, -beta + 1,
                                       killers, history, null_ok=False)
                if null_score >= beta:
                    return beta

    best_m = None
    first = True
    for m in _order_moves(board, moves, killers[depth] if depth < len(killers) else None,
                          history, tt_move):
        nb = board.copy()
        nb.make_move(m)

        # PVS: full window for first move, zero-window for rest
        if first:
            score = -_negamax(nb, depth - 1, -beta, -alpha, killers, history)
            first = False
        else:
            score = -_negamax(nb, depth - 1, -alpha - 1, -alpha, killers, history)
            if alpha < score < beta:
                score = -_negamax(nb, depth - 1, -beta, -score, killers, history)

        if score >= beta:
            # Killer move update (quiet moves only)
            if board.squares[m.to_row][m.to_col] == '..':
                if depth < len(killers):
                    killers[depth] = [m, killers[depth][0]]
                history[m.from_row * 8 + m.from_col][m.to_row * 8 + m.to_col] += depth * depth
            _tt_store(h, depth, beta, _TT_UPPER, m)
            return beta

        if score > alpha:
            alpha = score
            best_m = m

    flag = _TT_EXACT if alpha > orig_alpha else _TT_LOWER
    _tt_store(h, depth, alpha, flag, best_m)
    return alpha


# ── Niche-move bias ───────────────────────────────────────────────────────────

def _count_developed(board: Board) -> int:
    """Rough opening-phase proxy: count minor pieces off their starting squares."""
    c = 0
    starts = [('wN', 7, 1), ('wN', 7, 6), ('wB', 7, 2), ('wB', 7, 5),
              ('bN', 0, 1), ('bN', 0, 6), ('bB', 0, 2), ('bB', 0, 5)]
    for piece, r, col in starts:
        if board.squares[r][col] != piece:
            c += 1
    return c


def _niche_bonus(board: Board, m: Move) -> int:
    """
    Small bonus (0–15cp) for moves humans rarely play.
    Used ONLY at root tie-breaking — never affects search evaluation.
    """
    bonus = 0
    p = board.squares[m.from_row][m.from_col]
    if p == '..':
        return 0
    color, kind = p[0], p[1]
    developed = _count_developed(board)
    in_opening = developed < 6

    # Knight to rim — rare but sometimes the right call
    if kind == 'N' and m.to_col in (0, 7):
        bonus += 6

    # Flank pawn pushes in the opening
    if kind == 'P' and m.to_col in (0, 1, 6, 7) and in_opening:
        bonus += 5

    # Bishop fianchetto (b2/g2 for white, b7/g7 for black)
    if kind == 'B':
        if color == 'w' and m.to_row == 6 and m.to_col in (1, 6):
            bonus += 4
        if color == 'b' and m.to_row == 1 and m.to_col in (1, 6):
            bonus += 4

    # h-pawn / a-pawn 1-square push in opening (Grob/anti-systems)
    if kind == 'P' and m.to_col in (0, 7) and in_opening:
        if abs(m.to_row - m.from_row) == 1:
            bonus += 3

    return int(bonus * _W["niche_bias"])


# ── Root search with iterative deepening ─────────────────────────────────────

def best_move(board: Board, depth: int = None, history: list = None,
              time_limit_ms: int = 800, diversity_cp: int = 0,
              niche_bias: bool = False) -> Move:
    """
    Find the best move via iterative deepening.

    diversity_cp: if > 0, pick from moves scored within this many centipawns
                  of the best. Hard quality floor — never picks a worse move.
    niche_bias:   if True, weight the random choice within the diversity window
                  toward less-mainstream moves (knight rim, fianchetto, flank
                  pawns). Tied to the `niche_bias` weight in weights.json.
    """
    # Opening book — list of moves, pick one randomly
    if history is not None:
        book = OPENING_BOOK.get(tuple(history))
        if book:
            legal_ucis = {_move_to_uci_key(m): m for m in board.legal_moves()}
            valid = [legal_ucis[u] for u in book if u in legal_ucis]
            if valid:
                return random.choice(valid)

    moves = board.legal_moves()
    if not moves:
        return None

    _TT.clear()
    killers = [[None, None] for _ in range(_MAX_DEPTH + 1)]
    hist = [[0] * 64 for _ in range(64)]

    best_m = _order_moves(board, moves)[0]   # fallback
    deadline = time.monotonic() + time_limit_ms / 1000.0
    max_depth = depth if depth is not None else _MAX_DEPTH

    for d in range(1, max_depth + 1):
        if time.monotonic() >= deadline:
            break

        scored = []   # (score, move) for every root move this iteration
        alpha = -INF

        for m in _order_moves(board, moves, history=hist):
            nb = board.copy()
            nb.make_move(m)
            score = -_negamax(nb, d - 1, -INF, -alpha, killers, hist)
            scored.append((score, m))
            if score > alpha:
                alpha = score

        if not scored:
            break

        best_score = max(s for s, _ in scored)
        best_m = max(scored, key=lambda x: x[0])[1]

        # Diversity + niche-aware selection. Hard floor: must be within
        # diversity_cp of best (no bad moves). Niche bonus only breaks ties.
        if diversity_cp > 0:
            candidates = [(s, m) for s, m in scored if best_score - s <= diversity_cp]
            if niche_bias:
                weights = [1.0 + 0.3 * _niche_bonus(board, m) for _, m in candidates]
                best_m = random.choices([m for _, m in candidates], weights=weights, k=1)[0]
            else:
                best_m = random.choice([m for _, m in candidates])

        if time.monotonic() >= deadline:
            break

    return best_m


# Niche opening book for the human-like agent — unusual but not unsound lines
_HUMAN_BOOK: dict[tuple, list] = {
    (): ['d2d4', 'c2c4', 'b1c3', 'g1f3', 'e2e3'],
    ('e2e4',): ['c7c5', 'd7d6', 'g8f6', 'b8c6', 'e7e6', 'c7c6'],
    ('d2d4',): ['g8f6', 'e7e6', 'c7c5', 'd7d5', 'b7b6', 'f7f5'],
    ('c2c4',): ['e7e5', 'c7c5', 'g8f6', 'b7b6'],
    ('e2e4', 'c7c5'): ['g1f3', 'b1c3', 'c2c3', 'f2f4'],
    ('e2e4', 'e7e6'): ['d2d4', 'g1f3', 'b1c3'],
    ('d2d4', 'g8f6'): ['c2c4', 'g1f3', 'b1c3', 'f2f3'],
    ('d2d4', 'f7f5'): ['g1f3', 'c2c4', 'b1c3', 'e2e3'],
}


def _human_score(board: Board, m: Move, color: str) -> int:
    """Heuristic bonuses that mimic human preferences: develop, castle, control center."""
    bonus = 0
    piece = board.squares[m.from_row][m.from_col]
    kind = piece[1] if piece != '..' else ''
    target = board.squares[m.to_row][m.to_col]

    # Reward captures (but not obsessively)
    if target != '..':
        bonus += PIECE_VALUES.get(target[1], 0) // 4

    # Reward developing minor pieces early (toward center)
    if kind in ('N', 'B'):
        center_bonus = (3 - abs(m.to_col - 3.5)) + (3 - abs(m.to_row - 3.5))
        bonus += int(center_bonus * 8)

    # Reward center pawn pushes
    if kind == 'P' and m.to_col in (3, 4):
        bonus += 15

    # Reward castling (king moving 2 squares)
    if kind == 'K' and abs(m.to_col - m.from_col) == 2:
        bonus += 40

    # Slightly penalise moving the same piece twice early (rough approximation)
    if kind in ('N', 'B') and m.from_row in (0, 1, 6, 7):
        bonus -= 5

    # Occasionally prefer unusual/quiet moves (niche feel)
    if target == '..' and kind not in ('P', 'K'):
        bonus += random.randint(0, 12)

    return bonus


def human_like_move(board: Board, history: list = None) -> Move:
    """
    Plays like a human: uses a shallow search (depth 2) for tactical awareness,
    adds human-style heuristic bonuses, picks randomly among near-best moves,
    and follows a niche opening book. Goal is varied, plausible, non-robotic play.
    """
    # Niche opening book
    if history is not None:
        key = tuple(history)
        options = _HUMAN_BOOK.get(key)
        if options:
            legal_ucis = {_move_to_uci_key(m): m for m in board.legal_moves()}
            valid = [legal_ucis[u] for u in options if u in legal_ucis]
            if valid:
                return random.choice(valid)

    moves = board.legal_moves()
    if not moves:
        return None

    color = board.turn
    scored = []
    for m in moves:
        nb = board.copy()
        nb.make_move(m)
        # Shallow search for tactical awareness (depth 1 = sees immediate captures)
        search_score = -_quiesce(nb, -INF, INF, depth=2)
        human_bonus = _human_score(board, m, color)
        scored.append((search_score + human_bonus, m))

    best_score = max(s for s, _ in scored)
    # Pick randomly among moves within 60cp of best — wide window for human variety
    candidates = [m for s, m in scored if best_score - s <= 60]
    return random.choice(candidates)


def _move_to_uci_key(m: Move) -> str:
    files = 'abcdefgh'
    ranks = '87654321'
    s = files[m.from_col] + ranks[m.from_row] + files[m.to_col] + ranks[m.to_row]
    if m.promotion:
        s += m.promotion.lower()
    return s


def random_move(board: Board) -> Move:
    moves = board.legal_moves()
    if not moves:
        return None
    return random.choice(moves)
