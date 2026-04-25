import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ENGINE_DIR = Path(__file__).resolve().parents[1] / "BasicEngine"
sys.path.insert(0, str(ENGINE_DIR))
for module_name in (
    "board",
    "engine",
    "pressure_detector",
    "rare_move_selector",
    "pressure_novelty_engine",
):
    sys.modules.pop(module_name, None)

from board import Board, Move, EMPTY
from pressure_detector import analyze_pressure_point
from pressure_novelty_engine import PressureNoveltyEngine
from rare_move_selector import select_rare_move


def parse_uci(uci: str) -> Move:
    files = "abcdefgh"
    ranks = "87654321"
    return Move(
        ranks.index(uci[1]),
        files.index(uci[0]),
        ranks.index(uci[3]),
        files.index(uci[2]),
        uci[4:].upper() or None,
    )


def empty_board(pieces: dict[str, str], turn: str = "w") -> Board:
    board = Board.__new__(Board)
    board.squares = [[EMPTY] * 8 for _ in range(8)]
    board.turn = turn
    for square, piece in pieces.items():
        col = ord(square[0]) - ord("a")
        row = 8 - int(square[1])
        board.squares[row][col] = piece
    return board


class TestPressureNoveltyEnginePolicy(unittest.TestCase):
    def test_returns_base_move_when_position_is_not_critical(self):
        board = Board()
        engine = PressureNoveltyEngine()

        decision = engine.choose_move(board, move_count=0)

        self.assertEqual(decision.mode, "base")
        self.assertEqual(decision.move, decision.base_move)
        self.assertFalse(decision.critical_report.is_critical)

    def test_calls_selector_only_after_critical_trigger(self):
        board = Board()
        base = parse_uci("g1f3")
        novel = parse_uci("b1c3")

        with patch("pressure_novelty_engine.score_legal_moves", return_value={base: 30, novel: 20}), \
                patch("pressure_novelty_engine.analyze_pressure_point") as analyze, \
                patch("pressure_novelty_engine.select_rare_move") as selector:
            analyze.return_value.is_critical = True
            analyze.return_value.score = 0.8
            analyze.return_value.reasons = ["test critical"]
            selector.return_value = (novel, None, [])

            decision = PressureNoveltyEngine().choose_move(board, move_count=10)

        selector.assert_called_once()
        self.assertEqual(decision.mode, "fallback")
        self.assertEqual(decision.move, base)

    def test_returns_legal_move_on_real_position(self):
        board = Board()
        for uci in ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6"]:
            board.make_move(parse_uci(uci))

        decision = PressureNoveltyEngine().choose_move(board, move_count=3)

        self.assertIn(decision.move, board.legal_moves())
        self.assertIn(decision.mode, {"base", "novelty", "fallback"})


class TestBasicEngineBoardRules(unittest.TestCase):
    def test_castling_is_generated_and_applied(self):
        board = Board()
        for uci in ["e2e4", "e7e5", "g1f3", "b8c6", "f1e2", "g8f6"]:
            board.make_move(parse_uci(uci))

        self.assertIn("e1g1", {str(move) for move in board.legal_moves()})
        board.make_move(parse_uci("e1g1"))

        self.assertEqual(board.squares[7][6], "wK")
        self.assertEqual(board.squares[7][5], "wR")
        self.assertEqual(board.squares[7][7], "..")

    def test_en_passant_is_generated_and_applied(self):
        board = Board()
        for uci in ["e2e4", "a7a6", "e4e5", "d7d5"]:
            board.make_move(parse_uci(uci))

        self.assertIn("e5d6", {str(move) for move in board.legal_moves()})
        board.make_move(parse_uci("e5d6"))

        self.assertEqual(board.squares[2][3], "wP")
        self.assertEqual(board.squares[3][3], "..")


class TestPressureCriticality(unittest.TestCase):
    def test_starting_position_is_suppressed_as_opening(self):
        report = analyze_pressure_point(Board(), move_count=0)

        self.assertFalse(report.is_critical)
        self.assertTrue(any("opening" in reason for reason in report.reasons))

    def test_tactical_position_has_pressure_features(self):
        board = empty_board({
            "g1": "wK",
            "d1": "wQ",
            "e4": "wN",
            "g8": "bK",
            "d8": "bQ",
            "e5": "bR",
        })

        report = analyze_pressure_point(board, move_count=12, threshold=0.1)

        self.assertTrue(report.score > 0)
        self.assertGreaterEqual(report.features["capture_count"], 1)
        self.assertTrue(report.is_critical)


class TestRareMoveSelector(unittest.TestCase):
    def test_rejects_moves_outside_cp_loss_band(self):
        board = Board()
        best = parse_uci("g1f3")
        ok = parse_uci("b1c3")
        bad = parse_uci("a2a4")

        selected, _features, all_features = select_rare_move(
            board,
            scored_moves={best: 100, ok: 10, bad: -50},
            max_cp_loss=120,
        )

        feature_moves = {feature.move for feature in all_features}
        self.assertIn(best, feature_moves)
        self.assertIn(ok, feature_moves)
        self.assertNotIn(bad, feature_moves)
        self.assertIn(selected, {best, ok})

    def test_prefers_safe_structural_rarity_when_available(self):
        board = empty_board({
            "g1": "wK",
            "d1": "wQ",
            "a1": "wR",
            "g8": "bK",
            "d8": "bQ",
        })
        quiet_major = parse_uci("d1h5")
        obvious = parse_uci("d1d8")

        selected, features, _all_features = select_rare_move(
            board,
            scored_moves={obvious: 100, quiet_major: 95},
            max_cp_loss=120,
        )

        self.assertIn(selected, {quiet_major, obvious})
        self.assertIsNotNone(features)
        self.assertLessEqual(features.cp_loss, 120)
        self.assertGreaterEqual(features.rarity_score, 0.0)

    def test_rare_move_can_beat_higher_scored_textbook_move(self):
        board = Board()
        rare_edge_move = parse_uci("h2h4")
        natural_development = parse_uci("g1f3")

        selected, features, _all_features = select_rare_move(
            board,
            scored_moves={natural_development: 100, rare_edge_move: 95},
            max_cp_loss=120,
        )

        self.assertEqual(selected, rare_edge_move)
        self.assertIsNotNone(features)
        self.assertGreater(features.rarity_score, 0.0)
        self.assertLessEqual(features.cp_loss, 120)


if __name__ == "__main__":
    unittest.main(verbosity=2)
