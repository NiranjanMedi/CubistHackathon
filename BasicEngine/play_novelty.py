"""
Play a game using the Novelty Engine.
Usage: python3 play_novelty.py
"""

from board import Board
from novelty_engine import get_novel_move, analyze_position


def play_game(max_moves=50):
    board = Board()
    move_history = []

    print("=== Novelty Engine Game ===")
    print("Playing both sides with novelty-seeking moves\n")

    for ply in range(max_moves * 2):
        print(board)
        print()

        # Check for game end
        legal_moves = board.legal_moves()
        if not legal_moves:
            kr, kc = board.find_king(board.turn)
            opp = 'b' if board.turn == 'w' else 'w'
            if board.is_attacked(kr, kc, opp):
                winner = 'Black' if board.turn == 'w' else 'White'
                print(f"Checkmate! {winner} wins.")
            else:
                print("Stalemate!")
            break

        # Get novelty move with analysis
        analysis = analyze_position(board)
        move = get_novel_move(board)

        side = 'White' if board.turn == 'w' else 'Black'
        move_num = (ply // 2) + 1

        print(f"Move {move_num} ({side}): {move}")
        print(f"  KL Divergence: {analysis['kl_divergence']:.3f}")
        print(f"  Novelty triggered: {analysis['is_novelty_position']}")
        print()

        board.make_move(move)
        move_history.append(str(move))

    print("\n=== Game History ===")
    print(' '.join(move_history))


def play_vs_human():
    """Play against the novelty engine."""
    board = Board()

    print("=== Play vs Novelty Engine ===")
    print("You are White. Enter moves in UCI format (e.g., e2e4)")
    print("Type 'quit' to exit, 'show' to see the board\n")

    while True:
        print(board)
        print()

        if board.turn == 'w':
            # Human's turn
            user_input = input("Your move: ").strip().lower()

            if user_input == 'quit':
                break
            if user_input == 'show':
                continue

            # Parse UCI move
            try:
                legal_moves = board.legal_moves()
                move = None
                for m in legal_moves:
                    if str(m) == user_input:
                        move = m
                        break

                if move is None:
                    print(f"Invalid move. Legal moves: {[str(m) for m in legal_moves[:10]]}...")
                    continue

                board.make_move(move)
            except Exception as e:
                print(f"Error: {e}")
                continue
        else:
            # Engine's turn
            print("Engine thinking...")
            move = get_novel_move(board, verbose=True)

            if move is None:
                print("No legal moves - game over!")
                break

            print(f"Engine plays: {move}\n")
            board.make_move(move)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'human':
        play_vs_human()
    else:
        play_game()
