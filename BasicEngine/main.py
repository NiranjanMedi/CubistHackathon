from board import Board
from engine import best_move as baseline_move
from discomfort_move import discomfort_move

# Default match-up: new style (DiscomfortBot) plays White, plain negamax (BaselineBot)
# plays Black. Swap by reassigning these or passing different selectors.
WHITE_PLAYER = discomfort_move
WHITE_NAME = "DiscomfortBot"
BLACK_PLAYER = baseline_move
BLACK_NAME = "BaselineBot"


def play_game(max_plies=200):
    board = Board()
    history = []

    print(f"=== Players ===")
    print(f"White: {WHITE_NAME}")
    print(f"Black: {BLACK_NAME}")
    print()
    print(board)
    print()

    for ply in range(max_plies):
        selector = WHITE_PLAYER if board.turn == 'w' else BLACK_PLAYER
        move = selector(board)
        if move is None:
            kr, kc = board.find_king(board.turn)
            opponent = 'b' if board.turn == 'w' else 'w'
            if board.is_attacked(kr, kc, opponent):
                winner = 'Black' if board.turn == 'w' else 'White'
                print(f"Checkmate. {winner} wins.")
            else:
                print("Stalemate.")
            break

        side_label = f"White ({WHITE_NAME})" if board.turn == 'w' else f"Black ({BLACK_NAME})"
        print(f"{ply + 1}. {side_label}: {move}")
        board.make_move(move)
        history.append(str(move))
        print(board)
        print()
    else:
        print("Move limit reached. Draw.")

    print("\n=== UCI move list ===")
    print(' '.join(history))
    print("\n=== Paste into a UCI engine ===")
    print(f"position startpos moves {' '.join(history)}")


if __name__ == '__main__':
    play_game()
