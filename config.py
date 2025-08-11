# Contains configuration data

# TODO: Add the following:
# ping interval (hard coded, 300s)
# broadcast address (depends on network)
# unicast port (50999)
# buffer size for port receive (unknown as of now)
# ttl default (if any)

import socket
import ipaddress
import sys

# Get Client IP
def get_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    # Doesn't send data, just uses the OS routing table
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]
  finally:
    s.close()
    

# Get Broadcast IP
def get_broadcast_ip(subnet_mask: int):
  """Get the broadcast address based on the local IP."""
  try:
    ip = ipaddress.ip_address(CLIENT_IP)
    network = ipaddress.ip_network(f"{ip}/{subnet_mask}", strict=False)  # Assuming /24 subnet
    return str(network.broadcast_address)
  except ValueError as e:
    print(f"Error determining broadcast address: {e}")
    sys.exit(1)

PING_INTERVAL = 300
PORT = 50999
SUBNET_MASK = 24
ENCODING = "utf-8"
CLIENT_IP = get_ip()
BROADCAST_IP = get_broadcast_ip(SUBNET_MASK)
VERBOSE = False
DEFAULT_TTL = 300
MESSAGES_DIR = "messages"
BUFSIZE = 4096
KEEP_ALIVE = 30
