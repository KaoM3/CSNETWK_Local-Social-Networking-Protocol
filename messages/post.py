from custom_types.user_id import UserID
from custom_types.token import Token
from datetime import datetime, timezone
from utils import msg_format
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from client_logger import client_logger
import socket

class Post(BaseMessage):
  """
  Represents a POST message containing user-generated content.
  """

  TYPE = "POST"
  SCOPE = Token.Scope.BROADCAST
  __hidden__ = False
  __schema__ = {
    "TYPE": TYPE,
    "USER_ID": {"type": UserID, "required": True},
    "CONTENT": {"type": str, "required": True},
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

  def __init__(self, content: str, ttl: int = 3600):
    unix_now = int(datetime.now(timezone.utc).timestamp())
    self.type = self.TYPE
    self.user_id = client_state.get_user_id()
    self.content = content
    self.message_id = msg_format.generate_message_id()
    ttl = msg_format.sanitize_ttl(ttl)
    self.token = Token(self.user_id, unix_now + ttl, self.SCOPE)

  @classmethod
  def parse(cls, data: dict) -> "Post":
    new_obj = cls.__new__(cls)
    new_obj.type = data["TYPE"]
    new_obj.user_id = UserID.parse(data["USER_ID"])
    new_obj.content = str(data["CONTENT"])

    message_id = data["MESSAGE_ID"]
    msg_format.validate_message_id(message_id)
    new_obj.message_id = message_id

    new_obj.token = Token.parse(data["TOKEN"])
    msg_format.validate_token(new_obj.token, expected_scope=cls.SCOPE, expected_user_id=new_obj.user_id)

    msg_format.validate_message(new_obj.payload, new_obj.__schema__)
    return new_obj

  def send(self, sock: socket.socket, ip: str, port: int, encoding: str = "utf-8"):
    """
    Sends the POST message to all followers using a provided socket.
    """
    msg = msg_format.serialize_message(self.payload)

    for follower in client_state.get_followers():
      try:
        follower_ip = follower.get_ip()
        sock.sendto(msg.encode(encoding), (follower_ip, port))
        client_logger.debug(f"Sent to {follower_ip}:{port}")
      except Exception as e:
        client_logger.error(f"Error sending to {follower}: {e}")

  @classmethod
  def receive(cls, raw: str) -> "Post":
    received = cls.parse(msg_format.deserialize_message(raw))
    following = client_state.get_following()
    if received.user_id not in following:
      raise ValueError(f"{received.user_id} is not followed by this client")
    return received


__message__ = Post
  