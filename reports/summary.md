# Code Cleanliness — Branch Ranking

| Rank | Branch | Score | One-line verdict |
|---|---|---|---|
| 1 | `feat/novelty` | 8 / 10 | Clean, consistent, only fully runnable branch |
| 2 | `nathan` | 7 / 10 | Best engine abstraction, no web server |
| 3 | `main` | 6 / 10 | Clean core, broken server/engine interface |
| 4 | `niranjan-engine` | 6 / 10 | Server works, KL divergence pipeline complete, board.py incomplete |
| 4 | `niranjan/ai-org-engine` | 5 / 10 | Most sophisticated novelty system, evaluate_novelty.py broken |

---

## `feat/novelty` — 8/10

The cleanest and only fully runnable branch. `engine.py` and `server.py` have matching signatures, imports are consistent relative-style throughout `BasicEngine/`, `board.py` has full castling and en passant, and the opening book and noise parameter are wired end-to-end without unnecessary complexity. Minor issues: a duplicate `_move_to_uci_key` function and a dead `random_move` that can be deleted in minutes.

**See:** [reports/feat-novelty.md](feat-novelty.md)

---

## `nathan` — 7/10

The cleanest internal engine architecture. `evaluate_root_moves` is the best selector interface in the repo — exact full-window scores, sorted by side preference — and `discomfort_move.py` builds on it with a principled `eval_floor + λ·discomfort` formula. `to_pgn.py` is production-quality. Held back by a `debug=True` default that spams stdout, the complete absence of a web server, and the older `board.py` without castling.

**See:** [reports/nathan.md](nathan.md)

---

## `main` — 6/10

A solid foundation let down by one critical runtime bug: `server.py` calls `best_move` with `history=` and `noise=` keyword arguments that the current `engine.py` doesn't accept, so every game request crashes. Also has dead code (`_rule_based_explanation`, `human_novelty_engine.py`) and inconsistent import conventions across `BasicEngine/`.

**See:** [reports/main.md](main.md)

---

## `niranjan-engine` — 6/10

The server works — `ENGINE_DIR` correctly points to `BasicEngine/` and the KL divergence novelty pipeline (`server.py` → `novelty_engine.py` → `human_model.py`) is complete and wired end-to-end. `lichess_bot.py` is the cleanest file in the repo. Held back by a `board_to_fen` function that hardcodes castling rights in every Lichess API query (producing wrong move frequencies mid-game), `board.py` missing castling/en passant, and `critical_point.py` being fully disconnected from the server pipeline.

**See:** [reports/niranjan-engine.md](niranjan-engine.md)

---

## `niranjan/ai-org-engine` — 5/10

The most ambitious novelty system: `pressure_detector.py` scores six board features, `rare_move_selector.py` computes an 18-field `MoveFeatures` per move, and `pressure_novelty_engine.py` integrates them cleanly. `server.py` actually resolves to a real path and runs. But `evaluate_novelty.py` (the benchmark script) is broken in three independent ways — wrong attribute name (`board.board` vs `board.squares`), missing `uci` module, missing `HumanNoveltyEngine` — and the try/except import pattern appears in every file.

**See:** [reports/niranjan-ai-org-engine.md](niranjan-ai-org-engine.md)

---

## Issues common to all branches

- **`board.py` divergence** — `feat/novelty` and `main` have the complete version with castling and en passant; the other three branches have an older version that silently generates wrong positions
- **Bare imports in `BasicEngine/`** — every branch except `feat/novelty` mixes `from board import` inside the package with `from BasicEngine.board import` outside it
- **`random_move` dead code** — defined in `engine.py` on every branch, called on none
- **No shared UCI parsing** — `server.py` and `uci_bridge.py`/`uci_bridge` re-implement the same coordinate conversion independently on every branch that has both
