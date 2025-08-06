# TODO: Implement Schema
# TODO: Implement send()
# TODO: Implement receive()
# TODO: Implement filter()

from datetime import datetime, timezone
import socket
import random

from custom_types.user_id import UserID
from custom_types.token import Token
from custom_types.base_message import BaseMessage
from utils import msg_format
from states.client_state import client_state


class TicTacToeInvite(BaseMessage):
    """
    Represents a TICTACTOE_INVITE message for initiating a game.
    """
    
    TYPE = "TICTACTOE_INVITE"
    __hidden__ = False
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "TO": {"type": UserID, "required": True},
        "GAMEID": {"type": str, "required": True},
        "SYMBOL": {"type": str, "required": True},
        "MESSAGE_ID": {"type": str, "required": True},
        "TIMESTAMP": {"type": int, "required": True},
        "TOKEN": {"type": Token, "required": True},
    }

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "TO": self.to_user,
            "GAMEID": self.game_id,
            "SYMBOL": self.symbol,
            "MESSAGE_ID": self.message_id,
            "TIMESTAMP": self.timestamp,
            "TOKEN": self.token,
        }

    def __init__(self, to: UserID, symbol: str, ttl: int = 3600):
        """Initialize game invitation with validation"""
        unix_now = int(datetime.now(timezone.utc).timestamp())

        # Validate symbol
        symbol = symbol.upper() 
        if symbol not in ['X', 'O']:
            raise ValueError("Symbol must be either 'X' or 'O'")
        
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        self.game_id = f"g{random.randint(0, 255)}"
        self.symbol = symbol
        self.timestamp = unix_now
        self.message_id = msg_format.generate_message_id()
        self.token = Token(self.from_user, unix_now + ttl, Token.Scope.GAME)


    @classmethod
    def parse(cls, data: dict) -> "TicTacToeInvite":
        """Parse a dictionary to reconstruct a TicTacToeInvite instance"""
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])
        new_obj.game_id = data["GAMEID"]
        new_obj.symbol = data["SYMBOL"]

        timestamp = int(data["TIMESTAMP"])
        msg_format.validate_timestamp(timestamp)
        new_obj.timestamp = timestamp

        message_id = data["MESSAGE_ID"]
        msg_format.validate_message_id(message_id)
        new_obj.message_id = message_id

        new_obj.token = Token.parse(data["TOKEN"])
        msg_format.validate_token(new_obj.token, expected_scope=Token.Scope.GAME, expected_user_id=new_obj.from_user)

        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj
   

    def send(self, socket: socket.socket, ip: str, port: int, encoding: str = "utf-8"):
        """Sends game invitation to target user and initializes game state"""
        # Send the invite payload first
        msg = msg_format.serialize_message(self.payload)
        socket.sendto(msg.encode(encoding), (self.to_user.get_ip(), port))


    @classmethod
    def receive(cls, raw: str) -> "TicTacToeInvite":
        """Processes a received game invitation and displays initial game info."""

        received_invite = cls.parse(msg_format.deserialize_message(raw))
        
        # Print invite information
        print(f"{received_invite.from_user} invited you to play Tic-Tac-Toe.")


        return received_invite



__message__ = TicTacToeInvite

