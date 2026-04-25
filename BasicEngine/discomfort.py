from board import Board
from engine import evaluate


def discomfort(post_move_board: Board, deep_white_signed: int,
               sign_flip_bonus: float = 1.0) -> float:
    """How much the side-to-move's intuitive (shallow) read oversells reality.

    Both inputs are interpreted in white-perspective centipawns.
    Returns a non-negative score in centipawn units.
    """
    shallow_white = evaluate(post_move_board)
    sign = 1 if post_move_board.turn == 'w' else -1
    shallow_opp = sign * shallow_white
    deep_opp = sign * deep_white_signed

    raw = max(0, shallow_opp - deep_opp)
    if shallow_opp > 0 and deep_opp < 0:
        raw *= (1 + sign_flip_bonus)
    return raw
