# Main processing hub, handles routing of incoming and outcoming messages

# TODO: Implement message parsing
# Encoding: Plain UTF-8 text, key-value format
# Separator: KEY: VALUE
# Terminator: Blank line (\n\n) [Each message should end with a (\n\n)]

# TODO: Implement token checking before:
# TODO: Implement routing to handler 
# TODO: Implement message dispatch
# TODO: Implement complex flow (i.e. acks retries timeouts)
import config
import utils.msg_format as msg_format
import socket
from typing import Type
import importlib
import pkgutil
import messages.base_message as base_message
from messages.base_message import BaseMessage

MESSAGE_REGISTRY: dict[str, Type[BaseMessage]] = {}

def load_messages(dir: str):
  """
  Loads all messages under the specified dir and validates their __message__ class

  Parameters:
  - dir: The subfolder under root containing the messages
  """
  module_dir = importlib.import_module(dir)
  for _, module_name, _ in pkgutil.iter_modules(module_dir.__path__):
    try:
      msg_module = importlib.import_module(f"{module_dir.__name__}.{module_name}")
      msg_class = getattr(msg_module, "__message__", None)

      if msg_module is base_message:
        continue
      elif msg_class is None:
        print(f"ERROR: [{module_name}] Missing __message__")
        continue

      msg_schema = msg_class.__schema__
      if msg_schema is None:
        print(f"ERROR: [{module_name}] Missing __schema__")
        continue

      msg_type = msg_schema.get("TYPE")
      if msg_type is None:
        print(f"ERROR: [{module_name}] Missing Field: TYPE")
        continue

      MESSAGE_REGISTRY[msg_type] = msg_class
      print(f"REGISTERED: [{module_name}]")  
    except Exception as err:
      print(f"ERROR: {err}")

  print(MESSAGE_REGISTRY)

def send(type: str, data: dict, socket: socket.socket, ip: str, port: int):
  message_class = base_message.BaseMessage(MESSAGE_REGISTRY.get(type))
  message_obj = message_class.parse(data)
  message_obj.send(socket, ip, port, config.ENCODING)

def route(data):
    parsed_data = data.decode(config.ENCODING)
    message = msg_format.deserialize_message(parsed_data)
    msg_type = message.get("TYPE")

    message_class = MESSAGE_REGISTRY.get(msg_type)
    if message_class is None:
      print(f"Unknown message type: {msg_type}")
      return
    message_obj = message_class.parse(message)
    message_obj.receive(data)

def get_module(module_name: str):
    """
    Returns the module object for the given module name.
    """
    return MESSAGE_REGISTRY[module_name]
  