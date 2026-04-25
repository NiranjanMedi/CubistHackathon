import random
from board import Board, Move


def random_move(board: Board):
    moves = board.legal_moves()
    if not moves:
        return None
    return random.choice(moves)
