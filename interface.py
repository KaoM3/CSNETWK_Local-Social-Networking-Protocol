import os
import config
import inspect
from custom_types.user_id import UserID
from custom_types.token import Token
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from client_logger import client_logger

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
    print(f"{i + 1}. Show Client Info")
    print(f"{i + 2}. Show Recent Messages")
    print(f"{i + 3}. Clear Screen")
    print(f"{i + 4}. Exit")
    choice = input("Enter your action number: ").strip()
    if choice.isdigit():
      choice_num = int(choice)
      if 1 <= choice_num <= len(message_registry):
        selected_key = list(message_registry.keys())[choice_num - 1]
        print(f"\nYou selected: {selected_key}")
        return selected_key
      elif choice_num == len(message_registry) + 1:
        show_client_details()
      elif choice_num == len(message_registry) + 2:
        show_recent_messages(client_state.get_recent_messages())
      elif choice_num == len(message_registry) + 3:
        clear_screen()
      elif choice_num == len(message_registry) + 4:
        print("Exiting. Goodbye!")
        return None
      else:
        print("Invalid choice. Please enter a valid number.")
    else:
      print("Invalid input. Please enter a number.")

def print_message(msg_obj: BaseMessage):
  """
  Prints the message's payload in a readable format.
  """
  for field, value in msg_obj.payload.items():
    client_logger.debug(f"{field}: {value}")

def show_recent_messages(recent_messages: list):
  for message in recent_messages:
    print_message(message)

def show_client_details():
  client_logger.info(f"UserID: \"{client_state.get_user_id()}\"!")
  client_logger.info(f"Using port: {config.PORT}")
  client_logger.info(f"Client IP: {config.CLIENT_IP}/{config.SUBNET_MASK}")
  client_logger.info(f"Broadcast IP: {config.BROADCAST_IP}")
  client_logger.info(f"Peers: {client_state.get_peers()}")
  client_logger.info(f"Followers: {client_state.get_followers()}")
  client_logger.info(f"Following: {client_state.get_following()}")

def get_func_args(func_signature: inspect.Signature) -> dict:
  new_msg_args = {}
  
  for name, param in func_signature.parameters.items():
    if name == "self":
      continue

    while True:
      user_input = input(f"{name}: ").strip()
      while not user_input:
        if param.default != inspect._empty:
          user_input = param.default
        else:
          user_input = input(f"{name} cannot be empty. Try again: ").strip()
      
      parser = type_parsers.get(param.annotation)
      if parser:
        try:
          new_msg_args[name] = parser(user_input)
          break
        except Exception as e:
          client_logger.warn(f"{e}")
      else:
        new_msg_args[name] = user_input
        break

  return new_msg_args


def get_user_id() -> str:
  username = input("Enter username: ")
  while not username:
    username = input("Username cannot be empty")
  user_id = f"{username}@{config.CLIENT_IP}"
  return user_id