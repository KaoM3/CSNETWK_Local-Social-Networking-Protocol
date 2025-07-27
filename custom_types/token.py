from custom_types.user_id import UserID
from enum import Enum
from utils import msg_format

class Token:
  class Scope(Enum):
    CHAT = "chat"
    FILE = "file"
    BROADCAST = "broadcast"
    FOLLOW = "follow"
    GAME = "game"
    GROUP = "group"

  user_id: UserID
  valid_until: int
  scope: Scope

  def __init__(self, user_id: UserID, valid_until: int, scope: Scope):
    if not isinstance(user_id, UserID):
      raise ValueError("Invalid Token: user_id is not of type UserID")
    self.user_id = user_id
    try:
      msg_format.validate_timestamp(valid_until)
      self.valid_until = valid_until
    except ValueError as err:
      raise ValueError(f"Invalid Token: {err}")
    self.scope = scope

  @classmethod
  def parse(cls, raw: str) -> "Token":
    parts = raw.split("|")
    if len(parts) != 3:
      raise ValueError(f"Invalid Token: Wrong format {raw}")
    
    # USER_ID VALIDATION
    user_id = UserID.parse(parts[0])
    
    # TIMESTAMP VALIDATION
    try:
      valid_until = int(parts[1])
      msg_format.validate_timestamp(valid_until)
    except ValueError as err:
      raise ValueError(f"Invalid Token: {err}")

    # SCOPE VALIDATION
    try:
      scope = Token.Scope(parts[2])
    except ValueError:
      raise ValueError(f"Invalid Token: Wrong scope {parts[2]}")
    
    return cls(user_id=user_id, valid_until=valid_until, scope=scope)

  def __eq__(self, other):
    if not isinstance(other, Token):
      return NotImplemented
    return self.user_id == other.user_id and self.valid_until == other.valid_until and self.scope == other.scope

  def __hash__(self):
    return hash((self.user_id, self.valid_until, self.scope))
  
  def __str__(self):
    return f"{str(self.user_id)}|{str(self.valid_until)}|{self.scope.value}"
  
  def __repr__(self):
    return str(self)
  