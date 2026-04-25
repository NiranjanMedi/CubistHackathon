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
