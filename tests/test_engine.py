import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from BasicEngine.board import Board, Move, EMPTY
from BasicEngine.engine import evaluate, best_move, _pst, _order_moves, _move_to_uci_key, PIECE_VALUES, random_move


class TestEvaluate:
    def test_starting_position_is_balanced(self):
        b = Board()
        assert evaluate(b) == 0

    def test_removing_black_queen_favors_white(self):
        b = Board()
        b.squares[0][3] = EMPTY  # remove black queen
        assert evaluate(b) > 0

    def test_removing_white_queen_favors_black(self):
        b = Board()
        b.squares[7][3] = EMPTY  # remove white queen
        assert evaluate(b) < 0

    def test_empty_board_except_kings_is_zero(self):
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[7][4] = 'wK'
        b.squares[0][4] = 'bK'
        # Kings have equal PST value when mirrored; score should be 0
        assert evaluate(b) == 0


class TestPst:
    def test_pst_known_value(self):
        # White pawn at starting square (row 6, col 0) should use PST[6][0]
        val = _pst('P', 6, 0, 'w')
        assert val == 5  # from PST['P'][6][0]

    def test_pst_black_mirrors_white(self):
        # Black piece at row 6 should use PST[7-6][col] = PST[1][col]
        val_w = _pst('P', 1, 0, 'w')
        val_b = _pst('P', 6, 0, 'b')
        assert val_w == val_b

    def test_unknown_piece_returns_zero(self):
        assert _pst('X', 4, 4, 'w') == 0


class TestOrderMoves:
    def test_captures_come_before_quiet_moves(self):
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[7][4] = 'wK'
        b.squares[0][4] = 'bK'
        b.squares[4][4] = 'wR'
        b.squares[4][0] = 'bP'   # capturable pawn
        b.castling = {'wK': False, 'wQ': False, 'bK': False, 'bQ': False}
        b.en_passant = None
        b.turn = 'w'
        moves = b.legal_moves()
        ordered = _order_moves(b, moves)
        # The first move should be a capture (target square is not empty)
        first = ordered[0]
        assert b.squares[first.to_row][first.to_col] != EMPTY


class TestMoveToUciKey:
    def test_e2e4(self):
        m = Move(6, 4, 4, 4)  # e2e4
        assert _move_to_uci_key(m) == 'e2e4'

    def test_promotion_lowercase(self):
        m = Move(1, 0, 0, 0, promotion='Q')
        key = _move_to_uci_key(m)
        assert key == 'a7a8q'


class TestBestMove:
    def test_returns_a_move_from_start(self):
        b = Board()
        m = best_move(b, depth=1)
        assert m is not None
        assert isinstance(m, Move)

    def test_returns_none_when_no_moves(self):
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[0][0] = 'bK'
        b.squares[2][1] = 'wQ'
        b.squares[1][2] = 'wK'
        b.castling = {'wK': False, 'wQ': False, 'bK': False, 'bQ': False}
        b.en_passant = None
        b.turn = 'b'
        assert best_move(b, depth=1) is None

    def test_captures_hanging_queen(self):
        # White rook can capture undefended black queen; engine should pick a capture
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[7][4] = 'wK'
        b.squares[7][0] = 'bK'  # black king far away, not on same rank as rook
        b.squares[4][4] = 'wR'
        b.squares[4][0] = 'bQ'  # hanging black queen on same rank
        b.castling = {'wK': False, 'wQ': False, 'bK': False, 'bQ': False}
        b.en_passant = None
        b.turn = 'w'
        m = best_move(b, depth=1)
        assert m is not None
        assert (m.to_row, m.to_col) == (4, 0)  # rook captures queen

    def test_opening_book_hit(self):
        b = Board()
        history = []
        # First move should be g2g4 per opening book
        m = best_move(b, depth=1, history=history)
        assert _move_to_uci_key(m) == 'g2g4'

    def test_opening_book_miss_falls_back(self):
        b = Board()
        history = ['e2e4']  # not in book as white's 2nd move context
        b.make_move(Move(6, 4, 4, 4))  # play e2e4
        b.turn = 'b'
        # No book entry; engine should still return some move
        m = best_move(b, depth=1, history=history)
        assert m is not None


class TestRandomMove:
    def test_returns_legal_move(self):
        b = Board()
        m = random_move(b)
        assert m in b.legal_moves()

    def test_returns_none_when_no_moves(self):
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[0][0] = 'bK'
        b.squares[2][1] = 'wQ'
        b.squares[1][2] = 'wK'
        b.castling = {'wK': False, 'wQ': False, 'bK': False, 'bQ': False}
        b.en_passant = None
        b.turn = 'b'
        assert random_move(b) is None
