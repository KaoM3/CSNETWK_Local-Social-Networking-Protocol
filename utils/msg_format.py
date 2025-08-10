import re
from states.game import game_session_manager

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
    turn = int(turn)
    if turn < 0:
      raise ValueError()
  except (ValueError, TypeError):
    raise ValueError(f"{turn}Invalid turn number")
  return turn


def check_game_id(game_id: str) -> str:
    pattern = r"g(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
    if re.fullmatch(pattern, game_id):
        if game_session_manager.find_game(game_id):
            return game_id
        else:
            raise ValueError(f"Game ID {game_id} does not exists")

    raise ValueError(f"Invalid GAMEID format: {game_id}")

def extract_message_type(msg: str) -> str:
  type_field = msg.split("\n", 1)[0]

  if type_field.startswith("TYPE: "):
    return type_field[6:].strip()
  
  raise ValueError("TYPE field is missing or malformed")