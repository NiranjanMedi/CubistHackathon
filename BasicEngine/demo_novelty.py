"""
Demo script for Component 2: Novelty Engine

Shows how the KL divergence-based novelty scoring works.
"""

from board import Board, Move
from novelty_engine import get_novel_move, analyze_position, KL_THRESHOLD
from engine import best_move


def print_separator():
    print("=" * 60)


def demo_position(board, description):
    """Analyze a position and show the novelty engine's decision."""
    print_separator()
    print(f"Position: {description}")
    print_separator()
    print(board)
    print()

    analysis = analyze_position(board)

    print(f"KL Divergence: {analysis['kl_divergence']:.3f}")
    print(f"Threshold: {KL_THRESHOLD}")
    print(f"Is Novelty Position: {analysis['is_novelty_position']}")
    print()

    print("Top Engine Moves (what's objectively good):")
    for m, p in analysis['top_engine_moves']:
        print(f"  {m}: {p*100:.1f}%")
    print()

    print("Top Human Moves (what humans expect):")
    for m, p in analysis['top_human_moves']:
        print(f"  {m}: {p*100:.1f}%")
    print()

    # Compare normal engine move vs novelty engine move
    normal_move = best_move(board, depth=2)
    novel_move = get_novel_move(board)

    print(f"Normal Engine would play: {normal_move}")
    print(f"Novelty Engine plays:     {novel_move}")

    if str(normal_move) != str(novel_move):
        print("  -> NOVELTY INJECTED!")
    else:
        print("  -> Same move (novelty not triggered)")
    print()


def main():
    print_separator()
    print("COMPONENT 2: NOVELTY ENGINE DEMO")
    print("Using KL Divergence to identify novelty opportunities")
    print_separator()
    print()

    # Position 1: Starting position
    board = Board()
    demo_position(board, "Starting Position")

    # Position 2: After 1.e4
    board = Board()
    board.make_move(Move(6, 4, 4, 4))  # e4
    demo_position(board, "After 1.e4 (Black to move)")

    # Position 3: Italian Game
    board = Board()
    moves = [
        Move(6, 4, 4, 4),  # e4
        Move(1, 4, 3, 4),  # e5
        Move(7, 6, 5, 5),  # Nf3
        Move(0, 1, 2, 2),  # Nc6
        Move(7, 5, 4, 2),  # Bc4
    ]
    for m in moves:
        board.make_move(m)
    demo_position(board, "Italian Game (Black to move)")

    # Position 4: Sicilian Defense
    board = Board()
    moves = [
        Move(6, 4, 4, 4),  # e4
        Move(1, 2, 3, 2),  # c5
        Move(7, 6, 5, 5),  # Nf3
    ]
    for m in moves:
        board.make_move(m)
    demo_position(board, "Sicilian Defense (Black to move)")

    print_separator()
    print("SUMMARY")
    print_separator()
    print("""
The Novelty Engine uses KL divergence to measure how much the engine's
preferred moves differ from what humans typically play.

When KL divergence is HIGH:
  - Engine and humans disagree about this position
  - This is a prime opportunity for novelty
  - We pick moves the engine likes but humans don't expect

When KL divergence is LOW:
  - Engine and humans mostly agree
  - Novelty won't help much here
  - We just play the best engine move

This approach ensures we inject novelty only where it has maximum impact.
""")


if __name__ == '__main__':
    main()
