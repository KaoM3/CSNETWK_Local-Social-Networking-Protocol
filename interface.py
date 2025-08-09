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

def format_prompt(lines: list):
  result = "\n"
  for line in lines:
    result += f"{line}\n"
  return result + "\n"

def get_message_type(message_registry: dict):
  prompt = []
  prompt.append("Select an action:")
  for i, (key, _) in enumerate(message_registry.items(), start=1):
    prompt.append(f"{i}. {key}")
  prompt.append(f"{i + 1}. Show Client Info")
  prompt.append(f"{i + 2}. Show Recent Messages")
  prompt.append(f"{i + 3}. Clear Screen")
  prompt.append(f"{i + 4}. Exit")
  while True:
    client_logger.info(format_prompt(prompt))
    choice = client_logger.input("Enter your action number: ").strip()
    if choice.isdigit():
      choice_num = int(choice)
      if 1 <= choice_num <= len(message_registry):
        selected_key = list(message_registry.keys())[choice_num - 1]
        client_logger.info(f"You selected: {selected_key}")
        return selected_key
      elif choice_num == len(message_registry) + 1:
        show_client_details()
      elif choice_num == len(message_registry) + 2:
        show_recent_messages()
      elif choice_num == len(message_registry) + 3:
        clear_screen()
      elif choice_num == len(message_registry) + 4:
        client_logger.info("Exiting. Goodbye!")
        return None
      else:
        client_logger.error("Invalid choice. Please enter a valid number.")
    else:
      client_logger.error("Invalid input. Please enter a number.")

def display_help(message_registry: dict):
  help_prompt = []
  help_prompt.append("Available Commands:")
  for value in message_registry.keys():
    if len(value) < 7:
      help_prompt.append(f"{value.lower()}:\t\tsend a new {value} message")
    else:
      help_prompt.append(f"{value.lower()}:\tsend a new {value} message")

  help_prompt.append("info:\t\tshows client details")
  help_prompt.append("recent:\t\tshows received messages")
  help_prompt.append("verbose:\ttoggles verbose mode settings")
  help_prompt.append("cls:\t\tclears the screen")
  help_prompt.append("help:\t\tshows available commands")
  help_prompt.append("exit:\t\texits the program")
  client_logger.info(format_prompt(help_prompt))

def toggle_verbose():
  if config.VERBOSE:
    config.VERBOSE = False
    client_logger.set_verbose(config.VERBOSE)
  else:
    config.VERBOSE = True
    client_logger.set_verbose(config.VERBOSE)
  client_logger.info(f"Verbose mode set to {config.VERBOSE}")

def get_command(message_registry: dict):
  valid_commands = message_registry.keys
  while True:
    command = input().upper().strip()
    if command in valid_commands():
      return command
    elif command == "":
      continue
    elif command == "VERBOSE":
      toggle_verbose()
    elif command == "HELP":
      display_help(message_registry)
    elif command == "CLS":
      clear_screen()
    elif command == "INFO":
      show_client_details()
    elif command == "RECENT":
      show_recent_messages()
    elif command == "EXIT":
      return None
    else:
      client_logger.warn(f"Command {command} is not valid. Enter help for list of commands.")
    

def print_message(msg_obj: BaseMessage):
  """
  Prints the message's payload in a readable format.
  """
  msg_info = msg_obj.info(config.VERBOSE)
  if msg_info != "":
    client_logger.info(msg_info)

def show_recent_messages():
  for message in client_state.get_recent_messages():
    msg_info = message.info(config.VERBOSE)
    if msg_info != "":
      client_logger.info(msg_info)

def show_client_details():
  client_logger.info(f"UserID: \"{client_state.get_user_id()}\"!")
  client_logger.info(f"Using port: {config.PORT}")
  client_logger.info(f"Client IP: {config.CLIENT_IP}/{config.SUBNET_MASK}")
  client_logger.info(f"Broadcast IP: {config.BROADCAST_IP}")
  client_logger.info(f"Peers: {client_state.get_peers()}")
  client_logger.info(f"Peer display names: {client_state.get_peer_display_names()}")
  client_logger.info(f"Followers: {client_state.get_followers()}")
  client_logger.info(f"Following: {client_state.get_following()}")

def get_func_args(func_signature: inspect.Signature) -> dict:
  new_msg_args = {}
  
  for name, param in func_signature.parameters.items():
    if name == "self":
      continue

    while True:
      if param.default != inspect._empty:
        input_prompt = f"{name} (default={param.default})"
      else:
        input_prompt = name
      user_input = client_logger.input(f"{input_prompt}: ").strip()
      while not user_input:
        if param.default != inspect._empty:
          user_input = param.default
        else:
          user_input = client_logger.input(f"{name} cannot be empty. Try again: ").strip()
      
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
  username = client_logger.input("Enter username: ")
  while not username:
    username = client_logger.input("Username cannot be empty")
  user_id = f"{username}@{config.CLIENT_IP}"
  return user_id