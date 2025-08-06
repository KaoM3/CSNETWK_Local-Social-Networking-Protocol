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



       


