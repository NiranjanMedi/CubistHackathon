# Interpretability Feature — Implementation Report

## Summary

Added a natural language move explanation feature: clicking "Explain move" sends the current board position to Claude, grounded in accurate engine search data (principal variation + scored alternatives), and displays a 2–4 sentence chess coaching explanation in the UI.

---

## Files Changed

### `BasicEngine/engine.py`

Two new functions added after the existing `_negamax`:

**`_negamax_pv(board, depth, alpha, beta) → (score, pv)`**
A variant of the negamax search that carries the principal variation (the engine's best line) back up the tree alongside the score. At each node, when a move improves alpha, the PV is updated to `[move] + child_pv`. Beta cutoffs return an empty PV (pruned branches have no reliable line to report).

**`analyze(board, depth=3) → dict`**
Runs a full search at the root and returns:
- `pv` — list of UCI strings representing the best line the engine found (e.g. `["b1c3", "b8c6", "g1f3"]`)
- `alternatives` — top-5 root-level candidate moves with exact scores, sorted descending
- `eval` — centipawn evaluation of the position after the best move (positive = good for White)

Root-level scores are exact because the root's alpha starts at `-INF`; each candidate is searched with a full window.

### `server.py`

**`_board_text(board) → str`**
Renders the board as a standard ASCII grid (uppercase = white, lowercase = black, dots = empty), e.g.:
```
  a b c d e f g h
8 r n b q k b n r
7 p p p p p p p p
...
```

**`GET /api/explain`**
1. Calls `analyze(_board, depth=3)` to get the PV, scored alternatives, and evaluation
2. Builds a structured prompt containing: board ASCII, turn, best move, principal variation, evaluation in centipawns, and top-5 candidates with scores
3. Sends to `claude-haiku-4-5-20251001` (max 300 tokens) and returns the explanation
4. Returns graceful JSON error if `ANTHROPIC_API_KEY` is unset or the API call fails

### `index.html`

- Added "Explain move" button alongside the Lightning button
- Added `.explain-card` panel below the move list (hidden until first request)
- Panel shows: "Engine reasoning" label, "Asking Claude…" spinner while loading, explanation text, and the principal variation line
- Button is disabled during the request to prevent duplicate calls

### `tests/helpers.py`

Fixed `pos()` to initialize `castling` and `en_passant` attributes, which `board.py` gained when castling and en passant support was added. Without this fix, 30 of 45 tests failed with `AttributeError: 'Board' object has no attribute 'castling'`.

---

## Design Notes

**Why the PV makes explanations more accurate**
A naive approach — just asking Claude "why is e2e4 good?" — produces plausible-sounding but invented chess reasoning. By passing the actual principal variation, the evaluation score, and the scored alternatives, Claude's explanation is grounded in what the engine actually computed. The explanation can reference specific continuations ("after b1c3 Black likely responds b8c6, and White follows with g1f3") rather than generic principles.

**Limitation: alpha-beta pruning hides rejected lines**
The engine cannot explain *why* it rejected pruned branches — those were never evaluated. The explanation covers the best line found and why the top candidates were ranked as they were, but not every move considered.

**Model choice**
`claude-haiku-4-5-20251001` is used for low latency (explanation appears in ~1–2 seconds). The prompt is ~250 tokens; responses are capped at 300 tokens.

---

## Usage

Start the server with an API key:
```
ANTHROPIC_API_KEY=sk-ant-... venv/bin/python server.py
```

Click "Explain move" at any point in a game. The feature works for both Human vs Engine and Engine vs Engine modes, and reflects the current board state at the time of the click.

---

## Test Results

All 45 existing tests pass after the `helpers.py` fix:
```
Ran 45 tests in 0.17s
OK

Engine move-choice score: 20/20
```
