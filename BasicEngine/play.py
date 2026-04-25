import sys
from board import Board
from discomfort_move import discomfort_move


def parse_uci(s, legal):
    s = s.strip().lower()
    for m in legal:
        if str(m) == s:
            return m
    return None


def play(human_color='w', max_plies=400, debug=True):
    board = Board()
    history = []
    print(board)
    print()

    while len(history) < max_plies:
        legal = board.legal_moves()
        if not legal:
            kr, kc = board.find_king(board.turn)
            opp = 'b' if board.turn == 'w' else 'w'
            if board.is_attacked(kr, kc, opp):
                winner = 'Black' if board.turn == 'w' else 'White'
                print(f"Checkmate. {winner} wins.")
            else:
                print("Stalemate.")
            break

        if board.turn == human_color:
            while True:
                try:
                    s = input(f"Your move ({board.turn}, e.g. e2e4, or 'q' to quit): ")
                except EOFError:
                    return
                if s.strip().lower() in ('q', 'quit', 'exit'):
                    return
                m = parse_uci(s, legal)
                if m is not None:
                    break
                sample = ', '.join(str(x) for x in legal[:8])
                print(f"  invalid. legal moves include: {sample} ...")
            board.make_move(m)
            history.append(str(m))
            print()
            print(board)
            print()
        else:
            print("Engine thinking...")
            m = discomfort_move(board, debug=debug)
            if m is None:
                break
            print(f"Engine plays: {m}")
            board.make_move(m)
            history.append(str(m))
            print()
            print(board)
            print()

    else:
        print("Move limit reached. Draw.")

    print()
    print("=== UCI history ===")
    print(' '.join(history))


if __name__ == '__main__':
    color = sys.argv[1].lower() if len(sys.argv) > 1 else 'w'
    if color not in ('w', 'b'):
        print(f"Unknown color {color!r}; defaulting to white.")
        color = 'w'
    play(human_color=color)
