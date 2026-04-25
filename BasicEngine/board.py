from dataclasses import dataclass
from typing import List, Optional

EMPTY = '..'

KNIGHT_DIRS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
               (1, -2), (1, 2), (2, -1), (2, 1)]
KING_DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
             (0, 1), (1, -1), (1, 0), (1, 1)]
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS


@dataclass(frozen=True)
class Move:
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    promotion: Optional[str] = None

    def __repr__(self):
        files = 'abcdefgh'
        ranks = '87654321'
        s = f"{files[self.from_col]}{ranks[self.from_row]}{files[self.to_col]}{ranks[self.to_row]}"
        if self.promotion:
            s += self.promotion.lower()
        return s


def starting_squares() -> List[List[str]]:
    return [
        ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
        ['bP'] * 8,
        [EMPTY] * 8, [EMPTY] * 8, [EMPTY] * 8, [EMPTY] * 8,
        ['wP'] * 8,
        ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR'],
    ]


class Board:
    def __init__(self):
        self.squares = starting_squares()
        self.turn = 'w'
        self.castling_rights = set('KQkq')
        self.ep_target = None

    def __str__(self):
        rows = []
        for i, row in enumerate(self.squares):
            rank = 8 - i
            rows.append(f"{rank}  " + ' '.join(row))
        rows.append('    a  b  c  d  e  f  g  h')
        return '\n'.join(rows)

    def in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def copy(self):
        b = Board.__new__(Board)
        b.squares = [row[:] for row in self.squares]
        b.turn = self.turn
        b.castling_rights = getattr(self, 'castling_rights', set()).copy()
        b.ep_target = getattr(self, 'ep_target', None)
        return b

    def make_move(self, m: Move):
        piece = self.squares[m.from_row][m.from_col]
        target = self.squares[m.to_row][m.to_col]
        original_piece = piece
        self.ep_target = None

        if original_piece[1] == 'K' and abs(m.to_col - m.from_col) == 2:
            if m.to_col > m.from_col:
                rook_from_col, rook_to_col = 7, 5
            else:
                rook_from_col, rook_to_col = 0, 3
            self.squares[m.from_row][rook_to_col] = self.squares[m.from_row][rook_from_col]
            self.squares[m.from_row][rook_from_col] = EMPTY

        if original_piece[1] == 'P' and target == EMPTY and m.from_col != m.to_col:
            self.squares[m.from_row][m.to_col] = EMPTY

        if original_piece[1] == 'P' and abs(m.to_row - m.from_row) == 2:
            self.ep_target = ((m.from_row + m.to_row) // 2, m.from_col)

        if m.promotion:
            piece = piece[0] + m.promotion
        self.squares[m.to_row][m.to_col] = piece
        self.squares[m.from_row][m.from_col] = EMPTY
        self.update_castling_rights(original_piece, target, m)
        self.turn = 'b' if self.turn == 'w' else 'w'

    def update_castling_rights(self, piece, captured, move):
        if not hasattr(self, 'castling_rights'):
            self.castling_rights = set()

        if piece == 'wK':
            self.castling_rights.discard('K')
            self.castling_rights.discard('Q')
        elif piece == 'bK':
            self.castling_rights.discard('k')
            self.castling_rights.discard('q')
        elif piece == 'wR':
            if (move.from_row, move.from_col) == (7, 7):
                self.castling_rights.discard('K')
            elif (move.from_row, move.from_col) == (7, 0):
                self.castling_rights.discard('Q')
        elif piece == 'bR':
            if (move.from_row, move.from_col) == (0, 7):
                self.castling_rights.discard('k')
            elif (move.from_row, move.from_col) == (0, 0):
                self.castling_rights.discard('q')

        if captured == 'wR':
            if (move.to_row, move.to_col) == (7, 7):
                self.castling_rights.discard('K')
            elif (move.to_row, move.to_col) == (7, 0):
                self.castling_rights.discard('Q')
        elif captured == 'bR':
            if (move.to_row, move.to_col) == (0, 7):
                self.castling_rights.discard('k')
            elif (move.to_row, move.to_col) == (0, 0):
                self.castling_rights.discard('q')

    def find_king(self, color):
        target = color + 'K'
        for r in range(8):
            for c in range(8):
                if self.squares[r][c] == target:
                    return r, c
        raise ValueError(f"No {color} king on board")

    def is_attacked(self, r, c, by_color):
        for sr in range(8):
            for sc in range(8):
                p = self.squares[sr][sc]
                if p == EMPTY or p[0] != by_color:
                    continue
                if (r, c) in attacked_squares(self, sr, sc):
                    return True
        return False

    def pseudo_legal_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                p = self.squares[r][c]
                if p == EMPTY or p[0] != self.turn:
                    continue
                moves.extend(piece_moves(self, r, c))
        return moves

    def legal_moves(self):
        legal = []
        for m in self.pseudo_legal_moves():
            nb = self.copy()
            nb.make_move(m)
            kr, kc = nb.find_king(self.turn)
            if not nb.is_attacked(kr, kc, nb.turn):
                legal.append(m)
        return legal


def piece_moves(board, r, c):
    p = board.squares[r][c]
    color, kind = p[0], p[1]
    if kind == 'P':
        return pawn_moves(board, r, c, color)
    if kind == 'N':
        return jump_moves(board, r, c, color, KNIGHT_DIRS)
    if kind == 'B':
        return slide_moves(board, r, c, color, BISHOP_DIRS)
    if kind == 'R':
        return slide_moves(board, r, c, color, ROOK_DIRS)
    if kind == 'Q':
        return slide_moves(board, r, c, color, QUEEN_DIRS)
    if kind == 'K':
        return king_moves(board, r, c, color)
    return []


def attacked_squares(board, r, c):
    p = board.squares[r][c]
    color, kind = p[0], p[1]
    out = []
    if kind == 'P':
        direction = -1 if color == 'w' else 1
        for dc in (-1, 1):
            nr, nc = r + direction, c + dc
            if board.in_bounds(nr, nc):
                out.append((nr, nc))
    elif kind == 'N':
        for dr, dc in KNIGHT_DIRS:
            nr, nc = r + dr, c + dc
            if board.in_bounds(nr, nc):
                out.append((nr, nc))
    elif kind == 'K':
        for dr, dc in KING_DIRS:
            nr, nc = r + dr, c + dc
            if board.in_bounds(nr, nc):
                out.append((nr, nc))
    else:
        if kind == 'B': dirs = BISHOP_DIRS
        elif kind == 'R': dirs = ROOK_DIRS
        else: dirs = QUEEN_DIRS
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while board.in_bounds(nr, nc):
                out.append((nr, nc))
                if board.squares[nr][nc] != EMPTY:
                    break
                nr += dr
                nc += dc
    return out


def jump_moves(board, r, c, color, dirs):
    moves = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if not board.in_bounds(nr, nc):
            continue
        target = board.squares[nr][nc]
        if target == EMPTY or target[0] != color:
            moves.append(Move(r, c, nr, nc))
    return moves


def king_moves(board, r, c, color):
    moves = jump_moves(board, r, c, color, KING_DIRS)
    home_row = 7 if color == 'w' else 0
    opponent = 'b' if color == 'w' else 'w'
    king_side = 'K' if color == 'w' else 'k'
    queen_side = 'Q' if color == 'w' else 'q'
    rights = getattr(board, 'castling_rights', set())

    if (r, c) != (home_row, 4) or board.is_attacked(home_row, 4, opponent):
        return moves

    if (king_side in rights
            and board.squares[home_row][5] == EMPTY
            and board.squares[home_row][6] == EMPTY
            and board.squares[home_row][7] == color + 'R'
            and not board.is_attacked(home_row, 5, opponent)
            and not board.is_attacked(home_row, 6, opponent)):
        moves.append(Move(home_row, 4, home_row, 6))

    if (queen_side in rights
            and board.squares[home_row][1] == EMPTY
            and board.squares[home_row][2] == EMPTY
            and board.squares[home_row][3] == EMPTY
            and board.squares[home_row][0] == color + 'R'
            and not board.is_attacked(home_row, 3, opponent)
            and not board.is_attacked(home_row, 2, opponent)):
        moves.append(Move(home_row, 4, home_row, 2))

    return moves


def slide_moves(board, r, c, color, dirs):
    moves = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        while board.in_bounds(nr, nc):
            target = board.squares[nr][nc]
            if target == EMPTY:
                moves.append(Move(r, c, nr, nc))
            elif target[0] != color:
                moves.append(Move(r, c, nr, nc))
                break
            else:
                break
            nr += dr
            nc += dc
    return moves


def pawn_moves(board, r, c, color):
    moves = []
    direction = -1 if color == 'w' else 1
    start_row = 6 if color == 'w' else 1
    promo_row = 0 if color == 'w' else 7

    nr = r + direction
    if board.in_bounds(nr, c) and board.squares[nr][c] == EMPTY:
        if nr == promo_row:
            for promo in 'QRBN':
                moves.append(Move(r, c, nr, c, promotion=promo))
        else:
            moves.append(Move(r, c, nr, c))
            if r == start_row:
                nr2 = r + 2 * direction
                if board.squares[nr2][c] == EMPTY:
                    moves.append(Move(r, c, nr2, c))

    for dc in (-1, 1):
        nr, nc = r + direction, c + dc
        if not board.in_bounds(nr, nc):
            continue
        target = board.squares[nr][nc]
        if target != EMPTY and target[0] != color:
            if nr == promo_row:
                for promo in 'QRBN':
                    moves.append(Move(r, c, nr, nc, promotion=promo))
            else:
                moves.append(Move(r, c, nr, nc))
        elif getattr(board, 'ep_target', None) == (nr, nc):
            moves.append(Move(r, c, nr, nc))

    return moves
