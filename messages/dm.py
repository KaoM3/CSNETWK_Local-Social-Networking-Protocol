import socket
import secrets
import log
import config
from custom_types.user_id import UserID
from custom_types.token import Token
from datetime import datetime, timezone
from utils import format

dm_schema = {
  "TYPE": "DM",
  "FROM": {"type": UserID, "required": True},
  "TO": {"type": UserID, "required": True},
  "CONTENT": {"type": str, "required": True},
  "TIMESTAMP": {"type": int, "required": True},
  "MESSAGE_ID": {"type": str, "required": True},
  "TOKEN": {"type": Token, "required": True},
}

def send(sock: socket.socket, from_user: str, to_user: str, content: str):
  try:
    from_uid = UserID.parse(from_user)
    to_uid = UserID.parse(to_user)
    expiry = int(datetime.now(timezone.utc).timestamp()) + config.DEFAULT_TTL
    token = Token.parse(f"{from_user}|{str(expiry)}|chat")
    msg = {
      "TYPE": "DM",
      "FROM": from_uid,
      "TO": to_uid,
      "CONTENT": content,
      "TIMESTAMP": int(datetime.now(timezone.utc).timestamp()),
      "MESSAGE_ID": secrets.token_hex(8),
      "TOKEN": token,
    }
    if format.validate_message(msg, dm_schema) == False:
      log.drop("SEND DM")
      return
    
    serialized_msg = format.serialize_message(msg)
    sock.sendto(serialized_msg.encode(config.ENCODING), (to_uid.get_ip(), config.PORT))
    log.send(msg)

  except ValueError as e:
    log.drop(f"ERROR {e}")

# Receives a profile message from a socket (routed from router)
def receive(message: dict):
  try:
    token = Token.parse(message.get("TOKEN"))
    received_msg = {
      "TYPE": message.get("TYPE"),
      "FROM": UserID.parse(message.get("FROM")),
      "TO": UserID.parse(message.get("TO")),
      "CONTENT": message.get("CONTENT"),
      "TIMESTAMP": int(message.get("TIMESTAMP")),
      "MESSAGE_ID": message.get("MESSAGE_ID"),
      "TOKEN": token,
    }

    if Token.validate(token) == False:
      log.drop(f"INVALID TOKEN: {message}")
      return

    if format.validate_message(received_msg, dm_schema) == False:
      log.drop(f"INVALID FORMAT: {message}")
      return
    
    log.receive(received_msg)
  except Exception as e:
    log.drop(f"ERROR processing received message: {e}")