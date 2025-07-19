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
import utils.format as format
import messages.profile as profile
import messages.dm as dm

import importlib
import pkgutil
import messages.base_message as base_message

MESSAGE_REGISTRY = {}

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


def route(data, address):
  parsed_data = data.decode(config.ENCODING)
  message = format.deserialize_message(parsed_data)
  type = message.get("TYPE")

  if type == "PROFILE":
    profile.receive(message)

  elif type == "DM":
    dm.receive(message)
