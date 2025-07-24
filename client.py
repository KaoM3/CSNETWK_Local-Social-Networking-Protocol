import socket
import config
import threading
import argparse
import log
import time
import router
import interface
from states import client


# Is the entry point of the application.
# Handles user input as well

# TODO: Add config initialization
# TODO: Create broadcasting socket
# TODO: Create unicast socket
UNICAST_SOCKET = None
BROADCAST_SOCKET = None

def initialize_sockets(port):
  # Socket Setup
  global UNICAST_SOCKET
  global BROADCAST_SOCKET

  UNICAST_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  # TODO: For LOCAL MACHINE TESTING use args, but remove in FINAL PRODUCT
  UNICAST_SOCKET.bind((config.CLIENT_IP, port))#config.PORT))

  BROADCAST_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  BROADCAST_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  BROADCAST_SOCKET.bind(('0.0.0.0', port))

def run_threads():
  # Concurrent Thread for receiving unicast messages
  def unicast_receive_loop():
    while True:
      data, address = UNICAST_SOCKET.recvfrom(1024)
      log.debug("\nUNICAST RECEIVE\n")
      received_msg = router.recv_message(data, address)
      if received_msg is not None:
        interface.print_message(received_msg)
  threading.Thread(target=unicast_receive_loop, daemon=True).start()

  # Concurrent Thread for broadcasting every 300s:
  def broadcast_presence():
    while True:
      # TODO: Update to be dynamic (PING at first, PROFILE if sent by user)
      router.send(BROADCAST_SOCKET, "PING", {"TYPE": "PING", "USER_ID": f"{client.get_user_id()}"}, config.BROADCAST_IP, config.PORT)
      unknown_msg = "THIS SHOULD NOT BE RECEIVED (DROP THIS MSG)"
      BROADCAST_SOCKET.sendto(unknown_msg.encode(config.ENCODING), (config.BROADCAST_IP, config.PORT))
      time.sleep(config.PING_INTERVAL)
  threading.Thread(target=broadcast_presence, daemon=True).start()

def main():
  # PORT AND VERBOSE MODE
  parser = argparse.ArgumentParser()
  parser.add_argument("--port", type=int, help="Port number to use")
  parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
  args = parser.parse_args()

  # Setup logging with verbose flag
  log.setup_logging(verbose=args.verbose or config.VERBOSE)
  print("Using port:", args.port or config.PORT)
  print(config.CLIENT_IP)

  # Socket initialization
  initialize_sockets(args.port or config.PORT)

  # Initialize router
  router.load_messages(config.MESSAGES_DIR)

  # Set client UserID
  client.set_user_id(interface.get_user_id())

  # Run Threads
  run_threads()
  

  interface.create_message("PROFILE")  # Example usage, can be replaced with any message type
  #interface.create_message("PING")  # Example usage, can be replaced with any message type
  #interface.create_message("DM")  # Example usage, can be replaced with any message type
  
  interface.interface()



  #interface.create_profile_message()
  input("Press ENTER to terminate")

if __name__ == "__main__":
  main()