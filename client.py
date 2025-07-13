import socket
import config
import threading
import argparse

# Is the entry point of the application.
# Handles user input as well

# TODO: Add config initialization
# TODO: Create broadcasting socket
# TODO: Create unicast socket

def main():
  # PORT AND CLIENT IP
  parser = argparse.ArgumentParser()
  parser.add_argument("port", type=int, help="Port number to use")
  args = parser.parse_args()
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

if __name__ == "__main__":
  main()