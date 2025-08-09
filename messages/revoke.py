from custom_types.user_id import UserID
from custom_types.token import Token
from utils import msg_format
from custom_types.base_message import BaseMessage
import socket
from states.client_state import client_state
import config

class Revoke(BaseMessage):
  TYPE = "REVOKE"
  __hidden__ = True
  __schema__ = {
    "TYPE": TYPE,
    "TOKEN": {"type": Token, "required": True}
  }

  @property
  def payload(self) -> dict:
    return {
      "TYPE": self.TYPE,
      "TOKEN": self.token
    }

  def __init__(self, token: Token):
    self.type = self.TYPE
    self.token = token
    msg_format.validate_message(self.payload, self.__schema__)

  @classmethod
  def parse(cls, data: dict) -> "Revoke":
    new_instance = cls.__new__(cls)
    new_instance.type = data["TYPE"]
    new_instance.token = Token.parse(data["TOKEN"])
    msg_format.validate_message(new_instance.payload, cls.__schema__)
    return new_instance
        
  def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8") -> tuple[str, int]:
    if ip == "default":
      ip = config.CLIENT_IP
    return super().send(socket, ip, port, encoding)

  @classmethod
  def receive(cls, raw: str) -> "Revoke":
    received = cls.parse(msg_format.deserialize_message(raw))
    client_state.revoke_token(received.token)
    return received
  
  def info(self, verbose:bool=False) -> str:
    if verbose:
      return f"{self.payload}"
    return ""

__message__ = Revoke