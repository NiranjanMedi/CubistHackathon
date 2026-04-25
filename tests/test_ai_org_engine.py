"""
Unit tests for the AI Org Engine (HumanNoveltyEngine + supporting components).

Tests cover:
1. Move legality — all returned moves are legal, illegal moves are rejected
2. Move quality — engine plays sensible moves (captures free pieces, avoids blunders,
   finds checkmate, promotes pawns, defends against immediate threats)
"""

import sys
import unittest
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1] / "BasicEngine"
sys.path.insert(0, str(ENGINE_DIR))
for module_name in (
    "board", "engine", "novelty_engine", "human_model",
    "critical_point", "human_novelty_engine",
):
    sys.modules.pop(module_name, None)

from board import Board, Move, EMPTY
from engine import best_move, evaluate, score_legal_moves
from human_novelty_engine import HumanNoveltyEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_uci(uci: str) -> Move:
    files = "abcdefgh"
    ranks = "87654321"
    from_col = files.index(uci[0])
    from_row = ranks.index(uci[1])
    to_col = files.index(uci[2])
    to_row = ranks.index(uci[3])
    promo = uci[4:].upper() or None
    return Move(from_row, from_col, to_row, to_col, promo)


def play_moves(uci_list):
    board = Board()
    for uci in uci_list:
        board.make_move(parse_uci(uci))
    return board


def empty_board(pieces: dict, turn: str = "w") -> Board:
    board = Board.__new__(Board)
    board.squares = [[EMPTY] * 8 for _ in range(8)]
    board.turn = turn
    board.castling_rights = set()
    board.ep_target = None
    for sq, piece in pieces.items():
        col = ord(sq[0]) - ord("a")
        row = 8 - int(sq[1])
        board.squares[row][col] = piece
    return board


# ---------------------------------------------------------------------------
# 1. Move legality
# ---------------------------------------------------------------------------

class TestMoveLegality(unittest.TestCase):
    """All moves returned by legal_moves() must leave the king safe."""

    def _assert_all_legal(self, board: Board):
        for move in board.legal_moves():
            nb = board.copy()
            nb.make_move(move)
            opp = nb.turn
            kr, kc = nb.find_king(board.turn)
            self.assertFalse(
                nb.is_attacked(kr, kc, opp),
                f"Move {move} leaves {board.turn} king in check",
            )

    def test_starting_position_all_legal(self):
        self._assert_all_legal(Board())

    def test_after_e4_e5_all_legal(self):
        self._assert_all_legal(play_moves(["e2e4", "e7e5"]))

    def test_in_check_only_blocking_moves_generated(self):
        # Scholar's mate threat — black queen checks white king via f2
        board = play_moves(["e2e4", "e7e5", "f1c4", "d8h4", "g1f3", "h4f2"])
        legal_ucis = {str(m) for m in board.legal_moves()}
        # White king must move or block — no normal moves allowed
        for m in board.legal_moves():
            nb = board.copy()
            nb.make_move(m)
            kr, kc = nb.find_king("w")
            self.assertFalse(nb.is_attacked(kr, kc, "b"), f"{m} leaves king in check")

    def test_pinned_piece_cannot_expose_king(self):
        # White bishop on e2 is pinned by black bishop on a6 (via d3) — simplified pin
        # Place: wK e1, wR e4 (pinned by bQ e8), bK a8
        board = empty_board({
            "e1": "wK",
            "e4": "wR",   # pinned on the e-file by bQ
            "e8": "bQ",
            "a8": "bK",
        }, turn="w")
        board.castling_rights = set()
        legal_ucis = {str(m) for m in board.legal_moves()}
        # Rook starts on e4: any legal move whose from-square is e4 must stay on the e-file
        illegal_rook_moves = {uci for uci in legal_ucis
                              if uci[:2] == "e4" and uci[2] != "e"}
        self.assertEqual(illegal_rook_moves, set(),
                         "Pinned rook should not be able to move off the e-file")

    def test_castling_not_generated_through_check(self):
        # White king-side castling is blocked because f1 is attacked
        board = empty_board({
            "e1": "wK",
            "h1": "wR",
            "f8": "bR",   # attacks f1
            "e8": "bK",
        }, turn="w")
        board.castling_rights = {"K"}
        legal_ucis = {str(m) for m in board.legal_moves()}
        self.assertNotIn("e1g1", legal_ucis,
                         "Should not castle king-side when f1 is attacked")

    def test_en_passant_is_legal(self):
        board = play_moves(["e2e4", "a7a6", "e4e5", "d7d5"])
        legal_ucis = {str(m) for m in board.legal_moves()}
        self.assertIn("e5d6", legal_ucis)

    def test_stalemate_has_no_legal_moves(self):
        # Classic stalemate: black king trapped, not in check
        board = empty_board({
            "a8": "bK",
            "b6": "wK",
            "c7": "wQ",
        }, turn="b")
        self.assertEqual(board.legal_moves(), [])

    def test_promotion_moves_all_legal(self):
        # White pawn on a7, no obstacles
        board = empty_board({
            "a7": "wP",
            "e1": "wK",
            "e8": "bK",
        }, turn="w")
        legal_ucis = {str(m) for m in board.legal_moves()}
        # UCI promotion format: {from}{to}{piece} e.g. a7a8q
        for promo in ("a7a8q", "a7a8r", "a7a8b", "a7a8n"):
            self.assertIn(promo, legal_ucis)

    def test_human_novelty_engine_returns_legal_move_starting(self):
        board = Board()
        engine = HumanNoveltyEngine()
        decision = engine.choose_move(board, move_count=0)
        self.assertIsNotNone(decision.move)
        self.assertIn(decision.move, board.legal_moves())

    def test_human_novelty_engine_returns_legal_move_middlegame(self):
        board = play_moves([
            "e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6",
            "d2d3", "f8c5", "c2c3", "d7d6",
        ])
        engine = HumanNoveltyEngine()
        decision = engine.choose_move(board, move_count=5)
        self.assertIsNotNone(decision.move)
        self.assertIn(decision.move, board.legal_moves())

    def test_best_move_never_returns_illegal_move(self):
        # Run best_move across several positions and verify legality each time
        positions = [
            [],
            ["e2e4", "e7e5"],
            ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6"],
        ]
        for uci_list in positions:
            board = play_moves(uci_list)
            move = best_move(board, depth=2)
            if move is not None:
                self.assertIn(move, board.legal_moves(),
                              f"best_move returned illegal move {move} in position {uci_list}")


# ---------------------------------------------------------------------------
# 2. Move quality
# ---------------------------------------------------------------------------

class TestMoveQuality(unittest.TestCase):
    """Engine should make objectively sound decisions in clear-cut positions."""

    def test_captures_free_queen(self):
        # White can capture an undefended black queen
        board = empty_board({
            "e1": "wK",
            "d4": "wR",
            "d8": "bQ",   # undefended, on same file as wR
            "h8": "bK",
        }, turn="w")
        move = best_move(board, depth=2)
        self.assertEqual(str(move), "d4d8",
                         "Engine should capture the free queen")

    def test_finds_checkmate_in_one(self):
        # Fool's mate: black to play Qh4#
        board = play_moves(["f2f3", "e7e5", "g2g4"])
        # board.turn is now 'b'
        move = best_move(board, depth=2)
        self.assertEqual(str(move), "d8h4",
                         "Engine should find Qh4# (checkmate in one)")

    def test_avoids_losing_queen_for_nothing(self):
        # White queen on d1, undefended black pawn on a4 — but moving queen to a4
        # would hang it to a black rook on a8
        board = empty_board({
            "e1": "wK",
            "d1": "wQ",
            "a8": "bR",   # controls the a-file
            "a4": "bP",   # tempting pawn but taking it drops queen to bR
            "h8": "bK",
        }, turn="w")
        move = best_move(board, depth=3)
        # Queen should NOT go to a4 (hanging to rook on a8)
        self.assertNotEqual(str(move), "d1a4",
                            "Engine should not hang the queen on a4")

    def test_promotes_pawn_to_queen(self):
        # White pawn on a7 with a clear path — should promote to queen
        board = empty_board({
            "a7": "wP",
            "e1": "wK",
            "e8": "bK",
        }, turn="w")
        move = best_move(board, depth=2)
        self.assertIsNotNone(move)
        self.assertEqual(move.promotion, "Q",
                         "Should promote the passed pawn to a queen")

    def test_defends_against_checkmate_threat(self):
        # Black queen threatens Qxf2# (checkmate). White must defend.
        board = play_moves(["e2e4", "e7e5", "f1c4", "d8h4"])
        # White is under threat of Qxf2# — must block or move king or interpose
        move = best_move(board, depth=3)
        self.assertIsNotNone(move)
        nb = board.copy()
        nb.make_move(move)
        # After white's reply, Qxf2 should not be checkmate
        # i.e. if black plays Qxf2, white king is not mated (has escape or it's not even check)
        qxf2 = parse_uci("h4f2")
        if qxf2 in nb.legal_moves():
            nb2 = nb.copy()
            nb2.make_move(qxf2)
            # Should not be checkmate
            self.assertTrue(
                len(nb2.legal_moves()) > 0,
                "White should have defended the f2 checkmate threat",
            )

    def test_does_not_blunder_starting_material(self):
        # In the starting position, any move should not immediately lose material
        board = Board()
        eval_before = evaluate(board)
        move = best_move(board, depth=2)
        self.assertIsNotNone(move)
        nb = board.copy()
        nb.make_move(move)
        eval_after = evaluate(nb)
        # White should not immediately drop a piece (>= -150 cp loss after one move)
        self.assertGreater(eval_after, eval_before - 150,
                           "Opening move should not lose significant material")

    def test_rook_captures_hanging_rook(self):
        board = empty_board({
            "e1": "wK",
            "a1": "wR",
            "a8": "bR",   # undefended
            "h8": "bK",
        }, turn="w")
        move = best_move(board, depth=2)
        self.assertEqual(str(move), "a1a8",
                         "Should capture the hanging rook")

    def test_score_legal_moves_returns_all_moves(self):
        board = Board()
        scored = score_legal_moves(board, depth=1)
        legal = set(board.legal_moves())
        self.assertEqual(set(scored.keys()), legal,
                         "score_legal_moves should score every legal move")

    def test_human_novelty_engine_mode_is_valid(self):
        board = Board()
        engine = HumanNoveltyEngine()
        decision = engine.choose_move(board, move_count=0)
        self.assertIn(decision.mode, {"engine", "novelty"},
                      "Decision mode must be one of the expected values")

    def test_human_novelty_engine_in_check_plays_legal_move(self):
        # White king is in check — engine must play a legal move
        board = empty_board({
            "e1": "wK",
            "e8": "bR",   # gives check
            "h8": "bK",
        }, turn="w")
        engine = HumanNoveltyEngine()
        decision = engine.choose_move(board, move_count=10)
        self.assertIsNotNone(decision.move)
        self.assertIn(decision.move, board.legal_moves(),
                      "Engine must play a legal move when in check")


if __name__ == "__main__":
    unittest.main(verbosity=2)
