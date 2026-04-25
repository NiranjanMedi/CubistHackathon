"""Flask API for playing the tracked BasicEngine novelty engine."""

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

ENGINE_DIR = Path(__file__).resolve().parent / "BasicEngine"
sys.path.insert(0, str(ENGINE_DIR))

from board import Board, Move
from novelty_engine import analyze_position, get_novel_move

app = Flask(__name__)
CORS(app, origins="*")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


def board_to_dict(board: Board) -> dict:
    """Serialise the board so the frontend can render it."""
    squares = {}
    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p != "..":
                squares[f"{r},{c}"] = p
    return {
        "squares": squares,
        "turn": board.turn,
    }


def uci_to_move(s: str) -> Move:
    """Parse a UCI string like 'e2e4' or 'e7e8q' into a Move."""
    col_of = lambda ch: ord(ch) - ord("a")
    row_of = lambda ch: 8 - int(ch)
    promo = s[4].upper() if len(s) == 5 else None
    return Move(
        row_of(s[1]),
        col_of(s[0]),
        row_of(s[3]),
        col_of(s[2]),
        promotion=promo,
    )


def move_to_uci(m: Move) -> str:
    files = "abcdefgh"
    ranks = "87654321"
    s = f"{files[m.from_col]}{ranks[m.from_row]}{files[m.to_col]}{ranks[m.to_row]}"
    if m.promotion:
        s += m.promotion.lower()
    return s


_board = Board()
_history = []


def _reset():
    global _board, _history
    _board = Board()
    _history = []


def _game_result(board: Board):
    """Returns (winner_color_or_None, 'checkmate'|'stalemate'|None)."""
    legal = board.legal_moves()
    if legal:
        return None, None
    kr, kc = board.find_king(board.turn)
    opp = "b" if board.turn == "w" else "w"
    if board.is_attacked(kr, kc, opp):
        return opp, "checkmate"
    return None, "stalemate"


def _engine_decision():
    analysis = analyze_position(_board)
    move = get_novel_move(_board)
    return {
        "move": move,
        "analysis": analysis,
        "mode": "novelty" if analysis.get("is_novelty_position") else "base",
        "reason": (
            "KL divergence crossed novelty threshold"
            if analysis.get("is_novelty_position")
            else "KL divergence below novelty threshold"
        ),
    }


def _decision_metadata(decision):
    analysis = decision.get("analysis", {})
    return {
        "engine_mode": decision.get("mode", "base"),
        "engine_reason": decision.get("reason", ""),
        "critical": bool(analysis.get("is_novelty_position", False)),
        "critical_score": analysis.get("kl_divergence", 0.0),
        "novelty_score": analysis.get("kl_divergence", 0.0),
        "cp_loss": 0,
        "tags": [f"KL divergence: {analysis.get('kl_divergence', 0.0):.3f}"],
        "rarity_score": analysis.get("kl_divergence", 0.0),
        "engine_variant": "basic_novelty",
    }


@app.route("/api/state", methods=["GET"])
def get_state():
    """Return current board + whose turn + move history."""
    legal = [move_to_uci(m) for m in _board.legal_moves()]
    winner, result_type = _game_result(_board)
    return jsonify({
        **board_to_dict(_board),
        "engine_variant": "basic_novelty",
        "history": _history,
        "legal_moves": legal,
        "is_over": len(legal) == 0,
        "winner": winner,
        "result_type": result_type,
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    """Start a fresh game."""
    _reset()
    legal = [move_to_uci(m) for m in _board.legal_moves()]
    return jsonify({
        "ok": True,
        **board_to_dict(_board),
        "history": [],
        "legal_moves": legal,
        "is_over": False,
        "winner": None,
        "result_type": None,
    })


@app.route("/api/move", methods=["POST"])
def human_move():
    """
    Apply a human move (sent as UCI string) then let the engine reply.
    Body: { "move": "e2e4" }
    """
    data = request.get_json(force=True)
    uci = data.get("move", "")
    legal = _board.legal_moves()

    try:
        m = uci_to_move(uci)
    except Exception:
        return jsonify({"error": f"Cannot parse move: {uci}"}), 400

    if m not in legal:
        return jsonify({"error": "Illegal move"}), 400

    _board.make_move(m)
    _history.append(uci)

    result = {
        "human_move": uci,
        "engine_move": None,
        **board_to_dict(_board),
        "history": _history,
    }

    if _board.legal_moves():
        decision = _engine_decision()
        em = decision["move"]
        if em:
            euci = move_to_uci(em)
            _board.make_move(em)
            _history.append(euci)
            result["engine_move"] = euci
            result.update(_decision_metadata(decision))
            result.update(board_to_dict(_board))
            result["history"] = _history

    winner, result_type = _game_result(_board)
    result["is_over"] = winner is not None or result_type == "stalemate"
    result["legal_moves"] = [move_to_uci(m) for m in _board.legal_moves()]
    result["winner"] = winner
    result["result_type"] = result_type
    return jsonify(result)


@app.route("/api/engine_move", methods=["POST"])
def engine_move():
    """Let the engine play one move (use this for engine-vs-engine mode)."""
    if not _board.legal_moves():
        return jsonify({"error": "Game over"}), 400

    decision = _engine_decision()
    em = decision["move"]
    if em is None:
        return jsonify({"error": "No engine move found"}), 400
    euci = move_to_uci(em)
    _board.make_move(em)
    _history.append(euci)

    winner, result_type = _game_result(_board)
    return jsonify({
        "engine_move": euci,
        **_decision_metadata(decision),
        **board_to_dict(_board),
        "history": _history,
        "is_over": winner is not None or result_type == "stalemate",
        "legal_moves": [move_to_uci(m) for m in _board.legal_moves()],
        "winner": winner,
        "result_type": result_type,
    })


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))
