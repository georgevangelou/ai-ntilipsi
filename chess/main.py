from game import Board
from ui import ChessGameUI

def main():
    board = Board()
    ui = ChessGameUI(board)
    ui.run()

if __name__ == "__main__":
    main()