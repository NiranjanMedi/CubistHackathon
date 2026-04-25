"""
Consultation mode: Enter a position and get the novelty engine's recommendation.
Use this while playing on chess.com to see what novel moves exist.

Usage: python3 consult.py
"""

from board import Board, Move
from novelty_engine import get_novel_move, analyze_position
from engine import best_move


def parse_move(board, uci_str):
    """Parse UCI string like 'e2e4' into a Move object."""
    if len(uci_str) < 4:
        return None

    files = 'abcdefgh'
    ranks = '87654321'

    try:
        from_col = files.index(uci_str[0])
        from_row = ranks.index(uci_str[1])
        to_col = files.index(uci_str[2])
        to_row = ranks.index(uci_str[3])

        promo = None
        if len(uci_str) == 5:
            promo = uci_str[4].upper()

        move = Move(from_row, from_col, to_row, to_col, promo)

        # Verify it's legal
        if move in board.legal_moves():
            return move
        return None
    except:
        return None


def main():
    board = Board()

    print("=" * 50)
    print("NOVELTY ENGINE CONSULTATION MODE")
    print("=" * 50)
    print()
    print("Commands:")
    print("  <move>  - Enter a move in UCI format (e.g., e2e4)")
    print("  undo    - Take back last move")
    print("  analyze - Show novelty analysis")
    print("  suggest - Get move suggestion")
    print("  fen     - Show current FEN")
    print("  reset   - Reset to starting position")
    print("  quit    - Exit")
    print()

    history = []

    while True:
        print(board)
        turn = "White" if board.turn == 'w' else "Black"
        print(f"\n{turn} to move")

        cmd = input("> ").strip().lower()

        if cmd == 'quit':
            break

        elif cmd == 'reset':
            board = Board()
            history = []
            print("Board reset.\n")

        elif cmd == 'undo':
            if history:
                board = Board()
                history.pop()
                for m in history:
                    board.make_move(m)
                print("Move undone.\n")
            else:
                print("No moves to undo.\n")

        elif cmd == 'analyze':
            print("\nAnalyzing position...")
            analysis = analyze_position(board)
            print(f"\nKL Divergence: {analysis['kl_divergence']:.3f}")
            print(f"Novelty Position: {analysis['is_novelty_position']}")
            print(f"\nTop Engine Moves:")
            for m, p in analysis['top_engine_moves']:
                print(f"  {m}: {p*100:.1f}%")
            print(f"\nTop Human Moves:")
            for m, p in analysis['top_human_moves']:
                print(f"  {m}: {p*100:.1f}%")
            print()

        elif cmd == 'suggest':
            print("\nCalculating...")
            novel = get_novel_move(board, verbose=True)
            normal = best_move(board, depth=3)
            print(f"\nNovelty Engine suggests: {novel}")
            print(f"Normal Engine suggests:  {normal}")
            if str(novel) != str(normal):
                print("  ^ NOVELTY MOVE!")
            print()

        elif cmd == 'fen':
            from human_model import board_to_fen
            print(f"\nFEN: {board_to_fen(board)}\n")

        else:
            # Try to parse as a move
            move = parse_move(board, cmd)
            if move:
                board.make_move(move)
                history.append(move)
                print()
            else:
                legal = [str(m) for m in board.legal_moves()]
                print(f"Invalid move. Examples: {legal[:5]}")
                print()


if __name__ == '__main__':
    main()
