# Noise Parameter — Implementation Report

## Summary

Added an optional `noise` parameter to `_negamax` and `best_move` in `BasicEngine/engine.py`. When non-zero, a random offset is added to leaf-node evaluations, making the engine play more variably across games while leaving the default deterministic behaviour unchanged.

---

## Files Changed

### `BasicEngine/engine.py`

**`_negamax` signature updated**:

```python
def _negamax(board, depth, alpha, beta, noise=0):
    if depth == 0:
        score = evaluate(board)
        if noise:
            score += random.randint(-noise, noise)
        return score if board.turn == 'w' else -score
    ...
    for m in _order_moves(board, moves):
        nb = board.copy()
        nb.make_move(m)
        score = -_negamax(nb, depth - 1, -beta, -alpha, noise)  # noise passed through
```

**`best_move` passes noise to `_negamax`**:

```python
def best_move(board, depth=3, history=None, noise=0):
    ...
    for m in _order_moves(board, moves):
        nb = board.copy()
        nb.make_move(m)
        score = -_negamax(nb, depth - 1, -INF, -alpha, noise)
```

---

## Design Notes

**Where noise is applied**: at depth-0 leaf nodes only, after the static `evaluate()` call. Interior node scores are computed from children and are therefore already affected by the noisy leaves — there is no need to add noise at interior nodes separately.

**Why `random.randint`**: produces a uniform distribution over `[-noise, noise]` in integer centipawns, matching the scale of the evaluation function. `noise=80` means ±80cp variance, roughly the value of a positional pawn advantage — enough to meaningfully change move choices without causing obvious blunders on most positions.

**Default unchanged**: `noise=0` short-circuits the `if noise:` branch entirely, leaving deterministic behaviour for all existing callers.

**Propagation**: passing `noise` through every recursive call ensures all leaves in the same search share the same noise level. If noise were only applied at the root, interior evaluations would remain deterministic and the effect would be limited to a single ply.
