from datetime import datetime, timezone
import socket

from custom_types.user_id import UserID
from custom_types.token import Token
from custom_types.base_message import BaseMessage
from utils import msg_format
from states.client_state import client_state

class Follow(BaseMessage):
  """
  Represents a FOLLOW message indicating subscription to another user's updates.
  """

  TYPE = "FOLLOW"

  __schema__ = {
    "TYPE": TYPE,
    "FROM": {"type": UserID, "required": True, "input": True},
    "TO": {"type": UserID, "required": True, "input": True},
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

  def __init__(self, from_: UserID, to: UserID, ttl: int = 3600):
    unix_now = int(datetime.now(timezone.utc).timestamp())
    self.type = self.TYPE
    self.from_user = from_
    self.to_user = to
    self.timestamp = unix_now
    self.message_id = msg_format.generate_message_id()
    self.token = Token(from_, unix_now + ttl, Token.Scope.FOLLOW)

  def send(self, socket: socket.socket, ip: str, port: int, encoding: str="utf-8"):
    """Send follow request and update local following list"""
    msg = msg_format.serialize_message(self.payload)
    socket.sendto(msg.encode(encoding), (self.payload.get("TO"), port))
    client_state.add_following(self.to_user)

  @classmethod
  def parse(cls, data: dict) -> "Follow":
    return cls.__new__(cls)._init_from_dict(data)

  def _init_from_dict(self, data: dict):
    self.type = data["TYPE"]
    self.from_user = UserID.parse(data["FROM"])
    self.to_user = UserID.parse(data["TO"])

    timestamp = int(data["TIMESTAMP"])
    msg_format.validate_timestamp(timestamp)
    self.timestamp = timestamp

    message_id = data["MESSAGE_ID"]
    msg_format.validate_message_id(message_id)
    self.message_id = message_id

    self.token = Token.parse(data["TOKEN"])
    msg_format.validate_message(self.payload, self.__schema__)
    return self

  @classmethod
  def receive(cls, raw: str) -> "Follow":
    """Process received follow request and update followers list"""
    follow_msg = cls.parse(msg_format.deserialize_message(raw))
    client_state.add_follower(follow_msg.from_user)
    return follow_msg

__message__ = Follow