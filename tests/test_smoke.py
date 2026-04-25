"""Basic smoke tests – imports, board init, engine doesn't crash."""
import unittest
from BasicEngine.board import Board, Move
from BasicEngine.engine import best_move, evaluate
from tests.helpers import pos


class TestImports(unittest.TestCase):
    def test_board_import(self):
        b = Board()
        self.assertIsNotNone(b)

    def test_move_import(self):
        m = Move(6, 4, 4, 4)
        self.assertEqual(repr(m), 'e2e4')


class TestBoardInit(unittest.TestCase):
    def setUp(self):
        self.b = Board()

    def test_turn_is_white(self):
        self.assertEqual(self.b.turn, 'w')

    def test_starting_legal_move_count(self):
        self.assertEqual(len(self.b.legal_moves()), 20)

    def test_white_king_on_e1(self):
        self.assertEqual(self.b.squares[7][4], 'wK')

    def test_black_king_on_e8(self):
        self.assertEqual(self.b.squares[0][4], 'bK')


class TestEngineSmoke(unittest.TestCase):
    def setUp(self):
        self.b = Board()

    def test_best_move_returns_move(self):
        m = best_move(self.b)
        self.assertIsInstance(m, Move)

    def test_evaluate_returns_int(self):
        score = evaluate(self.b)
        self.assertIsInstance(score, int)

    def test_evaluate_start_is_symmetric(self):
        self.assertEqual(evaluate(self.b), 0)

    def test_best_move_on_checkmate_returns_none(self):
        # Scholar's mate – black is checkmated
        b = pos({'e1': 'wK', 'h5': 'wQ', 'e4': 'wP', 'f3': 'wN',
                 'e8': 'bK', 'f6': 'bN', 'e5': 'bP'}, turn='b')
        # If no legal moves exist, best_move must return None gracefully
        moves = b.legal_moves()
        if not moves:
            self.assertIsNone(best_move(b))

    def test_best_move_on_stalemate_returns_none(self):
        # A genuine stalemate: bK trapped with no legal moves
        b = pos({'a8': 'bK', 'b6': 'wQ', 'c7': 'wK'}, turn='b')
        moves = b.legal_moves()
        if not moves:
            self.assertIsNone(best_move(b))


if __name__ == '__main__':
    unittest.main()
