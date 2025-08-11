from datetime import datetime, timezone
from custom_types.fields import UserID, Timestamp, MessageID
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from utils import msg_format
import socket

class FileReceived(BaseMessage):
    TYPE = "FILE_RECEIVED"
    __hidden__ = True
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "TO": {"type": UserID, "required": True},
        "FILEID": {"type": MessageID, "required": True},
        "STATUS": {"type": str, "required": True},
        "TIMESTAMP": {"type": Timestamp, "required": True}
    }

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "TO": self.to_user,
            "FILEID": self.fileid,
            "STATUS": self.status,
            "TIMESTAMP": self.timestamp
        }

    def __init__(self, to: UserID, fileid: MessageID, status: str = "COMPLETE"):
        unix_now = int(datetime.now(timezone.utc).timestamp())
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        self.fileid = fileid
        self.status = status
        self.timestamp = Timestamp(unix_now)

    @classmethod
    def parse(cls, data: dict) -> "FileReceived":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])
        new_obj.fileid = MessageID.parse(data["FILEID"])
        new_obj.status = str(data["STATUS"])
        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        
        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8") -> tuple[str, int]:
        if ip == "default":
            ip = self.to_user.get_ip()
        return super().send(socket, ip, port, encoding)

    @classmethod
    def receive(cls, raw: str) -> "FileReceived":
        received = cls.parse(msg_format.deserialize_message(raw))
        if received.to_user != client_state.get_user_id():
            raise ValueError("Message is not intended to be received by this client")
        return received

    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        return ""  # Don't print anything as per spec

__message__ = FileReceived