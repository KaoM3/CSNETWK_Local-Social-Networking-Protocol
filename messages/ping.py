from custom_types.user_id import UserID
from utils import msg_format
from messages.base_message import BaseMessage
import socket

class Ping(BaseMessage):
  TYPE = "PING"
  __schema__ = {
    "TYPE": TYPE,
    "USER_ID": {"type": UserID, "required": True, "input": True}
  }

  @property
  def payload(self) -> dict:
    return {
      "TYPE": self.TYPE,
      "USER_ID": self.user_id
    }

  def __init__(self, user_id: UserID):
    self.type = self.TYPE
    self.user_id = user_id
    msg_format.validate_message(self.payload, self.__schema__)

  @classmethod
  def parse(cls, data: dict) -> "Ping":
    return cls(
      user_id=UserID.parse(data["USER_ID"])
    )
        
  @classmethod
  def receive(cls, raw: str) -> "Ping":
    return cls.parse(msg_format.deserialize_message(raw))

  def send(self, socket: socket.socket, ip: str, port: int, encoding: str="utf-8"):
    msg = msg_format.serialize_message(self.payload)
    socket.sendto(msg.encode(encoding), (ip, port))

__message__ = Ping