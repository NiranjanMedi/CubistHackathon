"""
tuner.py — Hill-climbing evaluation weight tuner.

After each completed game, replays positions and nudges weights so that
the engine's evaluation better predicts the game outcome. This is a
simplified form of Texel tuning: no gradient, just ±STEP hill-climbing
on each weight independently.
"""

from .board import Board
from .engine import evaluate, get_weights, set_weights

_STEP = 0.04   # how much to nudge each weight per game
_FILES = 'abcdefgh'
_RANKS = '87654321'


def _uci_to_move_coords(uci: str):
    """Return (from_row, from_col, to_row, to_col) from a UCI string."""
    fc = ord(uci[0]) - ord('a')
    fr = 8 - int(uci[1])
    tc = ord(uci[2]) - ord('a')
    tr = 8 - int(uci[3])
    return fr, fc, tr, tc


def _replay_positions(history: list[str]) -> list[Board]:
    """Replay history and return list of Board snapshots (one per ply)."""
    from .board import Move
    board = Board()
    snapshots = []
    for uci in history:
        snapshots.append(board.copy())
        fr, fc, tr, tc = _uci_to_move_coords(uci)
        promo = uci[4].upper() if len(uci) == 5 else None
        m = Move(fr, fc, tr, tc, promotion=promo)
        board.make_move(m)
    return snapshots


def _avg_eval_sign(positions: list[Board]) -> float:
    """Return mean of sign(eval) across positions, from white's perspective."""
    if not positions:
        return 0.0
    total = sum(evaluate(b) for b in positions)
    return total / len(positions)


def tune_from_game(history: list[str], winner: str | None) -> dict:
    """
    Run one hill-climbing pass over all weights given a completed game.
    Returns the updated weights dict.

    winner: 'w' = engine (white) won, 'b' = human AI won, None = draw
    """
    if not history:
        return get_weights()

    # Target: positive = good for white (engine), negative = good for black
    target = 1.0 if winner == 'w' else (-1.0 if winner == 'b' else 0.0)

    positions = _replay_positions(history)
    if not positions:
        return get_weights()

    weights = get_weights()
    baseline = _avg_eval_sign(positions)
    baseline_error = abs(baseline - target * 500)  # 500cp ~ decisive advantage

    for key in weights:
        # Try nudging up
        w_up = dict(weights)
        w_up[key] = min(3.0, weights[key] + _STEP)
        set_weights(w_up)
        score_up = abs(_avg_eval_sign(positions) - target * 500)

        # Try nudging down
        w_down = dict(weights)
        w_down[key] = max(0.1, weights[key] - _STEP)
        set_weights(w_down)
        score_down = abs(_avg_eval_sign(positions) - target * 500)

        # Keep whichever direction reduced error (or revert if neither helped)
        if score_up < score_down and score_up < baseline_error:
            set_weights(w_up)
            weights = get_weights()
            baseline_error = score_up
        elif score_down < baseline_error:
            set_weights(w_down)
            weights = get_weights()
            baseline_error = score_down
        else:
            set_weights(weights)  # revert

    return get_weights()
