# Contains configuration data

# TODO: Add the following:
# ping interval (hard coded, 300s)
# broadcast address (depends on network)
# unicast port (50999)
# buffer size for port receive (unknown as of now)
# ttl default (if any)

import socket

def get_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    # Doesn't send data, just uses the OS routing table
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]
  finally:
    s.close()

PING_INTERVAL = 300
UNICAST_PORT = 50999
CLIENT_IP = get_ip()
