from dataclasses import dataclass
from typing import Optional, Tuple

try:
    from .board import Board, Move, EMPTY
    from .engine import PIECE_VALUES, evaluate, score_legal_moves
    from .pressure_detector import analyze_pressure_point
except ImportError:
    from board import Board, Move, EMPTY
    from engine import PIECE_VALUES, evaluate, score_legal_moves
    from pressure_detector import analyze_pressure_point


@dataclass(frozen=True)
class MoveFeatures:
    move: Move
    engine_score: int
    cp_loss: int
    gives_check: bool
    is_capture: bool
    captured_value: int
    moved_piece_value: int
    creates_threat: bool
    attacks_higher_value_piece: bool
    quiet_threat: bool
    trades_down: bool
    queen_trade: bool
    legal_replies_after: int
    ambiguity_score: float
    surprise_shape_score: float
    rarity_score: float
    naturalness_score: float
    final_score: float
    tags: tuple[str, ...]


def _opponent(color: str) -> str:
    return 'b' if color == 'w' else 'w'


def _move_gives_check(board: Board, move: Move) -> bool:
    nb = board.copy()
    moving_color = board.turn
    nb.make_move(move)
    kr, kc = nb.find_king(nb.turn)
    return nb.is_attacked(kr, kc, moving_color)


def _is_capture(board: Board, move: Move) -> bool:
    return board.squares[move.to_row][move.to_col] != EMPTY


def _attacks_higher_value_piece(board: Board, color: str) -> bool:
    enemy = _opponent(color)
    try:
        from .board import attacked_squares
    except ImportError:
        from board import attacked_squares

    for r in range(8):
        for c in range(8):
            piece = board.squares[r][c]
            if piece == EMPTY or piece[0] != color:
                continue
            attacker_value = PIECE_VALUES.get(piece[1], 0)
            for ar, ac in attacked_squares(board, r, c):
                target = board.squares[ar][ac]
                if target != EMPTY and target[0] == enemy:
                    if PIECE_VALUES.get(target[1], 0) > attacker_value:
                        return True
    return False


def _creates_threat(before: Board, after: Board, moving_color: str) -> bool:
    if _attacks_higher_value_piece(after, moving_color):
        return True
    enemy = _opponent(moving_color)
    try:
        kr, kc = after.find_king(enemy)
        if after.is_attacked(kr, kc, moving_color):
            return True
    except ValueError:
        return False

    before_eval = evaluate(before)
    after_eval = evaluate(after)
    delta = after_eval - before_eval
    return delta > 80 if moving_color == 'w' else delta < -80


def _move_shape_score(board: Board, move: Move, is_capture: bool, gives_check: bool) -> tuple[float, float, list[str]]:
    piece = board.squares[move.from_row][move.from_col]
    color, kind = piece[0], piece[1]
    tags = []
    rarity = 0.0
    naturalness = 0.0

    legal_captures = any(_is_capture(board, legal) for legal in board.legal_moves())

    if not is_capture and not gives_check:
        rarity += 0.18
        tags.append("quiet")
    if legal_captures and not is_capture:
        rarity += 0.20
        tags.append("declines available capture")
    if kind in ("Q", "R") and not is_capture:
        rarity += 0.18
        tags.append("quiet major-piece move")
    if kind in ("N", "B") and move.to_col in (0, 7):
        rarity += 0.14
        tags.append("rim maneuver")
    if color == 'w' and move.to_row > move.from_row:
        rarity += 0.18
        tags.append("backward move")
    if color == 'b' and move.to_row < move.from_row:
        rarity += 0.18
        tags.append("backward move")
    if kind in ("Q", "R") and move.to_row == move.from_row and not is_capture:
        rarity += 0.12
        tags.append("lateral major-piece move")
    if kind == 'P' and move.to_col in (0, 7):
        rarity += 0.10
        tags.append("edge pawn")
    if kind == 'K' and abs(move.to_col - move.from_col) != 2:
        rarity += 0.10
        naturalness += 0.18
        tags.append("unusual king move")
    if kind in ("N", "B") and abs(move.to_row - move.from_row) + abs(move.to_col - move.from_col) > 3:
        rarity += 0.10
        tags.append("piece reroute")

    # Obvious or textbook-looking moves are less novel even when good.
    if is_capture:
        naturalness += 0.28
        tags.append("obvious capture penalty")
    if gives_check:
        naturalness += 0.24
        tags.append("obvious check penalty")
    if kind == 'P' and move.from_col in (3, 4) and abs(move.to_row - move.from_row) in (1, 2):
        naturalness += 0.20
        tags.append("central pawn move penalty")
    start_row = 7 if color == 'w' else 0
    if kind in ("N", "B") and move.from_row == start_row and move.to_col in (2, 3, 4, 5):
        naturalness += 0.24
        tags.append("natural development penalty")
    if kind == 'K' and abs(move.to_col - move.from_col) == 2:
        naturalness += 0.18
        tags.append("castling penalty")

    rarity_score = max(0.0, min(1.0, rarity - naturalness * 0.65))
    return rarity_score, min(1.0, naturalness), tags


def _queen_trade(board: Board, move: Move) -> bool:
    moved = board.squares[move.from_row][move.from_col]
    captured = board.squares[move.to_row][move.to_col]
    return moved[1] == 'Q' and captured == _opponent(moved[0]) + 'Q'


def _trades_down(board: Board, move: Move) -> bool:
    moved = board.squares[move.from_row][move.from_col]
    captured = board.squares[move.to_row][move.to_col]
    if captured == EMPTY:
        return False
    return PIECE_VALUES.get(captured[1], 0) <= PIECE_VALUES.get(moved[1], 0)


def extract_move_features(
    board: Board,
    move: Move,
    engine_score: int,
    best_score: int,
    max_cp_loss: int,
) -> MoveFeatures:
    moved_piece = board.squares[move.from_row][move.from_col]
    captured = board.squares[move.to_row][move.to_col]
    moving_color = board.turn
    is_capture = captured != EMPTY
    gives_check = _move_gives_check(board, move)

    after = board.copy()
    after.make_move(move)

    pressure_after = analyze_pressure_point(after, move_count=None)
    creates_threat = _creates_threat(board, after, moving_color)
    attacks_higher = _attacks_higher_value_piece(after, moving_color)
    quiet_threat = creates_threat and not is_capture and not gives_check
    legal_replies_after = len(after.legal_moves())
    cp_loss = best_score - engine_score
    rarity_score, naturalness_score, tags = _move_shape_score(board, move, is_capture, gives_check)
    surprise_shape_score = rarity_score

    if creates_threat:
        tags.append("creates threat")
    if attacks_higher:
        tags.append("attacks higher-value piece")
    if quiet_threat:
        rarity_score = min(1.0, rarity_score + 0.18)
        tags.append("quiet threat")

    ambiguity_score = min(1.0, (
        0.35 * pressure_after.score
        + 0.25 * min(1.0, legal_replies_after / 35)
        + (0.20 if creates_threat else 0.0)
        + (0.12 if quiet_threat else 0.0)
        + (0.08 if not is_capture else 0.0)
    ))

    if _queen_trade(board, move):
        ambiguity_score = max(0.0, ambiguity_score - 0.25)
        tags.append("queen trade penalty")
    if _trades_down(board, move):
        ambiguity_score = max(0.0, ambiguity_score - 0.08)
        tags.append("simplifying capture penalty")

    normalized_engine = 1.0 - min(1.0, cp_loss / max(1, max_cp_loss))
    if cp_loss > max_cp_loss * 0.75:
        rarity_score = max(0.0, rarity_score - 0.12)
        tags.append("near soundness limit")

    final_score = (
        0.35 * normalized_engine
        + 0.45 * rarity_score
        + 0.20 * ambiguity_score
    )

    return MoveFeatures(
        move=move,
        engine_score=engine_score,
        cp_loss=cp_loss,
        gives_check=gives_check,
        is_capture=is_capture,
        captured_value=0 if captured == EMPTY else PIECE_VALUES.get(captured[1], 0),
        moved_piece_value=PIECE_VALUES.get(moved_piece[1], 0),
        creates_threat=creates_threat,
        attacks_higher_value_piece=attacks_higher,
        quiet_threat=quiet_threat,
        trades_down=_trades_down(board, move),
        queen_trade=_queen_trade(board, move),
        legal_replies_after=legal_replies_after,
        ambiguity_score=ambiguity_score,
        surprise_shape_score=surprise_shape_score,
        rarity_score=rarity_score,
        naturalness_score=naturalness_score,
        final_score=final_score,
        tags=tuple(tags),
    )


def select_rare_move(
    board: Board,
    scored_moves: Optional[dict[Move, int]] = None,
    max_cp_loss: int = 120,
) -> Tuple[Optional[Move], Optional[MoveFeatures], list[MoveFeatures]]:
    """Pick a rare/unorthodox but base-engine-safe move."""
    scored = scored_moves if scored_moves is not None else score_legal_moves(board, depth=3)
    if not scored:
        return None, None, []

    best_score = max(scored.values())
    base_move = max(scored, key=scored.get)
    candidates = {
        move: score for move, score in scored.items()
        if best_score - score <= max_cp_loss
    }

    features = [
        extract_move_features(board, move, score, best_score, max_cp_loss)
        for move, score in candidates.items()
    ]
    features.sort(
        key=lambda item: (
            item.final_score,
            item.rarity_score,
            item.ambiguity_score,
            -item.cp_loss,
            str(item.move),
        ),
        reverse=True,
    )

    for item in features:
        if item.move != base_move and item.rarity_score >= 0.22 and item.final_score >= 0.48:
            return item.move, item, features
    return base_move, next((item for item in features if item.move == base_move), None), features
