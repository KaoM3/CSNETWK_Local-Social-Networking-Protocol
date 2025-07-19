from utils import msg_format
from custom_types.user_id import UserID
from messages.base_message import BaseMessage

class Profile(BaseMessage):
  TYPE = "PROFILE"
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
      "STATUS": self.status,
    }
  
  def __init__(self, user_id: UserID, display_name: str, status: str):
    self.type = self.TYPE
    self.user_id = user_id
    self.display_name = display_name
    self.status = self.status
    msg_format.validate_message(self.payload, self.__schema__)

  @classmethod
  def parse(cls, data: str) -> "Profile":
    return cls(
      user_id = UserID.parse(data["USER_ID"]),
      display_name = str(data["DISPLAY_NAME"]),
      status = str(data["STATUS"])
    )
  
  @classmethod
  def receive(cls, raw: str) -> "Profile":
    return cls.parse(msg_format.deserialize_message(raw))
  
__message__ = Profile