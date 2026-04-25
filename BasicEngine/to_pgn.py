"""Convert a UCI move list into PGN and save it to past_games/. Use it like:

    python to_pgn.py "e2e4 e7e5 g1f3 ..."        # from argv
    python to_pgn.py < moves.txt                 # from stdin
    python main.py | python to_pgn.py            # piped from main.py

If the input contains the line `=== UCI move list ===`, only the line
immediately following it is used (matches main.py's output format).

Output goes to ../past_games/game_<timestamp>.pgn (next to BasicEngine/)."""

import sys
import os
import io
import datetime
import chess
import chess.pgn

PAST_GAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "past_games")


def extract_uci_tokens(text: str):
    if "=== UCI move list ===" in text:
        after = text.split("=== UCI move list ===", 1)[1]
        # Take just the first non-empty line after the marker
        for line in after.splitlines():
            line = line.strip()
            if line:
                text = line
                break
    return [t for t in text.split() if t]


def extract_player_names(text: str):
    """Pull White/Black names from a `=== Players ===` block, if present."""
    white = black = None
    if "=== Players ===" in text:
        block = text.split("=== Players ===", 1)[1]
        for line in block.splitlines()[:6]:
            line = line.strip()
            if line.lower().startswith("white:"):
                white = line.split(":", 1)[1].strip() or None
            elif line.lower().startswith("black:"):
                black = line.split(":", 1)[1].strip() or None
    return white, black


def uci_to_pgn(tokens, white="White", black="Black",
               event="Hackathon Self-Play"):
    game = chess.pgn.Game()
    game.headers["Event"] = event
    game.headers["White"] = white
    game.headers["Black"] = black
    board = game.board()
    node = game
    for tok in tokens:
        try:
            move = chess.Move.from_uci(tok)
        except ValueError:
            print(f"# skipping unparseable token: {tok!r}", file=sys.stderr)
            continue
        if move not in board.legal_moves:
            print(f"# illegal move {tok} at ply {board.ply()+1}; stopping", file=sys.stderr)
            break
        board.push(move)
        node = node.add_main_variation(move)

    if board.is_checkmate():
        result = "0-1" if board.turn == chess.WHITE else "1-0"
    elif board.is_stalemate() or board.is_insufficient_material() or \
            board.can_claim_draw():
        result = "1/2-1/2"
    else:
        result = "*"
    game.headers["Result"] = result

    out = io.StringIO()
    exporter = chess.pgn.FileExporter(out)
    game.accept(exporter)
    return out.getvalue()


def write_pgn_file(pgn_text: str) -> str:
    os.makedirs(PAST_GAMES_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.abspath(os.path.join(PAST_GAMES_DIR, f"game_{stamp}.pgn"))
    with open(path, "w") as f:
        f.write(pgn_text)
    return path


def main():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        text = " ".join(sys.argv[1:])
    else:
        text = sys.stdin.read()
    tokens = extract_uci_tokens(text)
    if not tokens:
        print("no UCI tokens found", file=sys.stderr)
        sys.exit(1)
    white, black = extract_player_names(text)
    kwargs = {}
    if white:
        kwargs["white"] = white
    if black:
        kwargs["black"] = black
    pgn = uci_to_pgn(tokens, **kwargs)
    path = write_pgn_file(pgn)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
