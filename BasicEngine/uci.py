#!/usr/bin/env python3
"""
UCI Protocol Interface for Novelty Chess Engine

This allows the engine to communicate with Lichess-bot or any UCI-compatible GUI.

Usage:
    python uci.py
"""

import sys
from board import Board, Move
from engine import best_move
from critical_point import is_critical_point
from novelty_engine import get_novel_move

# Engine info
ENGINE_NAME = "NoveltyEngine"
ENGINE_AUTHOR = "CubistHackathon"

# Global state
board = Board()
move_history = []
opponent_rating = 1500  # Default, updated from Lichess


def parse_uci_move(uci_str: str) -> Move:
    """Convert UCI string (e.g., 'e2e4') to Move object."""
    files = 'abcdefgh'
    ranks = '87654321'

    from_col = files.index(uci_str[0])
    from_row = ranks.index(uci_str[1])
    to_col = files.index(uci_str[2])
    to_row = ranks.index(uci_str[3])

    promo = None
    if len(uci_str) == 5:
        promo = uci_str[4].upper()

    return Move(from_row, from_col, to_row, to_col, promo)


def move_to_uci(move: Move) -> str:
    """Convert Move object to UCI string."""
    return str(move)


def uci_loop():
    """Main UCI communication loop."""
    global board, move_history, opponent_rating

    while True:
        try:
            line = input().strip()
        except EOFError:
            break

        if not line:
            continue

        tokens = line.split()
        cmd = tokens[0]

        if cmd == "uci":
            print(f"id name {ENGINE_NAME}")
            print(f"id author {ENGINE_AUTHOR}")
            # Options
            print("option name OpponentRating type spin default 1500 min 800 max 3000")
            print("uciok")

        elif cmd == "isready":
            print("readyok")

        elif cmd == "ucinewgame":
            board = Board()
            move_history = []

        elif cmd == "position":
            if "startpos" in tokens:
                board = Board()
                move_history = []

                if "moves" in tokens:
                    moves_idx = tokens.index("moves") + 1
                    for uci_move in tokens[moves_idx:]:
                        move = parse_uci_move(uci_move)
                        board.make_move(move)
                        move_history.append(uci_move)

            elif "fen" in tokens:
                # FEN parsing not fully implemented
                # For now, just handle moves after FEN
                if "moves" in tokens:
                    moves_idx = tokens.index("moves") + 1
                    for uci_move in tokens[moves_idx:]:
                        move = parse_uci_move(uci_move)
                        board.make_move(move)
                        move_history.append(uci_move)

        elif cmd == "setoption":
            if "OpponentRating" in tokens:
                try:
                    value_idx = tokens.index("value") + 1
                    opponent_rating = int(tokens[value_idx])
                except (ValueError, IndexError):
                    pass

        elif cmd == "go":
            # Determine move count
            move_count = len(move_history) // 2

            # Check if we should play a novel move
            try:
                if is_critical_point(board, opponent_rating, move_count):
                    move = get_novel_move(board)
                    info = "novelty"
                else:
                    move = best_move(board, depth=3)
                    info = "normal"
            except Exception as e:
                # Fallback to normal engine
                move = best_move(board, depth=3)
                info = "fallback"

            if move:
                uci_move = move_to_uci(move)
                print(f"info string {info} move")
                print(f"bestmove {uci_move}")
            else:
                print("bestmove (none)")

        elif cmd == "quit":
            break

        # Flush output
        sys.stdout.flush()


if __name__ == "__main__":
    uci_loop()
