# Code Cleanliness Report — `nathan`

**Overall score: 7 / 10**

## Summary

The `nathan` branch has the cleanest internal engine architecture of all five branches. `evaluate_root_moves` is an excellent abstraction — it cleanly separates "score every move" from "pick a move", which is exactly the interface `discomfort_move.py` needs. `discomfort.py` is focused and well-documented. `to_pgn.py` is production-quality. The branch is held back by a `debug=True` default that would spam stdout in any integration, the absence of a web server, and an older `board.py` that lacks castling and en passant.

---

## Strengths

- **`evaluate_root_moves` is the best engine interface here.** It uses a full `(-INF, INF)` window per root move so all scores are exact, returns a sorted list of `(move, white_signed_cp)`, and its docstring explains the design choice. Every other branch's `best_move` is opaque by comparison.
- **`discomfort.py` is clean and focused.** 20 lines, a precise docstring, and a clear mathematical model. The `sign_flip_bonus` is a single, well-named parameter.
- **`to_pgn.py` is the best standalone file in the repo.** Handles piped input, stdin, and the `=== UCI move list ===` marker format. Uses `chess.pgn` correctly. Handles illegal moves and result headers cleanly.
- **`main.py` is a clean self-play harness.** `WHITE_PLAYER`/`BLACK_PLAYER` as top-level variables makes the comparison setup readable at a glance.
- **Past games directory** with actual game records — the only branch with evidence of end-to-end play tested.

---

## Biggest Issues

### 1. `debug=True` is the default in `discomfort_move.py`

`discomfort_move.py:15`:
```python
def discomfort_move(board, depth=DEFAULT_DEPTH, lam=DEFAULT_LAMBDA,
                    eval_floor_cp=DEFAULT_FLOOR_CP, debug: bool = True):
```
Every call prints a five-row table to stdout. `main.py` calls this on every white move. Any future server integration would need to remember to pass `debug=False`, and it's easy to forget. The print block should default off.

### 2. No web server — branch is CLI-only

There is no `server.py` on this branch. The discomfort selector is the most interesting novelty feature in the repo, but there is no way to play against it in the browser without writing a server from scratch.

### 3. `board.py` is the older version — no castling or en passant

The `Board` class here has no `castling` dict, no `en_passant` attribute, and no `castling_moves()`. `make_move` doesn't handle castling or en passant captures. `main`'s `board.py` has a significantly more complete implementation.

### 4. Bare imports throughout `BasicEngine/`

All files use `from board import Board`, `from engine import evaluate_root_moves` etc. — bare absolute imports that only work when `BasicEngine/` is on `sys.path`. Inconsistent with any caller outside the directory.

### 5. `random_move` is dead code in `engine.py`

`engine.py` still defines `random_move` at the bottom. Nothing on this branch calls it.

---

## Concrete Examples

| File | Line(s) | Issue |
|---|---|---|
| `BasicEngine/discomfort_move.py` | 15 | `debug=True` default — prints to stdout on every call |
| `BasicEngine/engine.py` | last function | `random_move` — dead code, no callers |
| `BasicEngine/board.py` | entire file | No castling, no en passant — older incomplete version |
| `BasicEngine/discomfort.py` | 1 | `from board import Board` — bare import |
| *(missing)* | — | No `server.py` — feature not accessible from the browser |

---

## Top Cleanup Recommendations

1. **Change `debug=True` to `debug=False`** in `discomfort_move.py`.
2. **Add `server.py`** wiring `discomfort_move` as the engine — the selector is feature-complete; it just needs a Flask wrapper.
3. **Update `board.py`** to `main`'s version which includes castling and en passant.
4. **Delete `random_move`** from `engine.py`.
5. **Switch to relative imports** (`from .board import`) so the package works regardless of `sys.path`.
