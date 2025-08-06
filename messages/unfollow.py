from datetime import datetime, timezone
import socket

from custom_types.user_id import UserID
from custom_types.token import Token
from custom_types.base_message import BaseMessage
from utils import msg_format
from states.client_state import client_state

class Unfollow(BaseMessage):
  """
  Represents an UNFOLLOW message indicating unsubscription from another user's updates.
  """

  TYPE = "UNFOLLOW"
  SCOPE = Token.Scope.FOLLOW
  __hidden__ = False
  __schema__ = {
    "TYPE": TYPE,
    "FROM": {"type": UserID, "required": True},
    "TO": {"type": UserID, "required": True},
    "TIMESTAMP": {"type": int, "required": True},
    "MESSAGE_ID": {"type": str, "required": True},
    "TOKEN": {"type": Token, "required": True},
  }

  @property
  def payload(self) -> dict:
    return {
      "TYPE": self.TYPE,
      "FROM": self.from_user,
      "TO": self.to_user,
      "TIMESTAMP": self.timestamp,
      "MESSAGE_ID": self.message_id,
      "TOKEN": self.token,
    }

  def __init__(self, to: UserID, ttl: int = 3600):
    unix_now = int(datetime.now(timezone.utc).timestamp())
    self.type = self.TYPE
    self.from_user = client_state.get_user_id()
    self.to_user = to
    self.timestamp = unix_now
    self.message_id = msg_format.generate_message_id()
    self.token = Token(self.from_user, unix_now + ttl, self.SCOPE)

  @classmethod
  def parse(cls, data: dict) -> "Unfollow":
    new_obj = cls.__new__(cls)
  
    new_obj.type = data["TYPE"]
    new_obj.from_user = UserID.parse(data["FROM"])
    new_obj.to_user = UserID.parse(data["TO"])

    timestamp = int(data["TIMESTAMP"])
    msg_format.validate_timestamp(timestamp)
    new_obj.timestamp = timestamp

    message_id = data["MESSAGE_ID"]
    msg_format.validate_message_id(message_id)
    new_obj.message_id = message_id

    new_obj.token = Token.parse(data["TOKEN"])
    msg_format.validate_token(new_obj.token, expected_scope=cls.SCOPE, expected_user_id=new_obj.from_user)
    
    msg_format.validate_message(new_obj.payload, new_obj.__schema__)
    return new_obj

  def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8"):
    """Send unfollow request and update local following list"""
    if ip == "default":
      ip = self.to_user.get_ip()
    super().send(socket, ip, port, encoding)
    client_state.remove_following(self.to_user)

  @classmethod
  def receive(cls, raw: str) -> "Unfollow":
    """Process received unfollow request and update followers list"""
    received = cls.parse(msg_format.deserialize_message(raw))
    if received.to_user != client_state.get_user_id():
      raise ValueError("Message is not intended to be received by this client")
    client_state.remove_follower(received.from_user)
    return received
  
  def info(self, verbose:bool = False) -> str:
    if verbose:
      return f"{self.payload}"
    return f"User {self.from_user} has unfollowed you"


__message__ = Unfollow