from dataclasses import dataclass
from datetime import datetime, timezone
from custom_types.user_id import UserID
from enum import Enum

class Scope(Enum):
  CHAT = "chat"
  FILE = "file"
  BROADCAST = "broadcast"
  FOLLOW = "follow"
  GAME = "game"
  GROUP = "group"

@dataclass
class Token:
  user_id: UserID
  valid_until: int
  scope: Scope

  @classmethod
  def parse(cls, raw: str) -> "Token":
    parts = raw.split("|")
    if len(parts) != 3:
      raise ValueError("Invalid token format")
    
    # USER_ID VALIDATION
    user_id = UserID.parse(parts[0])
    
    # TIMESTAMP VALIDATION
    try:
      valid_until = int(parts[1])
      if valid_until < 0:
        raise ValueError("Timestamp cannot be negative")
      
      datetime.fromtimestamp(valid_until, tz=timezone.utc)
    except (ValueError, OverflowError) as e:
      raise ValueError(f"Invalid timestamp: {parts[1]}") from e

    # SCOPE VALIDATION
    try:
      scope = Scope(parts[2])
    except ValueError as e:
      raise ValueError(f"Invalid scope: {parts[2]}") from e
    
    return cls(user_id=user_id, valid_until=valid_until, scope=scope)