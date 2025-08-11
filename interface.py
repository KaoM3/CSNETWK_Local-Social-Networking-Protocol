import os
import config
import inspect
from custom_types.fields import UserID, Token, Timestamp, TTL
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from states.file_state import file_state
from client_logger import client_logger

type_parsers = {
  UserID: UserID.parse,
  Token: Token.parse,
  Timestamp: Timestamp.parse,
  TTL: TTL.parse
  # add more types as needed
}

def clear_screen():
  os.system('cls' if os.name == 'nt' else 'clear')

def format_prompt(lines: list):
  result = "\n"
  for line in lines:
    result += f"{line}\n"
  return result + "\n"

def display_help(message_registry: dict):
  help_prompt = []
  help_prompt.append("Available Message Commands:")
  for value in message_registry.keys():
    if len(value) < 7:
      help_prompt.append(f"{value.lower()}:\t\tsend a new {value} message")
    else:
      help_prompt.append(f"{value.lower()}:\tsend a new {value} message")

  help_prompt.append("\nAdditional Commands:")
  help_prompt.append("info:\t\tshows client details")
  help_prompt.append("recent:\t\tshows received messages")
  help_prompt.append("accept:\t\taccepts a received file_offer")
  help_prompt.append("reject:\t\trejects a received file_offer")
  help_prompt.append("verbose:\ttoggles verbose mode settings")
  help_prompt.append("cls:\t\tclears the screen")
  help_prompt.append("help:\t\tshows available commands")
  help_prompt.append("exit:\t\texits the program")
  help_prompt.append("ctrl^c:\t\taborts message creation")
  client_logger.info(format_prompt(help_prompt))

def debug_info():
  config_info = []
  client_state_info = []
  file_state_info = []

  config_info.append("CONFIG VARIABLES\n")
  config_info.append(f"PING_INTERVAL: {config.PING_INTERVAL}")
  config_info.append(f"PORT: {config.PORT}")
  config_info.append(f"SUBNET_MASK: {config.SUBNET_MASK}")
  config_info.append(f"ENCODING: {config.ENCODING}")
  config_info.append(f"CLIENT_IP: {config.CLIENT_IP}")
  config_info.append(f"BROADCAST_IP: {config.BROADCAST_IP}")
  config_info.append(f"VERBOSE: {config.VERBOSE}")
  config_info.append(f"DEFAULT_TTL: {config.DEFAULT_TTL}")
  config_info.append(f"MESSAGES_DIR: {config.MESSAGES_DIR}")
  config_info.append(f"BUFSIZE: {config.BUFSIZE}")

  client_state_info.append("CLIENT_STATE VARIABLES\n")
  client_state_info.append(f"UserID: {client_state.get_user_id()}")
  client_state_info.append(f"Peers: {client_state.get_peers()}")
  client_state_info.append(f"Peer display names: {client_state.get_peer_display_names()}")
  client_state_info.append(f"Followers: {client_state.get_followers()}")
  client_state_info.append(f"Following: {client_state.get_following()}")

  file_state_info.append("FILE_STATE VARIABLES\n")
  file_state_info.append(f"Recent: {file_state.get_recent()}")
  file_state_info.append(f"Accepted Files: {file_state.get_accepted_files()}")
  file_state_info.append(f"Pending Transfers: {file_state.get_pending_transfers()}")

  client_logger.info(format_prompt(config_info))
  client_logger.info(format_prompt(client_state_info))
  client_logger.info(format_prompt(file_state_info))
  
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
    elif command == "ACCEPT":
      try:
        file_state.accept_file()
      except Exception as e:
        client_logger.warn(e)
    elif command == "REJECT":
      try:
        file_state.reject_file()
      except Exception as e:
        client_logger.warn(e)
    elif command == "DEBUG":
      debug_info()
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
  client_logger.info("Recent Messages:")
  for message in client_state.get_recent_messages():
    msg_info = message.info(config.VERBOSE)
    if msg_info != "":
      client_logger.info(msg_info)

def show_client_details():
  client_logger.info(f"UserID: {client_state.get_user_id()}")
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
      try:
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
      except KeyboardInterrupt:
        client_logger.warn("Aborting message creation")
        return None
  return new_msg_args


def get_user_id() -> str:
  username = client_logger.input("Enter username: ")
  while not username:
    username = client_logger.input("Username cannot be empty")
  user_id = f"{username}@{config.CLIENT_IP}"
  return user_id