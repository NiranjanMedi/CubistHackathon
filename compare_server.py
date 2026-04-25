"""Comparison server: Baseline engine (left) vs Novelty engine (right)."""

import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

ENGINE_DIR = Path(__file__).resolve().parent / "BasicEngine"
sys.path.insert(0, str(ENGINE_DIR))

from board import Board, Move
from engine import best_move
from human_novelty_engine import HumanNoveltyEngine

app = Flask(__name__)
CORS(app, origins="*")

# ── helpers ───────────────────────────────────────────────────────────────────

def board_to_dict(board: Board) -> dict:
    squares = {}
    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p != '..':
                squares[f"{r},{c}"] = p
    return {"squares": squares, "turn": board.turn}


def uci_to_move(s: str) -> Move:
    col_of = lambda ch: ord(ch) - ord('a')
    row_of = lambda ch: 8 - int(ch)
    promo = s[4].upper() if len(s) == 5 else None
    return Move(row_of(s[1]), col_of(s[0]), row_of(s[3]), col_of(s[2]), promotion=promo)


def move_to_uci(m: Move) -> str:
    files = 'abcdefgh'
    ranks = '87654321'
    s = f"{files[m.from_col]}{ranks[m.from_row]}{files[m.to_col]}{ranks[m.to_row]}"
    return s + m.promotion.lower() if m.promotion else s


def game_result(board: Board):
    legal = board.legal_moves()
    if legal:
        return None, None
    kr, kc = board.find_king(board.turn)
    opp = 'b' if board.turn == 'w' else 'w'
    if board.is_attacked(kr, kc, opp):
        return opp, 'checkmate'
    return None, 'stalemate'


def serialise(board: Board, history: list) -> dict:
    winner, rt = game_result(board)
    legal = board.legal_moves()
    return {
        **board_to_dict(board),
        "history": history,
        "legal_moves": [move_to_uci(m) for m in legal],
        "is_over": winner is not None or rt == 'stalemate',
        "winner": winner,
        "result_type": rt,
    }


# ── session state ─────────────────────────────────────────────────────────────

_board_a = Board()
_board_b = Board()
_history_a: list[str] = []
_history_b: list[str] = []
_novelty = HumanNoveltyEngine(opponent_rating=1500)


def _reset():
    global _board_a, _board_b, _history_a, _history_b
    _board_a = Board()
    _board_b = Board()
    _history_a = []
    _history_b = []


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "compare.html")


@app.route("/api/state")
def state():
    return jsonify({
        "a": serialise(_board_a, _history_a),
        "b": serialise(_board_b, _history_b),
    })


@app.route("/api/move", methods=["POST"])
def move():
    data = request.get_json(force=True)
    uci = data.get("move", "")
    try:
        m = uci_to_move(uci)
    except Exception:
        return jsonify({"error": f"Cannot parse move: {uci}"}), 400

    if m not in _board_a.legal_moves():
        return jsonify({"error": "Illegal move"}), 400

    result = {}

    # ── board A: human move then baseline reply ───────────────────────────────
    _board_a.make_move(m)
    _history_a.append(uci)
    if _board_a.legal_moves():
        em = best_move(_board_a, depth=3)
        if em:
            euci = move_to_uci(em)
            _board_a.make_move(em)
            _history_a.append(euci)
            result["a_engine_move"] = euci
            result["a_engine_mode"] = "minimax"

    # ── board B: same human move then novelty reply ───────────────────────────
    if m in _board_b.legal_moves():
        _board_b.make_move(m)
        _history_b.append(uci)
        if _board_b.legal_moves():
            decision = _novelty.choose_move(_board_b, move_count=len(_history_b) // 2)
            if decision.move:
                euci = move_to_uci(decision.move)
                _board_b.make_move(decision.move)
                _history_b.append(euci)
                result["b_engine_move"] = euci
                result["b_engine_mode"] = decision.mode
                result["b_engine_reason"] = decision.reason

    result["a"] = serialise(_board_a, _history_a)
    result["b"] = serialise(_board_b, _history_b)
    return jsonify(result)


@app.route("/api/reset", methods=["POST"])
def reset():
    _reset()
    return jsonify({
        "a": serialise(_board_a, _history_a),
        "b": serialise(_board_b, _history_b),
    })


if __name__ == "__main__":
    app.run(debug=True, port=8000)
