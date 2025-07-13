from messages.utils import format
import socket
import config
import log
from messages.profile.schema import profile_schema

# Sends a new PROFILE msg to the client's broadcast socket
def send(sock: socket, user_id: str, display_name: str, status: str):
  if format.validate_id(user_id) == False:
    # TODO: CHANGE ACCORDING TO SPECS
    log.drop("PROFILE: User Id Invalid")
    return

  msg = {
    "TYPE": "PROFILE",
    "USER_ID": user_id,
    "DISPLAY_NAME":  display_name,
    "STATUS": status,
  }
  if format.validate_message(msg, profile_schema) == False:
    log.drop("PROFILE: Message Invalid")
    return
  
  serialized_msg = format.serialize_message(msg)
  sock.sendto(serialized_msg.encode(config.ENCODING), (config.BROADCAST_ADDRESS, config.PORT))
  log.send(msg)
