"""
Lichess bot client for the novelty chess engine.

Setup:
    pip install requests
    export LICHESS_BOT_TOKEN=<your OAuth token with bot:play scope>
    python lichess_bot.py

The bot account must already be upgraded to a bot account on lichess.org.
Generate a token at: https://lichess.org/account/oauth/token
Required scope: bot:play
"""

import os
import sys
import json
import logging
import threading
import time

import requests

# Make BasicEngine importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BasicEngine'))

from uci_bridge import board_from_moves
from novelty_engine import get_novel_move
from engine import best_move as engine_best_move

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger(__name__)

LICHESS_HOST = "https://lichess.org"
BOT_USERNAME = "nirengine"

# Challenge filters
ACCEPTED_VARIANTS = {"standard"}
MIN_CLOCK_SECONDS = 60    # 1 minute minimum initial time
MAX_CLOCK_SECONDS = 900   # 15 minutes maximum initial time


def compute_move(uci_moves: list) -> str:
    """
    Return the engine's best move as a UCI string given the move history.

    Uses the novelty engine (KL-divergence based). Falls back to depth-3
    negamax if the novelty engine returns nothing.
    """
    board = board_from_moves(uci_moves)
    move = get_novel_move(board)
    if move is None:
        move = engine_best_move(board, depth=3)
    if move is None:
        raise RuntimeError("No legal moves available")
    return str(move)


class LichessBot:
    def __init__(self, token: str):
        if not token:
            raise ValueError("LICHESS_BOT_TOKEN environment variable is not set")
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
        })

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, stream: bool = False, **kwargs) -> requests.Response:
        return self.session.get(
            f"{LICHESS_HOST}{path}", stream=stream, timeout=None, **kwargs
        )

    def _post(self, path: str, **kwargs) -> requests.Response:
        return self.session.post(f"{LICHESS_HOST}{path}", **kwargs)

    def _stream_ndjson(self, path: str):
        """Yield parsed JSON objects from a Lichess NDJSON stream."""
        with self._get(path, stream=True) as r:
            r.raise_for_status()
            for raw in r.iter_lines():
                if raw:
                    yield json.loads(raw)

    # ------------------------------------------------------------------
    # Top-level event loop
    # ------------------------------------------------------------------

    def run(self):
        log.info("Bot starting as %s", BOT_USERNAME)
        while True:
            try:
                for event in self._stream_ndjson("/api/stream/event"):
                    self._handle_event(event)
            except Exception as exc:
                log.error("Event stream error: %s — reconnecting in 5 s", exc)
                time.sleep(5)

    def _handle_event(self, event: dict):
        etype = event.get("type")
        if etype == "challenge":
            self._handle_challenge(event["challenge"])
        elif etype == "gameStart":
            game_id = event["game"]["id"]
            t = threading.Thread(
                target=self._play_game, args=(game_id,), daemon=True
            )
            t.start()
        elif etype == "gameFinish":
            log.info("Game finished: %s", event["game"]["id"])

    # ------------------------------------------------------------------
    # Challenge handling
    # ------------------------------------------------------------------

    def _handle_challenge(self, challenge: dict):
        cid = challenge["id"]
        challenger = challenge.get("challenger", {}).get("id", "?")
        variant = challenge.get("variant", {}).get("key", "standard")
        tc = challenge.get("timeControl", {})
        tc_type = tc.get("type", "unlimited")

        # Only standard chess
        if variant not in ACCEPTED_VARIANTS:
            log.info("Declining %s from %s: variant %s", cid, challenger, variant)
            self._post(
                f"/api/challenge/{cid}/decline",
                json={"reason": "variant"},
            )
            return

        # Only real-time games within time range
        if tc_type == "clock":
            initial = tc.get("limit", 0)
            if not (MIN_CLOCK_SECONDS <= initial <= MAX_CLOCK_SECONDS):
                log.info(
                    "Declining %s from %s: clock %ds out of range", cid, challenger, initial
                )
                self._post(
                    f"/api/challenge/{cid}/decline",
                    json={"reason": "timeControl"},
                )
                return
        elif tc_type == "correspondence":
            log.info("Declining %s from %s: correspondence", cid, challenger)
            self._post(
                f"/api/challenge/{cid}/decline",
                json={"reason": "timeControl"},
            )
            return

        log.info("Accepting challenge %s from %s (%s)", cid, challenger, tc_type)
        r = self._post(f"/api/challenge/{cid}/accept")
        if not r.ok:
            log.warning("Failed to accept challenge %s: %s", cid, r.status_code)

    # ------------------------------------------------------------------
    # Game loop
    # ------------------------------------------------------------------

    def _play_game(self, game_id: str):
        log.info("Joining game %s", game_id)
        my_color = None

        try:
            for state in self._stream_ndjson(f"/api/bot/game/stream/{game_id}"):
                stype = state.get("type")

                if stype == "gameFull":
                    white_id = state.get("white", {}).get("id", "").lower()
                    my_color = "w" if white_id == BOT_USERNAME.lower() else "b"
                    opp_side = state.get("black" if my_color == "w" else "white", {})
                    opp_name = opp_side.get("id", "?")
                    log.info(
                        "Game %s: playing as %s vs %s",
                        game_id,
                        "white" if my_color == "w" else "black",
                        opp_name,
                    )
                    self._maybe_move(game_id, state["state"], my_color)

                elif stype == "gameState":
                    if my_color is None:
                        continue
                    status = state.get("status", "started")
                    if status != "started":
                        log.info("Game %s ended: %s", game_id, status)
                        break
                    self._maybe_move(game_id, state, my_color)

        except Exception as exc:
            log.error("Error in game %s: %s", game_id, exc)

    def _maybe_move(self, game_id: str, state: dict, my_color: str):
        """Make a move if it is our turn."""
        moves_str = state.get("moves", "")
        moves = moves_str.split() if moves_str.strip() else []

        whites_turn = len(moves) % 2 == 0
        if (my_color == "w") != whites_turn:
            return  # Not our turn

        log.info("Game %s: computing move (ply %d)…", game_id, len(moves))
        try:
            move = compute_move(moves)
            log.info("Game %s: playing %s", game_id, move)
            r = self._post(f"/api/bot/game/{game_id}/move/{move}")
            if r.ok:
                log.info("Game %s: move %s accepted", game_id, move)
            else:
                log.error(
                    "Game %s: move %s rejected (%s): %s",
                    game_id, move, r.status_code, r.text[:200],
                )
        except Exception as exc:
            log.error("Game %s: failed to compute/send move: %s", game_id, exc)


if __name__ == "__main__":
    token = os.environ.get("LICHESS_BOT_TOKEN", "")
    if not token:
        print("ERROR: LICHESS_BOT_TOKEN is not set.")
        print("1. Create an OAuth token at https://lichess.org/account/oauth/token")
        print("   Required scope: bot:play")
        print("2. Run:  export LICHESS_BOT_TOKEN=lip_xxxxxxxxxxxx")
        print("3. Run:  python lichess_bot.py")
        sys.exit(1)

    # Optionally forward the bot token to the opening explorer (reduces rate-limiting)
    if not os.environ.get("LICHESS_API_TOKEN"):
        os.environ["LICHESS_API_TOKEN"] = token

    bot = LichessBot(token)
    bot.run()
