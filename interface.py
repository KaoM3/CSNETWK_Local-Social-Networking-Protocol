import os
import config
import keyword
import log
from custom_types.user_id import UserID
from custom_types.token import Token
from custom_types.base_message import BaseMessage

type_parsers = {
  UserID: UserID.parse,
  Token: Token.parse,
  # add more types as needed
}

def clear_screen():
  os.system('cls' if os.name == 'nt' else 'clear')

def get_message_type(message_registry: dict):
  while True:
    print("\nSelect an action:")
    for i, (key, _) in enumerate(message_registry.items(), start=1):
      print(f"{i}. {key}")
    print(f"{i + 1}. Exit")
    print(f"{i + 2}. Clear Screen")
    choice = input("Enter your action number: ").strip()
    if choice.isdigit():
      choice_num = int(choice)
      if 1 <= choice_num <= len(message_registry):
        selected_key = list(message_registry.keys())[choice_num - 1]
        print(f"\nYou selected: {selected_key}")
        return selected_key
      elif choice_num == len(message_registry) + 1:
        print("Exiting. Goodbye!")
        return None
      elif choice_num == len(message_registry) + 2:
        clear_screen()
      else:
        print("Invalid choice. Please enter a valid number.")
    else:
      print("Invalid input. Please enter a number.")

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

  log.debug(new_msg_args)
  return new_msg_args

def get_user_id() -> str:
  username = input("Enter username: ")
  user_id = f"{username}@{config.CLIENT_IP}"
  return user_id