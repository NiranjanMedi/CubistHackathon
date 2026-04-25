from board import Board
from engine import random_move


def play_random_game(max_plies=200):
    board = Board()
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
            return

        side = 'White' if board.turn == 'w' else 'Black'
        print(f"{ply + 1}. {side}: {move}")
        board.make_move(move)
        print(board)
        print()

    print("Move limit reached. Draw.")


if __name__ == '__main__':
    play_random_game()
