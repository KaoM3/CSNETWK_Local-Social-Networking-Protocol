from states.client_state import client_state
from custom_types.base_message import BaseMessage
from custom_types.fields import UserID, Token, Timestamp, MessageID, TTL
from datetime import datetime, timezone
from utils import msg_format
import socket

class Follow(BaseMessage):
  """
  Represents a FOLLOW message indicating subscription to another user's updates.
  """

  TYPE = "FOLLOW"
  SCOPE = Token.Scope.FOLLOW
  __hidden__ = False
  __schema__ = {
    "TYPE": TYPE,
    "FROM": {"type": UserID, "required": True},
    "TO": {"type": UserID, "required": True},
    "TIMESTAMP": {"type": Timestamp, "required": True},
    "MESSAGE_ID": {"type": MessageID, "required": True},
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
    self.timestamp = Timestamp(unix_now)
    self.message_id = MessageID.generate()
    self.ttl = TTL.parse(ttl)
    self.token = Token(self.from_user, self.timestamp + self.ttl, self.SCOPE)

  @classmethod
  def parse(cls, data: dict) -> "Follow":
    new_obj = cls.__new__(cls)
    new_obj.type = data["TYPE"]
    new_obj.from_user = UserID.parse(data["FROM"])
    new_obj.to_user = UserID.parse(data["TO"])
    new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
    new_obj.message_id = MessageID.parse(data["MESSAGE_ID"])    
    new_obj.token = Token.parse(data["TOKEN"])
    Token.validate_token(new_obj.token, expected_scope=cls.SCOPE, expected_user_id=new_obj.from_user)
    return new_obj
  
  def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8") -> tuple[str, int]:
    """Send follow request and update local following list"""
    if ip == "default":
      ip = self.to_user.get_ip()
    dest = super().send(socket, ip, port, encoding)
    client_state.add_following(self.to_user)
    return dest

  @classmethod
  def receive(cls, raw: str) -> "Follow":
    """Process received follow request and update followers list"""
    received = cls.parse(msg_format.deserialize_message(raw))
    if received.to_user != client_state.get_user_id():
      raise ValueError("Message is not intended to be received by this client")
    client_state.add_follower(received.from_user)
    return received
  
  def info(self, verbose:bool = False) -> str:
    if verbose:
      return f"{self.payload}"
    return f"User {self.from_user} has followed you"

__message__ = Follow