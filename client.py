import socket
import config
import threading
import argparse
import log

# Is the entry point of the application.
# Handles user input as well

# TODO: Add config initialization
# TODO: Create broadcasting socket
# TODO: Create unicast socket

def main():
  # PORT AND VERBOSE MODE
  parser = argparse.ArgumentParser()
  parser.add_argument("port", type=int, help="Port number to use")
  parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
  args = parser.parse_args()

  # Setup logging with verbose flag
  log.setup_logging(verbose=args.verbose)
  print("Using port:", args.port)
  print(config.CLIENT_IP)

  unicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  # For LOCAL MACHINE TESTING use args
  unicast_socket.bind((config.CLIENT_IP, args.port))#config.UNICAST_PORT))

  # TODO: Implement listening for incoming messages
  def unicast_receive_loop():
    while True:
      data, addr = unicast_socket.recvfrom(1024)
      print(f"[RECV] {addr}: {data.decode()}")

  threading.Thread(target=unicast_receive_loop, daemon=True).start()
  input("Press Enter to exit...\n")

# TODO: Implement passing incoming messages to route.py
# TODO: Implement user interactions (console based)
