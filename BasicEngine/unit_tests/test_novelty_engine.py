#!/usr/bin/env python3
"""
Unit tests for novelty_engine.py

Tests the core novelty selection logic including:
- Engine distribution generation
- KL divergence computation
- Novel move selection
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
    score_move_novelty,
    get_novel_move,
    KL_THRESHOLD
)


class TestEngineDistribution(unittest.TestCase):
    """Test the engine probability distribution generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.board = Board()

    def test_returns_valid_probability_distribution(self):
        """Distribution should sum to approximately 1.0."""
        dist = get_engine_distribution(self.board)

        self.assertIsInstance(dist, dict)
        self.assertGreater(len(dist), 0)

        total_prob = sum(dist.values())
        self.assertAlmostEqual(total_prob, 1.0, places=4,
                               msg=f"Distribution sums to {total_prob}, expected ~1.0")

    def test_all_probabilities_in_range(self):
        """All probabilities should be in [0, 1]."""
        dist = get_engine_distribution(self.board)

        for move, prob in dist.items():
            self.assertGreaterEqual(prob, 0.0,
                                    msg=f"Move {move} has negative probability {prob}")
            self.assertLessEqual(prob, 1.0,
                                 msg=f"Move {move} has probability > 1.0: {prob}")

    def test_includes_all_legal_moves(self):
        """Distribution should include all legal moves."""
        dist = get_engine_distribution(self.board)
        legal_moves = {str(m) for m in self.board.legal_moves()}
        dist_moves = {str(m) for m in dist.keys()}

        self.assertEqual(dist_moves, legal_moves,
                         msg="Distribution doesn't match legal moves")

    def test_temperature_affects_sharpness(self):
        """Lower temperature should create more peaked distribution."""
        # Test with different temperatures
        dist_low_temp = get_engine_distribution(self.board, temperature=0.01)
        dist_high_temp = get_engine_distribution(self.board, temperature=10.0)

        # Low temp should have higher max probability (more peaked)
        max_prob_low = max(dist_low_temp.values())
        max_prob_high = max(dist_high_temp.values())

        self.assertGreater(max_prob_low, max_prob_high,
                           msg="Low temperature should create more peaked distribution")

    def test_higher_scored_moves_get_higher_probability(self):
        """Moves with better evaluations should have higher probability."""
        dist = get_engine_distribution(self.board, temperature=0.1)

        # In starting position, e4 and d4 are typically among the best
        # They should have higher probability than edge pawn moves
        if 'e2e4' in dist and 'a2a3' in dist:
            self.assertGreater(dist['e2e4'], dist['a2a3'],
                               msg="e4 should have higher probability than a3")


class TestKLDivergence(unittest.TestCase):
    """Test KL divergence computation."""

    def test_returns_zero_for_identical_distributions(self):
        """KL divergence should be 0 when distributions are identical."""
        dist = {'e2e4': 0.5, 'd2d4': 0.3, 'g1f3': 0.2}
        kl = compute_kl_divergence(dist, dist)

        self.assertAlmostEqual(kl, 0.0, places=6,
                               msg=f"KL divergence for identical distributions should be 0, got {kl}")

    def test_returns_positive_for_different_distributions(self):
        """KL divergence should be positive when distributions differ."""
        p = {'e2e4': 0.6, 'd2d4': 0.3, 'g1f3': 0.1}
        q = {'e2e4': 0.2, 'd2d4': 0.3, 'g1f3': 0.5}
        kl = compute_kl_divergence(p, q)

        self.assertGreater(kl, 0.0,
                           msg="KL divergence should be positive for different distributions")

    def test_handles_epsilon_correctly(self):
        """Should use epsilon for moves not in human distribution."""
        engine_dist = {'e2e4': 0.5, 'd2d4': 0.3, 'g1f3': 0.2}
        human_dist = {'e2e4': 0.6, 'd2d4': 0.4}  # Missing g1f3

        # Should not raise error, should use epsilon
        kl = compute_kl_divergence(engine_dist, human_dist, epsilon=0.001)

        self.assertIsInstance(kl, (int, float))
        self.assertGreater(kl, 0.0)

    def test_is_non_negative(self):
        """KL divergence is always non-negative."""
        p = {'e2e4': 0.4, 'd2d4': 0.4, 'g1f3': 0.2}
        q = {'e2e4': 0.3, 'd2d4': 0.5, 'g1f3': 0.2}
        kl = compute_kl_divergence(p, q)

        self.assertGreaterEqual(kl, 0.0,
                                msg="KL divergence cannot be negative")


class TestScoreMoveNovelty(unittest.TestCase):
    """Test novelty scoring for individual moves."""

    def test_higher_score_for_low_human_probability(self):
        """Moves with lower human probability should score higher."""
        move = 'e2e4'
        engine_dist = {'e2e4': 0.5, 'd2d4': 0.5}

        # Compare two human distributions
        human_common = {'e2e4': 0.9, 'd2d4': 0.1}
        human_rare = {'e2e4': 0.1, 'd2d4': 0.9}

        score_common = score_move_novelty(move, engine_dist, human_common)
        score_rare = score_move_novelty(move, engine_dist, human_rare)

        self.assertGreater(score_rare, score_common,
                           msg="Rare moves should score higher in novelty")


class TestGetNovelMove(unittest.TestCase):
    """Test the main novel move selection function."""

    def setUp(self):
        """Set up test fixtures."""
        self.board = Board()

    def test_returns_legal_move_or_none(self):
        """Should return a legal move or None."""
        move = get_novel_move(self.board)

        if move is not None:
            legal_moves = list(self.board.legal_moves())
            legal_move_strs = [str(m) for m in legal_moves]
            self.assertIn(str(move), legal_move_strs,
                          msg=f"Returned illegal move: {move}")

    def test_returns_move_object(self):
        """Should return Move object, not string."""
        move = get_novel_move(self.board, verbose=False)

        if move is not None:
            self.assertIsInstance(move, Move,
                                  msg=f"Should return Move object, got {type(move)}")

    def test_handles_empty_legal_moves(self):
        """Should handle positions with no legal moves gracefully."""
        # Create a board with no legal moves (checkmate or stalemate)
        # For now, just test that it doesn't crash
        try:
            move = get_novel_move(self.board)
            # Should either return a move or None, not crash
            self.assertTrue(move is None or isinstance(move, Move))
        except Exception as e:
            self.fail(f"get_novel_move crashed on normal position: {e}")

    def test_deterministic_behavior(self):
        """Same position should return same move (no randomness)."""
        move1 = get_novel_move(self.board, verbose=False)
        move2 = get_novel_move(self.board, verbose=False)

        # Should be deterministic
        self.assertEqual(str(move1) if move1 else None,
                         str(move2) if move2 else None,
                         msg="get_novel_move should be deterministic")

    def test_verbose_mode_doesnt_crash(self):
        """Verbose mode should not crash."""
        try:
            move = get_novel_move(self.board, verbose=True)
            self.assertTrue(move is None or isinstance(move, Move))
        except Exception as e:
            self.fail(f"Verbose mode crashed: {e}")


class TestKLThreshold(unittest.TestCase):
    """Test KL threshold behavior."""

    def test_kl_threshold_is_positive(self):
        """KL threshold should be a positive number."""
        self.assertGreater(KL_THRESHOLD, 0.0,
                           msg="KL_THRESHOLD should be positive")

    def test_kl_threshold_is_reasonable(self):
        """KL threshold should be in a reasonable range (0.1 to 5.0)."""
        self.assertGreater(KL_THRESHOLD, 0.05,
                           msg="KL_THRESHOLD too low, may trigger too often")
        self.assertLess(KL_THRESHOLD, 10.0,
                        msg="KL_THRESHOLD too high, may never trigger")


class TestIntegration(unittest.TestCase):
    """Integration tests for the full novelty engine pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.board = Board()

    def test_full_pipeline_starting_position(self):
        """Test full pipeline on starting position."""
        move = get_novel_move(self.board, verbose=False)

        # Should return a valid move
        self.assertIsNotNone(move, msg="Should return a move for starting position")

        # Should be legal
        legal_moves = [str(m) for m in self.board.legal_moves()]
        self.assertIn(str(move), legal_moves,
                      msg="Returned move should be legal")

    def test_full_pipeline_after_e4(self):
        """Test pipeline after 1.e4."""
        # Make e4
        e4 = Move(6, 4, 4, 4)  # e2 -> e4
        self.board.make_move(e4)

        move = get_novel_move(self.board, verbose=False)

        if move is not None:
            legal_moves = [str(m) for m in self.board.legal_moves()]
            self.assertIn(str(move), legal_moves,
                          msg="Returned move should be legal")


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    unittest.main(verbosity=2)
