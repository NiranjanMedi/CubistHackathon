import random
from .board import Board, Move

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Unusual opening book keyed by move history tuple → UCI reply.
# Lines chosen to be unfamiliar to casual players.
OPENING_BOOK: dict[tuple, str] = {
    # Grob's Attack (White): 1.g4
    (): 'g2g4',
    # After 1.g4 d5: 2.h3 (Grob sideline)
    ('g2g4', 'd7d5'): 'h2h3',
    ('g2g4', 'e7e5'): 'h2h3',
    ('g2g4', 'c7c5'): 'h2h3',
    # After 1.g4 d5 2.h3 e5: 3.Bg2
    ('g2g4', 'd7d5', 'h2h3', 'e7e5'): 'f1g2',
    ('g2g4', 'e7e5', 'h2h3', 'd7d5'): 'f1g2',
    # Black Owen's Defense replies to 1.e4 and 1.d4
    ('e2e4',): 'b7b6',
    ('d2d4',): 'f7f5',
    ('c2c4',): 'b7b6',
    ('b2b4',): 'e7e5',
    # After 1.e4 b6: 2...Bb7 when white plays d4
    ('e2e4', 'b7b6', 'd2d4'): 'c8b7',
    # After 1.d4 f5: Dutch-ish 2...Nf6
    ('d2d4', 'f7f5', 'c2c4'): 'g8f6',
    ('d2d4', 'f7f5', 'g1f3'): 'g8f6',
    # Nimzo-Larsen (White): 1.b3
    # (alternate line if White has not moved yet — covered by () above as g4)
}

# Piece-square tables from white's perspective (row 0 = rank 8, row 7 = rank 1).
# For black, flip vertically: use table[7 - r][c].
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
}

INF = 10 ** 9


def _pst(kind, r, c, color):
    table = PST.get(kind)
    if table is None:
        return 0
    return table[r][c] if color == 'w' else table[7 - r][c]


def evaluate(board: Board) -> int:
    """Static evaluation: positive = good for white, negative = good for black."""
    score = 0
    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p == '..':
                continue
            color, kind = p[0], p[1]
            val = PIECE_VALUES.get(kind, 0) + _pst(kind, r, c, color)
            score += val if color == 'w' else -val
    return score


def _order_moves(board: Board, moves):
    """Put captures first, ordered by MVV-LVA (high-value victim, low-value attacker)."""
    def key(m):
        target = board.squares[m.to_row][m.to_col]
        if target == '..':
            return 0
        return -(PIECE_VALUES.get(target[1], 0) * 10
                 - PIECE_VALUES.get(board.squares[m.from_row][m.from_col][1], 0))
    return sorted(moves, key=key)


def _negamax(board: Board, depth: int, alpha: int, beta: int, noise: int = 0) -> int:
    """Negamax with alpha-beta. Score is from the current player's perspective."""
    if depth == 0:
        score = evaluate(board)
        if noise:
            score += random.randint(-noise, noise)
        return score if board.turn == 'w' else -score

    moves = board.legal_moves()
    if not moves:
        kr, kc = board.find_king(board.turn)
        opp = 'b' if board.turn == 'w' else 'w'
        if board.is_attacked(kr, kc, opp):
            return -100000 + depth  # checkmate — prefer shorter path to it
        return 0  # stalemate

    for m in _order_moves(board, moves):
        nb = board.copy()
        nb.make_move(m)
        score = -_negamax(nb, depth - 1, -beta, -alpha, noise)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def best_move(board: Board, depth: int = 3, history: list = None, noise: int = 0) -> Move:
    # Check opening book first
    if history is not None:
        book_uci = OPENING_BOOK.get(tuple(history))
        if book_uci:
            legal_ucis = {_move_to_uci_key(m): m for m in board.legal_moves()}
            if book_uci in legal_ucis:
                return legal_ucis[book_uci]

    moves = board.legal_moves()
    if not moves:
        return None

    best_score = -INF
    best_m = None
    alpha = -INF

    for m in _order_moves(board, moves):
        nb = board.copy()
        nb.make_move(m)
        score = -_negamax(nb, depth - 1, -INF, -alpha, noise)
        if score > best_score:
            best_score = score
            best_m = m
        if score > alpha:
            alpha = score

    return best_m


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
