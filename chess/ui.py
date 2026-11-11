import pygame
from typing import Tuple, Optional
from constants import *
from game import Board

class ChessGameUI:
    def __init__(self, board: Board):
        pygame.init()
        self.screen = pygame.display.set_mode((600, 600))
        pygame.display.set_caption("Chess")
        self.board = board
        self.selected_sq: Optional[Tuple[int, int]] = None
        self.running = True
        self.font = pygame.font.SysFont("Arial", 32)

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                color = BOARD_LIGHT if (row + col) % 2 == 0 else BOARD_DARK
                pygame.draw.rect(self.screen, color, (col * 75, row * 75, 75, 75))

    def draw_pieces(self):
        for row in range(8):
            for col in range(8):
                piece = self.board.grid[row][col]
                if piece:
                    color = WHITE_PIECE if piece.color == 'white' else BLACK_PIECE
                    # Draw a circle for the piece for now
                    pygame.draw.circle(self.screen, color, (col * 75 + 37, row * 75 + 37), 30)
                    # Label the piece
                    text = self.font.render(piece.type, True, (0, 0, 0) if piece.color == 'black' else (255, 255, 255))
                    self.screen.blit(text, (col * 75 + 30, row * 75 + 30))

    def draw_history(self):
        # Show the last 5 moves
        history = self.board.history[-5:]
        for i, move in enumerate(history):
            text = self.font.render(move, True, (0, 0, 0))
            # Position the text
            self.screen.blit(text, (10, 40 + i * 30))
        for row in range(8):
            for col in range(8):
                piece = self.board.grid[row][col]
                if piece:
                    color = WHITE_PIECE if piece.color == 'white' else BLACK_PIECE
                    # Draw a circle for the piece for now
                    pygame.draw.circle(self.screen, color, (col * 75 + 37, row * 75 + 37), 30)
                    # Label the piece
                    text = self.font.render(piece.type, True, (0, 0, 0) if piece.color == 'black' else (255, 255, 255))
                    self.screen.blit(text, (col * 75 + 30, row * 75 + 30))

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    col, row = x // 75, y // 75
                    
                    if self.selected_sq is None:
                        piece = self.board.get_piece_at(row, col)
                        if piece and piece.color == self.board.turn:
                            self.selected_sq = (row, col)
                    else:
                        if self.board.move_piece(self.selected_sq, (row, col)):
                            self.selected_sq = None
                        else:
                            # If move is invalid, select the new piece if it's our turn
                            new_piece = self.board.get_piece_at(row, col)
                            if new_piece and new_piece.color == self.board.turn:
                                self.selected_sq = (row, col)
                            else:
                                self.selected_sq = None
            
            self.screen.fill(WHITE)
            self.draw_board()
            self.draw_pieces()
            self.draw_history()
            
            if self.selected_sq:
                pygame.draw.rect(self.screen, HIGHLIGHT, (self.selected_sq[1] * 75, self.selected_sq[0] * 75, 75, 75))
                
                # Show legal moves
                legal_moves = self.board.get_valid_moves(self.selected_sq, self.board.turn)
                for move in legal_moves:
                    pygame.draw.circle(self.screen, (0, 255, 0), (move[1] * 75 + 37, move[0] * 75 + 37), 10)
            
            # Display turn
            turn_text = self.font.render(f"Turn: {self.board.turn}", True, (0, 0, 0))
            self.screen.blit(turn_text, (10, 10))
            
            if self.board.game_over:
                msg = "Game Over!" if self.board.winner else "Stalemate"
                winner_text = f"Winner: {self.board.winner}" if self.board.winner else "Draw"
                game_over_text = self.font.render(f"{msg} {winner_text}", True, (255, 0, 0))
                self.screen.blit(game_over_text, (150, 250))
            
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()