import config
import socket
import importlib
import pkgutil
import traceback
import utils.msg_format as msg_format
from typing import Type
from custom_types.base_message import BaseMessage
from client_logger import client_logger

MESSAGE_REGISTRY: dict[str, Type[BaseMessage]] = {}

def load_messages(dir: str):
  """
  Loads all messages under the specified dir and validates their __message__ class

  Parameters:
  - dir: The subfolder under root containing the messages
  """
  module_dir = importlib.import_module(dir)
  client_logger.info(f"Importing messages from {list(module_dir.__path__)}")
  for _, module_name, _ in pkgutil.iter_modules(module_dir.__path__):
    try:
      msg_module = importlib.import_module(f"{module_dir.__name__}.{module_name}")
      msg_class = getattr(msg_module, "__message__", None)

      if msg_class is None:
        client_logger.error(f"[{module_name}] Missing __message__")
        continue

      msg_schema = msg_class.__schema__
      if msg_schema is None:
        client_logger.error(f"[{module_name}] Missing __schema__")
        continue

      msg_type = msg_schema.get("TYPE")
      if msg_type is None:
        client_logger.error(f"[{module_name}] Missing Field: TYPE")
        continue

      MESSAGE_REGISTRY[msg_type] = msg_class
      client_logger.success(f"REGISTERED: [{module_name}]")  
    except Exception:
      client_logger.error("ERROR: (load_messages)" + traceback.format_exc())

def send_message(socket: socket.socket, type: str, data: dict, ip: str, port: int) -> "BaseMessage":
  try:
    message_class = MESSAGE_REGISTRY.get(type)
    message_obj = message_class(**data)
    dest = message_obj.send(socket, ip, port, config.ENCODING)
    client_logger.send(f"MESSAGE: {message_obj.payload} TO ({dest[0]}, {dest[1]})")
    return message_obj
  except Exception as e:
    client_logger.warn("Failed to send message")
    client_logger.warn(f"{e}")
    client_logger.debug(f"ERROR in send_message(): {traceback.format_exc()}")

def recv_message(raw: bytes, address) -> BaseMessage:
  try:
    msg_str = raw.decode(config.ENCODING, errors="ignore")
    msg_type = msg_format.extract_message_type(msg_str)

    message_obj = MESSAGE_REGISTRY[msg_type].receive(msg_str)

    client_logger.receive(f"MESSAGE: {message_obj.payload} FROM {address}")
    return message_obj
  except Exception as err:
    client_logger.drop({raw.decode(config.ENCODING, errors="ignore")})
    client_logger.drop({err})

def get_module(module_name: str):
  """
  Returns the module object for the given module name.
  """
  return MESSAGE_REGISTRY[module_name]
  