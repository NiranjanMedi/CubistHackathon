Inspect the current chess engine project and add an interpretability feature that explains why the engine chose its move.

Goal:
Make the engine’s decision understandable to a user by exposing the search data behind the move and generating a short natural-language explanation.

Important constraints:
- Do not rewrite the chess engine.
- Preserve the existing move validation and search logic unless you find a clear bug.
- Keep the change focused and easy to review.
- Do not add large dependencies.
- The explanation should be grounded in actual engine data, not generic chess advice.

Please implement:

1. Engine analysis function

Add or improve an `analyze(board, depth=3)` style function that returns structured data about the engine’s decision.

It should include:
- Best move
- Evaluation score
- Principal variation / best line if available
- Top candidate moves with scores
- Nodes searched and time taken if available

Example output shape:

```json
{
  "best_move": "e2e4",
  "eval": 35,
  "pv": ["e2e4", "e7e5", "g1f3"],
  "alternatives": [
    {"move": "e2e4", "score": 35},
    {"move": "d2d4", "score": 22},
    {"move": "g1f3", "score": 18}
  ],
  "nodes": 12345,
  "time_ms": 210
}