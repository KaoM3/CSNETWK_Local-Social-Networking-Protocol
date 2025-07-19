import socket
import config
import threading
import argparse
import log
import time
import router

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
      router.route(data, address)
       
  threading.Thread(target=unicast_receive_loop, daemon=True).start()

  # Concurrent Thread for broadcasting every 300s:
  def broadcast_presence():
    while True:
      # TODO: Update to be dynamic (PING at first, PROFILE if sent by user)
      router.send(BROADCAST_SOCKET, f"TEST_USER@{config.CLIENT_IP}", "TEST_USER", "TEST_STATUS")
      time.sleep(config.PING_INTERVAL)
  threading.Thread(target=broadcast_presence, daemon=True).start()

  def broadcast_receive_loop():
    while True:
      raw, address = BROADCAST_SOCKET.recvfrom(1024)
      router.route(raw, address)
  threading.Thread(target=broadcast_receive_loop, daemon=True).start()

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
  run_threads()

  router.load_messages(config.MESSAGES_DIR)

  input("Press Enter to Terminate\n")

# TODO: Implement passing incoming messages to route.py
# TODO: Implement user interactions (console based)

if __name__ == "__main__":
  main()