# Code Cleanliness Report — `feat/novelty`

**Overall score: 8 / 10**

## Summary

The cleanest and only fully runnable branch. `engine.py` and `server.py` are in sync, the package import style is consistent (relative imports with `__init__.py`), the board has castling and en passant, and all the lightning/opening-book/noise wiring is properly connected end-to-end. The branch has a narrow set of focused files with no dead modules. Minor issues are small enough to fix in minutes.

---

## Strengths

- **`server.py` and `engine.py` match.** `best_move(board, depth, history, noise)` is the signature in both. No runtime crashes.
- **Correct package structure.** `BasicEngine/__init__.py` exists and `engine.py` uses `from .board import Board, Move` — the only branch where this is done consistently.
- **`board.py` is the most complete version.** Full castling and en passant support including castling rights tracking on captures.
- **Opening book is clean.** `OPENING_BOOK` is a plain dict literal with inline comments explaining each line choice. Easy to extend.
- **Noise integration is minimal.** One `if noise: score += random.randint(...)` at the leaf — exactly as much code as the feature needs.

---

## Biggest Issues

### 1. `_move_to_uci_key` in `engine.py` duplicates `move_to_uci` in `server.py`

`engine.py:148-154` implements the same file+rank string conversion as `server.py:49-54`. Since `server.py` already imports `Move` from the engine package, it could import a shared helper instead of maintaining two copies.

### 2. `random_move` is dead code

`engine.py:155-159`: `random_move` is defined but never called anywhere on this branch. The server and all callers use `best_move`.

### 3. Bare `except Exception` in `server.py`

`server.py:115`:
```python
try:
    m = uci_to_move(uci)
except Exception:
    return jsonify({"error": f"Cannot parse move: {uci}"}), 400
```
Same issue as other branches — catches everything including unexpected bugs.

### 4. `files` and `ranks` redefined in multiple functions

`move_to_uci` (server.py:50-51) and `_move_to_uci_key` (engine.py:149-150) both define `files = 'abcdefgh'` and `ranks = '87654321'` as local variables. These are used in at least four places across the two files. Module-level constants would be cleaner.

---

## Concrete Examples

| File | Line(s) | Issue |
|---|---|---|
| `BasicEngine/engine.py` | 148–154 | `_move_to_uci_key` duplicates `server.py`'s `move_to_uci` |
| `BasicEngine/engine.py` | 155–159 | `random_move` — never called, dead code |
| `server.py` | 115 | `except Exception` without logging |
| `server.py` | 50–51 & `engine.py` | 149–150 | `files`/`ranks` strings redefined in four places |

---

## Top Cleanup Recommendations

1. **Extract `files` and `ranks` as module-level constants** in `server.py` and remove the duplicate `_move_to_uci_key` from `engine.py`.
2. **Delete `random_move`** from `engine.py` — it has no callers.
3. **Narrow the `except`** in `uci_to_move` to `(ValueError, IndexError)`.
