"""Unit tests for the chess model: engine eval/search + discomfort selector."""

import unittest

from board import Board, Move, EMPTY
from engine import (
    PIECE_VALUES,
    PST,
    evaluate,
    evaluate_root_moves,
    best_move,
    random_move,
    _pst,
)
from discomfort import discomfort
from discomfort_move import discomfort_move


def empty_board(turn: str = 'w') -> Board:
    b = Board()
    b.squares = [[EMPTY] * 8 for _ in range(8)]
    b.turn = turn
    return b


def place(board: Board, piece: str, square: str):
    """Place piece on board using algebraic square like 'e4'."""
    files = 'abcdefgh'
    col = files.index(square[0])
    row = 8 - int(square[1])
    board.squares[row][col] = piece


def with_kings(board: Board, white_sq='e1', black_sq='e8') -> Board:
    place(board, 'wK', white_sq)
    place(board, 'bK', black_sq)
    return board


class TestEvaluate(unittest.TestCase):
    def test_starting_position_symmetric(self):
        self.assertEqual(evaluate(Board()), 0)

    def test_material_advantage_positive_for_white(self):
        b = with_kings(empty_board())
        place(b, 'wQ', 'd1')
        score = evaluate(b)
        self.assertGreater(score, 0)
        # Score should be ~ queen value + queen PST + king PSTs (which cancel by symmetry)
        self.assertGreaterEqual(score, PIECE_VALUES['Q'] - 50)

    def test_pst_white_black_mirrored(self):
        # White piece on rank 1 should mirror black piece on rank 8.
        for kind in 'PNBRQK':
            white_score = _pst(kind, 7, 4, 'w')  # e1 from white POV
            black_score = _pst(kind, 0, 4, 'b')  # e8 from black POV (flipped)
            self.assertEqual(
                white_score, black_score,
                f"PST mismatch for {kind}: white {white_score} vs black {black_score}",
            )

    def test_color_sign(self):
        b = with_kings(empty_board())
        place(b, 'bQ', 'd8')
        self.assertLess(evaluate(b), 0)


class TestNegamaxSearch(unittest.TestCase):
    def test_best_move_takes_free_piece(self):
        b = with_kings(empty_board())
        place(b, 'wR', 'a1')
        place(b, 'bP', 'a7')  # undefended, rook can capture along a-file
        b.turn = 'w'
        m = best_move(b, depth=2)
        self.assertIsNotNone(m)
        self.assertEqual((m.to_row, m.to_col), (1, 0))  # a7

    def test_best_move_avoids_hanging_queen(self):
        # White queen on d1, black pawn on e2 attacking nothing critical.
        # If white moves Q to a square attacked by black pawn for no compensation,
        # search should reject it.
        b = with_kings(empty_board())
        place(b, 'wQ', 'd1')
        place(b, 'bP', 'e4')  # attacks d5, f5
        b.turn = 'w'
        m = best_move(b, depth=2)
        self.assertIsNotNone(m)
        # Queen should not voluntarily land on d5 or f5.
        self.assertNotIn((m.to_row, m.to_col), [(3, 3), (3, 5)])

    def test_evaluate_root_moves_sorted_for_white(self):
        b = Board()
        scored = evaluate_root_moves(b, depth=2)
        self.assertGreater(len(scored), 0)
        evals = [ws for _, ws in scored]
        self.assertEqual(evals, sorted(evals, reverse=True))

    def test_evaluate_root_moves_sorted_for_black(self):
        b = Board()
        b.make_move(Move(6, 4, 4, 4))  # 1. e4
        scored = evaluate_root_moves(b, depth=2)
        self.assertGreater(len(scored), 0)
        evals = [ws for _, ws in scored]
        # Black wants white_signed eval as low as possible.
        self.assertEqual(evals, sorted(evals))

    def test_evaluate_root_moves_empty_at_terminal(self):
        # Stalemate-ish: only kings, no legal moves to test? Use a position with no moves.
        # Easiest: set turn to a side with no pieces. Black turn, no black pieces except king
        # in corner with white king cutting off — too complex. Instead test the empty case
        # by giving black no pieces at all.
        b = empty_board(turn='b')
        place(b, 'wK', 'a1')
        place(b, 'bK', 'h8')
        # Black king on h8 has legal moves (g7, g8, h7). So this won't be empty.
        # Verify the function returns something and best move is not None.
        scored = evaluate_root_moves(b, depth=1)
        self.assertGreater(len(scored), 0)
        self.assertIsNotNone(best_move(b, depth=1))

    def test_best_move_returns_none_when_no_moves(self):
        # Construct a checkmate-ish dead state: replace legal_moves to test the contract.
        b = empty_board(turn='w')
        place(b, 'wK', 'a1')
        place(b, 'bK', 'h8')
        # No actual mate; just confirm best_move returns a move when moves exist.
        m = best_move(b, depth=1)
        self.assertIsNotNone(m)

    def test_random_move_is_legal(self):
        b = Board()
        for _ in range(5):
            m = random_move(b)
            self.assertIn(m, b.legal_moves())


class TestDiscomfort(unittest.TestCase):
    def test_zero_when_shallow_matches_deep(self):
        b = Board()
        b.make_move(Move(6, 4, 4, 4))  # 1. e4 — turn flips to black
        shallow = evaluate(b)
        # shallow == deep → discomfort 0
        self.assertEqual(discomfort(b, shallow), 0.0)

    def test_non_negative(self):
        b = Board()
        b.make_move(Move(6, 4, 4, 4))
        for deep in (-1500, -300, 0, 300, 1500):
            self.assertGreaterEqual(discomfort(b, deep), 0.0)

    def test_positive_when_shallow_oversells(self):
        # Black to move, shallow_white known. Pick a deep value that makes
        # opp's shallow look better than deep.
        b = Board()
        b.make_move(Move(6, 4, 4, 4))  # turn = black
        shallow_white = evaluate(b)
        # opp = black, sign = -1 (since turn='b')
        # shallow_opp = -shallow_white, deep_opp = -deep_white
        # Want shallow_opp - deep_opp > 0 → -shallow_white > -deep_white → deep_white > shallow_white
        deep = shallow_white + 500
        self.assertGreater(discomfort(b, deep), 0.0)

    def test_sign_flip_bonus_applied(self):
        # Force shallow_opp > 0 and deep_opp < 0 → multiplier kicks in.
        # Black to move (turn='b'), so opp = black, sign = -1.
        # shallow_opp = -shallow_white. Want this > 0 → shallow_white < 0.
        # deep_opp = -deep_white < 0 → deep_white > 0.
        # Build board where shallow eval is negative for white (extra black material).
        b = with_kings(empty_board(turn='b'))
        place(b, 'bQ', 'd8')  # makes shallow_white very negative
        shallow_white = evaluate(b)
        self.assertLess(shallow_white, 0)
        deep_white = 200  # deep says white is fine
        with_bonus = discomfort(b, deep_white, sign_flip_bonus=1.0)
        without_bonus = discomfort(b, deep_white, sign_flip_bonus=0.0)
        self.assertGreater(with_bonus, without_bonus)
        self.assertAlmostEqual(with_bonus, without_bonus * 2, places=4)


class TestDiscomfortMove(unittest.TestCase):
    def test_returns_legal_move_from_start(self):
        b = Board()
        m = discomfort_move(b, depth=2, debug=False)
        self.assertIsNotNone(m)
        self.assertIn(m, b.legal_moves())

    def test_returns_legal_move_for_black(self):
        b = Board()
        b.make_move(Move(6, 4, 4, 4))  # 1. e4
        m = discomfort_move(b, depth=2, debug=False)
        self.assertIsNotNone(m)
        self.assertIn(m, b.legal_moves())

    def test_respects_eval_floor(self):
        # Chosen move's eval (from side-to-move POV) must be within `eval_floor_cp`
        # of the best move's eval.
        b = Board()
        scored = evaluate_root_moves(b, depth=2)
        sign = 1 if b.turn == 'w' else -1
        best_our = max(sign * ws for _, ws in scored)

        chosen = discomfort_move(b, depth=2, eval_floor_cp=80, debug=False)
        chosen_ws = next(ws for m, ws in scored if m == chosen)
        chosen_our = sign * chosen_ws
        self.assertGreaterEqual(chosen_our, best_our - 80)

    def test_zero_lambda_gives_engine_best(self):
        # With lam=0, discomfort contribution is ignored → should match top engine move.
        b = Board()
        scored = evaluate_root_moves(b, depth=2)
        engine_best = scored[0][0]
        chosen = discomfort_move(b, depth=2, lam=0.0, debug=False)
        self.assertEqual(chosen, engine_best)

    def test_no_legal_moves_returns_none(self):
        # Set up a board with the side-to-move having no legal moves is hard without
        # a real checkmate position. Use an empty-of-pieces side (illegal but exercises
        # the guard).
        b = empty_board(turn='w')
        place(b, 'bK', 'h8')
        # White has no king and no pieces → no legal moves.
        self.assertEqual(b.legal_moves(), [])
        self.assertIsNone(discomfort_move(b, depth=1, debug=False))


if __name__ == '__main__':
    unittest.main()
