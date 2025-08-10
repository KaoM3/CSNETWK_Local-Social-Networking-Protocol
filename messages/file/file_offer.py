from datetime import datetime, timezone
from custom_types.fields import UserID, Token, Timestamp, TTL, MessageID
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from utils import msg_format
import socket

class FileOffer(BaseMessage):
    TYPE = "FILE_OFFER"
    SCOPE = Token.Scope.FILE
    __hidden__ = False
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "TO": {"type": UserID, "required": True},
        "FILENAME": {"type": str, "required": True},
        "FILESIZE": {"type": int, "required": True},
        "FILETYPE": {"type": str, "required": True},
        "FILEID": {"type": MessageID, "required": True},
        "DESCRIPTION": {"type": str, "required": False},
        "TIMESTAMP": {"type": Timestamp, "required": True},
        "TOKEN": {"type": Token, "required": True}
    }

    @property
    def payload(self) -> dict:
        payload = {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "TO": self.to_user,
            "FILENAME": self.filename,
            "FILESIZE": self.filesize,
            "FILETYPE": self.filetype,
            "FILEID": self.fileid,
            "TIMESTAMP": self.timestamp,
            "TOKEN": self.token
        }
        if self.description:
            payload["DESCRIPTION"] = self.description
        return payload

    def __init__(self, to: UserID, filename: str, filesize: int, filetype: str, description: str = "", ttl: TTL = 3600):
        unix_now = int(datetime.now(timezone.utc).timestamp())
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        self.filename = filename
        self.filesize = filesize
        self.filetype = filetype
        self.fileid = MessageID.generate()
        self.description = description
        self.timestamp = Timestamp(unix_now)
        self.token = Token(self.from_user, self.timestamp + ttl, self.SCOPE)

    @classmethod
    def parse(cls, data: dict) -> "FileOffer":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])
        new_obj.filename = str(data["FILENAME"])
        new_obj.filesize = int(data["FILESIZE"])
        new_obj.filetype = str(data["FILETYPE"])
        new_obj.fileid = MessageID.parse(data["FILEID"])
        new_obj.description = data.get("DESCRIPTION", "")
        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        new_obj.token = Token.parse(data["TOKEN"])
        
        Token.validate_token(new_obj.token, expected_scope=cls.SCOPE, expected_user_id=new_obj.from_user)
        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8") -> tuple[str, int]:
        if ip == "default":
            ip = self.to_user.get_ip()
        return super().send(socket, ip, port, encoding)

    @classmethod
    def receive(cls, raw: str) -> "FileOffer":
        received = cls.parse(msg_format.deserialize_message(raw))
        if received.to_user != client_state.get_user_id():
            raise ValueError("Message is not intended to be received by this client")
        
        # Ask user if they want to accept
        from client_logger import client_logger
        response = client_logger.input("Accept file? (y/n): ").lower()
        if response == 'y':
            from states.file_state import file_state
            file_state.accept_file(received.fileid)
            file_state.add_pending_transfer(
                received.fileid,
                received.filename,
                0,  # Will be set when receiving first chunk
                received.filetype,
                received.filesize
            )
            
        return received

    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        return f"User {self.from_user} is sending you a file do you accept?"

__message__ = FileOffer