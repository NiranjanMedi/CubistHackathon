#!/usr/bin/env python3
"""
Quick test script to verify the novelty engine works.
Run: python test_novelty.py
"""

from BasicEngine.board import Board
from BasicEngine.novelty_engine import get_novel_move, analyze_position

def test_starting_position():
    """Test engine on starting position."""
    print("=" * 60)
    print("Testing Novelty Engine - Starting Position")
    print("=" * 60)

    board = Board()

    # Analyze the position
    print("\n1. Analyzing position...")
    analysis = analyze_position(board)

    print(f"\nKL Divergence: {analysis['kl_divergence']:.4f}")
    print(f"Novelty position: {analysis['is_novelty_position']}")
    print(f"Mode: {'NOVELTY' if analysis['is_novelty_position'] else 'BASE'}")

    print("\nTop engine moves:")
    for move, prob in analysis['top_engine_moves']:
        print(f"  {move}: {prob:.4f}")

    print("\nTop human moves:")
    for move, prob in analysis['top_human_moves']:
        print(f"  {move}: {prob:.4f}")

    # Get the move
    print("\n2. Getting move...")
    move = get_novel_move(board)
    print(f"\nRecommended move: {move}")

    print("\n" + "=" * 60)
    print("✓ Test passed! Engine is working.")
    print("=" * 60)

def test_after_e4():
    """Test engine after 1.e4."""
    print("\n" + "=" * 60)
    print("Testing After 1.e4")
    print("=" * 60)

    board = Board()

    # Make e4
    from BasicEngine.board import Move
    e4_move = Move(6, 4, 4, 4)  # e2 to e4
    board.make_move(e4_move)

    # Analyze
    analysis = analyze_position(board)
    print(f"\nKL Divergence: {analysis['kl_divergence']:.4f}")
    print(f"Novelty position: {analysis['is_novelty_position']}")

    # Get move
    move = get_novel_move(board)
    print(f"Recommended move: {move}")

    print("\n✓ Test passed!")

if __name__ == "__main__":
    try:
        test_starting_position()
        test_after_e4()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYour novelty engine is ready to use.")
        print("Run: python server.py")
        print("Visit: http://localhost:5000")

    except Exception as e:
        print("\n" + "=" * 60)
        print("ERROR!")
        print("=" * 60)
        print(f"\n{type(e).__name__}: {e}")
        print("\nMake sure you have all dependencies:")
        print("  pip install flask flask-cors")
        import traceback
        traceback.print_exc()
