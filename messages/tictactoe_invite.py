# TODO: Implement Schema
# TODO: Implement send()
# TODO: Implement receive()
# TODO: Implement filter()

from datetime import datetime, timezone
import socket
import random
import config
import client

from custom_types.fields import UserID, Token, Timestamp, MessageID, TTL
from custom_types.base_message import BaseMessage
from utils import msg_format
from states.client_state import client_state
from messages.ack import Ack
from states.game import game_session_manager


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
        "MESSAGE_ID": {"type": MessageID, "required": True},
        "TIMESTAMP": {"type": Timestamp, "required": True},
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

    def __init__(self, to: UserID, symbol: str, ttl: TTL = 3600):
        """Initialize game invitation with validation"""
        unix_now = int(datetime.now(timezone.utc).timestamp())

        # Validate symbol
        symbol = symbol.upper() 
        if symbol not in ['X', 'O']:
            raise ValueError("Symbol must be either 'X' or 'O'")
        
        while True:
            game_id = f"g{random.randint(0, 255)}"
            if not game_session_manager.find_game(game_id):
                break 


        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        self.game_id = game_id
        self.symbol = symbol
        self.timestamp = Timestamp(unix_now)
        self.message_id = MessageID.generate()
        self.token = Token(self.from_user, self.timestamp + ttl, Token.Scope.GAME)


    @classmethod
    def parse(cls, data: dict) -> "TicTacToeInvite":
        """Parse a dictionary to reconstruct a TicTacToeInvite instance"""
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])
        new_obj.game_id = data["GAMEID"]
        new_obj.symbol = data["SYMBOL"]
        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        new_obj.message_id = MessageID.parse(data["MESSAGE_ID"]) 
        new_obj.token = Token.parse(data["TOKEN"])
        Token.validate_token(new_obj.token, expected_scope=Token.Scope.GAME, expected_user_id=new_obj.from_user)

        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj
   

    def send(self, socket: socket.socket, ip: str, port: int, encoding: str = "utf-8"):
        """Sends game invitation to target user and initializes game state"""

        game = game_session_manager.find_game(self.game_id)

        if not game:
            game_session_manager.create_game(self.game_id)
            if self.symbol == "X":
                game_session_manager.assign_players(self.game_id, self.from_user, self.to_user)
            else:
                game_session_manager.assign_players(self.game_id, self.to_user, self.from_user)
    
        if ip == "default":
            ip = self.to_user.get_ip()
        return super().send(socket, ip, port, encoding)


    @classmethod
    def receive(cls, raw: str) -> "TicTacToeInvite":
        """Processes a received game invitation and displays initial game info."""

        received_invite = cls.parse(msg_format.deserialize_message(raw))

        
        # Print invite information
        print(f"{received_invite.from_user} invited you to play Tic-Tac-Toe.")
        
        client.initialize_sockets(config.PORT)
        ack = Ack(message_id=received_invite.message_id)
        ack.send(socket=client.get_broadcast_socket(), ip=received_invite.from_user.get_ip(), port=config.PORT)

        game = game_session_manager.find_game(received_invite.game_id)

        if not game:
            game_session_manager.create_game(received_invite.game_id)
            if received_invite.symbol == "X":
                game_session_manager.assign_players(received_invite.game_id, received_invite.from_user, received_invite.to_user)
            else:
                game_session_manager.assign_players(received_invite.game_id, received_invite.to_user, received_invite.from_user)

        return received_invite



__message__ = TicTacToeInvite

