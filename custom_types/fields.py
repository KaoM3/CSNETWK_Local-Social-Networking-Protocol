from datetime import datetime, timezone
from utils import msg_format
from enum import Enum
import ipaddress
import secrets
import re
  
class TTL:
  value: int
  def __init__(self, value: int):
    if self.is_valid(value):
      self.value = value
    else:
      raise ValueError("Invalid TTL: must be a positive integer")

  @classmethod
  def is_valid(cls, ttl: int) -> bool:
    if ttl <= 0:
      return False
    return True
      
  @classmethod
  def parse(cls, raw) -> "TTL":
    if not cls.is_valid(raw):
      raise ValueError("Invalid TTL: must be a positive integer")
    return cls(raw)
  
  def get_value(self) -> int:
    return self.value
  
  def __eq__(self, other):
    if not isinstance(other, TTL):
      return NotImplemented
    return self.value == other.value

  def __hash__(self):
    return hash(self.value)
  
  def __str__(self):
    return f"{self.value}"
  
  def __repr__(self):
    return str(self.value)
  
class Timestamp:
  time: int

  def __init__(self, unix):
    self._validate(unix)
    self.time = unix

  def is_expired(self) -> bool:
    if self.time > datetime.now().timestamp():
      return False
    return True
  
  @classmethod
  def _validate(cls, unix: int):
    if not isinstance(unix, int):
      raise TypeError(f"Invalid Timestamp {unix}: should be an integer")
    elif unix < 0:
      raise ValueError(f"Invalid Timestamp {unix}: cannot be negative")
    try:
      datetime.fromtimestamp(unix, tz=timezone.utc)
    except (ValueError, OverflowError):
      raise ValueError(f"Invalid Timestamp {unix}: is not valid unix")

  @classmethod
  def is_valid(cls, unix: int) -> bool:
    try:
      cls._validate(unix)
      return True
    except:
      return False

  @classmethod
  def parse(cls, raw) -> "Timestamp":
    return cls(int(raw))
  
  def get_time(self) -> int:
    return self.time
  
  def __eq__(self, other):
    if not isinstance(other, Timestamp):
      return NotImplemented
    return self.time == other.time

  def __hash__(self):
    return hash(self.time)
  
  def __str__(self):
    return f"{self.time}"
  
  def __repr__(self):
    return str(self.time)
  
  def __add__(self, other):
    if isinstance(other, TTL):
      return Timestamp(self.time + other.value)
    elif isinstance(other, int):
      return Timestamp(self.time + other)
    return NotImplemented
  
  def __radd__(self, other):
    return self.__add__(other)
  
  def __lt__(self, other):
    if isinstance(other, Timestamp):
      return self.time < other.time
    if isinstance(other, int):
      return self.time < other
    return NotImplemented

  def __le__(self, other):
    if isinstance(other, Timestamp):
      return self.time <= other.time
    if isinstance(other, int):
      return self.time <= other
    return NotImplemented

  def __gt__(self, other):
    if isinstance(other, Timestamp):
      return self.time > other.time
    if isinstance(other, int):
      return self.time > other
    return NotImplemented

  def __ge__(self, other):
    if isinstance(other, Timestamp):
      return self.time >= other.time
    if isinstance(other, int):
      return self.time >= other
    return NotImplemented

class MessageID:
  code: int

  def __init__(self, code: str):
    self._validate(code)
    self.code = code

  @classmethod
  def _validate(cls, message_id: str):
    if not isinstance(message_id, str):
      raise ValueError("MESSAGE_ID must be a string")
    if len(message_id) != 16:
      raise ValueError("MESSAGE_ID must be exactly 16 characters")
    if not re.fullmatch(r'[0-9a-f]{16}', message_id):
      raise ValueError("MESSAGE_ID must be a lowercase hexadecimal string")
    
  @classmethod 
  def is_valid(cls, message_id: str):
    try:
      cls._validate(message_id)
      return True
    except:
      return False
    
  @classmethod
  def parse(cls, raw) -> "MessageID":
    cls._validate(raw)
    obj = cls.__new__(cls)
    obj.code = raw
    return obj

  @classmethod
  def generate(cls) -> "MessageID":
    random_bits = secrets.randbits(64)
    code = f"{random_bits:016x}" 
    return cls(code)
  
  def get_code(self) -> str:
    return self.code
  
  def __str__(self):
    return f"{self.code}"

  def __repr__(self):
    return str(self.code)

  def __eq__(self, other):
    if not isinstance(other, MessageID):
      return NotImplemented
    return self.code == other.code

  def __hash__(self):
    return hash(self.code)

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

class Token:
  class Scope(Enum):
    CHAT = "chat"
    FILE = "file"
    BROADCAST = "broadcast"
    FOLLOW = "follow"
    GAME = "game"
    GROUP = "group"

  user_id: UserID
  valid_until: Timestamp
  scope: Scope

  def __init__(self, user_id: UserID, valid_until: Timestamp, scope: Scope):
    if not isinstance(user_id, UserID):
      raise ValueError(f"Invalid Token: {user_id} is not of type UserID")
    if not isinstance(valid_until, Timestamp):
      raise ValueError(f"Invalid Token: {valid_until} is not of type Timestamp")
    if not isinstance(scope, Token.Scope):
      raise ValueError(f"Invalid Token: {scope} is not of type Token.Scope")
    self.user_id = user_id
    self.valid_until = valid_until
    self.scope = scope

  def is_expired(self) -> bool:
    if self.valid_until > datetime.now().timestamp():
      return False
    return True
  
  @classmethod
  def validate_token(cls, token, *, expected_user_id: UserID, expected_scope):
    if not isinstance(token, cls):
      raise TypeError(f"In function validate_token {token} is not of type Token")
    elif not isinstance(expected_user_id, UserID):
      raise TypeError(f"In function validate_token {expected_user_id} is not of type UserID")
    elif not isinstance(expected_scope, cls.Scope):
      raise TypeError(f"In function validate_token {expected_scope} is not of type Token.Scope")
    
    if token.user_id != expected_user_id:
      raise ValueError("Invalid Token: user_id mismatch")
    if token.valid_until.is_expired():
      raise ValueError("Invalid Token: expired")
    if token.scope != expected_scope:
      raise ValueError(f"Invalid Token: expected scope '{expected_scope}', got '{token.scope}'")
  
  @classmethod
  def parse(cls, raw: str) -> "Token":
    parts = raw.split("|")
    if len(parts) != 3:
      raise ValueError(f"Invalid Token: Wrong format {raw}")
    
    # USER_ID VALIDATION
    user_id = UserID.parse(parts[0])
    
    # TIMESTAMP VALIDATION
    valid_until = Timestamp.parse(parts[1])

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