import threading
import log
from typing import Dict, Optional
from custom_types.user_id import UserID

class GameState:
    """Tracks the state of TicTacToe games and prints the board only."""

    def __init__(self):
        self.board = [' '] * 9
        self.last_symbol: Optional[str] = None  

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
        self.board[position] = symbol
        self.last_symbol = symbol  # ✅ Save the last move symbol
        log.info(f"Player {symbol} moved to position {position}")


class GameSessionManager:
    """Manages multiple game sessions identified by game_id."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, GameState] = {}

    def create_game(self, game_id: str) -> GameState:
        """Creates a new game session with the given game_id."""
        with self._lock:
            if game_id in self._sessions:
                raise ValueError(f"Game with ID '{game_id}' already exists.")
            self._sessions[game_id] = GameState()
            log.info(f"Created new game with ID: {game_id}")
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
                log.info(f"Deleted game with ID: {game_id}")
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





game_session_manager = GameSessionManager()
