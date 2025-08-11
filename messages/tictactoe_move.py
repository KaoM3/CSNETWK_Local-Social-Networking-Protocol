# TODO: Implement Schema
# TODO: Implement send()
# TODO: Implement receive()

from custom_types.fields import UserID, Token, MessageID, TTL, Timestamp
from datetime import datetime, timezone
from utils import msg_format
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from messages.ack import Ack
from messages.tictactoe_result import TicTacToeResult
from states.game import game_session_manager
from client_logger import client_logger
import socket
import config
import client
import time


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
        "MESSAGE_ID": {"type": MessageID, "required": True},
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

    def __init__(self, to: UserID, game_id: str, position: int, ttl: TTL = 3600):
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
        
        active = game_session_manager.is_active_game(game_id)
        if not active:
            raise ValueError(f"Game {game_id} is not currently active")
        else:
            game_turn = game_session_manager.get_turn(game_id)

        unix_now = int(datetime.now(timezone.utc).timestamp())
        
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        self.game_id = msg_format.check_game_id(game_id)
        self.position = msg_format.sanitize_position(position)
        self.symbol = game_session_manager.get_player_symbol(game_id, self.from_user)
        self.turn = msg_format.sanitize_turn(game_turn)
        self.message_id = MessageID.generate()
        self.token = Token(self.from_user, Timestamp(unix_now) + ttl, Token.Scope.GAME)

    @classmethod
    def parse(cls, data: dict) -> "TicTacToeMove":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"] 
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])

        new_obj.game_id = msg_format.check_game_id(data["GAMEID"])
        new_obj.position = msg_format.sanitize_position(data["POSITION"])
        new_obj.symbol = data["SYMBOL"]
        new_obj.turn = msg_format.sanitize_turn(data["TURN"])

        new_obj.message_id = MessageID.parse(data["MESSAGE_ID"]) 
        new_obj.token = Token.parse(data["TOKEN"])
        Token.validate_token(new_obj.token, expected_scope=Token.Scope.GAME, expected_user_id=new_obj.from_user)
        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj


    def send(self, socket: socket.socket, ip: str = "default", port: int = 50999, encoding: str = "utf-8"):
        """Sends game move to other player and updates game state"""

        if ip == "default":
            ip = self.to_user.get_ip()

        # Validate receiver is part of the game
        game_session_manager.is_player(self.game_id, self.to_user)

        # Get or create the game
        game = game_session_manager.find_game(self.game_id)
        if not game and self.turn != 0:
            game = game_session_manager.create_game(self.game_id)
            game_session_manager.assign_players(self.game_id, self.from_user, self.to_user)

        # Validate turn sync
        if self.turn != game.turn:
            raise ValueError(f"Turn mismatch: expected {game.turn}, got {self.turn}")

        # Apply move
        game.move(self.from_user, self.position)
        client_logger.info(game.get_board_string())

        # Check game result
        winning_line = None
        if game_session_manager.is_winning_move(self.game_id):
            winning_line = game_session_manager.find_winning_line(self.game_id)
            result = TicTacToeResult(
                to=self.from_user,
                gameid=self.game_id,
                result="WIN",
                symbol=self.symbol,  
                winning_line=winning_line,
                turn=self.turn,
            )
            result.send(socket=client.get_unicast_socket(), ip=self.from_user.get_ip(), port=config.PORT)

        elif game_session_manager.is_draw(self.game_id):
            result = TicTacToeResult(
                to=self.from_user,
                gameid=self.game_id,
                result="DRAW",
                symbol=self.symbol,
                winning_line=None,
                turn=self.turn,
            )
            result.send(socket=client.get_unicast_socket(), ip=self.from_user.get_ip(), port=config.PORT)

        # Default IP resolution
        retries = 0
        dest = ("failed", port)
        client_logger.process(f"Waiting for {self.to_user}")
        client_state.add_recent_message_sent(self)
        while retries < 3:
            # Send message
            dest = super().send(socket, ip, port, encoding)
            client_logger.debug(f"Sent tictactoe_move {self.message_id}, attempt {retries + 1}")

            # Wait a bit for ACK
            time.sleep(2)  # Lower this to 0.5 or 1 if latency is tight

            # Check for ACK
            if client_state.get_ack_message(self.message_id) is not None:
                client_logger.debug(f"Received ACK for file {self.message_id}")
                break
            retries += 1
        if client_state.get_ack_message(self.message_id) is None:
            client_logger.warn(f"No ACK received for invite {self.message_id} after {retries} attempts.")
            client_logger.warn(f"Aborting TICTACTOE_MOVE.")
            client_state.remove_recent_message_sent(self)
            game.undo()
            return dest
        return dest
     
    @classmethod
    def receive(cls, raw: str) -> "TicTacToeMove":
        """Process received game move and update game state"""
        move_received = cls.parse(msg_format.deserialize_message(raw))
        if move_received.to_user != client_state.get_user_id():
            raise ValueError("Message is not intended to be received by this client")

        client.initialize_sockets(config.PORT)

        # Acknowledge
        client.initialize_sockets(config.PORT)
        ack = Ack(message_id=move_received.message_id)
        dest = ack.send(socket=client.get_unicast_socket(), ip=move_received.from_user.get_ip(), port=config.PORT)
        client_logger.debug(f"ACK SENT TO {dest}")

        # Validate player
        game = game_session_manager.find_game(move_received.game_id)
        if not game:
            game = game_session_manager.create_game(move_received.game_id)
            game_session_manager.assign_players(
                move_received.game_id, move_received.from_user, move_received.to_user
            )

        game_session_manager.is_player(move_received.game_id, move_received.from_user)

        # Validate turn
        if move_received.turn != game.turn:
            raise ValueError(f"Turn mismatch: expected {game.turn}, got {move_received.turn}")

        # Apply move
        game.move(move_received.from_user, move_received.position)
        client_logger.info(game.get_board_string())

        # Check result
        winning_line = None
        if game_session_manager.is_winning_move(move_received.game_id):
            winning_line = game_session_manager.find_winning_line(move_received.game_id)
            result = TicTacToeResult(
                to=move_received.to_user,
                gameid=move_received.game_id,
                result="LOSS",
                symbol=move_received.symbol,
                winning_line=winning_line,
                turn=move_received.turn,
            )
            result.send(socket=client.get_unicast_socket(),
                        ip=move_received.to_user.get_ip(),
                        port=config.PORT)

        elif game_session_manager.is_draw(move_received.game_id):
            result = TicTacToeResult(
                to=move_received.to_user,
                gameid=move_received.game_id,
                result="DRAW",
                symbol=move_received.symbol,
                winning_line=None,
                turn=move_received.turn,
            )
            result.send(socket=client.get_unicast_socket(),
                        ip=move_received.to_user.get_ip(),
                        port=config.PORT)

        return move_received
    
    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"Turn {self.turn}:\n{game_session_manager.find_game(self.game_id).get_board_string()}\n{self.payload}"
        else:
            return f"Turn {self.turn}:\n{game_session_manager.find_game(self.game_id).get_board_string()}"




__message__ = TicTacToeMove