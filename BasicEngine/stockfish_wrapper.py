"""
Stockfish Engine Wrapper

Provides Stockfish-based evaluation for the novelty engine.
Converts BasicEngine Board representation to python-chess format
and uses Stockfish for strong position evaluation.
"""

import chess
import chess.engine
from typing import Optional
from .board import Board, Move


# Stockfish path - adjust if needed
STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"

# Global engine instance to avoid reopening
_engine: Optional[chess.engine.SimpleEngine] = None


def get_stockfish_engine():
    """Get or create the Stockfish engine instance."""
    global _engine
    if _engine is None:
        _engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    return _engine


def close_stockfish_engine():
    """Close the Stockfish engine instance."""
    global _engine
    if _engine is not None:
        _engine.quit()
        _engine = None


def board_to_fen(board: Board) -> str:
    """
    Convert BasicEngine Board to FEN string.

    Args:
        board: BasicEngine Board object

    Returns:
        FEN string representation
    """
    # Build piece placement
    rows = []
    for row in board.squares:
        fen_row = ""
        empty_count = 0
        for square in row:
            if square == '..':
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                # Convert 'wP' to 'P', 'bP' to 'p', etc.
                color, piece = square[0], square[1]
                fen_piece = piece if color == 'w' else piece.lower()
                fen_row += fen_piece
        if empty_count > 0:
            fen_row += str(empty_count)
        rows.append(fen_row)

    piece_placement = '/'.join(rows)

    # Active color
    active_color = 'w' if board.turn == 'w' else 'b'

    # Castling rights (simplified - assume all available for now)
    # TODO: Track castling rights properly if needed
    castling = 'KQkq'

    # En passant (simplified - no en passant tracking)
    # TODO: Track en passant if needed
    en_passant = '-'

    # Halfmove clock and fullmove number (simplified)
    halfmove = '0'
    fullmove = '1'

    return f"{piece_placement} {active_color} {castling} {en_passant} {halfmove} {fullmove}"


def evaluate_with_stockfish(board: Board, depth: int = 15, time_limit: float = 0.1) -> int:
    """
    Evaluate a position using Stockfish.

    Args:
        board: BasicEngine Board to evaluate
        depth: Search depth for Stockfish
        time_limit: Time limit in seconds for analysis

    Returns:
        Evaluation in centipawns from white's perspective.
        Positive = good for white, negative = good for black.
    """
    engine = get_stockfish_engine()

    # Convert to FEN and create python-chess board
    fen = board_to_fen(board)
    chess_board = chess.Board(fen)

    # Analyze position
    try:
        info = engine.analyse(
            chess_board,
            chess.engine.Limit(depth=depth, time=time_limit)
        )

        # Extract score
        score = info.get("score")
        if score is None:
            return 0

        # Convert to centipawns
        # Handle mate scores
        if score.is_mate():
            mate_in = score.relative.moves
            if mate_in > 0:
                # Winning for side to move
                return 10000 - mate_in * 10
            else:
                # Losing for side to move
                return -10000 - mate_in * 10
        else:
            # Regular centipawn score (from white's perspective)
            cp_score = score.white().score(mate_score=10000)
            return cp_score if cp_score is not None else 0

    except Exception as e:
        print(f"Stockfish evaluation error: {e}")
        return 0


def get_stockfish_best_move(board: Board, depth: int = 15, time_limit: float = 0.1) -> Optional[Move]:
    """
    Get Stockfish's best move for a position.

    Args:
        board: BasicEngine Board
        depth: Search depth
        time_limit: Time limit in seconds

    Returns:
        Best move as BasicEngine Move object, or None
    """
    engine = get_stockfish_engine()

    # Convert to FEN and create python-chess board
    fen = board_to_fen(board)
    chess_board = chess.Board(fen)

    try:
        result = engine.play(
            chess_board,
            chess.engine.Limit(depth=depth, time=time_limit)
        )

        if result.move is None:
            return None

        # Convert UCI move to BasicEngine Move
        uci_move = result.move.uci()
        return uci_to_move(uci_move)

    except Exception as e:
        print(f"Stockfish move error: {e}")
        return None


def uci_to_move(uci: str) -> Move:
    """
    Convert UCI string to BasicEngine Move object.

    Args:
        uci: UCI move string like 'e2e4' or 'e7e8q'

    Returns:
        BasicEngine Move object
    """
    files = 'abcdefgh'
    ranks = '87654321'

    from_col = files.index(uci[0])
    from_row = ranks.index(uci[1])
    to_col = files.index(uci[2])
    to_row = ranks.index(uci[3])

    promotion = None
    if len(uci) == 5:
        promotion = uci[4].upper()

    return Move(from_row, from_col, to_row, to_col, promotion)
