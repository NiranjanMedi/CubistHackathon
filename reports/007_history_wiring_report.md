# History Wiring — Implementation Report

## Summary

Updated `server.py` to pass `_history` and `noise=80` to `best_move` when lightning mode is active. This connects the UI toggle to the opening book (which needs the move sequence) and to the noise parameter (which makes play variable).

---

## Files Changed

### `server.py`

**`/api/move` endpoint** — reads `mode` from the request body and conditionally passes history and noise:

```python
lightning = data.get("mode") == "lightning"
if _board.legal_moves():
    em = best_move(
        _board,
        depth=3,
        history=_history if lightning else None,
        noise=80 if lightning else 0,
    )
```

**`/api/engine_move` endpoint** — same pattern:

```python
lightning = data.get("mode") == "lightning"
em = best_move(
    _board,
    depth=3,
    history=_history if lightning else None,
    noise=80 if lightning else 0,
)
```

**`_history` list** — already maintained correctly; no structural changes required:

```python
_history = []          # list of UCI strings, append order

# in human_move():
_history.append(uci)   # human move
_history.append(euci)  # engine reply

# in _reset():
_history = []
```

---

## Design Notes

**Why `_history` works as-is**: the opening book uses `tuple(history)` as its key, where `history` is the full list of moves played by both sides in order. `_history` is already maintained in exactly this format — `['g2g4', 'd7d5', 'h2h3', ...]` — so no conversion is needed.

**Noise value 80**: chosen to produce ±80 centipawn variance at leaf nodes. This is roughly one pawn's positional value, enough to make the engine choose meaningfully different moves across games without causing frequent obvious blunders.

**Non-lightning path unchanged**: when `mode != "lightning"`, `history=None` and `noise=0` are passed, both of which are the defaults. The engine runs pure deterministic minimax, identical to its behaviour before these features were added.

**Lightning activates both features together**: opening book + noise are always coupled through the single `lightning` flag. This is intentional — the book steers into unusual positions, and the noise ensures those positions play out differently each time.
