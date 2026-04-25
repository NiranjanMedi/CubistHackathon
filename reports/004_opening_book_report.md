# Opening Book — Implementation Report

## Summary

Added an unusual opening book to `BasicEngine/engine.py` keyed on move history tuples. The book steers the engine into niche lines (Grob's Attack, Owen's Defense, Dutch-ish lines) that casual players are unlikely to have studied.

---

## Files Changed

### `BasicEngine/engine.py`

**`OPENING_BOOK` dict** added near the top of the file:

```python
OPENING_BOOK: dict[tuple, str] = {
    # Grob's Attack (White): 1.g4
    (): 'g2g4',
    ('g2g4', 'd7d5'): 'h2h3',
    ('g2g4', 'e7e5'): 'h2h3',
    ('g2g4', 'c7c5'): 'h2h3',
    ('g2g4', 'd7d5', 'h2h3', 'e7e5'): 'f1g2',
    ('g2g4', 'e7e5', 'h2h3', 'd7d5'): 'f1g2',
    # Owen's Defense replies (Black)
    ('e2e4',): 'b7b6',
    ('d2d4',): 'f7f5',
    ('c2c4',): 'b7b6',
    ('b2b4',): 'e7e5',
    ('e2e4', 'b7b6', 'd2d4'): 'c8b7',
    ('d2d4', 'f7f5', 'c2c4'): 'g8f6',
    ('d2d4', 'f7f5', 'g1f3'): 'g8f6',
}
```

**`best_move` signature updated** to accept `history=None`:

```python
def best_move(board, depth=3, history=None, noise=0):
    if history is not None:
        book_uci = OPENING_BOOK.get(tuple(history))
        if book_uci:
            legal_ucis = {_move_to_uci_key(m): m for m in board.legal_moves()}
            if book_uci in legal_ucis:
                return legal_ucis[book_uci]
    # ... fall through to minimax
```

A helper `_move_to_uci_key(m)` converts a `Move` object to a UCI string for the legality check.

---

## Design Notes

**Key format**: tuples of UCI strings in play order — `('g2g4', 'd7d5')` means White played g4, Black replied d5. The empty tuple `()` matches the very first move of any game.

**Legality guard**: the book move is only returned if it appears in `board.legal_moves()`. This prevents crashes if the board state diverges from what the book expects (e.g. the caller passed a wrong history).

**Opening choices**: Grob's Attack (1.g4) is objectively dubious but deeply unfamiliar to club players. Owen's Defense (1…b6) and the Dutch irregular (1…f5) are chosen for the same reason — rare enough that opponents won't have prepared responses.

**No effect when `history=None`**: the lookup is skipped entirely, so callers that don't pass history get pure minimax as before.
