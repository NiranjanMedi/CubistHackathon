"""
Test the full pipeline: Component 1 (Critical Point) + Component 2 (Novelty Engine)

This shows how the two components work together.
"""

from board import Board, Move
from critical_point import is_critical_point, analyze_critical_point
from novelty_engine import get_novel_move
from engine import best_move


def get_best_move_with_novelty(board: Board, opponent_rating: int, move_count: int) -> tuple:
    """
    Full pipeline: decide whether to play novel or normal move.

    Returns: (move, was_novel, analysis)
    """
    # Component 1: Should we inject novelty?
    analysis = analyze_critical_point(board, opponent_rating, move_count)

    if analysis['is_critical_point']:
        # Component 2: Get novel move
        move = get_novel_move(board)
        return (move, True, analysis)
    else:
        # Normal engine move
        move = best_move(board, depth=3)
        return (move, False, analysis)


def play_game_with_novelty(opponent_rating: int = 1500, max_moves: int = 30):
    """Play a game using the full novelty pipeline."""
    board = Board()
    move_count = 0

    print(f"=== Playing vs {opponent_rating} ELO opponent ===")
    print()

    while move_count < max_moves * 2:
        legal_moves = board.legal_moves()
        if not legal_moves:
            break

        move, was_novel, analysis = get_best_move_with_novelty(
            board, opponent_rating, move_count // 2
        )

        if move is None:
            break

        side = "White" if board.turn == 'w' else "Black"
        move_num = (move_count // 2) + 1

        novelty_tag = " [NOVELTY]" if was_novel else ""
        print(f"{move_num}. {side}: {move}{novelty_tag}")

        if was_novel:
            print(f"   Discomfort: {analysis['discomfort']:.0f}cp")
            print(f"   Shallow: {analysis['shallow_eval']:+d}, Deep: {analysis['deep_eval']:+d}")

        board.make_move(move)
        move_count += 1

    print()
    print("Final position:")
    print(board)


def test_specific_position():
    """Test on a specific position to see the pipeline decision."""
    board = Board()

    # Play some moves to get to middlegame
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

    print("=== Testing Specific Position ===")
    print(board)
    print()

    for rating in [1200, 1500, 1800, 2100]:
        move, was_novel, analysis = get_best_move_with_novelty(board, rating, move_count=12)

        status = "NOVELTY" if was_novel else "NORMAL"
        print(f"Rating {rating}: {move} [{status}]")
        print(f"  Discomfort: {analysis['discomfort']:.0f}cp, Phase: {analysis['game_phase']}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'game':
        rating = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
        play_game_with_novelty(opponent_rating=rating)
    else:
        test_specific_position()
        print()
        print("Run 'python3 test_pipeline.py game 1500' to play a full game")
