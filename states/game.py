import threading
from client_logger import client_logger
from typing import Dict, Optional


class GameState:
    """Tracks the state of TicTacToe games and prints the board only."""

    def __init__(self):
        self.board = [' '] * 9
        self.last_symbol: Optional[str] = None  
        self.turn = 1  
        self.player_x: Optional[str] = None
        self.player_o: Optional[str] = None
        self.starting_symbol: str = "X"  # X always starts unless changed


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

    def move(self, user_id: str, position: int):
        """
        Validates and makes a move for the given user.
        
        Raises:
            ValueError: If player is invalid, it's not their turn, 
                        position is invalid, or symbol is invalid.
        """
        # Validate player and turn
        if user_id not in [self.player_x, self.player_o]:
            raise ValueError(f"User {user_id} is not a player in this game")

        if user_id == self.player_x:
            if self.turn % 2 != 1:
                raise ValueError(f"Player X ({user_id}) can only move on turns 1, 3, 5, etc. Current turn: {self.turn}")
            symbol = 'X'
        else:  # user_id == self.player_o
            if self.turn % 2 != 0:
                raise ValueError(f"Player O ({user_id}) can only move on turns 2, 4, 6, etc. Current turn: {self.turn}")
            symbol = 'O'

        # Validate position
        if not (0 <= position <= 8):
            raise ValueError("Position must be between 0 and 8")
        if self.board[position] != ' ':
            raise ValueError("Position already taken")

        # Make the move
        self.board[position] = symbol
        self.last_symbol = symbol
        self.turn += 1
        client_logger.info(f"Player {symbol} ({user_id}) moved to position {position}")


class GameSessionManager:
    """Manages multiple game sessions identified by game_id."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, GameState] = {}

    def get_turn(self, game_id: str) -> int:
        """Returns the current turn number for the specified game."""
        game = self.find_game(game_id)
        return game.turn


    def assign_players(self, game_id: str, player_x: str, player_o: str):
        """Assigns players to X and O for a specific game."""
        game = self.find_game(game_id)
        if not game:
            raise ValueError(f"Game with ID '{game_id}' does not exist.")
        game.player_x = player_x
        game.player_o = player_o
        client_logger.info(f"Assigned {player_x} as X and {player_o} as O in game {game_id}")



    def get_player_symbol(self, game_id: str, user_id: str) -> Optional[str]:
        """Returns the symbol of the player in the game."""
        game = self.find_game(game_id)
        if not game:
            raise ValueError(f"Game with ID '{game_id}' does not exist.")

        if user_id == game.player_x:
            return 'X'
        elif user_id == game.player_o:
            return 'O'
        
        return None

    def create_game(self, game_id: str) -> GameState:
        """Creates a new game session with the given game_id."""
        with self._lock:
            if game_id in self._sessions:
                raise ValueError(f"Game with ID '{game_id}' already exists.")
            self._sessions[game_id] = GameState()
            client_logger.info(f"Created new game with ID: {game_id}")
            return self._sessions[game_id]

    def find_game(self, game_id: str) -> Optional[GameState]:
        """Finds an existing game by game_id."""
        with self._lock:
            return self._sessions.get(game_id)

    def delete_game(self, game_id: str) -> bool:
        """Deletes a game session."""
        with self._lock:
            if game_id in self._sessions:
                del self._sessions[game_id]
                client_logger.info(f"Deleted game with ID: {game_id}")
                return True
            return False

    def list_game_ids(self) -> list:
        """Returns a list of all active game IDs."""
        with self._lock:
            return list(self._sessions.keys())
        
    def is_winning_move(self, game_id: str) -> bool:
        """Check if the last move results in a win."""
        game = self.find_game(game_id)
        if not game or not game.last_symbol:
            return False
        
        symbol = game.last_symbol  

        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  
            [0, 4, 8], [2, 4, 6]              
        ]

        for combo in winning_combinations:
            if all(game.board[i] == symbol for i in combo):
                return True

        return False
    
    def find_winning_line(self, game_id: str) -> Optional[str]:
        """Finds and returns the winning line as a comma-separated string, e.g., '0,1,2'."""
        game = self.find_game(game_id)
        if not game or not game.last_symbol:
            return None

        symbol = game.last_symbol

        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]

        for combo in winning_combinations:
            if all(game.board[i] == symbol for i in combo):
                return ",".join(str(pos) for pos in combo)  

        return None


# Global instance
game_session_manager = GameSessionManager()
