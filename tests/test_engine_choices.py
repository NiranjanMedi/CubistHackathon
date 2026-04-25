"""Engine move-choice sanity tests (no scoring, just pass/fail)."""
import unittest
from BasicEngine.engine import best_move
from BasicEngine.board import Board
from tests.helpers import pos, uci


class TestEngineChoices(unittest.TestCase):

    def test_captures_hanging_queen(self):
        b = pos({'h1': 'wK', 'a1': 'wR', 'a6': 'bQ', 'a8': 'bK'})
        self.assertEqual(uci(best_move(b, 3)), 'a1a6')

    def test_checkmate_in_one(self):
        # Qb7# – bK on a8 has no escape; wK on c6 defends b7 so bK can't capture Q
        b = pos({'c6': 'wK', 'b6': 'wQ', 'a8': 'bK'})
        self.assertEqual(uci(best_move(b, 3)), 'b6b7')

    def test_takes_free_rook(self):
        # wQ on d1 takes undefended bR on h5 (diagonal path, no king-capture ambiguity)
        b = pos({'e1': 'wK', 'd1': 'wQ', 'h5': 'bR', 'a8': 'bK'})
        self.assertEqual(uci(best_move(b, 3)), 'd1h5')

    def test_promotes_pawn_to_queen(self):
        b = pos({'e1': 'wK', 'a7': 'wP', 'h8': 'bK'})
        self.assertEqual(uci(best_move(b, 3)), 'a7a8q')

    def test_returns_legal_move_under_check(self):
        # bQ checks wK on e-file; engine must return a legal move, not crash
        b = pos({'e1': 'wK', 'e8': 'bQ', 'a8': 'bK'})
        m = best_move(b, 2)
        self.assertIsNotNone(m)
        self.assertIn(m, b.legal_moves())

    def test_recaptures_rook(self):
        b = pos({'h1': 'wK', 'd1': 'wR', 'd5': 'bR', 'a8': 'bK'})
        self.assertEqual(uci(best_move(b, 3)), 'd1d5')

    def test_knight_takes_free_bishop(self):
        b = pos({'h1': 'wK', 'd4': 'wN', 'f5': 'bB', 'a8': 'bK'})
        self.assertEqual(uci(best_move(b, 3)), 'd4f5')

    def test_king_takes_adjacent_queen(self):
        b = pos({'e1': 'wK', 'd2': 'bQ', 'h8': 'bK'})
        self.assertEqual(uci(best_move(b, 2)), 'e1d2')

    def test_knight_takes_hanging_queen(self):
        b = pos({'e1': 'wK', 'c3': 'wN', 'd5': 'bQ', 'a8': 'bK'})
        self.assertEqual(uci(best_move(b, 3)), 'c3d5')

    def test_knight_smothered_mate(self):
        # Nf7# – bK on h8 smothered by g7/g8/h7; wN on e5 jumps (-2,+1) to f7.
        # bP on g7 captures only f6/h6, never f7, so the knight can't be taken.
        b = pos({'a1': 'wK', 'e5': 'wN', 'h8': 'bK', 'g8': 'bR', 'g7': 'bP', 'h7': 'bP'})
        self.assertEqual(uci(best_move(b, 3)), 'e5f7')

    def test_best_move_from_start_is_legal(self):
        b = Board()
        m = best_move(b, 3)
        self.assertIn(m, b.legal_moves())

    def test_no_move_returned_when_game_over(self):
        # Stalemate: bK in corner, no moves
        b = pos({'a8': 'bK', 'b6': 'wQ', 'c7': 'wK'}, turn='b')
        if not b.legal_moves():
            self.assertIsNone(best_move(b))


if __name__ == '__main__':
    unittest.main(verbosity=2)
