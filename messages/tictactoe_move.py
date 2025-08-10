# TODO: Implement Schema
# TODO: Implement send()
# TODO: Implement receive()

from custom_types.user_id import UserID
from custom_types.token import Token
from datetime import datetime, timezone
from utils import msg_format
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from messages.ack import Ack
from messages.tictactoe_result import TicTacToeResult
from states.game import game_session_manager
import socket
import config
import client


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

    def __init__(self, to: UserID, game_id: str, position: int, 
                 symbol: str, ttl: int = 3600):
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
        
        game_turn = game_session_manager.get_turn(game_id) 
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


        unix_now = int(datetime.now(timezone.utc).timestamp())
        
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        self.game_id = msg_format.check_game_id(game_id)
        self.position = msg_format.sanitize_position(position)
        self.symbol = symbol
        self.turn = msg_format.sanitize_turn(game_turn)
        self.message_id = msg_format.generate_message_id()
        self.token = Token(self.from_user, unix_now + ttl, Token.Scope.GAME)

    @classmethod
    def parse(cls, data: dict) -> "TicTacToeMove":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"] 
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])


    
        new_obj.game_id = msg_format.check_game_id(data["GAMEID"])
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

        game = game_session_manager.find_game(self.game_id)

        if not game:
            game = game_session_manager.create_game(self.game_id)# Acknowledge the move

        game.move(self.position, self.symbol)
        game.print_board()

        if game_session_manager.is_winning_move(self.game_id):
            winning_line = game_session_manager.find_winning_line(self.game_id)
            print(f"Player {self.symbol} wins the game {self.game_id}!")
            print(f"Winning line: {winning_line}")
            result = TicTacToeResult(
                to=self.to_user,
                gameid=self.game_id,
                result="WIN",
                symbol=self.symbol,
                winning_line=winning_line,
                turn=self.turn,
            ) 
            result.send(socket=client.get_broadcast_socket(), ip=self.to_user.get_ip(), port=config.PORT)

        print(f"Move sent to {self.to_user} at position {self.position}")


     
    @classmethod
    def receive(cls, raw: str) -> "TicTacToeMove":
        """Process received game move and update game state"""
        move_received = cls.parse(msg_format.deserialize_message(raw))   
        print(f"Received move: {move_received.from_user} at position {move_received.position}")

        client.initialize_sockets(config.PORT)
        ack = Ack(message_id=move_received.message_id)
        ack.send(socket=client.get_broadcast_socket(), ip=move_received.from_user.get_ip(), port=config.PORT)

        game = game_session_manager.find_game(move_received.game_id)

        if not game:
            game = game_session_manager.create_game(move_received.game_id)

        game.move(move_received.position, move_received.symbol)
        game.print_board()

        if game_session_manager.is_winning_move(move_received.game_id):
            winning_line = game_session_manager.find_winning_line(move_received.game_id)
            print(f"Player {move_received.symbol} wins the game {move_received.game_id}!")
            print(f"Winning line: {winning_line}")
            result = TicTacToeResult(
                to=move_received.to_user,
                gameid=move_received.game_id,
                result="LOSS",
                symbol=move_received.symbol,
                winning_line=winning_line,
                turn=move_received.turn,
            ) 
            result.send(socket=client.get_broadcast_socket(), ip=move_received.to_user.get_ip(), port=config.PORT)

        return move_received



__message__ = TicTacToeMove