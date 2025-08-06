from utils import msg_format
from states.client_state import client_state
from custom_types.user_id import UserID
from custom_types.base_message import BaseMessage
import socket
import config

class Profile(BaseMessage):
  TYPE = "PROFILE"
  __hidden__ = False
  __schema__ = {
    "TYPE": "PROFILE",
    "USER_ID": {"type": UserID, "required": True},
    "DISPLAY_NAME": {"type": str, "required": True},
    "STATUS": {"type": str, "required": True},
  }

  @property
  def payload(self) -> dict:
    return {
      "TYPE": self.TYPE,
      "USER_ID": self.user_id,
      "DISPLAY_NAME": self.display_name,
      "STATUS": self.status
    }
  
  def __init__(self, display_name: str, status: str):
    self.type = self.TYPE
    self.user_id = client_state.get_user_id()
    self.display_name = display_name
    self.status = status
    msg_format.validate_message(self.payload, self.__schema__)

  def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8"):
    if ip == "default":
      ip = config.BROADCAST_IP
    super().send(socket, ip, port, encoding)

  @classmethod
  def parse(cls, data: str) -> "Profile":
    new_obj = cls.__new__(cls)
    new_obj.user_id = UserID.parse(data["USER_ID"])
    new_obj.display_name = str(data["DISPLAY_NAME"])
    new_obj.status = str(data["STATUS"])
    # TODO: Add accepting of AVATAR_ fields
    return new_obj
  
  @classmethod
  def receive(cls, raw: str) -> "Profile":
    received = cls.parse(msg_format.deserialize_message(raw))
    client_state.add_peer(received.user_id)
    client_state.update_peer_display_name(received.user_id, received.display_name)
    return received
  
  def info(self, verbose:bool = False) -> str:
    if verbose:
      return f"{self.payload}"
    if self.display_name == "":
      return f"{self.user_id}'s status: {self.status}"
    return f"{self.display_name}'s status: {self.status}"
  
__message__ = Profile