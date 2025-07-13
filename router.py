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
import messages.utils.format as format
import messages.profile as profile
def route(data, address):
  parsed_data = data.decode(config.ENCODING)
  message = format.deserialize_message(parsed_data)
  type = message.get("TYPE")

  if type == "PROFILE":
    profile.receive(message)
