import socket
import config
def main():

  
  MESSAGE = "TYPE: PING\nUSER_ID: example_user@192.168.1.100"
  MESSAGE2 = "TYPE: PING\nUSER_ID: example_user@192.1600\n\n"
  MESSAGE3 = "TYPE: PING\nUSER_ID: @192.168.1.100\n\n"
  MESSAGE_VALID = "TYPE: PING\nUSER_ID: example_user@192.168.1.100\n\n"

  # Create UDP socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  # Enable broadcasting mode
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

  # Send broadcast message
  sock.sendto(MESSAGE.encode('utf-8'), (config.BROADCAST_IP, config.PORT))
  sock.sendto(MESSAGE2.encode('utf-8'), (config.BROADCAST_IP, config.PORT))
  sock.sendto(MESSAGE3.encode('utf-8'), (config.BROADCAST_IP, config.PORT))
  sock.sendto(MESSAGE_VALID.encode('utf-8'), (config.BROADCAST_IP, config.PORT))
  print(f"Broadcast message sent to {config.BROADCAST_IP}:{config.PORT}")

if __name__ == "__main__":
  main()