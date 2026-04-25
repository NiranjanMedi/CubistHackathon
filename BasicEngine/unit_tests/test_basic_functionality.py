#!/usr/bin/env python3
"""
Basic functionality tests for BasicEngine novelty chess engine.

Tests core functions to ensure they work correctly.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from board import Board, Move
from novelty_engine import (
    get_engine_distribution,
    compute_kl_divergence,
    get_novel_move,
    analyze_position,
    KL_THRESHOLD
)
from critical_point import (
    is_critical_point,
    analyze_critical_point,
    get_game_phase,
    get_depth_for_rating
)


class TestNoveltyEngine(unittest.TestCase):
    """Test novelty engine core functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.board = Board()

    def test_engine_distribution_valid(self):
        """Engine distribution should be a valid probability distribution."""
        dist = get_engine_distribution(self.board)

        self.assertGreater(len(dist), 0, "Should return some moves")

        total_prob = sum(dist.values())
        self.assertAlmostEqual(total_prob, 1.0, places=2,
                               msg=f"Total probability should be ~1.0, got {total_prob}")

        for move, prob in dist.items():
            self.assertGreaterEqual(prob, 0, "Probabilities should be non-negative")
            self.assertLessEqual(prob, 1, "Probabilities should be <= 1")

    def test_kl_divergence_properties(self):
        """KL divergence should have correct mathematical properties."""
        # Same distribution -> KL = 0
        dist = {'e2e4': 0.5, 'd2d4': 0.3, 'g1f3': 0.2}
        kl = compute_kl_divergence(dist, dist)
        self.assertAlmostEqual(kl, 0.0, places=5, msg="Identical distributions should have KL=0")

        # Different distributions -> KL > 0
        dist2 = {'e2e4': 0.2, 'd2d4': 0.5, 'g1f3': 0.3}
        kl = compute_kl_divergence(dist, dist2)
        self.assertGreater(kl, 0, "Different distributions should have KL > 0")

        # KL is always non-negative
        self.assertGreaterEqual(kl, 0, "KL divergence should be non-negative")

    def test_get_novel_move_returns_legal(self):
        """get_novel_move should always return a legal move or None."""
        move = get_novel_move(self.board)

        if move is not None:
            legal_moves = list(self.board.legal_moves())
            self.assertIn(move, legal_moves, "Returned move should be legal")

    def test_analyze_position(self):
        """analyze_position should return expected structure."""
        analysis = analyze_position(self.board)

        required_keys = ['kl_divergence', 'is_novelty_position', 'recommended_move']
        for key in required_keys:
            self.assertIn(key, analysis, f"Analysis should include '{key}'")

        self.assertIsInstance(analysis['kl_divergence'], (int, float))
        self.assertIsInstance(analysis['is_novelty_position'], bool)


class TestCriticalPoint(unittest.TestCase):
    """Test critical point detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.board = Board()

    def test_game_phase_detection(self):
        """Test game phase is detected correctly."""
        # Opening
        phase = get_game_phase(self.board, move_count=5)
        self.assertEqual(phase, 'opening', "Move 5 should be opening")

        # Middlegame
        phase = get_game_phase(self.board, move_count=20)
        self.assertEqual(phase, 'middlegame', "Move 20 should be middlegame")

    def test_depth_calibration(self):
        """Test depth increases with rating."""
        depths = [get_depth_for_rating(r) for r in [1000, 1200, 1500, 1800, 2100]]

        for i in range(len(depths) - 1):
            self.assertGreaterEqual(depths[i+1], depths[i],
                                    "Depth should increase with rating")

    def test_is_critical_point_returns_bool(self):
        """is_critical_point should return boolean."""
        result = is_critical_point(self.board, opponent_rating=1500, move_count=15)
        self.assertIsInstance(result, bool)

    def test_analyze_critical_point_structure(self):
        """analyze_critical_point should return expected structure."""
        analysis = analyze_critical_point(self.board, 1500, 15)

        required_keys = ['is_critical_point', 'game_phase', 'shallow_eval', 'deep_eval']
        for key in required_keys:
            self.assertIn(key, analysis, f"Analysis should include '{key}'")


class TestIntegration(unittest.TestCase):
    """Integration tests for full pipeline."""

    def test_full_pipeline(self):
        """Test the full novelty engine pipeline."""
        board = Board()

        # Get engine move
        move = get_novel_move(board)
        self.assertIsNotNone(move, "Should return a move")

        # Analyze position
        analysis = analyze_position(board)
        self.assertIn('kl_divergence', analysis)

        # Check critical point
        is_critical = is_critical_point(board, 1500, 0)
        self.assertIsInstance(is_critical, bool)

    def test_deterministic_behavior(self):
        """Same position should give same result."""
        board = Board()

        move1 = get_novel_move(board)
        move2 = get_novel_move(board)

        self.assertEqual(str(move1), str(move2),
                         "Should be deterministic")


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    unittest.main(verbosity=2)
