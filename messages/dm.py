from custom_types.user_id import UserID
import custom_types.token as token
from datetime import datetime, timezone
from utils import msg_format
from messages.base_message import BaseMessage

class Dm(BaseMessage):
  TYPE = "DM"
  __schema__ = {
    "TYPE": TYPE,
    "FROM": {"type": UserID, "required": True, "input": True},
    "TO": {"type": UserID, "required": True, "input": True},
    "CONTENT": {"type": str, "required": True, "input": True},
    "TIMESTAMP": {"type": int, "required": True},
    "MESSAGE_ID": {"type": str, "required": True},
    "TOKEN": {"type": token.Token, "required": True},
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
  
  def __init__(self, from_: UserID, to: UserID, content: str):
    unix_now = int(datetime.now(timezone.utc).timestamp())
    self.type = self.TYPE
    self.from_user = from_
    self.to_user = to
    self.content = content
    self.timestamp = unix_now
    self.message_id = msg_format.generate_message_id()
    self.token = token.Token(from_, unix_now + 600, token.Scope.CHAT) # 10 minutes valid

  
  @classmethod
  def parse(cls, data: dict) -> "Dm":
    return cls.__new__(cls)._init_from_dict(data)
  
  def _init_from_dict(self, data: dict):
    self.type = data["TYPE"]
    self.from_user = UserID.parse(data["FROM"])
    self.to_user = UserID.parse(data["TO"])
    self.content = data["CONTENT"]
    
    timestamp = int(data["TIMESTAMP"])
    msg_format.validate_timestamp(timestamp)
    self.timestamp = timestamp
    
    message_id = data["MESSAGE_ID"]
    msg_format.validate_message_id(message_id)
    self.message_id = message_id
    
    self.token = token.Token.parse(data["TOKEN"])
    msg_format.validate_message(self.payload, self.__schema__)
    return self

  @classmethod
  def receive(cls, raw: str) -> "Dm":
    return cls.parse(msg_format.deserialize_message(raw))

__message__ = Dm