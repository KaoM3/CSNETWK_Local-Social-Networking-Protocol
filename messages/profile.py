from utils import msg_format
from states.client_state import client_state
from custom_types.user_id import UserID
from custom_types.base_message import BaseMessage

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

  @classmethod
  def parse(cls, data: str) -> "Profile":
    return cls(
      user_id = UserID.parse(data["USER_ID"]),
      display_name = str(data["DISPLAY_NAME"]),
      status = str(data["STATUS"])
    )
  
  @classmethod
  def receive(cls, raw: str) -> "Profile":
    received = cls.parse(msg_format.deserialize_message(raw))
    client_state.add_peer(received.user_id)
    return received
  
__message__ = Profile