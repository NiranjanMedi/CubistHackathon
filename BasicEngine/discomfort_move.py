from typing import Optional
from board import Board, Move
from engine import evaluate_root_moves
from discomfort import discomfort

DEFAULT_LAMBDA = 0.3
DEFAULT_FLOOR_CP = 80
DEFAULT_DEPTH = 3


def discomfort_move(board: Board, depth: int = DEFAULT_DEPTH,
                    lam: float = DEFAULT_LAMBDA,
                    eval_floor_cp: int = DEFAULT_FLOOR_CP,
                    debug: bool = True) -> Optional[Move]:
    scored = evaluate_root_moves(board, depth)
    if not scored:
        return None

    sign = 1 if board.turn == 'w' else -1
    best_our_eval = max(sign * ws for _, ws in scored)
    floor = best_our_eval - eval_floor_cp

    candidates = []
    for m, ws_eval in scored:
        our_eval = sign * ws_eval
        if our_eval < floor:
            continue
        nb = board.copy()
        nb.make_move(m)
        disc = discomfort(nb, ws_eval)
        final = our_eval + lam * disc
        candidates.append((m, our_eval, disc, final))

    if not candidates:
        return scored[0][0]

    candidates.sort(key=lambda x: x[3], reverse=True)

    if debug:
        print("  --- discomfort selector ---")
        print(f"  {'move':<7}{'eng_eval':>10}{'discom':>10}{'final':>10}")
        for m, oe, d, fs in candidates[:5]:
            print(f"  {str(m):<7}{oe:>10.0f}{d:>10.1f}{fs:>10.1f}")

    return candidates[0][0]
