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
import log
from custom_types.base_message import BaseMessage

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

      if msg_class is None:
        log.error(f"[{module_name}] Missing __message__")
        continue

      msg_schema = msg_class.__schema__
      if msg_schema is None:
        log.error(f"[{module_name}] Missing __schema__")
        continue

      msg_type = msg_schema.get("TYPE")
      if msg_type is None:
        log.error(f"[{module_name}] Missing Field: TYPE")
        continue

      MESSAGE_REGISTRY[msg_type] = msg_class
      log.success(f"REGISTERED: [{module_name}]")  
    except Exception as err:
      log.error(f"{err}")

def send(socket: socket.socket, type: str, data: dict, ip: str, port: int):
  message_class = MESSAGE_REGISTRY.get(type)
  message_obj = message_class.parse(data)
  message_obj.send(socket, ip, port, config.ENCODING)

def recv_message(raw: bytes, address) -> BaseMessage:
  try:
    msg_str = raw.decode(config.ENCODING, errors="ignore")
    msg_type = msg_format.extract_message_type(msg_str)

    message_obj = MESSAGE_REGISTRY[msg_type].receive(msg_str)
    log.receive(f"RECEIVED: {message_obj} FROM {address}")
    return message_obj
  except Exception as err:
    log.drop({raw.decode(config.ENCODING, errors="ignore")})
    log.error({err})

def get_module(module_name: str):
  """
  Returns the module object for the given module name.
  """
  return MESSAGE_REGISTRY[module_name]
  