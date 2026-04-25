"""Tests for legal-move generation correctness."""
import unittest
from BasicEngine.board import Board, Move
from tests.helpers import pos


def uci_set(moves):
    return {repr(m) for m in moves}


class TestPawnMoves(unittest.TestCase):
    def test_pawn_single_step(self):
        b = Board()
        moves = uci_set(b.legal_moves())
        self.assertIn('e2e3', moves)

    def test_pawn_double_step_from_start(self):
        b = Board()
        moves = uci_set(b.legal_moves())
        self.assertIn('e2e4', moves)

    def test_pawn_blocked_cannot_advance(self):
        # White pawn on e4, black pawn on e5 — neither can advance
        b = pos({'e1': 'wK', 'e4': 'wP', 'e5': 'bP', 'e8': 'bK'})
        moves = uci_set(b.legal_moves())
        self.assertNotIn('e4e5', moves)

    def test_pawn_capture_diagonal(self):
        # White pawn on e4, black pawn on d5
        b = pos({'e1': 'wK', 'e4': 'wP', 'd5': 'bP', 'e8': 'bK'})
        moves = uci_set(b.legal_moves())
        self.assertIn('e4d5', moves)

    def test_pawn_cannot_capture_same_color(self):
        b = pos({'e1': 'wK', 'e4': 'wP', 'd5': 'wN', 'e8': 'bK'})
        moves = uci_set(b.legal_moves())
        self.assertNotIn('e4d5', moves)

    def test_pawn_promotion_generates_queen(self):
        # White pawn one step from promotion
        b = pos({'e1': 'wK', 'a7': 'wP', 'h8': 'bK'})
        moves = uci_set(b.legal_moves())
        self.assertIn('a7a8q', moves)

    def test_black_pawn_double_step(self):
        b = Board()
        b.turn = 'b'
        moves = uci_set(b.legal_moves())
        self.assertIn('e7e5', moves)


class TestCheckLegality(unittest.TestCase):
    def test_move_into_check_is_illegal(self):
        # wK on e1, bR on a2 controls rank 2 — wK cannot step to e2
        b = pos({'e1': 'wK', 'a2': 'bR', 'a8': 'bK'})
        moves = uci_set(b.legal_moves())
        self.assertNotIn('e1e2', moves)

    def test_must_escape_check(self):
        # bQ on e8 checks wK on e1 — white must move
        b = pos({'e1': 'wK', 'e8': 'bQ', 'a8': 'bK'})
        moves = b.legal_moves()
        self.assertGreater(len(moves), 0)
        for m in moves:
            after = b.copy()
            after.make_move(m)
            kr, kc = after.find_king('w')
            self.assertFalse(after.is_attacked(kr, kc, 'b'), f"{repr(m)} leaves king in check")

    def test_pinned_piece_cannot_expose_king(self):
        # wK on e1, wR on e4 (pinned), bQ on e8 — wR cannot leave the e-file
        b = pos({'e1': 'wK', 'e4': 'wR', 'e8': 'bQ', 'a8': 'bK'})
        moves = uci_set(b.legal_moves())
        # Moving wR horizontally (e.g. e4d4) would expose wK to bQ
        self.assertNotIn('e4d4', moves)
        self.assertNotIn('e4f4', moves)


class TestKnightMoves(unittest.TestCase):
    def test_knight_l_shape(self):
        b = Board()
        moves = uci_set(b.legal_moves())
        self.assertIn('g1f3', moves)
        self.assertIn('b1c3', moves)

    def test_knight_cannot_move_straight(self):
        b = Board()
        moves = uci_set(b.legal_moves())
        self.assertNotIn('b1b3', moves)


if __name__ == '__main__':
    unittest.main()
