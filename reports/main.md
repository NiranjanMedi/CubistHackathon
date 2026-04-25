# Code Cleanliness Report — `main`

**Overall score: 6 / 10**

## Summary

`main` has a solid foundation: the engine and board are clean and well-structured, the test suite is thorough, and the Flask server has a sensible API shape. The branch is let down by a critical runtime mismatch between `server.py` and `engine.py`, inconsistent import styles across the package, and a handful of stranded or never-used files left over from iterative development.

---

## Strengths

- **`BasicEngine/engine.py`** is tight and readable. The negamax + alpha-beta implementation is well under 60 lines, PST tables are clearly labelled, and `_order_moves` has a precise docstring explaining MVV-LVA.
- **`BasicEngine/board.py`** covers castling and en passant with explicit, legible logic. The `copy()` and `legal_moves()` methods are clean.
- **Test suite** (`tests/`) is well-organised across four focused files. `tests/helpers.py` isolates the position-builder pattern cleanly.
- **`server.py`** has good route separation, a consistent `_game_result` helper, and exposes the right fields on every response.
- `novelty_engine.py` and `critical_point.py` both have clear module-level docstrings explaining their role in the larger system.

---

## Biggest Issues

### 1. Runtime crash: `server.py` calls `best_move` with arguments `engine.py` doesn't accept

`server.py:136` and `server.py:161`:
```python
em = best_move(_board, depth=3, history=_history if lightning else None, noise=80 if lightning else 0)
```
`BasicEngine/engine.py:131`:
```python
def best_move(board: Board, depth: int = 3) -> Move:
```
Any request to `/api/move` or `/api/engine_move` will raise `TypeError` immediately. The server cannot be used in its current state.

### 2. Inconsistent import style across `BasicEngine/`

Files inside `BasicEngine/` use bare absolute-style imports (`from board import Board`) rather than relative (`from .board import Board`) or package-qualified (`from BasicEngine.board import Board`). `server.py` on `main` imports as `from BasicEngine.board import Board`, which requires the project root to be on `sys.path` but the engine files to *not* treat themselves as a package. Mixing these conventions makes it easy to break one import style when fixing another.

Examples:
- `BasicEngine/engine.py:2` — `from board import Board, Move`
- `server.py:10` — `from BasicEngine.board import Board, Move`
- `BasicEngine/novelty_engine.py:12` — `from board import Board, Move`

### 3. `BasicEngine/human_novelty_engine.py` is stranded

`human_novelty_engine.py` exists in `BasicEngine/` but nothing on `main` imports it. `server.py` on `main` imports `best_move` directly. This file is dead code relative to this branch — it was created to satisfy a `server.py` that no longer exists here.

### 4. Bare `except Exception` swallows detail

`server.py:114`:
```python
try:
    m = uci_to_move(uci)
except Exception:
    return jsonify({"error": f"Cannot parse move: {uci}"}), 400
```
Catching `Exception` broadly hides bugs. A `ValueError` from a malformed string and an `IndexError` from a too-short string are meaningfully different failure modes.

### 5. `_rule_based_explanation` in `server.py` is never called

The function exists at `server.py` (written as a fallback for `/api/explain`) but the `/api/explain` route itself was removed in a later edit. The function and related helpers (`_PIECE_NAMES`, `_PIECE_VALS`, `_FILES`, `_RANKS`, `_sq`, `_board_text`) are all dead code.

---

## Concrete Examples

| File | Line(s) | Issue |
|---|---|---|
| `server.py` | 136, 161 | `best_move` called with `history=` and `noise=` — kwargs don't exist in engine |
| `BasicEngine/engine.py` | 2 | `from board import Board` — bare import, inconsistent with `server.py`'s package import |
| `BasicEngine/human_novelty_engine.py` | entire file | Never imported on this branch |
| `server.py` | 189–260 | `_rule_based_explanation` and its helpers — dead code, no caller |
| `server.py` | 114 | `except Exception` with no logging |

---

## Top Cleanup Recommendations

1. **Fix the server/engine mismatch** — either add `history` and `noise` parameters back to `engine.py:best_move`, or remove them from the `server.py` calls.
2. **Pick one import convention** — either make `BasicEngine` a proper package with relative imports (`from .board import`) or keep everything flat and adjust `sys.path` once at startup. Don't mix the two.
3. **Delete `human_novelty_engine.py`** from `main` until `server.py` actually uses it, or wire it in.
4. **Remove the dead explanation helpers** from `server.py` or restore the `/api/explain` route.
5. **Narrow the bare `except`** in `uci_to_move` to `(ValueError, IndexError)`.
