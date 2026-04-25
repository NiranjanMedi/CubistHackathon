"""
UCI bridge utilities: parse UCI move strings and reconstruct board from move history.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from board import Board, Move

_FILES = 'abcdefgh'
_RANKS = '87654321'


def parse_uci(uci: str) -> Move:
    """Parse a UCI move string (e.g. 'e2e4', 'e7e8q') into a Move object."""
    from_col = _FILES.index(uci[0])
    from_row = _RANKS.index(uci[1])
    to_col   = _FILES.index(uci[2])
    to_row   = _RANKS.index(uci[3])
    promotion = uci[4].upper() if len(uci) > 4 else None
    return Move(from_row, from_col, to_row, to_col, promotion)


def board_from_moves(uci_moves: list) -> Board:
    """Reconstruct board state by replaying UCI moves from the start position."""
    board = Board()
    for uci in uci_moves:
        if uci:
            board.make_move(parse_uci(uci))
    return board
