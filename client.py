import socket
import config
import threading
import argparse
import time
import ipaddress
import router
import inspect
import interface
import traceback
from states.client_state import client_state
from states.file_state import file_state
from client_logger import client_logger
from queue import Queue

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
  recv_queue = Queue()

  # Thread: socket listener, only receives and puts into queue
  def unicast_receive_loop():
    client_logger.debug("INIT THREAD: unicast_receive_loop()")
    while True:
      data, address = UNICAST_SOCKET.recvfrom(config.BUFSIZE)
      recv_queue.put((data, address))

  threading.Thread(target=unicast_receive_loop, daemon=True).start()

  # Thread: message processor, consumes from queue and processes messages
  def broadcast_receive_loop():
    client_logger.debug("INIT THREAD: broadcast_receive_loop()")
    while True:
      data, address = BROADCAST_SOCKET.recvfrom(config.BUFSIZE)
      #client_logger.debug(f"Received {data} via BROADCAST_SOCKET from {address}")
      received_msg = router.recv_message(data, address)
      if received_msg is not None:
        client_state.add_recent_message_received(received_msg)
        new_peer = None
        if hasattr(received_msg, "from_user"):
          new_peer = client_state.add_peer(received_msg.from_user)
        elif hasattr(received_msg, "user_id"):
          new_peer = client_state.add_peer(received_msg.user_id)
        if new_peer is not None:
          router.send_message(BROADCAST_SOCKET, "PING", {}, config.BROADCAST_IP, config.PORT)
        interface.print_message(received_msg)
  threading.Thread(target=broadcast_receive_loop, daemon=True).start()

  def unicast_process_loop():
    client_logger.debug("INIT THREAD: unicast_process_loop()")
    while True:
      data, address = recv_queue.get()  # blocks until item available
      try:
        received_msg = router.recv_message(data, address)
        if received_msg is not None:
          client_state.add_recent_message_received(received_msg)
          new_peer = None
          if hasattr(received_msg, "from_user"):
            new_peer = client_state.add_peer(received_msg.from_user)
          elif hasattr(received_msg, "user_id"):
            new_peer = client_state.add_peer(received_msg.user_id)
          if new_peer is not None:
            router.send_message(BROADCAST_SOCKET, "PING", {}, config.BROADCAST_IP, config.PORT)
          interface.print_message(received_msg)
      except Exception as e:
          client_logger.error(f"Error processing message from {address}:\n{e}")
  threading.Thread(target=unicast_process_loop, daemon=True).start()

  # Concurrent Thread for broadcasting every 300s:
  def broadcast_presence():
    client_logger.debug("INIT THREAD: broadcast_presence()")
    while True:
      # TODO: Update to be dynamic (PING at first, PROFILE if sent by user)
      try:
        sent_ping = router.send_message(BROADCAST_SOCKET, "PING", {}, config.BROADCAST_IP, config.PORT)
        if sent_ping is not None:
          client_state.add_recent_message_sent(sent_ping)
        time.sleep(config.PING_INTERVAL)
      except:
        client_logger.error("Error occurred in thread <BROADCAST_PRESENCE>:\n" + traceback.format_exc())
  threading.Thread(target=broadcast_presence, daemon=True).start()

  def update_states():
    while True:
      client_logger.debug("Updating states...")
      expired_messages = client_state.cleanup_expired_messages()
      file_state.complete_transfers()
      expired_file_offer_ids = []
      for msg in expired_messages:
        if msg.type == "FILE_OFFER":
          expired_file_offer_ids.append(msg.fileid)
      file_state.remove_transfers(expired_file_offer_ids)
      time.sleep(5)
  threading.Thread(target=update_states, daemon=True).start()

def main():
  # PORT AND VERBOSE MODE
  parser = argparse.ArgumentParser()
  parser.add_argument("--port", type=int, help="Port number to use")
  parser.add_argument("--subnet", type=int, help="Subnet Mask of the network in prefix form")
  parser.add_argument("--ipaddress", type=str, help="Ip address of the network")
  parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
  args = parser.parse_args()

  # Update config with compile arguments
  if args.port:
    config.PORT = args.port
  if args.subnet:
    config.SUBNET_MASK = args.subnet
  if args.verbose:
    config.VERBOSE = args.verbose
  if args.ipaddress:
    ip_override = ipaddress.ip_address(args.ipaddress)
    config.CLIENT_IP = str(ip_override)
    config.BROADCAST_IP = config.get_broadcast_ip(config.SUBNET_MASK)

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
  valid_message_commands = []
  for key in router.MESSAGE_REGISTRY:
    msg_class = router.MESSAGE_REGISTRY[key]
    if msg_class.__hidden__ == False:
      valid_message_commands.append(key)

  user_details = []
  user_details.append(f"WELCOME \"{client_state.get_user_id()}\"!")
  user_details.append(f"Using port: {config.PORT}")
  user_details.append(f"Client IP: {config.CLIENT_IP}/{config.SUBNET_MASK}")
  user_details.append(f"Broadcast IP: {config.BROADCAST_IP}")
  client_logger.info(interface.format_prompt(user_details))
  interface.display_help(valid_message_commands)

  while True:
    user_input = interface.get_command(valid_message_commands)
    if user_input in router.MESSAGE_REGISTRY:
      try:
        msg = router.MESSAGE_REGISTRY.get(user_input)
        msg_constructor_args = inspect.signature(msg.__init__)
        new_msg_args = interface.get_func_args(msg_constructor_args)
        if new_msg_args is None:
          continue
        dest_ip = "default"
        sent_msg = router.send_message(UNICAST_SOCKET, user_input, new_msg_args, dest_ip, config.PORT)
        if sent_msg is not None:
          client_state.add_recent_message_sent(sent_msg)
      except Exception:
        client_logger.error("Error occurred in <MAIN>:\n" + traceback.format_exc())
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