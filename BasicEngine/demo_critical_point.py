"""
Demo script for Component 1: Critical Point Detector

Shows how the discomfort-based detection works across different
positions and opponent ratings.
"""

from board import Board, Move
from critical_point import (
    is_critical_point,
    print_analysis,
    get_depth_for_rating,
    DISCOMFORT_THRESHOLD,
)


def demo_position(board, description, opponent_rating, move_count=None):
    """Analyze a position and show critical point detection."""
    print("=" * 60)
    print(f"Position: {description}")
    print(f"Opponent Rating: {opponent_rating}")
    print("=" * 60)
    print(board)
    print()
    print_analysis(board, opponent_rating, move_count)
    print()


def main():
    print("=" * 60)
    print("COMPONENT 1: CRITICAL POINT DETECTOR DEMO")
    print("=" * 60)
    print()
    print("Depth calibration by rating:")
    for rating in [1100, 1300, 1600, 1900, 2200]:
        print(f"  {rating} ELO -> depth {get_depth_for_rating(rating)}")
    print()
    print(f"Discomfort threshold: {DISCOMFORT_THRESHOLD} centipawns")
    print()

    # Position 1: Starting position (opening - should not trigger)
    board = Board()
    demo_position(board, "Starting position (opening)", 1500, move_count=0)

    # Position 2: Early middlegame
    board = Board()
    moves = [
        Move(6, 4, 4, 4),  # e4
        Move(1, 4, 3, 4),  # e5
        Move(7, 6, 5, 5),  # Nf3
        Move(0, 1, 2, 2),  # Nc6
        Move(7, 5, 3, 1),  # Bb5
        Move(1, 0, 2, 0),  # a6
        Move(3, 1, 2, 0),  # Bxa6 (sacrifice?)
        Move(1, 1, 2, 0),  # bxa6
        Move(6, 3, 4, 3),  # d4
        Move(3, 4, 4, 3),  # exd4
        Move(5, 5, 4, 3),  # Nxd4
        Move(0, 5, 3, 2),  # Bc5
    ]
    for m in moves:
        board.make_move(m)
    demo_position(board, "After piece exchange (middlegame)", 1500, move_count=12)

    # Position 3: Same position, different ratings
    print("=" * 60)
    print("COMPARING DIFFERENT OPPONENT RATINGS ON SAME POSITION")
    print("=" * 60)
    print()

    board = Board()
    moves = [
        Move(6, 4, 4, 4),  # e4
        Move(1, 4, 3, 4),  # e5
        Move(7, 6, 5, 5),  # Nf3
        Move(0, 1, 2, 2),  # Nc6
        Move(7, 5, 4, 2),  # Bc4
        Move(0, 5, 4, 1),  # Bc5
        Move(6, 2, 4, 2),  # c3
        Move(0, 6, 2, 5),  # Nf6
        Move(6, 3, 4, 3),  # d4
        Move(3, 4, 4, 3),  # exd4
        Move(4, 2, 3, 3),  # cxd4
        Move(4, 1, 3, 0),  # Bb4+
    ]
    for m in moves:
        board.make_move(m)

    print(board)
    print()

    for rating in [1100, 1400, 1700, 2000, 2300]:
        result = is_critical_point(board, rating, move_count=12)
        depth = get_depth_for_rating(rating)
        status = "CRITICAL" if result else "normal"
        print(f"  Rating {rating} (depth {depth}): {status}")

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
The Critical Point Detector measures POSITIONAL DECEPTION:
- Shallow eval: What the position looks like at a glance
- Deep eval: What calculation reveals (to opponent's depth)

When these diverge significantly, the opponent's intuition
will mislead them. This is when we inject novelty.

Key conditions:
1. Must be in middlegame (not opening or endgame)
2. Must not already be winning by >200cp
3. Discomfort (divergence) must exceed threshold

The same position may be critical against a 1200 but not
against a 2000, because the 2000 calculates deeper.
""")


if __name__ == '__main__':
    main()
