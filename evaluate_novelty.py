#!/usr/bin/env python3
"""
Novelty Engine Evaluation Script

This script compares two chess engine implementations to measure which one
produces more unusual/rare moves while maintaining soundness.

It evaluates engines on fixed test positions and measures:
1. Structural rarity - quiet moves, declined captures, backward moves, rim moves
2. Engine rank percentile - how the chosen move ranks among all legal moves
3. Deviation from base engine - percentage of moves different from baseline
4. CP loss (soundness check) - centipawn loss compared to best move

Usage:
    python evaluate_novelty.py

The script will compare:
- Previous engine: HumanNoveltyEngine (uses critical_point.py)
- New engine: Direct novelty_engine (uses KL divergence approach)
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from board import Board, Move
from engine import best_move, evaluate
from human_novelty_engine import HumanNoveltyEngine
from novelty_engine import get_novel_move


@dataclass
class MoveEvaluation:
    """Results from evaluating a single move."""
    move: Optional[Move]
    mode: str
    structural_rarity: float
    engine_rank_percentile: float
    cp_loss: int
    is_different_from_base: bool


@dataclass
class EngineComparison:
    """Aggregate results comparing two engines."""
    engine_name: str
    novelty_mode_count: int
    total_positions: int
    avg_structural_rarity: float
    pct_different_from_base: float
    avg_cp_loss: float
    position_results: List[MoveEvaluation]


def get_test_positions() -> List[Board]:
    """
    Returns a list of fixed test positions representing various game states.
    These are positions where novelty vs soundness tradeoffs are interesting.
    """
    positions = []

    # Position 1: Starting position
    positions.append(Board())

    # Position 2: After 1.e4 e5 2.Nf3 Nc6 (early middlegame)
    board = Board()
    moves = ["e2e4", "e7e5", "g1f3", "b8c6"]
    for uci in moves:
        from uci import parse_uci_move
        board.make_move(parse_uci_move(uci))
    positions.append(board)

    # Position 3: After 1.d4 d5 2.c4 e6 (Queen's Gambit)
    board = Board()
    moves = ["d2d4", "d7d5", "c2c4", "e7e6"]
    for uci in moves:
        from uci import parse_uci_move
        board.make_move(parse_uci_move(uci))
    positions.append(board)

    # Position 4: After 1.e4 c5 2.Nf3 d6 (Sicilian)
    board = Board()
    moves = ["e2e4", "c7c5", "g1f3", "d7d6"]
    for uci in moves:
        from uci import parse_uci_move
        board.make_move(parse_uci_move(uci))
    positions.append(board)

    # Position 5-12: Add more middlegame positions
    # For now, variations of common openings
    test_sequences = [
        ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],  # Ruy Lopez
        ["d2d4", "g8f6", "c2c4", "e7e6"],  # Indian Defense
        ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4"],  # Sicilian Open
        ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],  # Italian
        ["d2d4", "d7d5", "c2c4", "c7c6"],  # Slav Defense
        ["e2e4", "c7c6", "d2d4", "d7d5"],  # Caro-Kann
        ["e2e4", "e7e6", "d2d4", "d7d5"],  # French Defense
        ["g1f3", "d7d5", "c2c4", "c7c6"],  # Reti
    ]

    for seq in test_sequences:
        board = Board()
        for uci in seq:
            from uci import parse_uci_move
            board.make_move(parse_uci_move(uci))
        positions.append(board)

    return positions


def compute_structural_rarity(board: Board, move: Move) -> float:
    """
    Compute how structurally unusual a move is based on heuristics.

    Rarity indicators:
    - Quiet move (not capture/check) = +0.2
    - Declined capture (capture available but not taken) = +0.3
    - Backward move (piece moves toward own back rank) = +0.2
    - Rim move (piece moves to a/h file or 1/8 rank) = +0.1
    - Knight move to edge = +0.15

    Returns: float in [0, 1] where higher = more unusual
    """
    rarity = 0.0

    # Check if move is quiet (not capture)
    target_piece = board.board[move.to_row][move.to_col]
    is_capture = (target_piece != '.')

    if not is_capture:
        rarity += 0.2

    # Check if there are captures available but not taken
    has_captures = any(
        board.board[m.to_row][m.to_col] != '.'
        for m in board.legal_moves()
    )
    if has_captures and not is_capture:
        rarity += 0.3

    # Check if move is backward (toward own back rank)
    piece = board.board[move.from_row][move.from_col]
    if piece.isupper():  # White pieces
        if move.to_row > move.from_row:  # Moving toward rank 8
            rarity += 0.2
    else:  # Black pieces
        if move.to_row < move.from_row:  # Moving toward rank 1
            rarity += 0.2

    # Check if move is to rim (edge files/ranks)
    if move.to_col in [0, 7] or move.to_row in [0, 7]:
        rarity += 0.1

    # Extra penalty for knight to edge
    if piece.upper() == 'N' and (move.to_col in [0, 7] or move.to_row in [0, 7]):
        rarity += 0.15

    return min(rarity, 1.0)


def compute_engine_rank_percentile(board: Board, move: Move) -> float:
    """
    Compute what percentile the chosen move ranks among all legal moves.

    0.0 = worst move
    1.0 = best move
    0.5 = median move
    """
    legal_moves = list(board.legal_moves())
    if not legal_moves:
        return 0.0

    # Evaluate all moves
    move_scores = {}
    for m in legal_moves:
        test_board = board.copy()
        test_board.make_move(m)
        move_scores[str(m)] = evaluate(test_board)

    # Rank them (higher score = better)
    sorted_moves = sorted(move_scores.items(), key=lambda x: x[1], reverse=True)

    # Find the chosen move's rank
    move_str = str(move)
    for rank, (m, score) in enumerate(sorted_moves):
        if m == move_str:
            # Convert rank to percentile (0-indexed)
            percentile = 1.0 - (rank / len(sorted_moves))
            return percentile

    return 0.0


def compute_cp_loss(board: Board, move: Move) -> int:
    """
    Compute centipawn loss of the chosen move vs best move.

    Returns: positive integer (0 = no loss, higher = worse)
    """
    # Get best move score
    best_board = board.copy()
    best = best_move(best_board, depth=3)
    if not best:
        return 0

    best_board.make_move(best)
    best_score = evaluate(best_board)

    # Get chosen move score
    chosen_board = board.copy()
    chosen_board.make_move(move)
    chosen_score = evaluate(chosen_board)

    # Loss is difference (from current player's perspective)
    loss = abs(best_score - chosen_score)
    return loss


def evaluate_engine_on_position(
    board: Board,
    engine_name: str,
    engine_callable,
    move_count: int = 0
) -> MoveEvaluation:
    """
    Evaluate a single engine on a single position.

    Args:
        board: Position to evaluate
        engine_name: Name for logging
        engine_callable: Function that takes (board, move_count) and returns move/decision
        move_count: Move number in game

    Returns:
        MoveEvaluation with all metrics
    """
    # Get base move for comparison
    base = best_move(board, depth=3)

    # Get engine's chosen move
    if engine_name == "HumanNoveltyEngine":
        decision = engine_callable.choose_move(board, move_count)
        chosen_move = decision.move
        mode = decision.mode
    else:
        chosen_move = engine_callable(board)
        mode = "novelty" if chosen_move else "none"

    if not chosen_move:
        return MoveEvaluation(
            move=None,
            mode="no_move",
            structural_rarity=0.0,
            engine_rank_percentile=0.0,
            cp_loss=0,
            is_different_from_base=False
        )

    # Compute metrics
    rarity = compute_structural_rarity(board, chosen_move)
    percentile = compute_engine_rank_percentile(board, chosen_move)
    cp_loss = compute_cp_loss(board, chosen_move)
    is_different = (str(chosen_move) != str(base))

    return MoveEvaluation(
        move=chosen_move,
        mode=mode,
        structural_rarity=rarity,
        engine_rank_percentile=percentile,
        cp_loss=cp_loss,
        is_different_from_base=is_different
    )


def compare_engines(
    positions: List[Board],
    opponent_rating: int = 1500
) -> Tuple[EngineComparison, EngineComparison]:
    """
    Compare HumanNoveltyEngine vs direct novelty_engine on test positions.

    Returns:
        (previous_engine_results, new_engine_results)
    """
    # Initialize engines
    previous_engine = HumanNoveltyEngine(opponent_rating=opponent_rating)

    previous_results = []
    new_results = []

    print(f"\nEvaluating {len(positions)} positions...")
    print("=" * 60)

    for i, board in enumerate(positions):
        print(f"\nPosition {i+1}/{len(positions)}")

        # Evaluate previous engine (HumanNoveltyEngine)
        prev_eval = evaluate_engine_on_position(
            board,
            "HumanNoveltyEngine",
            previous_engine,
            move_count=i
        )
        previous_results.append(prev_eval)
        print(f"  Previous: {prev_eval.move} (mode={prev_eval.mode}, rarity={prev_eval.structural_rarity:.3f})")

        # Evaluate new engine (direct novelty_engine)
        new_eval = evaluate_engine_on_position(
            board,
            "NoveltyEngine",
            get_novel_move,
            move_count=i
        )
        new_results.append(new_eval)
        print(f"  New:      {new_eval.move} (rarity={new_eval.structural_rarity:.3f})")

    # Aggregate results
    def aggregate(results: List[MoveEvaluation], name: str) -> EngineComparison:
        valid_results = [r for r in results if r.move is not None]
        total = len(results)
        novelty_count = sum(1 for r in valid_results if r.mode == "novelty")

        if not valid_results:
            return EngineComparison(
                engine_name=name,
                novelty_mode_count=0,
                total_positions=total,
                avg_structural_rarity=0.0,
                pct_different_from_base=0.0,
                avg_cp_loss=0.0,
                position_results=results
            )

        avg_rarity = sum(r.structural_rarity for r in valid_results) / len(valid_results)
        pct_different = 100.0 * sum(r.is_different_from_base for r in valid_results) / len(valid_results)
        avg_loss = sum(r.cp_loss for r in valid_results) / len(valid_results)

        return EngineComparison(
            engine_name=name,
            novelty_mode_count=novelty_count,
            total_positions=total,
            avg_structural_rarity=avg_rarity,
            pct_different_from_base=pct_different,
            avg_cp_loss=avg_loss,
            position_results=results
        )

    previous_comparison = aggregate(previous_results, "HumanNoveltyEngine (previous)")
    new_comparison = aggregate(new_results, "NoveltyEngine (new)")

    return previous_comparison, new_comparison


def print_comparison_report(prev: EngineComparison, new: EngineComparison):
    """Print a formatted comparison report."""
    print("\n" + "=" * 60)
    print("NOVELTY ENGINE COMPARISON REPORT")
    print("=" * 60)

    print(f"\n{prev.engine_name}:")
    print(f"  Novelty-mode moves:      {prev.novelty_mode_count}/{prev.total_positions}")
    print(f"  Avg structural rarity:   {prev.avg_structural_rarity:.3f}")
    print(f"  % different from base:   {prev.pct_different_from_base:.1f}%")
    print(f"  Avg CP loss:             {prev.avg_cp_loss:.1f}")

    print(f"\n{new.engine_name}:")
    print(f"  Novelty-mode moves:      {new.novelty_mode_count}/{new.total_positions}")
    print(f"  Avg structural rarity:   {new.avg_structural_rarity:.3f}")
    print(f"  % different from base:   {new.pct_different_from_base:.1f}%")
    print(f"  Avg CP loss:             {new.avg_cp_loss:.1f}")

    print("\n" + "=" * 60)
    print("INTERPRETATION:")
    print("=" * 60)

    # Determine which engine is more novel
    if new.avg_structural_rarity > prev.avg_structural_rarity:
        rarity_diff = new.avg_structural_rarity - prev.avg_structural_rarity
        print(f"✓ New engine produces MORE unusual moves (+{rarity_diff:.3f} rarity)")
    elif prev.avg_structural_rarity > new.avg_structural_rarity:
        rarity_diff = prev.avg_structural_rarity - new.avg_structural_rarity
        print(f"✗ Previous engine produces more unusual moves (+{rarity_diff:.3f} rarity)")
    else:
        print("= Both engines have equal structural rarity")

    # Check deviation from base
    if new.pct_different_from_base > prev.pct_different_from_base:
        diff_diff = new.pct_different_from_base - prev.pct_different_from_base
        print(f"✓ New engine deviates MORE from base engine (+{diff_diff:.1f}%)")
    elif prev.pct_different_from_base > new.pct_different_from_base:
        diff_diff = prev.pct_different_from_base - new.pct_different_from_base
        print(f"✗ Previous engine deviates more from base engine (+{diff_diff:.1f}%)")
    else:
        print("= Both engines deviate equally from base")

    # Check soundness (lower CP loss = better)
    if new.avg_cp_loss < prev.avg_cp_loss:
        loss_diff = prev.avg_cp_loss - new.avg_cp_loss
        print(f"✓ New engine is MORE sound (-{loss_diff:.1f} cp loss)")
    elif prev.avg_cp_loss < new.avg_cp_loss:
        loss_diff = new.avg_cp_loss - prev.avg_cp_loss
        print(f"⚠ New engine is LESS sound (+{loss_diff:.1f} cp loss)")
    else:
        print("= Both engines have equal soundness")

    print("\n" + "=" * 60)


def main():
    """Run the novelty engine comparison benchmark."""
    print("Novelty Engine Evaluation")
    print("=" * 60)
    print("This script compares two engine implementations:")
    print("  1. HumanNoveltyEngine (uses critical_point detector)")
    print("  2. NoveltyEngine (direct KL divergence approach)")
    print()
    print("Metrics:")
    print("  - Structural rarity: quiet moves, declined captures, backward moves, rim moves")
    print("  - Engine rank percentile: how chosen move ranks among legal moves")
    print("  - Deviation from base: % of moves different from baseline engine")
    print("  - CP loss: soundness check (centipawn loss vs best move)")
    print("=" * 60)

    # Get test positions
    positions = get_test_positions()

    # Run comparison
    prev_results, new_results = compare_engines(positions, opponent_rating=1500)

    # Print report
    print_comparison_report(prev_results, new_results)

    print("\n✓ Evaluation complete!")
    print(f"  Tested {len(positions)} positions")
    print(f"  Use this script to track improvements in novelty generation")


if __name__ == "__main__":
    main()
