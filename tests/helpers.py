"""Shared test helpers."""
from BasicEngine.board import Board, EMPTY


def pos(pieces: dict, turn: str = 'w') -> Board:
    """Build a Board from a square→piece dict, e.g. {'e1':'wK', 'e8':'bK'}.

    Coordinates: file a-h, rank 1-8. Both kings must be present.
    """
    b = Board.__new__(Board)
    b.squares = [[EMPTY] * 8 for _ in range(8)]
    b.turn = turn
    for sq, piece in pieces.items():
        col = ord(sq[0]) - ord('a')
        row = 8 - int(sq[1])
        b.squares[row][col] = piece
    return b


def uci(m) -> str:
    """Return the UCI string for a Move (or None)."""
    return repr(m) if m is not None else None
