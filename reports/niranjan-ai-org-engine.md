# Code Cleanliness Report — `niranjan/ai-org-engine`

**Overall score: 5 / 10**

## Summary

The most architecturally ambitious branch. `pressure_detector.py` and `rare_move_selector.py` are genuinely sophisticated — the `MoveFeatures` dataclass with 18 fields and the multi-component rarity scoring formula are the most thorough novelty implementations in the repo. But `evaluate_novelty.py` is broken in three independent ways and cannot run, the try/except import pattern appears in every file, `board.py` is the older version without castling, and several files in `BasicEngine/` have unclear status. The server itself actually works, which keeps the score above the floor.

---

## Strengths

- **`server.py` is correct and clean.** It sets `ENGINE_DIR = Path(__file__).resolve().parent / "BasicEngine"` — the only branch (besides `main`) that actually resolves to a real path. Uses `PressureNoveltyEngine` consistently. No broken imports.
- **`pressure_detector.py` is the most thorough position analysis in the repo.** Weighted multi-feature criticality: hanging pieces, king danger, center tension, material imbalance, captures, checks. Returns a typed `CriticalityReport` dataclass. The feature weighting is explicit and tunable.
- **`rare_move_selector.py` has the clearest taxonomy of move rarity.** The 18-field `MoveFeatures` dataclass is self-documenting. The weighted formula (`0.35 * engine + 0.45 * rarity + 0.20 * ambiguity`) makes the tradeoff explicit.
- **`pressure_novelty_engine.py`** composes `pressure_detector` and `rare_move_selector` into a clean top-level selector. The integration layer is present and wired.

---

## Biggest Issues

### 1. `evaluate_novelty.py` is broken in three places

This top-level file cannot be imported or run:

**Wrong attribute name** (`evaluate_novelty.py:87`, `92`, `96`):
```python
target_piece = board.board[move.to_row][move.to_col]
has_captures = any(board.board[m.to_row][m.to_col] != '.' ...)
piece = board.board[move.from_row][move.from_col]
```
The attribute is `board.squares`, not `board.board`. Every board access crashes.

**Missing `uci` module** (`evaluate_novelty.py:43`, `52`, `61`, `71`, and repeated in every test position):
```python
from uci import parse_uci_move
board.make_move(parse_uci_move(uci))
```
There is no `uci.py` anywhere in this branch. This import fails at runtime on the very first test position.

**`HumanNoveltyEngine` doesn't exist on this branch** (`evaluate_novelty.py:28`):
```python
from human_novelty_engine import HumanNoveltyEngine
```
`human_novelty_engine.py` is on the `niranjan-engine` branch, not here. This import fails silently at the module level.

Any attempt to run `evaluate_novelty.py` will crash before evaluating a single position.

### 2. Try/except import pattern in every `BasicEngine/` file

Every file follows this pattern:
```python
try:
    from .board import Board, EMPTY
    from .engine import PIECE_VALUES, evaluate
except ImportError:
    from board import Board, EMPTY
    from engine import PIECE_VALUES, evaluate
```
And some go deeper — `board_attacked_squares()` in `pressure_detector.py` wraps a single function call in its own try/except import block. This pattern adds 4–8 lines of boilerplate per file and makes it unclear which import style is actually correct. A single `sys.path` setup in `server.py` or an `__init__.py` would eliminate all of it.

### 3. `board.py` missing castling and en passant

Same issue as `niranjan-engine` — the older `Board` version with no `castling` dict, no `en_passant`, and no `castling_moves()`. `main`'s `board.py` is the complete version.

### 4. `evaluate_novelty.py` uses single-character `'.'` as empty square

```python
target_piece = board.board[move.to_row][move.to_col]
is_capture = (target_piece != '.')
```
The board uses `'..'` (two chars) as the empty sentinel, defined as `EMPTY = '..'` in `board.py`. Single `'.'` comparisons would never match even if the attribute name were correct.

### 5. Several `BasicEngine/` files have unclear integration status

`BasicEngine/consult.py`, `BasicEngine/demo_novelty.py`, and `BasicEngine/play_novelty.py` exist but nothing in `server.py` imports them. It's not clear whether they're development scaffolding or intended entry points.

---

## Concrete Examples

| File | Line(s) | Issue |
|---|---|---|
| `evaluate_novelty.py` | 87, 92, 96 | `board.board[...]` — attribute is `board.squares` |
| `evaluate_novelty.py` | 43, 52, 61, 71, … | `from uci import parse_uci_move` — module doesn't exist |
| `evaluate_novelty.py` | 28 | `from human_novelty_engine import HumanNoveltyEngine` — module not on this branch |
| `evaluate_novelty.py` | 87 | `target != '.'` — empty sentinel is `'..'`, not `'.'` |
| `BasicEngine/pressure_detector.py` | 8–14 | try/except import block |
| `BasicEngine/rare_move_selector.py` | 8–14 | try/except import block |
| `BasicEngine/board.py` | entire file | No castling, no en passant — older incomplete version |

---

## Top Cleanup Recommendations

1. **Fix `evaluate_novelty.py`**: replace `board.board` with `board.squares`, replace `'.'` with `'..'`, replace `from uci import parse_uci_move` with inline UCI parsing, and either create `human_novelty_engine.py` or replace it with `PressureNoveltyEngine`.
2. **Remove try/except imports** — set `sys.path.insert(0, ENGINE_DIR)` once in `server.py` or add `__init__.py` with relative imports.
3. **Update `board.py`** to `main`'s version with castling and en passant.
4. **Clarify status of `consult.py`, `demo_novelty.py`, `play_novelty.py`** — document or delete.
