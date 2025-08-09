from states.client_state import client_state
from custom_types.base_message import BaseMessage
from custom_types.fields import UserID, Token, Timestamp, TTL
from datetime import datetime, timezone
from utils import msg_format
import socket

class Like(BaseMessage):
  TYPE = "LIKE"
  SCOPE = Token.Scope.BROADCAST
  ACTIONS = ["LIKE", "UNLIKE"]
  __hidden__ = False
  __schema__ = {
    "TYPE": TYPE,
    "FROM": {"type": UserID, "required": True},
    "TO": {"type": UserID, "required": True},
    "POST_TIMESTAMP": {"type": Timestamp, "required": True},
    "ACTION": {"type": str, "required": True},
    "TIMESTAMP": {"type": Timestamp, "required": True},
    "TOKEN": {"type": Token, "required": True},
  }

  @property
  def payload(self) -> dict:
    return {
      "TYPE": self.TYPE,
      "FROM": self.from_user,
      "TO": self.to_user,
      "POST_TIMESTAMP": self.post_timestamp,
      "ACTION": self.action,
      "TIMESTAMP": self.timestamp,
      "TOKEN": self.token,
    }

  def __init__(self, to: UserID, post_timestamp: Timestamp, action: str, ttl: TTL = 3600):
    unix_now = int(datetime.now(timezone.utc).timestamp())
    self.type = self.TYPE
    self.from_user = client_state.get_user_id()
    self.to_user = to
    self.post_timestamp = post_timestamp
    user_action = action.upper()
    if user_action not in self.ACTIONS:
      raise ValueError("Invalid action: must be LIKE or UNLIKE")
    self.action = user_action
    self.timestamp = Timestamp(unix_now)
    self.ttl = ttl
    self.token = Token(self.from_user, self.timestamp + self.ttl, self.SCOPE)

  @classmethod
  def parse(cls, data: dict) -> "Like":
    new_obj = cls.__new__(cls)
    msg_action = data["ACTION"]
    if msg_action not in cls.ACTIONS:
      raise ValueError("Invalid action: must be LIKE or UNLIKE")
    new_obj.action = msg_action
    new_obj.type = data["TYPE"]
    new_obj.from_user = UserID.parse(data["FROM"])
    new_obj.to_user = UserID.parse(data["TO"])
    new_obj.post_timestamp = Timestamp.parse(int(data["POST_TIMESTAMP"]))
    new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
    new_obj.token = Token.parse(data["TOKEN"])
    Token.validate_token(new_obj.token, expected_scope=cls.SCOPE, expected_user_id=new_obj.from_user)
    msg_format.validate_message(new_obj.payload, new_obj.__schema__)
    return new_obj

  def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str = "utf-8"):
    if ip == "default":
      ip = self.to_user.get_ip()
    return super().send(socket, ip, port, encoding)

  @classmethod
  def receive(cls, raw: str) -> "Like":
    received = cls.parse(msg_format.deserialize_message(raw))
    liked_msg = client_state.get_post_message(received.post_timestamp)
    if liked_msg is None:
      raise ValueError("Liked post not found")
    if received.to_user != client_state.get_user_id():
      raise ValueError("Message is not intended to be received by this client")
    return received
  
  def info(self, verbose:bool = False) -> str:
    if verbose:
      return f"{self.payload}"
    display_name = client_state.get_peer_display_name(self.from_user)
    if display_name != "":
      return f"{display_name} likes your post {client_state.get_post_message(self.post_timestamp)}"
    return f"{self.from_user} likes your post {client_state.get_post_message(self.post_timestamp)}"



__message__ = Like
  