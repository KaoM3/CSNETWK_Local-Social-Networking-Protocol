import secrets
import re
import config
from datetime import datetime, timezone
from custom_types.token import Token
from custom_types.user_id import UserID
  
def serialize_message(msg: dict) -> str:
  """Serializes `msg` into a string, ready to be encoded and sent over the network"""
  lines = []
  for key, value in msg.items():
    lines.append(f"{key}: {str(value)}")
  return "\n".join(lines) + "\n\n"

def deserialize_message(raw: str) -> dict:
  """
  Deserializes a string with key value pairs as the separator and terminates with \\n\\n to a dictionary with key value pairs.
  Removes leading and trailing whitespace or \\n characters.
  Skips over empty lines (no field, separator, or value)
  
  Parameters:
    raw (str): The string to be deserialized

  Returns:
    The dictionary form of the raw string

  Raises:
    ValueError: If the does not end with the proper terminator
    ValueError: If a field is malformed (no ":" as separator)
  """
  # Terminator Check
  raw = raw.replace('\r\n', '\n')   # Case for windows style
  if not raw.endswith('\n\n'):
    raise ValueError(f"Invalid terminator: {raw}")
  
  # Field and Separator Parsing (OWC allowed)
  msg = {}
  raw = raw.strip()
  lines = raw.split("\n")
  for line in lines:
    if not line.strip():
      continue
    if ':' not in line:
      raise ValueError(f"Invalid field (missing colon): {line}")
    key, value = line.split(":", 1)
    msg[key.strip()] = value.strip()
  return msg

def validate_message(msg: dict, schema: dict):
  """
  Checks `msg` if its keys and its data types match the provided `schema`

  Parameters:
    msg (dict): The message in dictionary form
    schema (dict): The schema that msg would be validated against 

  Raises:
    ValueError: If the TYPE field is missing
    ValueError: If message does not include required schema fields
    ValueError: If message includes fields not in schema fields
    TypeError: If message field's type does not match schema field's type
  """
  # Ensures that each schema has a type field and matches with the message's type field
  if schema.get("TYPE") == None:
    raise ValueError(f"Invalid message: \"TYPE\" field missing")
  elif msg.get("TYPE") != schema.get("TYPE"):
    raise ValueError(f"Invalid message: msg TYPE {msg.get("TYPE")} does not match schema TYPE {schema.get("TYPE")}")
  
  # Ensures the schema contains field that is seen in the message
  for field in msg:
    if field not in schema:
      raise ValueError(f"Unexpected field in message: {field}")

  # Iterates over the fields and rules in the schema (rules being the dictionary of flags)
  for field, rules in schema.items():
    if field == "TYPE":
      continue
    # Ensures fields are populated unless set by the flag as false.
    if rules.get("required", True):
      if field not in msg:
        raise ValueError(f"Missing required field: {field}")
    # Perform type validation for the field's value by checking if it is an instance of specified "type" in rules
    if field in msg and "type" in rules:
      if not isinstance(msg[field], rules["type"]):
        raise TypeError(f"Invalid type for {field}: expected {rules['type'].__name__}, got {type(msg[field]).__name__}")

def sanitize_ttl(ttl: int):
  try:
    ttl = int(ttl)
    if ttl <= 0:
      raise ValueError()
  except (ValueError, TypeError):
    ttl = config.DEFAULT_TTL
  return ttl

def sanitize_position(position: int):
  try:
    position = int(position)
    if position < 0 or position > 8:
      raise ValueError()
  except (ValueError, TypeError):
      raise ValueError("Position must be an integer between 0 and 8")
  return position

def sanitize_turn(turn: int):
  try:
    ttl = int(ttl)
    if ttl <= 0:
      raise ValueError()
  except (ValueError, TypeError):
    raise ValueError("Position must be an integer above 0")
  return turn

import re


def check_game_id(game_id: str) -> str:
    pattern = r"g(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
    if re.fullmatch(pattern, game_id):
        return game_id
    raise ValueError(f"Invalid GAMEID format: {game_id}")



def isTokenExpired(token: Token) -> bool:
  if token.valid_until > datetime.now().timestamp():
    return False
  return True

def validate_token(token: Token, *, expected_user_id: UserID, expected_scope: Token.Scope):
  if token.user_id != expected_user_id:
    raise ValueError("Invalid Token: user_id mismatch")
  
  if isTokenExpired(token):
    raise ValueError("Invalid Token: expired")
  
  if token.scope != expected_scope:
    raise ValueError(f"Invalid Token: expected scope '{expected_scope}', got '{token.scope}'")

def unix_to_datetime(utc_timestamp) -> datetime:
  utc_datetime = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc)
  return utc_datetime

def datetime_to_unix(utc_datetime: datetime) -> int:
  return int(utc_datetime.timestamp())

def validate_timestamp(unix: int):
  if not isinstance(unix, int) or unix < 0:
    raise ValueError(f"Invalid timestamp: {unix}")
  try:
    datetime.fromtimestamp(unix, tz=timezone.utc)
  except (ValueError, OverflowError):
      raise ValueError(f"Invalid timestamp: {unix}")

def generate_message_id() -> str:
  random_bits = secrets.randbits(64)
  return f"{random_bits:016x}" 

def validate_message_id(message_id: str):
  if not isinstance(message_id, str):
    raise ValueError("MESSAGE_ID must be a string")
  if len(message_id) != 16:
    raise ValueError("MESSAGE_ID must be exactly 16 characters")
  if not re.fullmatch(r'[0-9a-f]{16}', message_id):
    raise ValueError("MESSAGE_ID must be a lowercase hexadecimal string")
  
def extract_message_type(msg: str) -> str:
  type_field = msg.split("\n", 1)[0]

  if type_field.startswith("TYPE: "):
    return type_field[6:].strip()
  
  raise ValueError("TYPE field is missing or malformed")