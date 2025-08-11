from custom_types.fields import UserID
from utils import msg_format
from custom_types.base_message import BaseMessage
import socket
from states.client_state import client_state
import config

class Ping(BaseMessage):
  TYPE = "PING"
  __hidden__ = True
  __schema__ = {
    "TYPE": TYPE,
    "USER_ID": {"type": UserID, "required": True}
  }

  @property
  def payload(self) -> dict:
    return {
      "TYPE": self.TYPE,
      "USER_ID": self.user_id
    }

  def __init__(self):
    self.type = self.TYPE
    self.user_id = client_state.get_user_id()
    msg_format.validate_message(self.payload, self.__schema__)

  @classmethod
  def parse(cls, data: dict) -> "Ping":
    new_instance = cls.__new__(cls)
    new_instance.type = data["TYPE"]
    new_instance.user_id = UserID.parse(data["USER_ID"])
    msg_format.validate_message(new_instance.payload, cls.__schema__)
    return new_instance
        
  def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8") -> tuple[str, int]:
    if ip == "default":
      ip = config.BROADCAST_IP
    return super().send(socket, ip, port, encoding)

  @classmethod
  def receive(cls, raw: str) -> "Ping":
    received = cls.parse(msg_format.deserialize_message(raw))
    client_state.add_peer(received.user_id)
    if received.user_id not in client_state.get_peers():
      new_ping = Ping()
      new_ping.send(received.user_id.get_ip())
    return received
  
  def info(self, verbose:bool=False) -> str:
    if verbose:
      return f"{self.payload}"
    return ""

__message__ = Ping