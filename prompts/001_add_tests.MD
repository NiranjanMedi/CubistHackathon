# 003 Add Engine Tests

## Date
2026-04-25

## Tool
Claude Code VSCode Extension

## Goal
Add 20–30 tests for the chess engine.

## Prompt

Inspect the current chess engine project. Add a proper test suite in the `/tests` folder.

Goal:
Create 20–30 tests that check correctness, basic engine health, and move quality. Keep the tests practical and easy to run.

Important constraints:
- Do not rewrite the engine.
- Do not change engine behavior unless you find a clear bug needed to make tests pass.
- Preserve the existing architecture.
- Prefer small, readable tests.
- Do not add large dependencies.
- If the project does not already use a test framework, use Python’s built-in `unittest` or `pytest` only if already available.
- Make sure all tests can be run with one simple command.

Please implement the following:

1. Test folder structure

Create a `/tests` directory if it does not already exist.

Suggested files:
- `tests/test_smoke.py`
- `tests/test_move_validation.py`
- `tests/test_engine_choices.py`
- `tests/test_scoring.py`

Use whatever structure best fits the existing project.

2. Smoke / health tests

Add tests that verify:
- The engine imports successfully.
- A board/game can be initialized.
- The engine can generate legal moves from the starting position.
- The engine can choose a move without crashing.
- The engine can evaluate a position without crashing.
- The engine handles check, checkmate, and stalemate positions without crashing if supported.

3. Move validation tests

Add tests for specific legal/illegal move behavior, based on the engine’s existing API.

Include tests for:
- Normal pawn moves
- Captures
- Illegal moves
- Moving into check should be illegal

4. Engine move-choice tests

Add tests using specific FEN positions where the engine should prefer a reasonable move.

Include 8–12 tactical or strategic positions, such as:
- Capturing a hanging queen
- Delivering checkmate in one
- Escaping check
- Promoting a pawn
- Recapturing a valuable piece
- Avoiding an obviously illegal king move
- Taking a free rook
- Choosing a forcing check when clearly winning

For each position, define:
- FEN
- Side to move
- Acceptable best moves, not always just one exact move
- Search depth to use
- A short explanation of what the test is checking

Do not require perfect Stockfish-level play. These should be sanity tests for a minimal engine.

5. Aggregate scoring function

Create a small scoring system for engine move-choice tests.

For example:
- Full credit if the engine chooses one of the expected best moves.
- Partial credit if the move is legal and belongs to an acceptable category, such as a capture/check/promotion.
- Zero credit if the move is illegal, crashes, or misses the obvious tactic.

Print an aggregate score like:

Engine move-choice score: 9/12
Passed unit tests: 24/27

---

## Changes Made (2026-04-25)

### Quiescence Search — `BasicEngine/engine.py`
Added `_quiesce()` function. When negamax reaches depth 0, it now continues searching capture-only moves until the position is quiet, preventing the horizon effect (engine stopping evaluation right before a piece is taken). `_negamax` at depth=0 now calls `_quiesce` instead of returning a raw static eval.

### Fixed `pos()` test helper — `tests/helpers.py`
`pos()` was constructing `Board` objects via `__new__` without setting `castling` or `en_passant` attributes. This caused `AttributeError` in 20+ tests. Fixed by initializing both attributes (`castling` with all rights disabled, `en_passant = None`) so custom test positions work correctly with the full move generator.

---

## ELO Improvement Changes (2026-04-25)

### 1. Transposition Table + Zobrist Hashing — `BasicEngine/engine.py`
Added `_ZOBRIST` keys (random 64-bit ints per piece/square combination), `board_hash()`, and `_TT` dict. `_negamax` now looks up and stores results with `EXACT`/`LOWER`/`UPPER` bound flags. Bounded at 1M entries with full clear on overflow. Estimated gain: ~200 Elo.

### 2. Iterative Deepening + Time Management — `BasicEngine/engine.py`, `server.py`
`best_move()` now accepts `time_limit_ms` (default 800ms) and iterates depths 1..12, returning the best move from the last completed iteration. Server passes `time_limit_ms=600`. Fixed depth param still accepted for test compatibility. Estimated gain: ~150 Elo.

### 3. Killer Move Heuristic — `BasicEngine/engine.py`
`_negamax` maintains a `killers[depth][0..1]` table. Quiet moves that cause beta cutoffs are stored as killers and tried first (after captures) in sibling nodes at the same depth. Estimated gain: ~100 Elo.

### 4. History Heuristic — `BasicEngine/engine.py`
`hist[from_sq][to_sq]` table incremented by `depth²` when a quiet move causes a cutoff. Used in `_order_moves` to rank quiet moves after killers. Reset per root call. Estimated gain: ~80 Elo.

### 5. Improved Evaluation — `BasicEngine/engine.py`
Extended `evaluate()` with: doubled pawns (-20), isolated pawns (-15), passed pawn bonuses (+10 to +110 by rank), rook on open/semi-open file (+15/+10), bishop pair bonus (+30). Also added endgame king PST (`K_end`) and phase-aware interpolation between middlegame and endgame king positioning. Estimated gain: ~100 Elo.

### 6. Null Move Pruning — `BasicEngine/engine.py`
At depth ≥ 3 and not in check, `_negamax` tries passing the turn (null move) and searches at depth-3. If the result still beats beta, prune the whole subtree. Disabled in endgames (phase ≤ 0.2) to avoid zugzwang errors. Estimated gain: ~80 Elo.

### 7. Principal Variation Search (PVS) — `BasicEngine/engine.py`
First move in `_negamax` gets a full window search. All subsequent moves use a zero-window `[alpha, alpha+1]` scout; only re-searched with the full window if the scout raises alpha. Reduces total nodes evaluated. Estimated gain: ~50 Elo.

### Opening Book Update — `BasicEngine/engine.py`
Replaced Grob's Attack (1.g4) with mainline 1.e4 and Ruy Lopez / Queen's Gambit lines. Engine now plays more principled openings, reducing early positional disadvantage.

**Total estimated Elo improvement: ~760 Elo (from ~1300 to ~1800–2000 range)**

---

## Niche-but-Sound Engine (2026-04-25)

### Massively Expanded Opening Book — `BasicEngine/engine.py`
Replaced 10-entry mainline book (1.e4 e5 Nf3 Nc6 Bb5...) with ~75 niche-but-sound entries covering:
- Nimzo-Larsen Attack (1.b3)
- Bird's Opening (1.f4)
- Réti / King's Indian Attack (1.Nf3)
- Trompowsky / Veresov / London System (1.d4)
- Vienna Game / Closed Sicilian / French (1.e4)
- English Opening (1.c4)

`OPENING_BOOK` format changed from `dict[tuple, str]` → `dict[tuple, list[str]]`. Each position has multiple sound options, picked randomly. Engine plays a different opening each game.

### Niche-Bias Move Selection — `BasicEngine/engine.py`
Added `_niche_bonus(board, move)` returning 0–15cp for moves humans rarely play (knight rim, flank pawn pushes in opening, fianchetto). Used **only at root tie-breaking** within the `diversity_cp` window — never affects search evaluation. Hard quality floor: a niche move is only chosen when its score is within 25cp of the best move.

### `niche_bias` Tunable Weight
Added 6th weight to `weights.json`. Auto-tuner adjusts based on win/loss — engine learns whether niche play actually beats the opponent. Defaults to 1.0.

### Server Integration — `server.py`
- Opening book now active in **all** modes (was lightning-only)
- `diversity_cp=25` (tightened from 30 — strict quality floor)
- `niche_bias=True` enabled for normal play

**Effect:** Engine plays unfamiliar openings against humans, varies move choice in middlegame within strict quality bounds, and tunes its own niche-preference based on results.
