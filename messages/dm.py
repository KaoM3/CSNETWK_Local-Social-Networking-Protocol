from custom_types.user_id import UserID
from custom_types.token import Token
from datetime import datetime, timezone
from utils import msg_format
from custom_types.base_message import BaseMessage
from states.client_state import client_state
import socket

class Dm(BaseMessage):
  TYPE = "DM"
  SCOPE = Token.Scope.CHAT
  __hidden__ = False
  __schema__ = {
    "TYPE": TYPE,
    "FROM": {"type": UserID, "required": True},
    "TO": {"type": UserID, "required": True},
    "CONTENT": {"type": str, "required": True},
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
      "CONTENT": self.content,
      "TIMESTAMP": self.timestamp,
      "MESSAGE_ID": self.message_id,
      "TOKEN": self.token,
    }
  
  def __init__(self, to: UserID, content: str, ttl: int = 3600):
    unix_now = int(datetime.now(timezone.utc).timestamp())
    self.type = self.TYPE
    self.from_user = client_state.get_user_id()
    self.to_user = to
    self.content = content
    self.timestamp = unix_now
    self.message_id = msg_format.generate_message_id()
    ttl = msg_format.sanitize_ttl(ttl)
    self.token = Token(self.from_user, unix_now + ttl, self.SCOPE)

  @classmethod
  def parse(cls, data: dict) -> "Dm":
    new_obj = cls.__new__(cls)
    new_obj.type = data["TYPE"]
    new_obj.from_user = UserID.parse(data["FROM"])
    new_obj.to_user = UserID.parse(data["TO"])
    new_obj.content = data["CONTENT"]
    
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
  
  def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8") -> tuple[str, int]:
    if ip == "default":
      ip = self.to_user.get_ip()
    return super().send(socket, ip, port, encoding)

  @classmethod
  def receive(cls, raw: str) -> "Dm":
    received = cls.parse(msg_format.deserialize_message(raw))
    if received.to_user != client_state.get_user_id():
      raise ValueError("Message is not intended to be received by this client")
    return received
  
  def info(self, verbose: bool = False) -> str:
    if verbose:
      return f"{self.payload}"
    display_name = client_state.get_peer_display_name(self.from_user)
    if display_name != "":
      return f"{display_name}: {self.content}"
    return f"{self.from_user}: {self.content}"

__message__ = Dm