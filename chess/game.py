from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
from constants import PAWN, ROOK, KNIGHT, BISHOP, QUEEN, KING

@dataclass
class Position:
    row: int
    col: int

class Piece:
    def __init__(self, type: str, color: str, row: int, col: int):
        self.type = type
        self.color = color  # 'white' or 'black'
        self.row = row
        self.col = col
        self.has_moved = False

    def __repr__(self):
        return f"{self.color} {self.type} at ({self.row}, {self.col})"

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.turn = 'white'
        self.setup_board()
        self.game_over = False
        self.winner = None
        self.history = []

    def setup_board(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        # Black pieces
        self.grid[0][0] = Piece(ROOK, 'black', 0, 0)
        self.grid[0][1] = Piece(KNIGHT, 'black', 0, 1)
        self.grid[0][2] = Piece(BISHOP, 'black', 0, 2)
        self.grid[0][3] = Piece(QUEEN, 'black', 0, 3)
        self.grid[0][4] = Piece(KING, 'black', 0, 4)
        self.grid[0][5] = Piece(BISHOP, 'black', 0, 5)
        self.grid[0][6] = Piece(KNIGHT, 'black', 0, 6)
        self.grid[0][7] = Piece(ROOK, 'black', 0, 7)
        for i in range(8):
            self.grid[1][i] = Piece(PAWN, 'black', 1, i)
        
        # White pieces
        for i in range(8):
            self.grid[6][i] = Piece(PAWN, 'white', 6, i)
        self.grid[7][0] = Piece(ROOK, 'white', 7, 0)
        self.grid[7][1] = Piece(KNIGHT, 'white', 7, 1)
        self.grid[7][2] = Piece(BISHOP, 'white', 7, 2)
        self.grid[7][3] = Piece(QUEEN, 'white', 7, 3)
        self.grid[7][4] = Piece(KING, 'white', 7, 4)
        self.grid[7][5] = Piece(BISHOP, 'white', 7, 5)
        self.grid[7][6] = Piece(KNIGHT, 'white', 7, 6)
        self.grid[7][7] = Piece(ROOK, 'white', 7, 7)

    def get_piece_at(self, row: int, col: int) -> Optional[Piece]:
        if 0 <= row < 8 and 0 <= col < 8:
            return self.grid[row][col]
        return None

    def is_on_board(self, row: int, col: int) -> bool:
        return 0 <= row < 8 and 0 <= col < 8

    def get_raw_moves(self, row: int, col: int, piece: Piece) -> List[Tuple[int, int]]:
        moves = []
        if piece.type == PAWN:
            direction = -1 if piece.color == 'white' else 1
            # Forward move
            if self.is_on_board(row + direction, col) and self.get_piece_at(row + direction, col) is None:
                moves.append((row + direction, col))
                if (piece.color == 'white' and row == 6) or (piece.color == 'black' and row == 1):
                    if self.is_on_board(row + 2 * direction, col) and self.get_piece_at(row + 2 * direction, col) is None and self.get_piece_at(row + direction, col) is None:
                        moves.append((row + 2 * direction, col))
            # Captures
            for dc in [-1, 1]:
                if self.is_on_board(row + direction, col + dc):
                    target = self.get_piece_at(row + direction, col + dc)
                    if target and target.color != piece.color:
                        moves.append((row + direction, col + dc))
            # En Passant
            if (piece.color == 'white' and row == 6) or (piece.color == 'black' and row == 1):
                for dc in [-1, 1]:
                    if self.is_on_board(row + direction, col + dc):
                        target = self.get_piece_at(row + direction, col + dc)
                        if target and target.type == PAWN and target.color != piece.color:
                            moves.append((row + direction, col + dc))

        elif piece.type == ROOK:
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while self.is_on_board(r, c):
                    target = self.get_piece_at(r, c)
                    if target:
                        if target.color != piece.color: moves.append((r, c))
                        break
                    moves.append((r, c))
                    r += dr
                    c += dc
        elif piece.type == KNIGHT:
            moves_list = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
            for dr, dc in moves_list:
                r, c = row + dr, col + dc
                if self.is_on_board(r, c):
                    target = self.get_piece_at(r, c)
                    if target is None or target.color != piece.color:
                        moves.append((r, c))
        elif piece.type == BISHOP:
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while self.is_on_board(r, c):
                    target = self.get_piece_at(r, c)
                    if target:
                        if target.color != piece.color: moves.append((r, c))
                        break
                    moves.append((r, c))
                    r += dr
                    c += dc
        elif piece.type == QUEEN:
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while self.is_on_board(r, c):
                    target = self.get_piece_at(r, c)
                    if target:
                        if target.color != piece.color: moves.append((r, c))
                        break
                    moves.append((r, c))
                    r += dr
                    c += dc
        elif piece.type == KING:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    r, c = row + dr, col + dc
                    if self.is_on_board(r, c):
                        target = self.get_piece_at(r, c)
                        if target is None or target.color != piece.color:
                            moves.append((r, c))
            # Castling
            if not piece.has_moved:
                if piece.color == 'white' and row == 7 and col == 4:
                    # Kingside
                    if self.get_piece_at(7, 5) is None and self.get_piece_at(7, 6) is None and self.get_piece_at(7, 7) is not None:
                        moves.append((7, 6))
                    # Queenside
                    if self.get_piece_at(7, 3) is not None and self.get_piece_at(7, 2) is None and self.get_piece_at(7, 1) is not None:
                        moves.append((7, 2))
                elif piece.color == 'black' and row == 0 and col == 4:
                    # Kingside
                    if self.get_piece_at(0, 5) is None and self.get_piece_at(0, 6) is None and self.get_piece_at(0, 7) is not None:
                        moves.append((0, 6))
                    # Queenside
                    if self.get_piece_at(0, 3) is not None and self.get_piece_at(0, 2) is None and self.get_piece_at(0, 1) is not None:
                        moves.append((0, 2))

        return list(set(moves))

    def get_valid_moves(self, start_pos: Tuple[int, int], current_turn: str) -> List[Tuple[int, int]]:
        start_row, start_col = start_pos
        piece = self.get_piece_at(start_row, start_col)
        
        if piece is None or piece.color != current_turn:
            return []

        possible_moves = self.get_raw_moves(start_row, start_col, piece)
        
        legal_moves = []
        for move in possible_moves:
            if move == (start_row, start_col): continue
            
            # Simulate move
            temp_piece = self.grid[start_row][start_col]
            self.grid[move[0]][move[1]] = temp_piece
            self.grid[start_row][start_col] = None
            
            # Verify all pieces are accounted for during simulation
            if not self._verify_all_pieces_on_board():
                continue
            
            if not self.is_king_in_check(current_turn):
                legal_moves.append(move)
            
            # Undo move
            self.grid[start_row][start_col] = temp_piece
            self.grid[move[0]][move[1]] = None
            
        return legal_moves

    def is_king_in_check(self, color: str) -> bool:
        king = None
        for r in range(8):
            for c in range(8):
                p = self.get_piece_at(r, c)
                if p and p.type == KING and p.color == color:
                    king = (r, c)
                    break
            if king: break
        
        if not king:
            return False
        
        enemy_color = 'black' if color == 'white' else 'white'
        for r in range(8):
            for c in range(8):
                p = self.get_piece_at(r, c)
                if p and p.color == enemy_color:
                    moves = self.get_raw_moves(r, c, p)
                    if king in moves:
                        return True
        return False

    def move_piece(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> bool:
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        
        piece = self.get_piece_at(start_row, start_col)
        if piece is None or piece.color != self.turn:
            return False
        
        valid_moves = self.get_valid_moves(start_pos, self.turn)
        if end_pos not in valid_moves:
            return False
        
        # Execute move
        target = self.get_piece_at(end_row, end_col)
        if target and target.color == piece.color:
            return False
        
        # Handle Promotion
        if piece.type == PAWN and ((piece.color == 'white' and end_row == 0) or (piece.color == 'black' and end_row == 7)):
            piece.type = QUEEN

        # Handle En Passant Capture
        if piece.type == PAWN:
            direction = -1 if piece.color == 'white' else 1
            capture_row = end_row + direction
            if self.is_on_board(capture_row, end_col):
                captured_piece = self.grid[capture_row][end_col]
                if captured_piece and captured_piece.type == PAWN:
                    self.grid[capture_row][end_col] = None

        # Handle Castling
        is_castling = False
        if piece.type == KING and not piece.has_moved and start_row == end_row and abs(start_col - end_col) == 2:
            is_castling = True

        piece.row = end_row
        piece.col = end_col
        piece.has_moved = True
        
        # Update board state BEFORE checking for check
        self.grid[end_row][end_col] = piece
        self.grid[start_row][start_col] = None
        
        if is_castling:
            if end_col == 6:  # Kingside
                # Rook moves from 7 to 5
                rook = self.grid[start_row][7]
                self.grid[start_row][5] = rook
                self.grid[start_row][7] = None
                rook.has_moved = True
            else:  # Queenside
                # Rook moves from 0 to 3
                rook = self.grid[start_row][0]
                self.grid[start_row][3] = rook
                self.grid[start_row][0] = None
                rook.has_moved = True
        
        if is_castling:
            if end_col == 6: # Kingside
                # Rook moves from 7 to 5
                self.grid[start_row][5] = self.grid[start_row][7]
                self.grid[start_row][7] = None
            else: # Queenside
                # Rook moves from 0 to 3
                self.grid[start_row][3] = self.grid[start_row][0]
                self.grid[start_row][0] = None

        # Record move
        self.history.append(f"{self.turn} moved {start_pos} to {end_pos}")

        # Verify all pieces are accounted for on the board
        self._verify_all_pieces_on_board()

        # Switch turn
        self.turn = 'black' if self.turn == 'white' else 'white'

        # Check for game over
        if self.is_checkmate(self.turn):
            self.game_over = True
            self.winner = 'black' if self.turn == 'white' else 'white'
        elif self.is_stalemate():
            self.game_over = True
            self.winner = None

        return True

    def is_checkmate(self, color: str) -> bool:
        all_moves = []
        for r in range(8):
            for c in range(8):
                p = self.get_piece_at(r, c)
                if p and p.color == color:
                    all_moves.extend(self.get_valid_moves((r, c), color))
        
        if not all_moves:
            return self.is_king_in_check(color)
        return False

    def is_stalemate(self) -> bool:
        all_moves = []
        for r in range(8):
            for c in range(8):
                p = self.get_piece_at(r, c)
                if p and p.color == self.turn:
                    all_moves.extend(self.get_valid_moves((r, c), self.turn))
        
        if not all_moves and not self.is_king_in_check(self.turn):
            return True
        return False

    def _verify_all_pieces_on_board(self) -> bool:
        """Verify that all pieces are properly tracked on the board."""
        piece_count = 0
        for row in range(8):
            for col in range(8):
                if self.grid[row][col]:
                    piece_count += 1
        
        # Standard chess has 32 pieces (16 white, 16 black)
        if piece_count != 32:
            print(f"Warning: Board has {piece_count} pieces instead of expected 32")
            return False
        return True