# TODO: Implement Schema
# TODO: Implement send()
# TODO: Implement receive()
from custom_types.fields import UserID, Token, Timestamp, MessageID, TTL
from datetime import datetime, timezone
from utils import msg_format
from custom_types.base_message import BaseMessage

from states.client_state import client_state
import socket


class TicTacToeResult(BaseMessage):
    """
    Represents a TICTACTOE_RESULT message announcing the outcome of a game.
    """

    TYPE = "TICTACTOE_RESULT"
    __hidden__ = True
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "TO": {"type": UserID, "required": True},
        "GAMEID": {"type": str, "required": True},
        "MESSAGE_ID": {"type": MessageID, "required": True},
        "RESULT": {"type": str, "required": True},   # WIN, LOSS, DRAW, FORFEIT
        "SYMBOL": {"type": str, "required": True},   # X or O
        "WINNING_LINE": {"type": str, "required": True},  # e.g., [0, 1, 2]
        "TURN": {"type": int, "required": True},
        "TOKEN": {"type": Token, "required": True},
        "TIMESTAMP": {"type": Timestamp, "required": True}
    }

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "TO": self.to_user,
            "GAMEID": self.game_id,
            "MESSAGE_ID": self.message_id,
            "RESULT": self.result,
            "SYMBOL": self.symbol,
            "WINNING_LINE": self.winning_line,
            "TURN": self.turn,
            "TIMESTAMP": self.timestamp,
            "TOKEN": self.token
            
        }

    def __init__(self, to: UserID, gameid: str, result: str, symbol: str,
                 winning_line: list, turn: int, ttl: TTL = 3600):
        """
        Initialize a TicTacToeResult message.
        
        Args:
            to: Recipient's UserID
            gameid: Game session ID
            result: One of WIN, LOSS, DRAW, FORFEIT
            symbol: X or O
            winning_line: List of positions (0-8) that formed the win
            turn: The final turn number
            ttl: Time to live for token
        """
        valid_results = {"WIN", "LOSS", "DRAW", "FORFEIT"}
        result = result.upper()
        if result not in valid_results:
            raise ValueError("Invalid result. Must be WIN, LOSS, DRAW, or FORFEIT")

        symbol = str(symbol).upper()
        if symbol not in {"X", "O"}:
            raise ValueError("Symbol must be 'X' or 'O'")

       # if not isinstance(winning_line, list) or not all(isinstance(pos, int) and 0 <= pos <= 8 for pos in winning_line):
       #     raise ValueError("WINNING_LINE must be a list of integers between 0 and 8")

        unix_now = int(datetime.now(timezone.utc).timestamp())

        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        self.game_id = str(gameid)
        self.result = result
        self.symbol = symbol
        self.winning_line = winning_line
        self.turn = msg_format.sanitize_turn(turn)
        self.message_id = MessageID.generate()
        self.token = Token(self.from_user, Timestamp(unix_now) + ttl, Token.Scope.GAME)
        self.timestamp = Timestamp(unix_now)

    @classmethod
    def parse(cls, data: dict) -> "TicTacToeResult":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])
        new_obj.game_id = data["GAMEID"]
        new_obj.result = data["RESULT"]
        new_obj.symbol = data["SYMBOL"]
        new_obj.winning_line = data["WINNING_LINE"]
        new_obj.turn = msg_format.sanitize_turn(data["TURN"])

        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        new_obj.message_id = MessageID.parse(data["MESSAGE_ID"]) 
        new_obj.token = Token.parse(data["TOKEN"])
        Token.validate_token(new_obj.token, expected_scope=Token.Scope.GAME, expected_user_id=new_obj.from_user)

        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    def send(self, socket: socket.socket, ip: str, port: int, encoding: str = "utf-8"):
        """Send game result to other player."""
        if ip == "default":
            ip = self.to_user.get_ip()
        return super().send(socket, ip, port, encoding)

    @classmethod
    def receive(cls, raw: str) -> "TicTacToeResult":
        """Process received game result and return result object."""
        result_received = cls.parse(msg_format.deserialize_message(raw))
        if result_received.to_user != client_state.get_user_id():
            raise ValueError("Message is not intended to be received by this client")
        print(f"Received game result: {result_received.result} from {result_received.from_user}")
        return result_received

    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}\n"
        else:
            return f"Player {self.symbol} wins the game {self.game_id}!\nWinning line: {self.winning_line}"

__message__ = TicTacToeResult
