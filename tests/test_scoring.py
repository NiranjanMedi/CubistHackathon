"""Aggregate scoring for engine move-choice tests.

Run this file directly:  python3 tests/test_scoring.py
It prints a human-readable score summary in addition to unittest results.
"""
import unittest
from BasicEngine.engine import best_move
from tests.helpers import pos, uci


# ---------------------------------------------------------------------------
# Each case: (label, board, best_moves, partial_pred, depth, note)
#   best_moves  – set of UCI strings that earn full credit
#   partial_pred – callable(move_uci) that returns True for partial credit
#   depth       – search depth to use
# ---------------------------------------------------------------------------

def _is_capture(board, m):
    if m is None:
        return False
    return board.squares[m.to_row][m.to_col] != '..'


def _is_promotion(m):
    return m is not None and m.promotion is not None


CASES = [
    (
        "capture hanging queen",
        pos({'h1': 'wK', 'a1': 'wR', 'a6': 'bQ', 'a8': 'bK'}),
        {'a1a6'},
        lambda b, m: _is_capture(b, m),
        3,
        "wR on a1 takes undefended bQ on a6",
    ),
    (
        "checkmate in one",
        pos({'c6': 'wK', 'b6': 'wQ', 'a8': 'bK'}),
        {'b6b7'},
        lambda b, m: _is_capture(b, m),
        3,
        "Qb7# — bK on a8 has no escape; wK defends b7",
    ),
    (
        "take free rook",
        pos({'e1': 'wK', 'd1': 'wQ', 'h5': 'bR', 'a8': 'bK'}),
        {'d1h5'},
        lambda b, m: _is_capture(b, m),
        3,
        "wQ takes undefended bR on h5 (diagonal)",
    ),
    (
        "promote pawn to queen",
        pos({'e1': 'wK', 'a7': 'wP', 'h8': 'bK'}),
        {'a7a8q'},
        lambda b, m: _is_promotion(m),
        3,
        "pawn on a7 promotes",
    ),
    (
        "escape check — return legal move",
        pos({'e1': 'wK', 'e8': 'bQ', 'a8': 'bK'}),
        None,           # any legal move is full credit
        lambda b, m: m is not None,
        2,
        "bQ checks wK on e1; engine must not crash",
    ),
    (
        "recapture rook",
        pos({'h1': 'wK', 'd1': 'wR', 'd5': 'bR', 'a8': 'bK'}),
        {'d1d5'},
        lambda b, m: _is_capture(b, m),
        3,
        "wR on d1 recaptures bR on d5",
    ),
    (
        "take free bishop with knight",
        pos({'h1': 'wK', 'd4': 'wN', 'f5': 'bB', 'a8': 'bK'}),
        {'d4f5'},
        lambda b, m: _is_capture(b, m),
        3,
        "wN on d4 takes undefended bB on f5",
    ),
    (
        "king takes adjacent hanging queen",
        pos({'e1': 'wK', 'd2': 'bQ', 'h8': 'bK'}),
        {'e1d2'},
        lambda b, m: _is_capture(b, m),
        2,
        "wK on e1 takes bQ on d2 (undefended)",
    ),
    (
        "knight forks king and rook",
        pos({'e1': 'wK', 'c3': 'wN', 'd5': 'bQ', 'a8': 'bK'}),
        {'c3d5'},
        lambda b, m: _is_capture(b, m),
        3,
        "wN takes undefended bQ on d5",
    ),
    (
        "knight smothered mate",
        pos({'a1': 'wK', 'e5': 'wN', 'h8': 'bK', 'g8': 'bR', 'g7': 'bP', 'h7': 'bP'}),
        {'e5f7'},
        lambda b, m: m is not None,
        3,
        "Nf7# — bK on h8 smothered; g7 pawn can't capture wN on f7",
    ),
]


def score_case(label, board, best_moves, partial_pred, depth, note):
    m = best_move(board, depth=depth)
    m_str = uci(m)
    if best_moves is None:
        # Full credit: any legal move
        if m is not None and m in board.legal_moves():
            return 2, 2, m_str
        return 0, 2, m_str
    if m_str in best_moves:
        return 2, 2, m_str
    if partial_pred(board, m):
        return 1, 2, m_str
    return 0, 2, m_str


class TestEngineScore(unittest.TestCase):
    """Each case runs as a separate test; the score is printed at the end."""

    @classmethod
    def setUpClass(cls):
        cls.results = []

    def _run(self, idx):
        label, board, best_moves, partial_pred, depth, note = CASES[idx]
        earned, total, chosen = score_case(label, board, best_moves, partial_pred, depth, note)
        self.__class__.results.append((label, earned, total, chosen, note))
        # Full credit → pass; partial or zero → fail with message
        self.assertEqual(
            earned, total,
            f"\n  Position : {label}\n  Note     : {note}\n  Chose    : {chosen}\n  Expected : {best_moves}",
        )

    def test_00_capture_hanging_queen(self):   self._run(0)
    def test_01_checkmate_in_one(self):        self._run(1)
    def test_02_take_free_rook(self):          self._run(2)
    def test_03_promote_pawn(self):            self._run(3)
    def test_04_escape_check(self):            self._run(4)
    def test_05_recapture_rook(self):          self._run(5)
    def test_06_take_free_bishop(self):        self._run(6)
    def test_07_king_takes_queen(self):        self._run(7)
    def test_08_knight_takes_queen(self):      self._run(8)
    def test_09_knight_smothered_mate(self):   self._run(9)

    @classmethod
    def tearDownClass(cls):
        if not cls.results:
            return
        earned_total = sum(e for _, e, _, _, _ in cls.results)
        max_total = sum(t for _, _, t, _, _ in cls.results)
        print(f"\n{'─'*56}")
        print(f"  Engine move-choice score: {earned_total}/{max_total}")
        for label, e, t, chosen, note in cls.results:
            mark = '✓' if e == t else ('~' if e > 0 else '✗')
            print(f"  {mark} [{e}/{t}] {label:35s} → {chosen}")
        print(f"{'─'*56}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
