import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from BasicEngine.board import Board, Move, EMPTY, starting_squares, piece_moves, pawn_moves


class TestBoardInit:
    def test_starting_turn_is_white(self):
        b = Board()
        assert b.turn == 'w'

    def test_castling_all_available(self):
        b = Board()
        assert all(b.castling.values())

    def test_en_passant_none_at_start(self):
        b = Board()
        assert b.en_passant is None

    def test_starting_pieces(self):
        b = Board()
        assert b.squares[0][0] == 'bR'
        assert b.squares[7][4] == 'wK'
        assert b.squares[0][4] == 'bK'
        assert b.squares[1][0] == 'bP'
        assert b.squares[6][0] == 'wP'


class TestBoardCopy:
    def test_copy_is_independent(self):
        b = Board()
        c = b.copy()
        c.squares[0][0] = EMPTY
        assert b.squares[0][0] == 'bR'

    def test_copy_preserves_turn(self):
        b = Board()
        b.turn = 'b'
        c = b.copy()
        assert c.turn == 'b'

    def test_copy_preserves_castling(self):
        b = Board()
        b.castling['wK'] = False
        c = b.copy()
        assert c.castling['wK'] is False
        c.castling['wQ'] = False
        assert b.castling['wQ'] is True  # original unaffected


class TestInBounds:
    def test_corners_in_bounds(self):
        b = Board()
        assert b.in_bounds(0, 0)
        assert b.in_bounds(7, 7)

    def test_out_of_bounds(self):
        b = Board()
        assert not b.in_bounds(-1, 0)
        assert not b.in_bounds(8, 0)
        assert not b.in_bounds(0, 8)
        assert not b.in_bounds(0, -1)


class TestFindKing:
    def test_find_white_king(self):
        b = Board()
        assert b.find_king('w') == (7, 4)

    def test_find_black_king(self):
        b = Board()
        assert b.find_king('b') == (0, 4)

    def test_no_king_raises(self):
        b = Board()
        b.squares[7][4] = EMPTY
        with pytest.raises(ValueError):
            b.find_king('w')


class TestMakeMove:
    def test_pawn_single_push(self):
        b = Board()
        m = Move(6, 4, 5, 4)
        b.make_move(m)
        assert b.squares[5][4] == 'wP'
        assert b.squares[6][4] == EMPTY
        assert b.turn == 'b'

    def test_double_pawn_push_sets_en_passant(self):
        b = Board()
        m = Move(6, 4, 4, 4)
        b.make_move(m)
        assert b.en_passant == (5, 4)

    def test_single_push_clears_en_passant(self):
        b = Board()
        b.make_move(Move(6, 4, 4, 4))  # sets en_passant
        b.make_move(Move(1, 0, 2, 0))  # black pawn single push
        b.make_move(Move(6, 0, 5, 0))  # white single push
        assert b.en_passant is None

    def test_turn_alternates(self):
        b = Board()
        assert b.turn == 'w'
        b.make_move(Move(6, 4, 5, 4))
        assert b.turn == 'b'
        b.make_move(Move(1, 4, 2, 4))
        assert b.turn == 'w'

    def test_promotion(self):
        b = Board()
        # Place a white pawn on row 1 ready to promote
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[7][4] = 'wK'
        b.squares[0][4] = 'bK'
        b.squares[1][0] = 'wP'
        b.turn = 'w'
        m = Move(1, 0, 0, 0, promotion='Q')
        b.make_move(m)
        assert b.squares[0][0] == 'wQ'
        assert b.squares[1][0] == EMPTY

    def test_kingside_castling_moves_rook(self):
        b = Board()
        # Clear squares between king and kingside rook
        b.squares[7][5] = EMPTY
        b.squares[7][6] = EMPTY
        b.castling['wK'] = True
        m = Move(7, 4, 7, 6)
        b.make_move(m)
        assert b.squares[7][6] == 'wK'
        assert b.squares[7][5] == 'wR'
        assert b.squares[7][7] == EMPTY

    def test_queenside_castling_moves_rook(self):
        b = Board()
        b.squares[7][1] = EMPTY
        b.squares[7][2] = EMPTY
        b.squares[7][3] = EMPTY
        b.castling['wQ'] = True
        m = Move(7, 4, 7, 2)
        b.make_move(m)
        assert b.squares[7][2] == 'wK'
        assert b.squares[7][3] == 'wR'
        assert b.squares[7][0] == EMPTY

    def test_king_move_removes_castling_rights(self):
        b = Board()
        b.squares[7][5] = EMPTY
        b.squares[7][6] = EMPTY
        b.make_move(Move(7, 4, 7, 5))
        assert b.castling['wK'] is False
        assert b.castling['wQ'] is False

    def test_en_passant_capture(self):
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[7][4] = 'wK'
        b.squares[0][4] = 'bK'
        b.squares[3][4] = 'wP'
        b.squares[3][5] = 'bP'
        b.en_passant = (2, 5)
        b.turn = 'w'
        m = Move(3, 4, 2, 5)
        b.make_move(m)
        assert b.squares[2][5] == 'wP'
        assert b.squares[3][5] == EMPTY  # captured pawn removed


class TestLegalMoves:
    def test_starting_position_has_20_moves(self):
        b = Board()
        assert len(b.legal_moves()) == 20

    def test_no_moves_after_stalemate_setup(self):
        # Minimal stalemate: black king in corner, no legal moves
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[0][0] = 'bK'
        b.squares[2][1] = 'wQ'
        b.squares[1][2] = 'wK'
        b.castling = {'wK': False, 'wQ': False, 'bK': False, 'bQ': False}
        b.en_passant = None
        b.turn = 'b'
        assert b.legal_moves() == []

    def test_king_cannot_move_into_check(self):
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[7][4] = 'wK'
        b.squares[0][4] = 'bK'
        b.squares[5][3] = 'bR'  # controls d-file
        b.turn = 'w'
        legal_cols = {m.to_col for m in b.legal_moves()}
        assert 3 not in legal_cols  # king can't move to column d (attacked by rook)


class TestIsAttacked:
    def test_pawn_attacks_diagonally(self):
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[4][4] = 'wP'
        assert b.is_attacked(3, 3, 'w')
        assert b.is_attacked(3, 5, 'w')
        assert not b.is_attacked(3, 4, 'w')

    def test_rook_attacks_along_rank(self):
        b = Board()
        b.squares = [[EMPTY] * 8 for _ in range(8)]
        b.squares[4][0] = 'bR'
        assert b.is_attacked(4, 7, 'b')
        assert not b.is_attacked(5, 7, 'b')
