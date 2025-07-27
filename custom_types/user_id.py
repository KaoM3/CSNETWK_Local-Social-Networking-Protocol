import ipaddress

class UserID:
  def __init__(self, username: str, ip: str):
    username = username.strip()
    ip = ip.strip()

    if not username:
      raise ValueError("Invalid UserID: missing username")
    
    try:
      ip_obj = ipaddress.ip_address(ip)
    except ValueError:
      raise ValueError(f"Invalid UserID: invalid ip: {ip}")
    
    self.username = username
    self.ip = str(ip_obj)

  @classmethod
  def parse(cls, raw: str) -> "UserID":
    raw = raw.strip()
    try:
      username, ip_str = raw.split("@", 1)
    except ValueError:
      raise ValueError(f"Invalid UserID: missing '@': {raw}")

    username = username.strip()
    ip_str = ip_str.strip()

    if not username:
      raise ValueError("Invalid UserID: missing username")

    try:
      ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
      raise ValueError(f"Invalid UserID: invalid ip: {ip_str}")
    
    return cls(username=username, ip=str(ip_obj))

  def __eq__(self, other):
    if not isinstance(other, UserID):
      return NotImplemented
    return self.username == other.username and self.ip == other.ip

  def __hash__(self):
    return hash((self.username, self.ip))

  def __str__(self) -> str:
    return f"{self.username}@{self.ip}"
  
  def get_ip(self) -> str:
    return self.ip
  
  def get_username(self) -> str:
    return self.username
  
  def __repr__(self) -> str:
    return str(self)