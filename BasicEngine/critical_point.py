"""
Component 1: Critical Point Detector

Determines when to switch from normal play to novelty-seeking mode.
Measures positional deception — how much the position looks different
on the surface versus what deep calculation reveals.

A position is a critical point when the opponent's intuition will
systematically mislead them about what is actually happening.
"""

from board import Board
from engine import evaluate, _negamax, PIECE_VALUES, INF

# ============================================================================
# HYPERPARAMETERS (tune these)
# ============================================================================

# Discomfort threshold in centipawns - novelty activates above this
DISCOMFORT_THRESHOLD = 80

# Multiplier when shallow and deep evals have opposite signs (trap condition)
SIGN_DISAGREEMENT_MULTIPLIER = 2.0

# Suppress novelty when already winning by this much (centipawns)
WINNING_THRESHOLD = 200

# Minimum move number before novelty can activate (suppress in opening)
MIN_MOVE_FOR_NOVELTY = 10

# Material threshold for endgame detection (excluding kings)
# Standard: Q=900, R=500, B=330, N=320, P=100
# Starting material (no kings): 2*900 + 4*500 + 4*330 + 4*320 + 16*100 = 7400
# Endgame threshold: roughly when queens are off and some pieces traded
ENDGAME_MATERIAL_THRESHOLD = 2600


# ============================================================================
# DEPTH CALIBRATION BY RATING
# ============================================================================

def get_depth_for_rating(rating: int) -> int:
    """
    Map opponent rating to search depth.
    Models how far this specific opponent actually calculates.

    Original specification:
    1000-1200 → depth 3
    1200-1500 → depth 5
    1500-1800 → depth 7
    1800-2100 → depth 9
    2100+     → depth 11

    Adjusted for current engine performance (no advanced pruning):
    1000-1200 → depth 2
    1200-1500 → depth 3
    1500-1800 → depth 4
    1800-2100 → depth 5
    2100+     → depth 6

    TODO: Increase depths once engine has better pruning/caching.
    """
    if rating < 1200:
        return 2
    elif rating < 1500:
        return 3
    elif rating < 1800:
        return 4
    elif rating < 2100:
        return 5
    else:
        return 6


# ============================================================================
# EVALUATION FUNCTIONS
# ============================================================================

def get_shallow_eval(board: Board) -> int:
    """
    Shallow evaluation: material + piece-square tables only.
    No search. This is what any human sees at an immediate glance.

    Returns score from current player's perspective.
    """
    raw_score = evaluate(board)  # This is already material + PST
    # Convert to current player's perspective
    return raw_score if board.turn == 'w' else -raw_score


def get_deep_eval(board: Board, depth: int) -> int:
    """
    Deep evaluation: negamax search to specified depth.
    Models what the opponent can actually calculate.

    Returns score from current player's perspective.
    """
    return _negamax(board, depth, -INF, INF)


# ============================================================================
# MATERIAL AND GAME PHASE
# ============================================================================

def count_material(board: Board) -> int:
    """
    Count total material on the board (excluding kings).
    Used for game phase detection.
    """
    total = 0
    for r in range(8):
        for c in range(8):
            piece = board.squares[r][c]
            if piece == '..' or piece[1] == 'K':
                continue
            total += PIECE_VALUES.get(piece[1], 0)
    return total


def get_move_count(board: Board) -> int:
    """
    Estimate move count from material and piece positions.
    This is approximate - ideally the caller tracks move count.

    For now, we detect opening by checking if pieces are still
    on their starting squares.
    """
    # Count pieces not on starting squares as a proxy for moves made
    developed_pieces = 0

    # Check white pieces
    if board.squares[7][1] != 'wN':  # b1 knight moved
        developed_pieces += 1
    if board.squares[7][6] != 'wN':  # g1 knight moved
        developed_pieces += 1
    if board.squares[7][2] != 'wB':  # c1 bishop moved
        developed_pieces += 1
    if board.squares[7][5] != 'wB':  # f1 bishop moved
        developed_pieces += 1
    if board.squares[6][3] != 'wP':  # d2 pawn moved
        developed_pieces += 1
    if board.squares[6][4] != 'wP':  # e2 pawn moved
        developed_pieces += 1

    # Check black pieces
    if board.squares[0][1] != 'bN':  # b8 knight moved
        developed_pieces += 1
    if board.squares[0][6] != 'bN':  # g8 knight moved
        developed_pieces += 1
    if board.squares[0][2] != 'bB':  # c8 bishop moved
        developed_pieces += 1
    if board.squares[0][5] != 'bB':  # f8 bishop moved
        developed_pieces += 1
    if board.squares[1][3] != 'bP':  # d7 pawn moved
        developed_pieces += 1
    if board.squares[1][4] != 'bP':  # e7 pawn moved
        developed_pieces += 1

    # Rough estimate: each side makes ~1 move per developed piece
    return developed_pieces


def get_game_phase(board: Board, move_count: int = None) -> str:
    """
    Detect game phase: 'opening', 'middlegame', or 'endgame'.

    - Opening: first 10 moves
    - Endgame: total material below threshold
    - Middlegame: everything else
    """
    if move_count is None:
        move_count = get_move_count(board)

    # Opening: first 10 moves
    if move_count < MIN_MOVE_FOR_NOVELTY:
        return 'opening'

    # Endgame: low material
    material = count_material(board)
    if material < ENDGAME_MATERIAL_THRESHOLD:
        return 'endgame'

    return 'middlegame'


# ============================================================================
# DISCOMFORT CALCULATION
# ============================================================================

def compute_discomfort(shallow_eval: int, deep_eval: int) -> float:
    """
    Compute the discomfort score measuring positional deception.

    divergence = |eval_deep - eval_shallow|

    If signs disagree (position looks winning but is losing, or vice versa),
    multiply by SIGN_DISAGREEMENT_MULTIPLIER because this produces
    categorically wrong decisions, not just imprecise ones.
    """
    divergence = abs(deep_eval - shallow_eval)

    # Check for sign disagreement (the trap condition)
    shallow_sign = 1 if shallow_eval > 0 else (-1 if shallow_eval < 0 else 0)
    deep_sign = 1 if deep_eval > 0 else (-1 if deep_eval < 0 else 0)

    if shallow_sign != 0 and deep_sign != 0 and shallow_sign != deep_sign:
        # Signs disagree - this is a trap!
        return divergence * SIGN_DISAGREEMENT_MULTIPLIER
    else:
        return divergence * 1.0


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def is_critical_point(board: Board, opponent_rating: int, move_count: int = None) -> bool:
    """
    Determine if the current position is a critical point for novelty injection.

    Args:
        board: Current board position
        opponent_rating: Estimated rating of the opponent (e.g., 1500)
        move_count: Optional move number (if not provided, estimated from position)

    Returns:
        True if novelty mode should activate, False otherwise

    Conditions for activation:
        1. Game phase must be middlegame (not opening or endgame)
        2. We must not already be winning by more than WINNING_THRESHOLD
        3. Discomfort score must exceed DISCOMFORT_THRESHOLD
    """
    # Get game phase
    phase = get_game_phase(board, move_count)

    # Condition 1: Only activate in middlegame
    if phase != 'middlegame':
        return False

    # Get evaluations
    shallow = get_shallow_eval(board)

    depth = get_depth_for_rating(opponent_rating)
    deep = get_deep_eval(board, depth)

    # Condition 2: Don't activate if already winning comfortably
    # (from current player's perspective, positive = good for us)
    if deep > WINNING_THRESHOLD:
        return False

    # Condition 3: Discomfort must exceed threshold
    discomfort = compute_discomfort(shallow, deep)

    return discomfort > DISCOMFORT_THRESHOLD


# ============================================================================
# ANALYSIS FUNCTIONS (for debugging/tuning)
# ============================================================================

def analyze_critical_point(board: Board, opponent_rating: int, move_count: int = None) -> dict:
    """
    Detailed analysis of critical point detection.
    Useful for debugging and hyperparameter tuning.
    """
    phase = get_game_phase(board, move_count)
    shallow = get_shallow_eval(board)

    depth = get_depth_for_rating(opponent_rating)
    deep = get_deep_eval(board, depth)

    discomfort = compute_discomfort(shallow, deep)
    is_critical = is_critical_point(board, opponent_rating, move_count)

    # Determine why it was/wasn't triggered
    reasons = []
    if phase != 'middlegame':
        reasons.append(f"Phase is {phase}, not middlegame")
    if deep > WINNING_THRESHOLD:
        reasons.append(f"Already winning by {deep}cp (threshold: {WINNING_THRESHOLD})")
    if discomfort <= DISCOMFORT_THRESHOLD:
        reasons.append(f"Discomfort {discomfort:.0f}cp below threshold {DISCOMFORT_THRESHOLD}")

    if is_critical:
        reasons = ["Discomfort exceeds threshold in middlegame"]

    return {
        'is_critical_point': is_critical,
        'game_phase': phase,
        'opponent_rating': opponent_rating,
        'search_depth': depth,
        'shallow_eval': shallow,
        'deep_eval': deep,
        'divergence': abs(deep - shallow),
        'sign_disagreement': (shallow > 0) != (deep > 0) and shallow != 0 and deep != 0,
        'discomfort': discomfort,
        'threshold': DISCOMFORT_THRESHOLD,
        'reasons': reasons,
        'material': count_material(board),
    }


def print_analysis(board: Board, opponent_rating: int, move_count: int = None):
    """Pretty-print the critical point analysis."""
    analysis = analyze_critical_point(board, opponent_rating, move_count)

    print(f"=== Critical Point Analysis ===")
    print(f"Opponent Rating: {analysis['opponent_rating']} (search depth: {analysis['search_depth']})")
    print(f"Game Phase: {analysis['game_phase']}")
    print(f"Material: {analysis['material']}")
    print()
    print(f"Shallow Eval: {analysis['shallow_eval']:+d} cp")
    print(f"Deep Eval:    {analysis['deep_eval']:+d} cp")
    print(f"Divergence:   {analysis['divergence']} cp")
    print(f"Sign Disagreement: {analysis['sign_disagreement']}")
    print(f"Discomfort:   {analysis['discomfort']:.0f} cp (threshold: {analysis['threshold']})")
    print()
    print(f">>> IS CRITICAL POINT: {analysis['is_critical_point']}")
    for reason in analysis['reasons']:
        print(f"    - {reason}")
