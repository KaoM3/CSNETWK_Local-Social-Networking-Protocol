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
from client_logger import client_logger
from messages.ack import Ack
from states.game import game_session_manager
import time




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
   

    def send(self, socket: socket.socket, ip: str = "default", port: int = 50999, encoding: str = "utf-8"):
        """Sends game invitation to target user and initializes game state"""

        if ip == "default":
            ip = self.to_user.get_ip()

        game = game_session_manager.find_game(self.game_id)

        if not game:
            game_session_manager.create_game(self.game_id)
            if self.symbol == "X":
                game_session_manager.assign_players(self.game_id, self.from_user, self.to_user)
            else:
                game_session_manager.assign_players(self.game_id, self.to_user, self.from_user)

        retries = 0
        dest = ("failed", port)
        client_logger.process(f"Waiting for {self.to_user}")
        client_state.add_recent_message_sent(self)
        while retries < 3:
            # Send message
            dest = super().send(socket, ip, port, encoding)
            client_logger.debug(f"Send tictactoe_invite {self.message_id}, attempt {retries + 1}")

            # Wait a bit for ACK
            time.sleep(2)  # Lower this to 0.5 or 1 if latency is tight

            # Check for ACK
            if client_state.get_ack_message(self.message_id) is not None:
                client_logger.debug(f"Received ACK for file {self.message_id}")
                break

            retries += 1
        if client_state.get_ack_message(self.message_id) is None:
            client_logger.warn(f"No ACK received for invite {self.message_id} after {retries} attempts.")
            client_logger.warn(f"Aborting TICTACTOE_INVITE.")
            game_session_manager.delete_game(self.game_id)
            client_state.remove_recent_message_sent(self)
            return dest
        client_logger.info(self.info(verbose=False))
        return dest


    @classmethod
    def receive(cls, raw: str) -> "TicTacToeInvite":
        """Processes a received game invitation and displays initial game info."""

        received_invite = cls.parse(msg_format.deserialize_message(raw))
        if received_invite.to_user != client_state.get_user_id():
            raise ValueError("Message is not intended to be received by this client")
        
        client.initialize_sockets(config.PORT)
        ack = Ack(message_id=received_invite.message_id)
        dest = ack.send(socket=client.get_unicast_socket(), ip=received_invite.from_user.get_ip(), port=config.PORT)
        client_logger.debug(f"ACK SENT TO {dest}")

        game = game_session_manager.find_game(received_invite.game_id)

        if not game:
            game_session_manager.create_game(received_invite.game_id)
            if received_invite.symbol == "X":
                game_session_manager.assign_players(received_invite.game_id, received_invite.from_user, received_invite.to_user)
            else:
                game_session_manager.assign_players(received_invite.game_id, received_invite.to_user, received_invite.from_user)

        return received_invite

    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        else:
            return f"{self.from_user} invited you to play Tic-Tac-Toe."

__message__ = TicTacToeInvite

