import socket
import config
import threading
import argparse
import log
import time
import router
import interface
import traceback
from states.client_state import client_state
from custom_types.user_id import UserID

UNICAST_SOCKET = None
BROADCAST_SOCKET = None

def initialize_sockets(port):
  # Socket Setup
  global UNICAST_SOCKET
  global BROADCAST_SOCKET

  UNICAST_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  UNICAST_SOCKET.bind((config.CLIENT_IP, port))

  BROADCAST_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  BROADCAST_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  BROADCAST_SOCKET.bind(('0.0.0.0', port))

def run_threads():
  # Concurrent Thread for receiving unicast messages
  def unicast_receive_loop():
    while True:
      data, address = UNICAST_SOCKET.recvfrom(1024)
      log.info("UNICAST RECEIVED")
      received_msg = router.recv_message(data, address)
      if received_msg is not None:
        interface.print_message(received_msg)
  threading.Thread(target=unicast_receive_loop, daemon=True).start()
  
  def broadcast_receive_loop():
    while True:
      data, address = BROADCAST_SOCKET.recvfrom(1024)
      log.info("BROADCAST RECEIVED")
      received_msg = router.recv_message(data, address)
      if received_msg is not None:
        interface.print_message(received_msg)
  threading.Thread(target=broadcast_receive_loop, daemon=True).start()

  # Concurrent Thread for broadcasting every 300s:
  def broadcast_presence():
    while True:
      # TODO: Update to be dynamic (PING at first, PROFILE if sent by user)
      router.send_message(BROADCAST_SOCKET, "PING", {"user_id": UserID.parse(f"{client_state.get_user_id()}")}, config.BROADCAST_IP, config.PORT)
      time.sleep(config.PING_INTERVAL)
  threading.Thread(target=broadcast_presence, daemon=True).start()

def main():
  # PORT AND VERBOSE MODE
  parser = argparse.ArgumentParser()
  parser.add_argument("--port", type=int, help="Port number to use")
  parser.add_argument("--subnet", type=int, help="Subnet Mask of the network")
  parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
  args = parser.parse_args()

  # Update config with compile arguments
  if args.port:
    config.PORT = args.port
  if args.subnet:
    config.SUBNET_MASK = args.subnet
  if args.verbose:
    config.VERBOSE = args.verbose

  # Setup logging with verbose flag
  log.setup_logging(config.VERBOSE)

  # Socket initialization
  initialize_sockets(config.PORT)

  # Initialize router
  router.load_messages(config.MESSAGES_DIR)

  # Set client UserID
  client_state.set_user_id(interface.get_user_id())

  # Run Threads
  run_threads()
  
  # Main Program Loop
  while True:
    log.info(f"WELCOME \"{client_state.get_user_id()}\"!")
    log.info(f"Using port: {config.PORT}")
    log.info(f"Client IP: {config.CLIENT_IP}/{config.SUBNET_MASK}")
    user_input = interface.get_message_type(router.MESSAGE_REGISTRY)
    if user_input in router.MESSAGE_REGISTRY:
      try:
        msg = router.MESSAGE_REGISTRY.get(user_input)
        new_msg = interface.create_message(msg.__schema__)
        ip_input = input("Enter dest ip: ")
        router.send_message(UNICAST_SOCKET, user_input, new_msg, ip_input, config.PORT)
      except Exception as e:
        log.error("An error occurred:\n" + traceback.format_exc())
    elif user_input is None:
      break

if __name__ == "__main__":
  main()

def get_broadcast_socket() -> socket.socket:
  if BROADCAST_SOCKET is None:
    raise RuntimeError("Sockets not initialized. Make sure client.initialize_sockets() was called.")
  return BROADCAST_SOCKET

def get_unicast_socket() -> socket.socket:
  if UNICAST_SOCKET is None:
    raise RuntimeError("Sockets not initialized. Make sure client.initialize_sockets() was called.")
  return UNICAST_SOCKET