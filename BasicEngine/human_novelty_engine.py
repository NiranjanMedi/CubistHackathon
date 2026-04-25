"""HumanNoveltyEngine: ties together critical-point detection and novelty selection."""

from dataclasses import dataclass
from typing import Optional

from board import Board, Move
from engine import best_move, evaluate
from novelty_engine import get_novel_move, get_engine_distribution, compute_kl_divergence
from human_model import get_human_distribution
from critical_point import analyze_critical_point


@dataclass
class Decision:
    move: Optional[Move]
    mode: str
    reason: str
    critical_analysis: dict
    kl_divergence: float = 0.0
    eval_cp: int = 0


class HumanNoveltyEngine:
    def __init__(self, opponent_rating: int = 1500):
        self.opponent_rating = opponent_rating

    def choose_move(self, board: Board, move_count: int = 0) -> Decision:
        if not board.legal_moves():
            return Decision(
                move=None,
                mode="engine",
                reason="No legal moves.",
                critical_analysis={"is_critical_point": False, "discomfort": 0},
            )

        critical_analysis = analyze_critical_point(board, self.opponent_rating, move_count)

        engine_dist = get_engine_distribution(board)
        human_dist = get_human_distribution(board)
        kl = compute_kl_divergence(engine_dist, human_dist)

        raw_eval = evaluate(board)
        eval_cp = raw_eval if board.turn == 'w' else -raw_eval

        if critical_analysis["is_critical_point"]:
            move = get_novel_move(board)
            discomfort = critical_analysis["discomfort"]
            return Decision(
                move=move,
                mode="novelty",
                reason=f"Critical position detected (discomfort={discomfort:.0f}cp). Playing novelty to exploit opponent pattern-matching.",
                critical_analysis=critical_analysis,
                kl_divergence=kl,
                eval_cp=eval_cp,
            )

        move = best_move(board, depth=3)
        return Decision(
            move=move,
            mode="engine",
            reason="Standard engine move — position not critical for novelty injection.",
            critical_analysis=critical_analysis,
            kl_divergence=kl,
            eval_cp=eval_cp,
        )
