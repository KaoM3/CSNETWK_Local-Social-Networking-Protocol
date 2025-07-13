# Is the entry point of the application.
# Handles user input as well

# TODO: Add config initialization
import socket
import config
import threading
import argparse


# TODO: Create broadcasting socket
# TODO: Create unicast socket
# TODO: Implement listening for incoming messages
# TODO: Implement passing incoming messages to route.py
# TODO: Implement user interactions (console based)
  # TODO: Implement listening for incoming messages


# Entry point of the application
# Handles user input and socket setup

import socket
import config
import threading
import argparse
import log




def receive_unicast(sock):
    """Continuously receive and print messages on the unicast socket."""
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"[RECV] {addr}: {data.decode()}")



def main():
    parser = argparse.ArgumentParser(description="LSNP Client")
    parser.add_argument("port", type=int, help="Port number to bind to")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
    args = parser.parse_args()

    # Setup logging with verbose flag
    log.setup_logging(verbose=args.verbose)

    # Print configuration for debugging
    log.send("Client started")
    log.receive(f"Using CLIENT_IP: {config.CLIENT_IP}")
    log.drop(f"Binding to port: {args.port}")

    # Set up unicast socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((config.CLIENT_IP, args.port))

    log.send("Unicast socket bound successfully")

    # Start listening thread
    threading.Thread(target=receive_unicast, args=(sock,), daemon=True).start()

    input("Press Enter to exit...\n")

if __name__ == "__main__":
    main()
