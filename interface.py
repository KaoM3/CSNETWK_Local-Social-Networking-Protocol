import os
import config
import keyword
import log
import inspect
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

def get_func_args(func_signature: inspect.Signature) -> dict:
  new_msg_args = {}
  
  for name, param in func_signature.parameters.items():
    if name == "self":
      continue

    while True:
      user_input = input(f"{name}: ").strip()
      while not user_input:
        if param.default != inspect._empty:
          user_input = input(f"{name} cannot be empty. Try again: ").strip()
        user_input = param.default
      
      parser = type_parsers.get(param.annotation)
      if parser:
        try:
          new_msg_args[name] = parser(user_input)
          break
        except Exception as e:
          log.warn(f"{e}")
      else:
        new_msg_args[name] = user_input
        break

  return new_msg_args


def get_user_id() -> str:
  username = input("Enter username: ")
  user_id = f"{username}@{config.CLIENT_IP}"
  return user_id