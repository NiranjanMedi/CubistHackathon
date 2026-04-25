from dataclasses import dataclass
from typing import Optional

try:
    from .board import Board, Move
    from .engine import best_move, score_legal_moves
    from .pressure_detector import CriticalityReport, analyze_pressure_point
    from .rare_move_selector import MoveFeatures, select_rare_move
except ImportError:
    from board import Board, Move
    from engine import best_move, score_legal_moves
    from pressure_detector import CriticalityReport, analyze_pressure_point
    from rare_move_selector import MoveFeatures, select_rare_move


@dataclass(frozen=True)
class NoveltyDecision:
    move: Optional[Move]
    mode: str
    reason: str
    base_move: Optional[Move]
    critical_score: float
    novelty_score: float
    candidate_count: int
    cp_loss: int
    tags: tuple[str, ...]
    critical_report: CriticalityReport
    selected_features: Optional[MoveFeatures]


class PressureNoveltyEngine:
    """Benchmark engine using practical pressure and ambiguity, not human probabilities."""

    def __init__(
        self,
        depth: int = 3,
        max_cp_loss: int = 120,
        critical_threshold: float = 0.52,
    ):
        self.depth = depth
        self.max_cp_loss = max_cp_loss
        self.critical_threshold = critical_threshold

    def choose_move(self, board: Board, move_count: Optional[int] = None) -> NoveltyDecision:
        scored = score_legal_moves(board, self.depth)
        base = max(scored, key=scored.get) if scored else best_move(board, self.depth)
        report = analyze_pressure_point(board, move_count, self.critical_threshold)

        if not scored or base is None:
            return NoveltyDecision(
                move=None,
                mode="base",
                reason="no legal move",
                base_move=None,
                critical_score=report.score,
                novelty_score=0.0,
                candidate_count=0,
                cp_loss=0,
                tags=(),
                critical_report=report,
                selected_features=None,
            )

        if not report.is_critical:
            return NoveltyDecision(
                move=base,
                mode="base",
                reason="; ".join(report.reasons),
                base_move=base,
                critical_score=report.score,
                novelty_score=0.0,
                candidate_count=0,
                cp_loss=0,
                tags=(),
                critical_report=report,
                selected_features=None,
            )

        selected, features, all_features = select_rare_move(board, scored, self.max_cp_loss)
        if selected is None or features is None:
            return NoveltyDecision(
                move=base,
                mode="fallback",
                reason="critical position, but no safe pressure novelty candidate",
                base_move=base,
                critical_score=report.score,
                novelty_score=0.0,
                candidate_count=0,
                cp_loss=0,
                tags=(),
                critical_report=report,
                selected_features=None,
            )

        mode = "novelty" if selected != base else "base"
        if mode == "novelty":
            reason = f"pressure novelty: {', '.join(features.tags) or 'ambiguity-preserving move'}"
        else:
            reason = "critical position, but base move remained best pressure candidate"

        return NoveltyDecision(
            move=selected,
            mode=mode,
            reason=reason,
            base_move=base,
            critical_score=report.score,
            novelty_score=features.final_score,
            candidate_count=len(all_features),
            cp_loss=features.cp_loss,
            tags=features.tags,
            critical_report=report,
            selected_features=features,
        )
