from messages.utils import format
import socket
import config
import log
from messages.profile.schema import profile_schema

# Receives a profile message from a socket
def receive(message):
  if format.validate_message(message, profile_schema) == False:
    log.drop(message)
    return
  log.receive(message)

