import socket
import config
import threading
import argparse
import time
import router
import inspect
import interface
import traceback
from states.client_state import client_state
from client_logger import client_logger

UNICAST_SOCKET = None
BROADCAST_SOCKET = None

def initialize_sockets(port):
  # Socket Setup
  global UNICAST_SOCKET
  global BROADCAST_SOCKET

  UNICAST_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  UNICAST_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  UNICAST_SOCKET.bind((config.CLIENT_IP, port))

  BROADCAST_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  BROADCAST_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  BROADCAST_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  BROADCAST_SOCKET.bind(('0.0.0.0', port))

def run_threads():
  # Concurrent Thread for receiving unicast messages
  def unicast_receive_loop():
    while True:
      data, address = UNICAST_SOCKET.recvfrom(1024)
      client_logger.debug(f"Received {data} via UNICAST_SOCKET from {address}")
      received_msg = router.recv_message(data, address)
      if received_msg is not None:
        client_state.add_recent_message(received_msg)
        interface.print_message(received_msg)
  threading.Thread(target=unicast_receive_loop, daemon=True).start()
  
  def broadcast_receive_loop():
    while True:
      data, address = BROADCAST_SOCKET.recvfrom(1024)
      client_logger.debug(f"Received {data} via BROADCAST_SOCKET from {address}")
      received_msg = router.recv_message(data, address)
      if received_msg is not None:
        client_state.add_recent_message(received_msg)
        interface.print_message(received_msg)
  threading.Thread(target=broadcast_receive_loop, daemon=True).start()

  # Concurrent Thread for broadcasting every 300s:
  def broadcast_presence():
    while True:
      # TODO: Update to be dynamic (PING at first, PROFILE if sent by user)
      router.send_message(BROADCAST_SOCKET, "PING", {}, config.BROADCAST_IP, config.PORT)
      time.sleep(config.PING_INTERVAL)
  threading.Thread(target=broadcast_presence, daemon=True).start()

  def cleanup_expired_messages():
    while True:
      client_state.cleanup_expired_messages()
      time.sleep(5)
  threading.Thread(target=cleanup_expired_messages, daemon=True).start()

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
  client_logger.set_verbose(config.VERBOSE)

  # Socket initialization
  initialize_sockets(config.PORT)

  # Initialize router
  router.load_messages(config.MESSAGES_DIR)

  # Set client UserID
  client_state.set_user_id(interface.get_user_id())

  # Run Threads
  run_threads()
  
  # Main Program Loop
  user_details = []
  user_details.append(f"WELCOME \"{client_state.get_user_id()}\"!")
  user_details.append(f"Using port: {config.PORT}")
  user_details.append(f"Client IP: {config.CLIENT_IP}/{config.SUBNET_MASK}")
  user_details.append(f"Broadcast IP: {config.BROADCAST_IP}")
  client_logger.info(interface.format_prompt(user_details))
  interface.display_help(router.MESSAGE_REGISTRY)
  while True:
    user_input = interface.get_command(router.MESSAGE_REGISTRY)
    if user_input in router.MESSAGE_REGISTRY:
      try:
        msg = router.MESSAGE_REGISTRY.get(user_input)
        msg_constructor_args = inspect.signature(msg.__init__)
        new_msg = interface.get_func_args(msg_constructor_args)
        ip_input = client_logger.input("Enter dest ip (optional): ")
        if ip_input == None or ip_input == "":
          ip_input = "default"
        router.send_message(UNICAST_SOCKET, user_input, new_msg, ip_input, config.PORT)
      except Exception as e:
        client_logger.error("An error occurred:\n" + traceback.format_exc())
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