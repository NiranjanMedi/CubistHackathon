"""
server.py – Flask API for the chess engine.
Run:  pip install flask flask-cors
      python server.py
"""

import json
import os
import threading
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from BasicEngine.board import Board, Move
from BasicEngine.engine import best_move, human_like_move, get_weights
from BasicEngine.tuner import tune_from_game

GAME_LOG_FILE = "game_logs.jsonl"

app = Flask(__name__)
CORS(app, origins="*")

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# ── helpers ──────────────────────────────────────────────────────────────────

def board_to_dict(board: Board) -> dict:
    """Serialise the board so the frontend can render it."""
    squares = {}
    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p != '..':
                squares[f"{r},{c}"] = p   # e.g. "wN", "bK"
    return {
        "squares": squares,
        "turn": board.turn,
    }


def uci_to_move(s: str) -> Move:
    """Parse a UCI string like 'e2e4' or 'e7e8q' into a Move."""
    col_of = lambda ch: ord(ch) - ord('a')
    row_of = lambda ch: 8 - int(ch)
    promo  = s[4].upper() if len(s) == 5 else None
    return Move(row_of(s[1]), col_of(s[0]),
                row_of(s[3]), col_of(s[2]),
                promotion=promo)


def move_to_uci(m: Move) -> str:
    files = 'abcdefgh'
    ranks = '87654321'
    s = f"{files[m.from_col]}{ranks[m.from_row]}{files[m.to_col]}{ranks[m.to_row]}"
    if m.promotion:
        s += m.promotion.lower()
    return s


# ── session state (in-memory; one game at a time) ────────────────────────────

_board   = Board()
_history = []          # list of UCI strings
_engine_thinking = False
_engine_move_result = None   # set by background thread when done
_state_lock = threading.Lock()

# ── training stats ────────────────────────────────────────────────────────────
_games_played = 0
_engine_wins  = 0
_human_ai_wins = 0


def _reset():
    global _board, _history, _engine_thinking, _engine_move_result
    _board   = Board()
    _history = []
    _engine_thinking = False
    _engine_move_result = None


def _game_result(board: Board):
    """Returns (winner_color_or_None, 'checkmate'|'stalemate'|None)."""
    legal = board.legal_moves()
    if legal:
        return None, None
    kr, kc = board.find_king(board.turn)
    opp = 'b' if board.turn == 'w' else 'w'
    if board.is_attacked(kr, kc, opp):
        return opp, 'checkmate'
    return None, 'stalemate'


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/api/state", methods=["GET"])
def get_state():
    """Return current board + whose turn + move history."""
    legal = [move_to_uci(m) for m in _board.legal_moves()]
    winner, result_type = _game_result(_board)
    return jsonify({
        **board_to_dict(_board),
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
    return jsonify({"ok": True, **board_to_dict(_board), "history": [], "legal_moves": legal, "is_over": False, "winner": None, "result_type": None})


@app.route("/api/move", methods=["POST"])
def human_move():
    """
    Apply a human move immediately and return. Engine reply is computed in the
    background — poll /api/engine_status to get it.
    Body: { "move": "e2e4", "mode": "lightning" }
    """
    global _engine_thinking, _engine_move_result

    data = request.get_json(force=True)
    uci  = data.get("move", "")

    with _state_lock:
        legal = _board.legal_moves()
        try:
            m = uci_to_move(uci)
        except Exception:
            return jsonify({"error": f"Cannot parse move: {uci}"}), 400

        if m not in legal:
            return jsonify({"error": "Illegal move"}), 400

        _board.make_move(m)
        _history.append(uci)

        winner, result_type = _game_result(_board)
        has_moves = bool(_board.legal_moves())

        result = {
            "human_move": uci,
            "engine_move": None,
            **board_to_dict(_board),
            "history": list(_history),
            "is_over": winner is not None or result_type == "stalemate",
            "legal_moves": [move_to_uci(mv) for mv in _board.legal_moves()],
            "winner": winner,
            "result_type": result_type,
            "engine_thinking": False,
        }

        if not has_moves or winner is not None or result_type == "stalemate":
            return jsonify(result)

        # Kick off engine computation in background
        lightning = data.get("mode") == "lightning"
        _engine_thinking = True
        _engine_move_result = None
        board_snapshot = _board.copy()
        history_snapshot = list(_history)

    def _think(board, history, lightning):
        global _engine_thinking, _engine_move_result
        em = best_move(board,
                       history=history,
                       time_limit_ms=600,
                       diversity_cp=25,
                       niche_bias=True)
        with _state_lock:
            _engine_move_result = move_to_uci(em) if em else None
            _engine_thinking = False

    threading.Thread(target=_think, args=(board_snapshot, history_snapshot, lightning), daemon=True).start()
    result["engine_thinking"] = True
    return jsonify(result)


@app.route("/api/engine_status", methods=["GET"])
def engine_status():
    """Poll this after /api/move. Returns engine_thinking=True while computing."""
    global _engine_thinking, _engine_move_result

    with _state_lock:
        if _engine_thinking:
            return jsonify({"engine_thinking": True})

        euci = _engine_move_result
        _engine_move_result = None

        if euci:
            em = uci_to_move(euci)
            _board.make_move(em)
            _history.append(euci)

        winner, result_type = _game_result(_board)
        return jsonify({
            "engine_thinking": False,
            "engine_move": euci,
            **board_to_dict(_board),
            "history": list(_history),
            "is_over": winner is not None or result_type == "stalemate",
            "legal_moves": [move_to_uci(m) for m in _board.legal_moves()],
            "winner": winner,
            "result_type": result_type,
        })


@app.route("/api/engine_move", methods=["POST"])
def engine_move():
    """Let the engine play one move (use this for engine-vs-engine mode)."""
    if not _board.legal_moves():
        return jsonify({"error": "Game over"}), 400

    data = request.get_json(force=True) or {}
    lightning = data.get("mode") == "lightning"
    em   = best_move(_board, history=_history, time_limit_ms=600, diversity_cp=25, niche_bias=True)
    euci = move_to_uci(em)
    _board.make_move(em)
    _history.append(euci)

    winner, result_type = _game_result(_board)
    return jsonify({
        "engine_move": euci,
        **board_to_dict(_board),
        "history": _history,
        "is_over":     winner is not None or result_type == 'stalemate',
        "legal_moves": [move_to_uci(m) for m in _board.legal_moves()],
        "winner":      winner,
        "result_type": result_type,
    })


@app.route("/api/human_ai_move", methods=["POST"])
def human_ai_move():
    """Human-like AI plays one move (used in Human AI vs Engine mode)."""
    if not _board.legal_moves():
        return jsonify({"error": "Game over"}), 400

    em = human_like_move(_board, history=_history)
    if not em:
        return jsonify({"error": "No moves"}), 400
    euci = move_to_uci(em)
    _board.make_move(em)
    _history.append(euci)

    winner, result_type = _game_result(_board)
    return jsonify({
        "engine_move": euci,
        **board_to_dict(_board),
        "history": list(_history),
        "is_over":     winner is not None or result_type == "stalemate",
        "legal_moves": [move_to_uci(m) for m in _board.legal_moves()],
        "winner":      winner,
        "result_type": result_type,
    })


@app.route("/api/log_game", methods=["POST"])
def log_game():
    """Save game log, run weight tuner, return updated stats."""
    global _games_played, _engine_wins, _human_ai_wins

    data = request.get_json(force=True) or {}
    history   = data.get("history", [])
    winner    = data.get("winner")
    result_type = data.get("result_type")
    mode      = data.get("mode", "unknown")

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "history": history,
        "winner": winner,
        "result_type": result_type,
        "mode": mode,
    }
    with open(GAME_LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    # Tune weights from this game (only for auto-train games)
    updated_weights = None
    if mode == "auto-train" and history:
        updated_weights = tune_from_game(history, winner)

    # Update stats
    _games_played += 1
    if winner == 'w':
        _engine_wins += 1
    elif winner == 'b':
        _human_ai_wins += 1

    return jsonify({
        "ok": True,
        "logged": len(history),
        "games_played": _games_played,
        "engine_wins": _engine_wins,
        "human_ai_wins": _human_ai_wins,
        "weights": updated_weights or get_weights(),
    })


@app.route("/api/weights", methods=["GET"])
def weights():
    """Return current evaluation weights and training stats."""
    return jsonify({
        "weights": get_weights(),
        "games_played": _games_played,
        "engine_wins": _engine_wins,
        "human_ai_wins": _human_ai_wins,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)