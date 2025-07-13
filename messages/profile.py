import log
import config
import socket
from utils import format
from custom_types.user_id import UserID

# Profile Template / Schema
profile_schema = {
  "TYPE": "PROFILE",
  "USER_ID": {"type": UserID, "required": True},
  "DISPLAY_NAME": {"type": str, "required": True},
  "STATUS": {"type": str, "required": True},
}

# Sends a new PROFILE msg to the client's broadcast socket
def send(sock: socket.socket, user_id: str, display_name: str, status: str):
  try:
    msg = {
      "TYPE": "PROFILE",
      "USER_ID": UserID.parse(user_id),
      "DISPLAY_NAME":  display_name,
      "STATUS": status,
    }
    if format.validate_message(msg, profile_schema) == False:
      log.drop("PROFILE: Message Invalid")
      return
    
    serialized_msg = format.serialize_message(msg)
    sock.sendto(serialized_msg.encode(config.ENCODING), (config.BROADCAST_IP, config.PORT))
    log.send(msg)
  except Exception as e:
    log.drop({f"PROFILE: {e}"})

# Receives a profile message from a socket (routed from router)
def receive(message: dict):

  received_msg = {
    "TYPE": message.get("TYPE"),
    "USER_ID": UserID.parse(message.get("USER_ID")),
    "DISPLAY_NAME": message.get("DISPLAY_NAME"),
    "STATUS": message.get("STATUS"),
  }

  try:
    if format.validate_message(received_msg, profile_schema) == False:
      log.drop(f"MALFORMED: {received_msg}")
      return
    log.receive(received_msg)
  except Exception as e:
    log.drop({f"PROFILE RECEIVE: {e}"})