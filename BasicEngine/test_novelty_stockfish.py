#!/usr/bin/env python3
"""
Test script for the Stockfish-powered novelty engine.
Plays a few moves and displays the novelty analysis.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BasicEngine.board import Board
from BasicEngine.novelty_engine import get_novel_move, analyze_position
from BasicEngine.stockfish_wrapper import close_stockfish_engine


def test_novelty_engine():
    """Test the novelty engine with Stockfish."""
    print("=" * 60)
    print("Testing Novelty Engine with Stockfish")
    print("=" * 60)
    print()

    board = Board()
    print("Starting position:")
    print(board)
    print()

    # Play a few moves
    for move_num in range(1, 4):
        print(f"\n{'=' * 60}")
        print(f"Move {move_num}")
        print(f"{'=' * 60}")

        # Analyze the position
        print("\nPosition analysis:")
        analysis = analyze_position(board)
        print(f"  KL Divergence: {analysis['kl_divergence']:.3f}")
        print(f"  Novelty position: {analysis['is_novelty_position']}")
        print(f"  Top engine moves: {analysis['top_engine_moves']}")
        print(f"  Top human moves: {analysis['top_human_moves']}")
        print(f"  Recommended move: {analysis['recommended_move']}")

        # Get and make the novel move
        print("\nGetting novel move with details...")
        move = get_novel_move(board, verbose=True)

        if move is None:
            print("Game over - no legal moves")
            break

        side = "White" if board.turn == 'w' else "Black"
        print(f"\n{side} plays: {move}")

        board.make_move(move)
        print("\nPosition after move:")
        print(board)

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

    # Clean up
    close_stockfish_engine()


if __name__ == "__main__":
    test_novelty_engine()
