from custom_types.fields import UserID, Token, MessageID
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from states.file_state import file_state
from messages.file_received import FileReceived
from utils import msg_format
import socket
import base64
import client
import config

class FileChunk(BaseMessage):
    TYPE = "FILE_CHUNK"
    SCOPE = Token.Scope.FILE
    __hidden__ = True
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "TO": {"type": UserID, "required": True},
        "FILEID": {"type": MessageID, "required": True},
        "CHUNK_INDEX": {"type": int, "required": True},
        "TOTAL_CHUNKS": {"type": int, "required": True},
        "CHUNK_SIZE": {"type": int, "required": True},
        "TOKEN": {"type": Token, "required": True},
        "DATA": {"type": str, "required": True}
    }

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "TO": self.to_user,
            "FILEID": self.fileid,
            "CHUNK_INDEX": self.chunk_index,
            "TOTAL_CHUNKS": self.total_chunks,
            "CHUNK_SIZE": self.chunk_size,
            "TOKEN": self.token,
            "DATA": self.data
        }

    def __init__(self, to: UserID, fileid: MessageID, chunk_index: int, total_chunks: int, 
                 chunk_size: int, token: Token, data: bytes):
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        self.fileid = fileid
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        self.chunk_size = chunk_size
        self.token = token
        self.data = base64.b64encode(data).decode('utf-8')

    @classmethod
    def parse(cls, data: dict) -> "FileChunk":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])
        new_obj.fileid = MessageID.parse(data["FILEID"])
        new_obj.chunk_index = int(data["CHUNK_INDEX"])
        new_obj.total_chunks = int(data["TOTAL_CHUNKS"])
        new_obj.chunk_size = int(data["CHUNK_SIZE"])
        new_obj.token = Token.parse(data["TOKEN"])
        new_obj.data = data["DATA"]

        Token.validate_token(new_obj.token, expected_scope=cls.SCOPE, expected_user_id=new_obj.from_user)
        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8") -> tuple[str, int]:
        if ip == "default":
            ip = self.to_user.get_ip()
        return super().send(socket, ip, port, encoding)

    @classmethod
    def receive(cls, raw: str) -> "FileChunk":
        received = cls.parse(msg_format.deserialize_message(raw))
        if received.to_user != client_state.get_user_id():
            raise ValueError("Message is not intended for this client")

        if not file_state.is_file_accepted(received.fileid):
            raise ValueError("File transfer was not accepted")
        
        # Add chunk and check if complete
        is_complete = file_state.add_chunk(
            received.fileid,
            received.chunk_index,
            received.data,
            received.total_chunks
        )

        if is_complete:
            from client_logger import client_logger
            client_logger.info(f"File transfer complete!")
            client.initialize_sockets(config.PORT)
            socket = client.get_unicast_socket()
            new_msg = FileReceived(received.to_user, received.fileid)
            new_msg.send(socket)

        return received

    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        return ""  # Don't print anything until all chunks are received

__message__ = FileChunk