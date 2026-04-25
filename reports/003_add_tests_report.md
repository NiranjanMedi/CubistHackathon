# Test Suite — Implementation Report

## Summary

Added 45 tests across four files under `tests/`. All 45 pass.

Run with:
```
.venv/bin/python -m unittest discover tests -v
```

---

## Files Created

### `tests/helpers.py`
Shared `pos(pieces, turn)` utility that builds a `Board` from a square→piece dict
(e.g. `{'e1':'wK', 'e8':'bK'}`). Used everywhere a custom position is needed since
the engine has no FEN parser.

### `tests/test_smoke.py` — 11 tests
Basic health checks: imports work, `Board()` initialises with the right turn and piece
layout, `evaluate()` returns `int` and scores zero on the symmetric starting position,
`best_move()` returns a `Move` from the start, and both checkmate and stalemate
terminal positions return `None` without crashing.

### `tests/test_move_validation.py` — 12 tests
Correctness of legal-move generation:
- Pawn single/double-step, blocked pawn, diagonal capture, no same-color capture,
  promotion generates queen, black pawn double-step.
- Moving into check is illegal; all legal moves must leave the king safe.
- Pinned piece cannot expose the king (wR on e4 pinned by bQ on e8 cannot leave
  the e-file).
- Knight L-shape moves, knight cannot move straight.

### `tests/test_engine_choices.py` — 12 tests
Pass/fail engine move-choice tests at depth 2–3:

| Test | Position | Expected |
|------|----------|----------|
| Capture hanging queen | wR vs undefended bQ | `a1a6` |
| Checkmate in one | Qb7# corner mate | `b6b7` |
| Take free rook | wQ diagonal to undefended bR | `d1h5` |
| Promote pawn | wP one step from promotion | `a7a8q` |
| Escape check | bQ checks wK | any legal move |
| Recapture rook | wR recaptures bR same file | `d1d5` |
| Knight takes free bishop | wN on d4 takes bB on f5 | `d4f5` |
| King takes adjacent queen | wK captures undefended bQ | `e1d2` |
| Knight takes hanging queen | wN on c3 takes bQ on d5 | `c3d5` |
| Knight smothered mate | wN e5→f7#; bK trapped in corner | `e5f7` |
| Best move from start is legal | — | any legal move |
| No move when game over | stalemate | `None` |

### `tests/test_scoring.py` — 10 tests + aggregate summary
Same 10 engine-choice positions as above, re-run with a 0/1/2 scoring scheme:
- **2 pts** — engine chose one of the expected best moves.
- **1 pt** — engine made a capture or promotion (reasonable but not optimal).
- **0 pts** — illegal, crash, or missed tactic.

Prints at the end of a test run:
```
Engine move-choice score: 20/20
```

---

## Design Notes

**No FEN parser needed.** Custom positions are built by direct `board.squares`
manipulation via `helpers.pos()`. This avoids adding a FEN dependency while keeping
each test position self-contained and readable.

**No new dependencies.** Uses only Python's built-in `unittest`.

**Engine code unchanged.** All tests pass against the existing engine as-is.

**Artificial positions require care.** Two initial position designs caused a
`ValueError: No b king on board` crash: if a sliding piece has a direct unobstructed
path to the enemy king, the engine generates a pseudo-legal "king capture" move; after
that move executes the king is gone, and the next `find_king` call raises. Fixed by
redesigning positions so no white piece has a clear line to the black king.

---

## Results

```
Ran 45 tests in 0.175s
OK

Engine move-choice score: 20/20
```
