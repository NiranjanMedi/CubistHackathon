from dataclasses import dataclass
from typing import Optional, Tuple

try:
    from .board import Board, EMPTY
    from .engine import PIECE_VALUES, evaluate
except ImportError:
    from board import Board, EMPTY
    from engine import PIECE_VALUES, evaluate


@dataclass(frozen=True)
class CriticalityReport:
    is_critical: bool
    score: float
    reasons: list[str]
    features: dict[str, float]


def _opponent(color: str) -> str:
    return 'b' if color == 'w' else 'w'


def _side_to_move_eval(board: Board) -> int:
    score = evaluate(board)
    return score if board.turn == 'w' else -score


def _move_gives_check(board: Board, move) -> bool:
    nb = board.copy()
    moving_color = board.turn
    nb.make_move(move)
    king_r, king_c = nb.find_king(nb.turn)
    return nb.is_attacked(king_r, king_c, moving_color)


def _is_capture(board: Board, move) -> bool:
    return board.squares[move.to_row][move.to_col] != EMPTY


def _piece_positions(board: Board):
    for r in range(8):
        for c in range(8):
            piece = board.squares[r][c]
            if piece != EMPTY:
                yield r, c, piece


def _is_attacked_by_lower_value_piece(board: Board, r: int, c: int, color: str) -> bool:
    value = PIECE_VALUES.get(board.squares[r][c][1], 0)
    enemy = _opponent(color)
    for er, ec, piece in _piece_positions(board):
        if piece[0] != enemy:
            continue
        if PIECE_VALUES.get(piece[1], 0) >= value:
            continue
        if (r, c) in board_attacked_squares(board, er, ec):
            return True
    return False


def board_attacked_squares(board: Board, r: int, c: int):
    try:
        from .board import attacked_squares
    except ImportError:
        from board import attacked_squares
    return attacked_squares(board, r, c)


def _hanging_pressure(board: Board) -> tuple[float, int]:
    pressure = 0
    count = 0
    for r, c, piece in _piece_positions(board):
        color = piece[0]
        enemy = _opponent(color)
        if board.is_attacked(r, c, enemy) and not board.is_attacked(r, c, color):
            count += 1
            pressure += min(1.0, PIECE_VALUES.get(piece[1], 0) / 900)
    return min(1.0, pressure / 3.0), count


def _attacked_value_pressure(board: Board) -> tuple[float, int]:
    weighted = 0
    count = 0
    for r, c, piece in _piece_positions(board):
        if piece[1] == 'K':
            continue
        if _is_attacked_by_lower_value_piece(board, r, c, piece[0]):
            count += 1
            weighted += min(1.0, PIECE_VALUES.get(piece[1], 0) / 900)
    return min(1.0, weighted / 2.0), count


def _king_danger(board: Board) -> float:
    color = board.turn
    enemy = _opponent(color)
    try:
        kr, kc = board.find_king(color)
    except ValueError:
        return 0.0

    attacked_nearby = 0
    total_nearby = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            nr, nc = kr + dr, kc + dc
            if not board.in_bounds(nr, nc):
                continue
            total_nearby += 1
            if board.is_attacked(nr, nc, enemy):
                attacked_nearby += 1

    shield_missing = 0
    direction = -1 if color == 'w' else 1
    for dc in (-1, 0, 1):
        nr, nc = kr + direction, kc + dc
        if board.in_bounds(nr, nc) and board.squares[nr][nc] != color + 'P':
            shield_missing += 1

    attack_score = attacked_nearby / max(1, total_nearby)
    shield_score = shield_missing / 3
    return min(1.0, 0.65 * attack_score + 0.35 * shield_score)


def _center_tension(board: Board) -> float:
    center = {(3, 3), (3, 4), (4, 3), (4, 4)}
    tension = 0
    for r, c in center:
        piece = board.squares[r][c]
        if piece != EMPTY:
            enemy = _opponent(piece[0])
            if board.is_attacked(r, c, enemy):
                tension += 1
    return min(1.0, tension / 4)


def _material_imbalance(board: Board) -> float:
    score = abs(evaluate(board))
    return min(1.0, score / 900)


def _phase_suppression(board: Board, move_count: Optional[int]) -> Tuple[bool, str]:
    non_king_material = 0
    queens = 0
    for _, _, piece in _piece_positions(board):
        if piece[1] != 'K':
            non_king_material += PIECE_VALUES.get(piece[1], 0)
        if piece[1] == 'Q':
            queens += 1

    if move_count is not None and move_count < 6:
        return True, "early opening"
    if non_king_material < 2200 and queens == 0:
        return True, "quiet endgame"
    if abs(_side_to_move_eval(board)) > 900:
        return True, "large evaluation imbalance"
    return False, ""


def analyze_pressure_point(
    board: Board,
    move_count: Optional[int] = None,
    threshold: float = 0.52,
) -> CriticalityReport:
    """Detect practical-pressure critical points without shallow/deep divergence."""
    suppressed, suppression_reason = _phase_suppression(board, move_count)
    legal_moves = board.legal_moves()
    captures = sum(1 for move in legal_moves if _is_capture(board, move))
    checks = sum(1 for move in legal_moves if _move_gives_check(board, move))
    hanging_pressure, hanging_count = _hanging_pressure(board)
    attacked_pressure, attacked_count = _attacked_value_pressure(board)

    features = {
        "branching_factor": min(1.0, len(legal_moves) / 40),
        "capture_density": min(1.0, captures / 8),
        "legal_check_pressure": min(1.0, checks / 4),
        "hanging_piece_pressure": hanging_pressure,
        "attacked_value_pressure": attacked_pressure,
        "king_danger": _king_danger(board),
        "center_tension": _center_tension(board),
        "material_imbalance": _material_imbalance(board),
        "legal_move_count": float(len(legal_moves)),
        "capture_count": float(captures),
        "check_count": float(checks),
        "hanging_piece_count": float(hanging_count),
        "attacked_high_value_piece_count": float(attacked_count),
    }

    score = (
        0.18 * features["king_danger"]
        + 0.16 * features["hanging_piece_pressure"]
        + 0.14 * features["legal_check_pressure"]
        + 0.14 * features["capture_density"]
        + 0.12 * features["center_tension"]
        + 0.10 * features["attacked_value_pressure"]
        + 0.08 * features["material_imbalance"]
        + 0.08 * features["branching_factor"]
    )

    reasons = []
    if suppressed:
        reasons.append(f"suppressed: {suppression_reason}")
    if captures >= 3:
        reasons.append(f"{captures} captures available")
    if checks:
        reasons.append(f"{checks} checking moves available")
    if hanging_count:
        reasons.append(f"{hanging_count} hanging/undefended pieces")
    if attacked_count:
        reasons.append(f"{attacked_count} high-value pieces attacked by lower-value pieces")
    if features["king_danger"] >= 0.35:
        reasons.append("king attack surface is exposed")
    if features["center_tension"] >= 0.25:
        reasons.append("center tension is unresolved")
    if not reasons:
        reasons.append("low tactical pressure")

    return CriticalityReport(
        is_critical=(not suppressed and score >= threshold),
        score=score,
        reasons=reasons,
        features=features,
    )
