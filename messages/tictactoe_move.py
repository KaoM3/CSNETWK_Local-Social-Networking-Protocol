# TODO: Implement Schema
# TODO: Implement send()
# TODO: Implement receive()

from custom_types.user_id import UserID
from custom_types.token import Token
from datetime import datetime, timezone
from utils import msg_format
from custom_types.base_message import BaseMessage
from states.client_state import client_state
import socket

class TicTacToeMove(BaseMessage):
    """
    Represents a TICTACTOE_MOVE message for game moves.
    """
    
    TYPE = "TICTACTOE_MOVE"
    __hidden__ = False
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "TO": {"type": UserID, "required": True},
        "GAMEID": {"type": str, "required": True},
        "MESSAGE_ID": {"type": str, "required": True},
        "POSITION": {"type": int, "required": True},
        "SYMBOL": {"type": str, "required": True},
        "TURN": {"type": int, "required": True},
        "TOKEN": {"type": Token, "required": True}
    }

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "TO": self.to_user,
            "GAMEID": self.game_id,
            "MESSAGE_ID": self.message_id,
            "POSITION": self.position,
            "SYMBOL": self.symbol,
            "TURN": self.turn,
            "TOKEN": self.token
        }

    def __init__(self, to: UserID, gameid: str, position: int, 
                 symbol: str, turn: int, ttl: int = 3600):
        """
        Initialize a new TicTacToe move.
        
        Args:
            from_: Sender's UserID
            to: Recipient's UserID
            gameid: Game session identifier
            position: Integer 0-8 representing board position
            symbol: Must be either 'X' or 'O'
            turn: Turn number in the game
            ttl: Time to live in seconds (default 3600)
        """
        
        try:
            position = int(position)
        except (TypeError, ValueError):
            raise ValueError("Position must be a valid integer")
            
        if not (0 <= position <= 8):
            raise ValueError("Position must be between 0 and 8")
        
        # Validate symbol
        symbol = str(symbol).upper()
        if symbol not in ['X', 'O']:
            raise ValueError("Symbol must be either 'X' or 'O'")

        # Convert turn to int
        try:
            turn = int(turn)
        except (TypeError, ValueError):
            raise ValueError("Turn must be a valid integer")

        unix_now = int(datetime.now(timezone.utc).timestamp())
        
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        self.game_id = str(gameid)
        self.position = msg_format.sanitize_position(position)
        self.symbol = symbol
        self.turn = msg_format.sanitize_position(turn)
        self.message_id = msg_format.generate_message_id()
        self.token = Token(self.from_user, unix_now + ttl, Token.Scope.GAME)

    @classmethod
    def parse(cls, data: dict) -> "TicTacToeMove":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"] 
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])

        new_obj.game_id = data["GAMEID"]
        #for future add a way to check if game_id is valid
        
        new_obj.position = msg_format.sanitize_position(data["POSITION"])

        new_obj.symbol = data["SYMBOL"]
        new_obj.turn = msg_format.sanitize_position(data["TURN"])

        message_id = data["MESSAGE_ID"]
        msg_format.validate_message_id(message_id)
        new_obj.message_id = message_id

        new_obj.token = Token.parse(data["TOKEN"])
        msg_format.validate_token(new_obj.token, expected_scope=Token.Scope.GAME, expected_user_id=new_obj.from_user)

        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj


    def send(self, socket: socket.socket, ip: str, port: int, encoding: str = "utf-8"):
        """Sends game move to other player and updates game state"""
        msg = msg_format.serialize_message(self.payload)
        socket.sendto(msg.encode(encoding), (self.to_user.get_ip(), port))
        print(f"Move sent to {self.to_user} at position {self.position}")


     
    @classmethod
    def receive(cls, raw: str) -> "TicTacToeMove":
        """Process received game move and update game state"""
        move_received = cls.parse(msg_format.deserialize_message(raw))   
        print(f"Received move: {move_received.from_user} at position {move_received.position}")
        return move_received



__message__ = TicTacToeMove