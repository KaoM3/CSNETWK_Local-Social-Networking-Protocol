import ipaddress
import log
from datetime import datetime, timezone
  
def serialize_message(msg: dict) -> str:
  lines = []
  for key, value in msg.items():
    lines.append(f"{key}: {value}")
  # Join lines with newline, then add the blank line terminator
  return "\n".join(lines) + "\n\n"

def deserialize_message(raw: str) -> dict:
  msg = {}
  # Strip to remove trailing whitespace/newlines
  raw = raw.strip()
  # Split by lines
  lines = raw.split("\n")
  for line in lines:
    # Skip empty lines (if any)
    if not line.strip():
      continue
    # Split at first colon only
    if ':' not in line:
      raise ValueError(f"Invalid line (missing colon): {line}")
    key, value = line.split(":", 1)
    msg[key.strip()] = value.strip()
  return msg

# Validates a message according to a provided schema
def validate_message(msg: dict, schema: dict) -> bool:
  if schema.get("TYPE") == None:
    log.drop("Schema must have a TYPE field")
    return False
  elif msg.get("TYPE") != schema.get("TYPE"):
    log.drop(f"Message type {msg.get("TYPE")} does not match schema type {schema.get("TYPE")}")
    return False
  
  for key, rules in schema.items():
    if key == "TYPE":
      continue

    # If field is required in schema
    if rules.get("required", False):
      if key not in msg:
        log.drop(f"Missing required field: {key}")
        return False

    if key in msg and "type" in rules:
      if not isinstance(msg[key], rules["type"]):
        log.drop(f"Invalid type for {key}: expected {rules['type'].__name__}, got {type(msg[key]).__name__}")
        return False

  return True

def unix_to_datetime(utc_timestamp) -> datetime:
  utc_datetime = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc)
  return utc_datetime

def datetime_to_unix(utc_datetime: datetime) -> int:
  return int(utc_datetime.timestamp())
