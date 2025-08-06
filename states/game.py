# game.py

import threading
import log
from typing import Dict, Optional
from custom_types.user_id import UserID


class GameState:
    """Tracks the state of TicTacToe games and prints the board only."""

    def __init__(self):
        self.board = [' '] * 9

    def get_board_string(self) -> str:
        """Returns the current game board as a string."""
        return (
            "\nCurrent Board:\n"
            f" {self.board[0]} | {self.board[1]} | {self.board[2]} \n"
            "-----------\n"
            f" {self.board[3]} | {self.board[4]} | {self.board[5]} \n"
            "-----------\n"
            f" {self.board[6]} | {self.board[7]} | {self.board[8]} "
        )

    def print_board(self):
        """Prints the current game board."""
        print(self.get_board_string())

    def move(self, position: int, symbol: str):
        """Make a move on the board."""
        if position < 0 or position > 8:
            raise ValueError("Position must be between 0 and 8")
        if self.board[position] != ' ':
            raise ValueError("Position already taken")
        if symbol not in ['X', 'O']:
            raise ValueError("Symbol must be either 'X' or 'O'")
        #???
        self.board[position] = symbol
        log.info(f"Player {symbol} moved to position {position}")


       

if __name__ == "__main__":
    game = GameState()
    game.board[3] = 'X'
    game.print_board()
