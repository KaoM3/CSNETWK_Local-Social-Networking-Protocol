import ipaddress
import log
from datetime import datetime, timezone
  
def serialize_message(msg: dict) -> str:
  """Serializes `msg` into a string, ready to be encoded and sent over the network"""
  lines = []
  for key, value in msg.items():
    lines.append(f"{key}: {value}")
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
  if schema.get("TYPE") == None:
    raise ValueError(f"Invalid message: \"TYPE\" field missing")
  elif msg.get("TYPE") != schema.get("TYPE"):
    raise ValueError(f"Invalid message: msg TYPE {msg.get("TYPE")} does not match schema TYPE {schema.get("TYPE")}")
  
  for key in msg:
    if key not in schema:
      raise ValueError(f"Unexpected field in message: {key}")

  for key, rules in schema.items():
    if key == "TYPE":
      continue
    # If field is required in schema, defaults to False
    if rules.get("required", False):
      if key not in msg:
        raise ValueError(f"Missing required field: {key}")
      
    if key in msg and "type" in rules:
      if not isinstance(msg[key], rules["type"]):
        raise TypeError(f"Invalid type for {key}: expected {rules['type'].__name__}, got {type(msg[key]).__name__}")

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
