import log
import config
import socket
from utils import format

# Profile Template / Schema
profile_schema = {
  "TYPE": "PROFILE",
  "USER_ID": {"type": str, "required": True},
  "DISPLAY_NAME": {"type": str, "required": True},
  "STATUS": {"type": str, "required": True},
}

# Sends a new PROFILE msg to the client's broadcast socket
def send(sock: socket.socket, user_id: str, display_name: str, status: str):
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
  sock.sendto(serialized_msg.encode(config.ENCODING), (config.BROADCAST_IP, config.PORT))
  log.send(msg)


# Receives a profile message from a socket (routed from router)
def receive(message: dict):
  if format.validate_message(message, profile_schema) == False:
    log.drop(message)
    return
  log.receive(message)