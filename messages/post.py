from custom_types.user_id import UserID
from custom_types.token import Token
from datetime import datetime, timezone
from utils import msg_format
from custom_types.base_message import BaseMessage
from states.client_state import client_state
import socket

class Post(BaseMessage):
  """
  Represents a POST message containing user-generated content.
  """

  TYPE = "POST"
  __hidden__ = False
  __schema__ = {
    "TYPE": TYPE,
    "USER_ID": {"type": UserID, "required": True, "input": True},
    "CONTENT": {"type": str, "required": True, "input": True},
    "MESSAGE_ID": {"type": str, "required": True},
    "TOKEN": {"type": Token, "required": True},
  }

  @property
  def payload(self) -> dict:
    return {
      "TYPE": self.TYPE,
      "USER_ID": self.user_id,
      "CONTENT": self.content,
      "MESSAGE_ID": self.message_id,
      "TOKEN": self.token,
    }

  def __init__(self, user_id: UserID, content: str, ttl: int = 3600):
    unix_now = int(datetime.now(timezone.utc).timestamp())
    self.type = self.TYPE
    self.user_id = user_id
    self.content = content
    self.message_id = msg_format.generate_message_id()
    self.token = Token(user_id, unix_now + ttl, Token.Scope.BROADCAST)

  @classmethod
  def parse(cls, data: dict) -> "Post":
    return cls.__new__(cls)._init_from_dict(data)

  def _init_from_dict(self, data: dict):
    self.type = data["TYPE"]
    self.user_id = UserID.parse(data["USER_ID"])
    self.content = str(data["CONTENT"])

    message_id = data["MESSAGE_ID"]
    msg_format.validate_message_id(message_id)
    self.message_id = message_id

    self.token = Token.parse(data["TOKEN"])

    # Extra Token Validation
    if self.user_id != self.token.user_id:
      raise ValueError("Invalid Token: user_id mismatch")
    
    if msg_format.isTokenExpired(self.token):
      raise ValueError("Invalid Token: expired")
    
    if self.token.scope != Token.Scope.BROADCAST:
      raise ValueError("Invalid Token: scope mismatch")

    msg_format.validate_message(self.payload, self.__schema__)
    return self

  def send(self, sock: socket.socket, ip: str, port: int, encoding: str = "utf-8"):
    """
    Sends the POST message to all followers using a provided socket.
    """
    msg = msg_format.serialize_message(self.payload)

    for follower in client_state.get_followers():
      try:
        follower_ip = follower.get_ip()
        sock.sendto(msg.encode(encoding), (follower_ip, port))
        print(f"Sent to {follower_ip}:{port}")
      except Exception as e:
        print(f"Error sending to {follower}: {e}")

  @classmethod
  def receive(cls, raw: str) -> "Post":
    return cls.parse(msg_format.deserialize_message(raw))


__message__ = Post
  