import ipaddress
from dataclasses import dataclass

# Immutable class for user ids
@dataclass(frozen=True)
class UserID:
  username: str
  ip: str

  @classmethod
  def parse(cls, raw: str) -> "UserID":
    raw = raw.strip()
    try:
      username, ip_str = raw.split("@", 1)
    except ValueError:
      raise ValueError(f"Invalid UserID format, missing '@': {raw}")

    username = username.strip()
    ip_str = ip_str.strip()

    if not username:
      raise ValueError("Username cannot be empty")

    try:
      ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
      raise ValueError(f"Invalid IP address: {ip_str}")
    
    return cls(username=username, ip=str(ip_obj))
    
  @staticmethod
  def validate(user_id: str) -> bool:
    if "@" not in user_id:
      return False

    try:
      name, ip = user_id.split("@", 1)
      if not name:
        return False
      # Validate IP using the ipaddress module
      ipaddress.ip_address(ip)
      return True
    except ValueError:
      return False

  def __str__(self) -> str:
    return f"{self.username}@{self.ip}"
  
  def get_ip(self) -> str:
    return self.ip