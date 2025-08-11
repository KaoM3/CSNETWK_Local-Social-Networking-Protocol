from custom_types.fields import MessageID
from custom_types.base_message import BaseMessage
from utils import msg_format
import socket

class Ack(BaseMessage):
    TYPE = "ACK"
    __hidden__ = True
    __schema__ = {
        "TYPE": TYPE,
        "MESSAGE_ID": {"type": MessageID, "required": True},
        "STATUS": {"type": str, "required": True},
    }

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "MESSAGE_ID": self.message_id,
            "STATUS": self.status,
        }

    def __init__(self, message_id: str, status: str = "RECEIVED"):
        self.type = self.TYPE
        self.message_id = message_id
        self.status = status

    @classmethod
    def parse(cls, data: dict) -> "Ack":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.message_id = MessageID.parse(data["MESSAGE_ID"])
        new_obj.status = data["STATUS"]

        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    def send(self, socket: socket.socket, ip: str = "default", port: int = 50999, encoding: str = "utf-8"):
        if ip == "default":
            raise ValueError("Unknown IP for ACK")
        return super().send(socket, ip, port, encoding)

    @classmethod
    def receive(cls, raw: str) -> "Ack":
        received = cls.parse(msg_format.deserialize_message(raw))
        return received
    
    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        else:
            return ""

__message__ = Ack