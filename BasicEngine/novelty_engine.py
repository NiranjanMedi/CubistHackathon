"""
Novelty Engine - Component 2

Selects moves that balance soundness (don't blunder) with novelty (play moves
humans haven't seen). Uses KL divergence to identify positions where engine
and human move preferences diverge - these are prime opportunities for novelty.
"""

from math import exp, log
from typing import Dict, Optional, Tuple
from board import Board, Move
from engine import evaluate
from human_model import get_human_distribution

# Configuration
KL_THRESHOLD = 1.0      # Above this, position is good for novelty
TEMPERATURE = 100.0     # For softmax over centipawn scores (higher = flatter)
EPSILON = 0.001         # Small prob for unseen moves


def get_engine_distribution(board: Board, temperature: float = TEMPERATURE) -> Dict[Move, float]:
    """
    Build probability distribution over moves based on engine evaluation.
    Uses softmax over eval scores to convert evaluations to probabilities.

    Args:
        board: Current position
        temperature: Controls distribution sharpness (lower = peakier)

    Returns:
        Dict mapping Move objects to probabilities
    """
    legal_moves = board.legal_moves()
    if not legal_moves:
        return {}

    # Score each move by evaluating the resulting position
    scores = {}
    for move in legal_moves:
        new_board = board.copy()
        new_board.make_move(move)
        # Negate because evaluate() is from white's perspective
        # and we want score from current player's perspective
        raw_score = evaluate(new_board)
        scores[move] = raw_score if board.turn == 'w' else -raw_score

    # Apply softmax to convert scores to probabilities
    max_score = max(scores.values())
    exp_scores = {}
    for move, score in scores.items():
        # Subtract max for numerical stability
        exp_scores[move] = exp((score - max_score) / temperature)

    total = sum(exp_scores.values())
    if total == 0:
        # Fallback to uniform if all scores are extremely negative
        prob = 1.0 / len(legal_moves)
        return {m: prob for m in legal_moves}

    return {m: s / total for m, s in exp_scores.items()}


def compute_kl_divergence(
    engine_dist: Dict[Move, float],
    human_dist: Dict[str, float],
    epsilon: float = EPSILON
) -> float:
    """
    Compute KL divergence: KL(Engine || Human)

    Measures how "surprised" a human would be by the engine's move distribution.
    High KL = engine and humans strongly disagree about this position.

    Args:
        engine_dist: Probability distribution from engine (Move -> float)
        human_dist: Probability distribution from humans (UCI string -> float)
        epsilon: Small probability for unseen moves

    Returns:
        KL divergence value (non-negative float)
    """
    kl = 0.0

    for move, p_engine in engine_dist.items():
        if p_engine <= 0:
            continue

        uci = str(move)
        p_human = human_dist.get(uci, epsilon)

        # KL contribution: P(x) * log(P(x) / Q(x))
        kl += p_engine * log(p_engine / p_human)

    return kl


def score_move_novelty(
    move: Move,
    engine_dist: Dict[Move, float],
    human_dist: Dict[str, float],
    epsilon: float = EPSILON
) -> float:
    """
    Score a single move for novelty value.

    High score = engine likes the move AND humans don't expect it.

    Formula: engine_prob / human_prob
    - If engine loves it (high prob) and humans ignore it (low prob) → high score
    - If engine dislikes it or humans expect it → low score
    """
    p_engine = engine_dist.get(move, 0)
    p_human = human_dist.get(str(move), epsilon)

    if p_engine <= 0:
        return 0.0

    return p_engine / p_human


def get_novel_move(board: Board, verbose: bool = False) -> Optional[Move]:
    """
    Main entry point: Select the best novel move for the current position.

    Algorithm:
    1. Build engine distribution (what's objectively good)
    2. Build human distribution (what humans expect)
    3. Compute KL divergence (how much do they disagree?)
    4. If high KL: pick move maximizing engine_prob / human_prob
    5. If low KL: just play the engine's best move

    Args:
        board: Current position
        verbose: If True, print debug info

    Returns:
        Best novel move, or None if no legal moves
    """
    legal_moves = board.legal_moves()
    if not legal_moves:
        return None

    # Step 1: Get engine distribution
    engine_dist = get_engine_distribution(board)

    # Step 2: Get human distribution
    human_dist = get_human_distribution(board)

    # Step 3: Compute KL divergence
    kl = compute_kl_divergence(engine_dist, human_dist)

    if verbose:
        print(f"KL Divergence: {kl:.3f} (threshold: {KL_THRESHOLD})")
        print(f"Position {'IS' if kl > KL_THRESHOLD else 'is NOT'} good for novelty")

    # Step 4 & 5: Select move based on KL
    if kl > KL_THRESHOLD:
        # High KL: this is a novelty opportunity
        # Pick move that engine likes but humans don't expect
        best_move = None
        best_score = float('-inf')

        for move in legal_moves:
            score = score_move_novelty(move, engine_dist, human_dist)
            if score > best_score:
                best_score = score
                best_move = move

        if verbose and best_move:
            p_eng = engine_dist.get(best_move, 0)
            p_hum = human_dist.get(str(best_move), EPSILON)
            print(f"Selected novel move: {best_move}")
            print(f"  Engine prob: {p_eng:.3f}, Human prob: {p_hum:.3f}")

        return best_move

    else:
        # Low KL: engine and humans agree, just play best engine move
        best_move = max(engine_dist, key=engine_dist.get)

        if verbose:
            print(f"Selected engine move: {best_move} (novelty not beneficial)")

        return best_move


def analyze_position(board: Board) -> dict:
    """
    Analyze a position for novelty potential. Useful for debugging.

    Returns dict with:
    - kl_divergence: How much engine/human disagree
    - is_novelty_position: Whether this is good for novelty
    - top_engine_moves: Top 3 engine moves with probs
    - top_human_moves: Top 3 human moves with probs
    - recommended_move: The move get_novel_move() would pick
    """
    engine_dist = get_engine_distribution(board)
    human_dist = get_human_distribution(board)
    kl = compute_kl_divergence(engine_dist, human_dist)

    # Sort moves by probability
    engine_sorted = sorted(engine_dist.items(), key=lambda x: -x[1])[:3]
    human_sorted = sorted(human_dist.items(), key=lambda x: -x[1])[:3]

    return {
        'kl_divergence': kl,
        'is_novelty_position': kl > KL_THRESHOLD,
        'top_engine_moves': [(str(m), p) for m, p in engine_sorted],
        'top_human_moves': human_sorted[:3],
        'recommended_move': str(get_novel_move(board))
    }
