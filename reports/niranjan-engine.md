# Code Cleanliness Report — `niranjan-engine`

**Overall score: 6 / 10**

## Summary

The previous report incorrectly stated that `server.py` was broken due to a hardcoded `lichess-bot/engines/novelty/` path. That is wrong — the actual `server.py` on this branch correctly sets `ENGINE_DIR = Path(__file__).resolve().parent / "BasicEngine"` and imports cleanly from `novelty_engine`. The server runs. The novelty pipeline (`server.py` → `novelty_engine.py` → `human_model.py`) is complete and wired end-to-end. The real issues are a `board.py` missing castling and en passant, a `board_to_fen` function that hardcodes castling rights (producing incorrect API lookups mid-game), and a silent exception swallow in `human_model.py`.

---

## Strengths

- **`server.py` works out of the box.** `ENGINE_DIR` resolves to `BasicEngine/`, all imports succeed, and the engine replies use `analyze_position` + `get_novel_move` from `novelty_engine.py`. The response shape includes `engine_mode`, `kl_divergence`, and `novelty_score` fields the frontend can render.
- **`novelty_engine.py` is mathematically precise.** `get_engine_distribution` (softmax over centipawn scores), `compute_kl_divergence` (KL(Engine ∥ Human)), and `score_move_novelty` (engine_prob / human_prob ratio) are all clearly named and do exactly what they say.
- **`human_model.py` handles API/fallback cleanly.** The heuristic fallback (central pawn preference, development bonuses, capture weight) fires transparently when no `LICHESS_API_TOKEN` is set. The in-memory cache avoids repeated API calls for the same FEN.
- **`lichess_bot.py`** is the standout file: clean class structure, proper error handling, structured logging with `logging.basicConfig`, and correct use of threading for concurrent games.
- **`uci_bridge.py`** is small, focused, and does exactly one thing.

---

## Biggest Issues

### 1. `board_to_fen` always hardcodes full castling rights

`human_model.py:54`:
```python
fen += 'KQkq - 0 1'  # Simplified: assume all castling, no en passant
```
The FEN sent to the Lichess Opening Explorer always claims all four castling rights and no en passant, regardless of actual game state. This causes incorrect API lookups for any position beyond the first few moves — the database will return wrong move frequencies. The comment acknowledges this, but it's a correctness issue for the core feature of this branch.

### 2. `board.py` missing castling and en passant

`Board.__init__` sets only `self.squares` and `self.turn`. There is no `castling` dict, no `en_passant` attribute, and no `castling_moves()`. `main`'s `board.py` has the complete implementation. Any game reaching a castling or en passant position will generate incorrect legal move sets.

### 3. Silent `except Exception` in `human_model.py`

`human_model.py:81-83`:
```python
except Exception as e:
    # Silently fall back to heuristic
    return None
```
`e` is captured but never used. The comment says "silently" but this swallows network timeouts, JSON parse errors, and auth failures identically. The heuristic fallback is reasonable, but at minimum the exception type should be logged.

### 4. `critical_point.py` is disconnected from the server pipeline

`server.py` imports `novelty_engine.analyze_position` and `get_novel_move`. `novelty_engine.py` imports only from `human_model`. `critical_point.py` is never in this chain — it's only used by `uci.py` (Lichess UCI bridge) and the `demo_critical_point.py`/`test_pipeline.py` scripts. The `===` banner comments and 300 lines of code in `critical_point.py` have no effect on what the web server does. The branch has two parallel novelty approaches (KL divergence in `novelty_engine` vs discomfort in `critical_point`) and the server uses only one.

### 5. Duplicate UCI parsing logic

`uci_bridge.py` implements `parse_uci` and `board_from_moves`. `server.py` implements `uci_to_move` and `move_to_uci` doing the same coordinate conversion. `lichess_bot.py` uses `uci_bridge`; `server.py` ignores it.

### 6. Step comments in `get_novel_move` restate what the code says

`novelty_engine.py:131-136`:
```python
# Step 1: Get engine distribution
engine_dist = get_engine_distribution(board)

# Step 2: Get human distribution
human_dist = get_human_distribution(board)

# Step 3: Compute KL divergence
kl = compute_kl_divergence(engine_dist, human_dist)
```
The function docstring already enumerates these steps. The variable names and function calls are self-explanatory without comments.

---

## Concrete Examples

| File | Line(s) | Issue |
|---|---|---|
| `BasicEngine/human_model.py` | 54 | `'KQkq - 0 1'` hardcoded — FEN incorrect mid-game |
| `BasicEngine/human_model.py` | 81 | `except Exception as e` with `e` unused, no logging |
| `BasicEngine/board.py` | entire file | No castling, no en passant |
| `BasicEngine/critical_point.py` | entire file | Disconnected from server pipeline |
| `BasicEngine/uci_bridge.py` + `server.py` | both | Duplicate UCI coordinate conversion |
| `BasicEngine/novelty_engine.py` | 131–136 | Step comments restate what the code says |

---

## Top Cleanup Recommendations

1. **Fix `board_to_fen`** — use the actual `castling` dict from `board.py` (after updating it) to emit correct castling rights; add en passant square.
2. **Update `board.py`** to `main`'s version with castling and en passant.
3. **Log the exception** in `human_model.py`'s `except` block — even `logging.debug(e)` would help.
4. **Consolidate UCI parsing** — delete `server.py`'s `uci_to_move`/`move_to_uci` and import from `uci_bridge.py` instead.
5. **Remove the step comments** in `get_novel_move` — the docstring and code already explain the algorithm.
