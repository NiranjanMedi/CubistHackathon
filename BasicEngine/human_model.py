"""
Human move distribution model using Lichess Opening Explorer API.
Provides probability distributions over moves based on how often humans play them.

NOTE: The Lichess Opening Explorer API now requires authentication.
For production use, you'll need to:
1. Create a Lichess account
2. Generate an API token at lichess.org/account/oauth/token
3. Set LICHESS_API_TOKEN environment variable

For now, we fall back to a heuristic-based human distribution when API is unavailable.
"""

import urllib.request
import urllib.parse
import json
import os
from typing import Dict, Optional
from .board import Board, Move

# In-memory cache to avoid repeated API calls
_cache: Dict[str, dict] = {}

# API token (optional - set via environment variable)
API_TOKEN = os.environ.get('LICHESS_API_TOKEN', '')


def board_to_fen(board: Board) -> str:
    """Convert our Board representation to FEN string for API queries."""
    rows = []
    for r in range(8):
        empty = 0
        row_str = ""
        for c in range(8):
            sq = board.squares[r][c]
            if sq == '..':
                empty += 1
            else:
                if empty > 0:
                    row_str += str(empty)
                    empty = 0
                color, kind = sq[0], sq[1]
                piece = kind if color == 'w' else kind.lower()
                row_str += piece
        if empty > 0:
            row_str += str(empty)
        rows.append(row_str)

    fen = '/'.join(rows)
    fen += ' w ' if board.turn == 'w' else ' b '
    fen += 'KQkq - 0 1'  # Simplified: assume all castling, no en passant
    return fen


def query_lichess(fen: str) -> Optional[dict]:
    """
    Query Lichess Opening Explorer API for move frequencies at a position.
    Returns raw API response or None if request fails.

    Note: Requires LICHESS_API_TOKEN environment variable for authentication.
    """
    if fen in _cache:
        return _cache[fen]

    if not API_TOKEN:
        # No token available - will use heuristic fallback
        return None

    try:
        encoded_fen = urllib.parse.quote(fen, safe='')
        url = f"https://explorer.lichess.ovh/lichess?fen={encoded_fen}"

        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        req.add_header('Authorization', f'Bearer {API_TOKEN}')

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            _cache[fen] = data
            return data
    except Exception as e:
        # Silently fall back to heuristic
        return None


def get_heuristic_human_distribution(board: Board) -> Dict[str, float]:
    """
    Estimate human move distribution using chess heuristics.
    Used as fallback when Lichess API is unavailable.

    Heuristics based on human playing patterns:
    - Humans prefer central pawn moves in openings
    - Humans like developing knights and bishops
    - Humans prefer captures (they're exciting)
    - Humans avoid edge pawn moves early
    - Humans like castling when available
    """
    from .engine import evaluate, PIECE_VALUES

    legal_moves = board.legal_moves()
    if not legal_moves:
        return {}

    scores = {}
    for move in legal_moves:
        score = 1.0  # Base score

        piece = board.squares[move.from_row][move.from_col]
        _, kind = piece[0], piece[1]
        target = board.squares[move.to_row][move.to_col]

        # Captures are popular with humans
        if target != '..':
            score += 2.0

        # Central moves are popular (columns d,e = 3,4)
        if move.to_col in (3, 4) and move.to_row in (3, 4):
            score += 1.5

        # Development moves (knights and bishops moving from back rank)
        if kind in ('N', 'B'):
            start_rank = 7 if board.turn == 'w' else 0
            if move.from_row == start_rank:
                score += 1.0

        # Central pawn moves are popular
        if kind == 'P' and move.from_col in (3, 4):
            score += 1.0

        # Edge pawn moves are less popular
        if kind == 'P' and move.from_col in (0, 7):
            score *= 0.5

        # Queen moves early are common (though not always good)
        if kind == 'Q':
            score += 0.5

        scores[str(move)] = score

    # Convert to probabilities via softmax
    total = sum(scores.values())
    return {m: s / total for m, s in scores.items()}


def get_human_distribution(board: Board, epsilon: float = 0.001) -> Dict[str, float]:
    """
    Get probability distribution over moves based on human play frequency.

    Tries Lichess API first, falls back to heuristic estimation.

    Args:
        board: Current board position
        epsilon: Small probability for unseen moves (avoids log(0) in KL)

    Returns:
        Dict mapping move UCI strings to probabilities
    """
    fen = board_to_fen(board)
    data = query_lichess(fen)

    if data is None or 'moves' not in data or len(data['moves']) == 0:
        # No API data - use heuristic fallback
        return get_heuristic_human_distribution(board)

    # Calculate total games for this position
    total = sum(m.get('white', 0) + m.get('draws', 0) + m.get('black', 0)
                for m in data['moves'])

    if total == 0:
        return get_heuristic_human_distribution(board)

    # Build distribution from API data
    distribution = {}
    for move_data in data['moves']:
        uci = move_data['uci']
        count = move_data.get('white', 0) + move_data.get('draws', 0) + move_data.get('black', 0)
        distribution[uci] = count / total

    # Add epsilon probability for legal moves not in database
    for move in board.legal_moves():
        uci = str(move)
        if uci not in distribution:
            distribution[uci] = epsilon

    # Renormalize to ensure probabilities sum to 1
    total_prob = sum(distribution.values())
    if total_prob > 0:
        distribution = {m: p / total_prob for m, p in distribution.items()}

    return distribution


def get_position_stats(board: Board) -> dict:
    """
    Get statistics about the position from Lichess database.
    Useful for debugging and analysis.
    """
    fen = board_to_fen(board)
    data = query_lichess(fen)

    if data is None:
        return {'found': False}

    total_games = sum(m.get('white', 0) + m.get('draws', 0) + m.get('black', 0)
                      for m in data.get('moves', []))

    return {
        'found': True,
        'total_games': total_games,
        'num_moves_played': len(data.get('moves', [])),
        'top_move': data['moves'][0]['uci'] if data.get('moves') else None
    }
