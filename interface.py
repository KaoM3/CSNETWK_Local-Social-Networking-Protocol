import os
import router
import config
import keyword
import log
import client
from custom_types.user_id import UserID
from custom_types.token import Token
from custom_types.base_message import BaseMessage

type_parsers = {
  UserID: UserID.parse,
  Token: Token.parse,
  # add more types as needed
}

def print_message(msg_obj: BaseMessage):
  """
  Prints the message's payload in a readable format.
  """
  for field, value in msg_obj.payload.items():
    log.debug(f"{field}: {value}")

def get_field(field: str, rules: dict):
  """
  Gets user input matching the rules provided

  Parameters:
    field (string): the field requiring the input
    rules (dict): rules or flags of the field

  Returns:
    The input given by the user, matches type indicated in rules
  """
  result = None
  while True:
    user_input = input(f"Enter {field}: ").strip()
    while not user_input:
      if "default" in rules:
        user_input = rules.get("default")
      user_input = input(f"{field} cannot be empty. Try again: ").strip()      
    # For custom data types that need parsers for validation, else no validation
    typ = rules.get("type", None)
    parser = type_parsers.get(typ)
    if parser:
      try:
        result = parser(user_input)
        break
      except Exception as e:
        log.warn(f"{e}")
    else:
      result = user_input
      break

  return result

def create_message(msg_schema: dict) -> dict:
  """
  Creates a new dictionary object matching the schema provided (msg_schema)

  Parameters:
    msg_schema (dict): The schema of a message module

  Returns:
    A dictionary matching the inputs asked by the schema
  """
  new_msg_args = {}
  for field, rules in msg_schema.items():
    if field == "TYPE":
      continue
    if rules.get("input", False):
      field_data = get_field(field, rules)
      arg_name = field.lower()
      # Handles for argument names that are keywords
      if keyword.iskeyword(arg_name):
        arg_name = arg_name+"_"
      new_msg_args[arg_name] = field_data

  print(new_msg_args)
  return new_msg_args

def get_user_id() -> str:
  username = input("Enter username: ")
  user_id = f"{username}@{config.CLIENT_IP}"
  print(f"WELCOME \"{user_id}\"!")
  return user_id