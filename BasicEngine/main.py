from board import Board
from engine import random_move


def play_random_game(max_plies=200):
    board = Board()
    history = []
    print(board)
    print()

    for ply in range(max_plies):
        move = random_move(board)
        if move is None:
            kr, kc = board.find_king(board.turn)
            opponent = 'b' if board.turn == 'w' else 'w'
            if board.is_attacked(kr, kc, opponent):
                winner = 'Black' if board.turn == 'w' else 'White'
                print(f"Checkmate. {winner} wins.")
            else:
                print("Stalemate.")
            break

        side = 'White' if board.turn == 'w' else 'Black'
        print(f"{ply + 1}. {side}: {move}")
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
    play_random_game()
