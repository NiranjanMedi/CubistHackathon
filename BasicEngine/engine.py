import random
from typing import Optional
from board import Board, Move

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

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


def _negamax(board: Board, depth: int, alpha: int, beta: int) -> int:
    """Negamax with alpha-beta. Score is from the current player's perspective."""
    if depth == 0:
        score = evaluate(board)
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
        score = -_negamax(nb, depth - 1, -beta, -alpha)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def evaluate_root_moves(board: Board, depth: int = 3):
    """Score every legal move with full-window negamax.
    Returns list of (move, white_signed_cp), sorted by side-to-move preference.
    Uses full (-INF, INF) window per root move so all scores are exact — needed
    by selectors that combine eval with other features."""
    moves = board.legal_moves()
    if not moves:
        return []

    results = []
    for m in _order_moves(board, moves):
        nb = board.copy()
        nb.make_move(m)
        our_score = -_negamax(nb, depth - 1, -INF, INF)
        white_signed = our_score if board.turn == 'w' else -our_score
        results.append((m, white_signed))

    sign = 1 if board.turn == 'w' else -1
    results.sort(key=lambda x: sign * x[1], reverse=True)
    return results


def best_move(board: Board, depth: int = 3) -> Optional[Move]:
    scored = evaluate_root_moves(board, depth)
    return scored[0][0] if scored else None


def random_move(board: Board) -> Optional[Move]:
    moves = board.legal_moves()
    if not moves:
        return None
    return random.choice(moves)
